import os
import sys
import time
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
from agents.workflow_graph import run_swarm

# Set up in-memory SQLite engine for Phase 4 metrics testing
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

class TestPhase4EvaluationMetrics(unittest.TestCase):

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
        # Clear database tables between tests
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

    def _get_auth_headers(self, username="eval_user", email="eval@example.com", password="password123"):
        """Helper to register and login a user, returning Authorization Bearer headers."""
        self.client.post("/auth/register", json={
            "username": username,
            "email": email,
            "password": password,
            "role": "USER"
        })
        login_resp = self.client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @patch("backend.services.swarm_service.run_swarm")
    def test_successful_task_metrics_storage(self, mock_run_swarm):
        """
        Test 1: Successful task execution collects and stores all measurable evaluation metrics:
        - execution_status ('SUCCESS')
        - execution_time_seconds (> 0)
        - iteration_count
        - agents_used
        - tester_result ('PASS')
        - configuration_type ('multi_agent')
        Along with metadata: task_id, task_type, created_at.
        """
        mock_run_swarm.return_value = {
            "task": "Build full software feature",
            "task_type": "full_software",
            "final_output": "Generated code and documentation.",
            "iteration_count": 2,
            "passed_tests": True,
            "agents_used": ["Classifier", "Planner", "Researcher", "Coder", "Tester", "Reviewer", "Documentation"],
            "logs": []
        }

        headers = self._get_auth_headers("metric_user_1", "m1@example.com")
        payload = {
            "task_text": "Build full software feature",
            "task_type": "full_software"
        }
        response = self.client.post("/tasks", json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()

        # Metadata
        self.assertIn("id", data)
        self.assertEqual(data["task_type"], "full_software")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertIsNotNone(data["created_at"])

        # Evaluation Metrics on Result
        result = data["result"]
        self.assertIsNotNone(result)
        self.assertEqual(result["execution_status"], "SUCCESS")
        self.assertIsInstance(result["execution_time_seconds"], float)
        self.assertGreaterEqual(result["execution_time_seconds"], 0.0)
        self.assertEqual(result["iteration_count"], 2)
        self.assertEqual(result["tester_result"], "PASS")
        self.assertEqual(result["configuration_type"], "multi_agent")
        self.assertEqual(
            result["agents_used"],
            ["Classifier", "Planner", "Researcher", "Coder", "Tester", "Reviewer", "Documentation"]
        )

    @patch("backend.services.swarm_service.run_swarm")
    def test_failed_task_metrics_storage(self, mock_run_swarm):
        """
        Test 2: Preserves FAILED task records, error details, and failure metrics:
        - execution_status ('FAILED')
        - execution_time_seconds (> 0)
        - iteration_count (0)
        - tester_result ('FAIL')
        - configuration_type ('multi_agent')
        - Queryable via GET /tasks history.
        """
        mock_run_swarm.side_effect = RuntimeError("Hugging Face API inference rate limit reached")

        headers = self._get_auth_headers("metric_fail_user", "fail@example.com")
        payload = {"task_text": "Task destined to fail"}
        response = self.client.post("/tasks", json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertEqual(data["status"], "FAILED")
        result = data["result"]
        self.assertIsNotNone(result)
        self.assertEqual(result["execution_status"], "FAILED")
        self.assertIsInstance(result["execution_time_seconds"], float)
        self.assertGreaterEqual(result["execution_time_seconds"], 0.0)
        self.assertEqual(result["iteration_count"], 0)
        self.assertEqual(result["tester_result"], "FAIL")
        self.assertEqual(result["configuration_type"], "multi_agent")
        self.assertIn("Hugging Face API inference rate limit reached", result["final_output"])

        # Verify failed task is retained in GET /tasks history with its metrics
        history_resp = self.client.get("/tasks", headers=headers)
        self.assertEqual(history_resp.status_code, 200)
        history = history_resp.json()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "FAILED")
        self.assertEqual(history[0]["result"]["execution_status"], "FAILED")
        self.assertGreaterEqual(history[0]["result"]["execution_time_seconds"], 0.0)

    @patch("backend.services.swarm_service.run_swarm")
    def test_execution_time_recording(self, mock_run_swarm):
        """
        Test 3: Measures wall-clock execution time accurately around swarm execution.
        """
        def slow_swarm(*args, **kwargs):
            time.sleep(0.06)
            return {
                "task": "Slow task",
                "task_type": "code_only",
                "final_output": "Done after pause",
                "iteration_count": 1,
                "passed_tests": True,
                "agents_used": ["Classifier", "Planner", "Coder", "Tester", "Documentation"]
            }

        mock_run_swarm.side_effect = slow_swarm

        headers = self._get_auth_headers("time_user", "time@example.com")
        resp = self.client.post("/tasks", json={"task_text": "Slow task"}, headers=headers)
        self.assertEqual(resp.status_code, 201)
        result = resp.json()["result"]

        self.assertGreaterEqual(result["execution_time_seconds"], 0.05)

    @patch("backend.services.swarm_service.run_swarm")
    def test_iteration_count_recording(self, mock_run_swarm):
        """
        Test 4: Accurately records self-correction iteration count.
        """
        mock_run_swarm.return_value = {
            "task": "Iterative task",
            "task_type": "code_only",
            "final_output": "Fixed after 3 attempts",
            "iteration_count": 3,
            "passed_tests": True,
            "agents_used": ["Classifier", "Planner", "Coder", "Tester"]
        }

        headers = self._get_auth_headers("iter_user", "iter@example.com")
        resp = self.client.post("/tasks", json={"task_text": "Iterative task"}, headers=headers)
        self.assertEqual(resp.status_code, 201)
        result = resp.json()["result"]

        self.assertEqual(result["iteration_count"], 3)

    @patch("backend.services.swarm_service.run_swarm")
    def test_active_agents_recording(self, mock_run_swarm):
        """
        Test 5: Accurately records list of active agents participating in the workflow.
        """
        # Scenario A: doc_only workflow uses fewer agents
        mock_run_swarm.return_value = {
            "task": "Write documentation",
            "task_type": "doc_only",
            "final_output": "# API Docs",
            "iteration_count": 1,
            "passed_tests": None,
            "agents_used": ["Classifier", "Researcher", "Documentation"]
        }

        headers = self._get_auth_headers("agent_user", "agent@example.com")
        resp = self.client.post("/tasks", json={"task_text": "Write documentation", "task_type": "doc_only"}, headers=headers)
        self.assertEqual(resp.status_code, 201)
        result = resp.json()["result"]

        self.assertEqual(result["agents_used"], ["Classifier", "Researcher", "Documentation"])
        self.assertEqual(len(result["agents_used"]), 3)

    @patch("backend.services.swarm_service.run_swarm")
    def test_tester_pass_fail_recording(self, mock_run_swarm):
        """
        Test 6: Accurately records tester result mapping:
        - True -> 'PASS'
        - False -> 'FAIL'
        - None / not applicable -> 'N/A'
        """
        headers = self._get_auth_headers("tester_user", "tester@example.com")

        # 6a. Passed tests
        mock_run_swarm.return_value = {
            "task": "Test task 1",
            "task_type": "code_only",
            "final_output": "code",
            "iteration_count": 1,
            "passed_tests": True,
            "agents_used": ["Classifier", "Tester"]
        }
        resp1 = self.client.post("/tasks", json={"task_text": "Test 1"}, headers=headers)
        self.assertEqual(resp1.json()["result"]["tester_result"], "PASS")

        # 6b. Failed tests
        mock_run_swarm.return_value = {
            "task": "Test task 2",
            "task_type": "code_only",
            "final_output": "code",
            "iteration_count": 3,
            "passed_tests": False,
            "agents_used": ["Classifier", "Tester"]
        }
        resp2 = self.client.post("/tasks", json={"task_text": "Test 2"}, headers=headers)
        self.assertEqual(resp2.json()["result"]["tester_result"], "FAIL")

        # 6c. Not applicable (e.g. doc_only)
        mock_run_swarm.return_value = {
            "task": "Test task 3",
            "task_type": "doc_only",
            "final_output": "docs",
            "iteration_count": 1,
            "passed_tests": None,
            "agents_used": ["Classifier", "Documentation"]
        }
        resp3 = self.client.post("/tasks", json={"task_text": "Test 3"}, headers=headers)
        self.assertEqual(resp3.json()["result"]["tester_result"], "N/A")

    @patch("backend.services.swarm_service.run_swarm")
    def test_configuration_type_default_and_single_agent_rejection(self, mock_run_swarm):
        """
        Test 7: Supports configuration_type metric for single-agent vs multi-agent comparison:
        - Defaults to 'multi_agent' when omitted
        - Stored as 'multi_agent' in DB and returned in API response
        - Explicit 'single_agent' request is rejected (not executed as multi-agent swarm or fake-labeled)
        - Confirms swarm execution is never invoked for single_agent
        """
        mock_run_swarm.return_value = {
            "task": "Benchmark task",
            "task_type": "code_only",
            "final_output": "Multi-agent output",
            "iteration_count": 1,
            "passed_tests": True,
            "agents_used": ["Classifier", "Coder", "Tester"]
        }

        headers = self._get_auth_headers("config_user", "config@example.com")

        # 7a. Default configuration_type -> 'multi_agent' succeeds
        resp_default = self.client.post("/tasks", json={"task_text": "Default config task"}, headers=headers)
        self.assertEqual(resp_default.status_code, 201)
        self.assertEqual(resp_default.json()["result"]["configuration_type"], "multi_agent")
        self.assertEqual(mock_run_swarm.call_count, 1)

        # 7b. Explicit single_agent configuration_type is rejected with validation error
        resp_single = self.client.post("/tasks", json={
            "task_text": "Single agent benchmark task",
            "configuration_type": "single_agent"
        }, headers=headers)
        # Rejected by FastAPI / Pydantic validation (422) as not currently supported
        self.assertEqual(resp_single.status_code, 422)
        err_detail = str(resp_single.json())
        self.assertIn("single_agent", err_detail)
        self.assertIn("not currently supported", err_detail)

        # Swarm execution was NOT called again (call_count remains 1)
        self.assertEqual(mock_run_swarm.call_count, 1)

        # 7c. Direct service call with single_agent also raises HTTPException (defense-in-depth)
        from fastapi import HTTPException
        from backend.services import task_service
        db = TestingSessionLocal()
        try:
            from backend.database import crud
            test_user = crud.get_user_by_username(db, "config_user")
            with self.assertRaises(HTTPException) as cm:
                task_service.create_and_execute_task(
                    db=db,
                    user=test_user,
                    task_text="Direct single_agent call",
                    configuration_type="single_agent"
                )
            self.assertEqual(cm.exception.status_code, 400)
            self.assertIn("not currently supported", cm.exception.detail)
        finally:
            db.close()

        # Swarm execution was still NOT called
        self.assertEqual(mock_run_swarm.call_count, 1)

    @patch("agents.base_agent.BaseAgent.call_llm")
    def test_live_workflow_graph_agent_tracking(self, mock_call_llm):
        """
        Test 8: Verifies LangGraph workflow dynamically tracks agents in agents_used
        without calling external Hugging Face inference API.
        """
        mock_call_llm.return_value = "Mocked LLM Response for Doc Only"
        
        # doc_only routes: classifier_node -> researcher_node -> documentation_node -> output_node
        result = run_swarm("Generate API documentation for endpoints", override_type="doc_only")
        
        self.assertIn("agents_used", result)
        agents = result["agents_used"]
        # Verify Classifier, Researcher, and Documentation were dynamically recorded
        self.assertIn("Classifier", agents)
        self.assertIn("Researcher", agents)
        self.assertIn("Documentation", agents)
        # Verify Coder and Tester were NOT recorded (dynamic routing isolation)
        self.assertNotIn("Coder", agents)
        self.assertNotIn("Tester", agents)

if __name__ == "__main__":
    unittest.main()
