import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.connection import Base, get_db
from backend.services.metrics_service import calculate_metrics_summary
from backend.experiments.ablation import (
    get_registered_experiments,
    get_active_configuration,
    is_configuration_executable
)
from agents.rag_engine import LightweightRAG
from agents.coder_agent import CoderAgent

# Set up in-memory SQLite engine
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestPhase4AblationAndAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    def setUp(self):
        self._orig_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        db = TestingSessionLocal()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        if self._orig_override is not None:
            app.dependency_overrides[get_db] = self._orig_override
        else:
            app.dependency_overrides.pop(get_db, None)

    def _get_auth_headers(self, username="eval_user", email="eval@example.com", password="password123", role="USER"):
        """Helper to register and login a user, returning Authorization Bearer headers."""
        self.client.post("/auth/register", json={
            "username": username,
            "email": email,
            "password": password,
            "role": role
        })
        login_resp = self.client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_bm25_rag_scoring_and_metadata(self):
        """Test BM25 RAG engine indexes documents, provides relevance scores and metadata."""
        rag = LightweightRAG()
        meta = rag.retrieve_with_metadata("FastAPI REST endpoints and routing", top_k=2)

        self.assertIn("context", meta)
        self.assertIn("chunks", meta)
        self.assertIn("retrieved_documents", meta)
        self.assertIsInstance(meta["top_score"], float)
        self.assertGreater(meta["top_score"], 0.0)
        self.assertIn("FastAPI", meta["context"])
        self.assertTrue(len(meta["retrieved_documents"]) > 0)

        # Test empty query / no matches
        empty_meta = rag.retrieve_with_metadata("xyznonexistentword999999", top_k=2)
        self.assertEqual(empty_meta["top_score"], 0.0)
        self.assertEqual(len(empty_meta["chunks"]), 0)

    @patch("agents.base_agent.BaseAgent.call_llm")
    def test_coder_agent_self_correction_context(self, mock_call_llm):
        """Test CoderAgent includes previous code, test results, and feedback during iteration."""
        mock_call_llm.return_value = "def fixed_code(): return True"
        coder = CoderAgent()

        code = coder.generate_code(
            task="Write math parser",
            plan="1. Tokenize. 2. Parse.",
            research_notes="Use shunting-yard algorithm",
            feedback="Fix ZeroDivisionError handling",
            iteration=2,
            previous_code="def parse(): return 1 / 0",
            test_results="FAILED: ZeroDivisionError encountered",
            rag_context="RAG: Always catch ZeroDivisionError"
        )
        self.assertEqual(code, "def fixed_code(): return True")

        # Verify prompt passed to call_llm contained all self-correction elements
        call_args = mock_call_llm.call_args[0]
        user_prompt = call_args[1]
        self.assertIn("ITERATION #2 (SELF-CORRECTION)", user_prompt)
        self.assertIn("def parse(): return 1 / 0", user_prompt)
        self.assertIn("ZeroDivisionError encountered", user_prompt)
        self.assertIn("Fix ZeroDivisionError handling", user_prompt)
        self.assertIn("RAG: Always catch ZeroDivisionError", user_prompt)

    def test_experiment_config_ablation_matrix(self):
        """Test experiment abstraction exposes active configuration and planned ablations."""
        configs = get_registered_experiments()
        self.assertEqual(len(configs), 4)

        names = [c["name"] for c in configs]
        self.assertIn("multi_agent_full", names)
        self.assertIn("multi_agent_no_rag", names)
        self.assertIn("multi_agent_no_correction", names)
        self.assertIn("single_agent_baseline", names)

        active = get_active_configuration()
        self.assertEqual(active.name, "multi_agent_full")
        self.assertTrue(active.is_executable)

        # Confirm single_agent is marked as non-executable
        self.assertFalse(is_configuration_executable("single_agent"))
        self.assertTrue(is_configuration_executable("multi_agent"))

    def test_metrics_service_empty_tasks(self):
        """Test metrics calculation handles zero tasks safely without divide-by-zero."""
        summary = calculate_metrics_summary([], scope="user")
        self.assertEqual(summary["total_tasks"], 0)
        self.assertEqual(summary["successful_tasks"], 0)
        self.assertEqual(summary["failed_tasks"], 0)
        self.assertEqual(summary["success_rate"], 0.0)
        self.assertEqual(summary["avg_execution_time_seconds"], 0.0)
        self.assertEqual(summary["avg_iteration_count"], 0.0)
        self.assertEqual(summary["tester_pass_rate"], 0.0)
        self.assertEqual(summary["agent_usage_frequency"], {})

    @patch("backend.services.swarm_service.run_swarm")
    def test_metrics_api_user_isolation(self, mock_run_swarm):
        """Test GET /tasks/metrics/summary returns only the requesting user's metrics."""
        mock_run_swarm.side_effect = [
            # User A task 1 (Success)
            {
                "task": "Task 1 User A",
                "task_type": "code_only",
                "final_output": "code output",
                "iteration_count": 1,
                "passed_tests": True,
                "agents_used": ["Classifier", "Coder", "Tester"],
                "logs": []
            },
            # User B task 1 (Failed task execution)
            RuntimeError("Inference rate limit reached")
        ]


        headers_a = self._get_auth_headers("user_metrics_a", "ma@example.com")
        headers_b = self._get_auth_headers("user_metrics_b", "mb@example.com")

        # User A creates task
        self.client.post("/tasks", json={"task_text": "Task A"}, headers=headers_a)
        # User B creates task
        self.client.post("/tasks", json={"task_text": "Task B"}, headers=headers_b)

        # User A metrics summary
        resp_a = self.client.get("/tasks/metrics/summary", headers=headers_a)
        self.assertEqual(resp_a.status_code, 200)
        metrics_a = resp_a.json()
        self.assertEqual(metrics_a["total_tasks"], 1)
        self.assertEqual(metrics_a["successful_tasks"], 1)
        self.assertEqual(metrics_a["failed_tasks"], 0)
        self.assertEqual(metrics_a["success_rate"], 100.0)
        self.assertEqual(metrics_a["tester_pass_count"], 1)
        self.assertEqual(metrics_a["scope"], "user")
        self.assertIn("Coder", metrics_a["agent_usage_frequency"])

        # User B metrics summary
        resp_b = self.client.get("/tasks/metrics/summary", headers=headers_b)
        self.assertEqual(resp_b.status_code, 200)
        metrics_b = resp_b.json()
        self.assertEqual(metrics_b["total_tasks"], 1)
        self.assertEqual(metrics_b["successful_tasks"], 0)
        self.assertEqual(metrics_b["failed_tasks"], 1)
        self.assertEqual(metrics_b["agent_usage_frequency"], {})
        self.assertEqual(metrics_b["success_rate"], 0.0)


    @patch("backend.services.swarm_service.run_swarm")
    def test_admin_metrics_global_aggregation(self, mock_run_swarm):
        """Test ADMIN can view global system-wide metrics across all users."""
        mock_run_swarm.side_effect = [
            {"task": "T1", "task_type": "code_only", "final_output": "out1", "iteration_count": 1, "passed_tests": True, "agents_used": ["Classifier", "Coder", "Tester"], "logs": []},
            {"task": "T2", "task_type": "doc_only", "final_output": "out2", "iteration_count": 1, "passed_tests": True, "agents_used": ["Classifier", "Documentation"], "logs": []}
        ]

        headers_u = self._get_auth_headers("regular_user", "reg@example.com")
        headers_adm = self._get_auth_headers("super_admin", "adm@example.com", role="ADMIN")

        # Regular user creates a task
        self.client.post("/tasks", json={"task_text": "User Task"}, headers=headers_u)
        # Admin creates a task
        self.client.post("/tasks", json={"task_text": "Admin Task"}, headers=headers_adm)

        # Admin calls /tasks/metrics/summary -> receives global aggregation (2 tasks)
        resp_global = self.client.get("/tasks/metrics/summary", headers=headers_adm)
        self.assertEqual(resp_global.status_code, 200)
        self.assertEqual(resp_global.json()["total_tasks"], 2)
        self.assertEqual(resp_global.json()["scope"], "global")

        # Admin calls /admin/metrics/summary -> 200 OK
        resp_adm_endpoint = self.client.get("/admin/metrics/summary", headers=headers_adm)
        self.assertEqual(resp_adm_endpoint.status_code, 200)
        self.assertEqual(resp_adm_endpoint.json()["total_tasks"], 2)

        # Regular user calls /admin/metrics/summary -> 403 Forbidden
        resp_forbidden = self.client.get("/admin/metrics/summary", headers=headers_u)
        self.assertEqual(resp_forbidden.status_code, 403)

    def test_experiment_configurations_api(self):
        """Test GET /tasks/experiments/configurations returns registered ablation options."""
        headers = self._get_auth_headers("exp_user", "exp@example.com")
        resp = self.client.get("/tasks/experiments/configurations", headers=headers)
        self.assertEqual(resp.status_code, 200)
        configs = resp.json()
        self.assertEqual(len(configs), 4)
        config_names = [c["name"] for c in configs]
        self.assertIn("multi_agent_full", config_names)
        self.assertIn("single_agent_baseline", config_names)

    def test_metrics_api_unauthorized(self):
        """Test accessing metrics endpoint without authentication token returns 401."""
        resp = self.client.get("/tasks/metrics/summary")
        self.assertEqual(resp.status_code, 401)

if __name__ == "__main__":
    unittest.main()
