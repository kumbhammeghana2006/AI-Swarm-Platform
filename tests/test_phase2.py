import os
import sys
import unittest
from unittest.mock import patch

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

# Set up in-memory SQLite engine for testing
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

# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

class TestPhase2Backend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

    def setUp(self):
        self.client = TestClient(app)
        # Clear table rows between tests for clean isolation
        db = TestingSessionLocal()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.commit()
        finally:
            db.close()

    def test_health_endpoint(self):
        """Test public health endpoint returns 200 OK and expected status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("service", data)

    def test_user_registration(self):
        """Test new user registration."""
        payload = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "password123",
            "role": "USER"
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "testuser@example.com")
        self.assertEqual(data["role"], "USER")
        self.assertNotIn("hashed_password", data)

    def test_duplicate_user_registration(self):
        """Test registration fails with 400 for duplicate username or email."""
        payload = {
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "password123"
        }
        resp1 = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp1.status_code, 201)

        # Duplicate username
        resp2 = self.client.post("/auth/register", json={
            "username": "dupuser",
            "email": "other@example.com",
            "password": "password123"
        })
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Username already registered", resp2.json()["detail"])

        # Duplicate email
        resp3 = self.client.post("/auth/register", json={
            "username": "otheruser",
            "email": "dup@example.com",
            "password": "password123"
        })
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("Email already registered", resp3.json()["detail"])

    def test_login_success_and_invalid(self):
        """Test login with valid credentials returns JWT token, invalid credentials fail with 401."""
        # Register user
        reg_payload = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "secretpassword"
        }
        self.client.post("/auth/register", json=reg_payload)

        # Valid login
        login_resp = self.client.post("/auth/login", json={
            "username": "loginuser",
            "password": "secretpassword"
        })
        self.assertEqual(login_resp.status_code, 200)
        token_data = login_resp.json()
        self.assertIn("access_token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")

        # Invalid login password
        bad_resp = self.client.post("/auth/login", json={
            "username": "loginuser",
            "password": "wrongpassword"
        })
        self.assertEqual(bad_resp.status_code, 401)

    def test_protected_endpoint_unauthorized(self):
        """Test accessing protected /tasks without JWT header returns 401."""
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 401)

    @patch("backend.services.swarm_service.run_swarm")
    def test_task_creation_and_mocked_swarm_integration(self, mock_run_swarm):
        """Test task creation triggers mocked swarm execution and persists Task & TaskResult."""
        mock_run_swarm.return_value = {
            "task": "Write python print script",
            "task_type": "code_only",
            "final_output": "# Swarm Platform Result [CODE_ONLY]\n\n## Generated Code\nprint('hello')",
            "iteration_count": 1,
            "logs": ["[Mocked Node] Completed"]
        }

        # Register and login user
        self.client.post("/auth/register", json={
            "username": "coder",
            "email": "coder@example.com",
            "password": "password123"
        })
        login_res = self.client.post("/auth/login", json={
            "username": "coder",
            "password": "password123"
        }).json()
        token = login_res["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        task_payload = {
            "task_text": "Write python print script",
            "task_type": "code_only"
        }
        response = self.client.post("/tasks", json=task_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["task_text"], "Write python print script")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertIsNotNone(data["result"])
        self.assertEqual(data["result"]["execution_status"], "SUCCESS")
        self.assertIn("Generated Code", data["result"]["final_output"])
        
        # Verify run_swarm was called with expected task and override_type
        mock_run_swarm.assert_called_once_with(task="Write python print script", override_type="code_only")

    @patch("backend.services.swarm_service.run_swarm")
    def test_task_history_isolation(self, mock_run_swarm):
        """Test task history isolation between different users."""
        mock_run_swarm.return_value = {
            "task": "Sample task",
            "task_type": "doc_only",
            "final_output": "Sample output for isolation test",
            "iteration_count": 1,
            "logs": []
        }

        # Create User A
        self.client.post("/auth/register", json={"username": "usera", "email": "a@ex.com", "password": "pass"})
        token_a = self.client.post("/auth/login", json={"username": "usera", "password": "pass"}).json()["access_token"]

        # Create User B
        self.client.post("/auth/register", json={"username": "userb", "email": "b@ex.com", "password": "pass"})
        token_b = self.client.post("/auth/login", json={"username": "userb", "password": "pass"}).json()["access_token"]

        # User A creates a task
        self.client.post("/tasks", json={"task_text": "Task A"}, headers={"Authorization": f"Bearer {token_a}"})
        
        # User B creates a task
        self.client.post("/tasks", json={"task_text": "Task B"}, headers={"Authorization": f"Bearer {token_b}"})

        # User A fetches history
        resp_a = self.client.get("/tasks", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(resp_a.status_code, 200)
        tasks_a = resp_a.json()
        self.assertEqual(len(tasks_a), 1)
        self.assertEqual(tasks_a[0]["task_text"], "Task A")

        # User B fetches history
        resp_b = self.client.get("/tasks", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(resp_b.status_code, 200)
        tasks_b = resp_b.json()
        self.assertEqual(len(tasks_b), 1)
        self.assertEqual(tasks_b[0]["task_text"], "Task B")

    @patch("backend.services.swarm_service.run_swarm")
    def test_admin_authorization(self, mock_run_swarm):
        """Test ADMIN users can access system-wide tasks while USER receives 403 Forbidden."""
        mock_run_swarm.return_value = {
            "task": "Admin task",
            "task_type": "doc_only",
            "final_output": "Admin output",
            "iteration_count": 1,
            "logs": []
        }

        # Create normal USER
        self.client.post("/auth/register", json={"username": "normaluser", "email": "n@ex.com", "password": "pass", "role": "USER"})
        user_token = self.client.post("/auth/login", json={"username": "normaluser", "password": "pass"}).json()["access_token"]

        # Create ADMIN user
        self.client.post("/auth/register", json={"username": "adminuser", "email": "admin@ex.com", "password": "pass", "role": "ADMIN"})
        admin_token = self.client.post("/auth/login", json={"username": "adminuser", "password": "pass"}).json()["access_token"]

        # Normal user creates task
        self.client.post("/tasks", json={"task_text": "Normal task"}, headers={"Authorization": f"Bearer {user_token}"})

        # Normal user tries to access /admin/tasks -> 403 Forbidden
        resp_forbidden = self.client.get("/admin/tasks", headers={"Authorization": f"Bearer {user_token}"})
        self.assertEqual(resp_forbidden.status_code, 403)

        # Admin accesses /admin/tasks -> 200 OK with all tasks
        resp_admin = self.client.get("/admin/tasks", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(resp_admin.status_code, 200)
        self.assertGreaterEqual(len(resp_admin.json()), 1)

    @patch("backend.services.swarm_service.run_swarm")
    def test_task_execution_llm_failure_handling(self, mock_run_swarm):
        """Test task creation handles LLM failures cleanly and persists FAILED status."""
        mock_run_swarm.side_effect = RuntimeError("LLM request failed. Please check network or HF_TOKEN permissions.")

        # Register and login user
        self.client.post("/auth/register", json={
            "username": "failuser",
            "email": "fail@example.com",
            "password": "password123"
        })
        login_res = self.client.post("/auth/login", json={
            "username": "failuser",
            "password": "password123"
        }).json()
        token = login_res["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        task_payload = {"task_text": "Task expecting failure"}
        response = self.client.post("/tasks", json=task_payload, headers=headers)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["task_text"], "Task expecting failure")
        self.assertEqual(data["status"], "FAILED")
        self.assertIsNotNone(data["result"])
        self.assertEqual(data["result"]["execution_status"], "FAILED")
        self.assertIn("LLM inference service is currently unavailable or rate limited", data["result"]["final_output"])

    @patch("backend.services.swarm_service.run_swarm")
    def test_task_history_stores_both_completed_and_failed_statuses(self, mock_run_swarm):
        """Test task history correctly stores and returns both COMPLETED and FAILED task statuses."""
        mock_run_swarm.side_effect = [
            {
                "task": "Successful task",
                "task_type": "code_only",
                "final_output": "Success result",
                "iteration_count": 1,
                "logs": []
            },
            RuntimeError("Rate limit exceeded")
        ]

        self.client.post("/auth/register", json={"username": "mixeduser", "email": "mixed@ex.com", "password": "pass"})
        token = self.client.post("/auth/login", json={"username": "mixeduser", "password": "pass"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create successful task
        self.client.post("/tasks", json={"task_text": "Successful task"}, headers=headers)
        # 2. Create failed task
        self.client.post("/tasks", json={"task_text": "Failing task"}, headers=headers)

        # 3. Retrieve history
        resp = self.client.get("/tasks", headers=headers)
        self.assertEqual(resp.status_code, 200)
        history = resp.json()
        self.assertEqual(len(history), 2)

        statuses = [t["status"] for t in history]
        self.assertIn("COMPLETED", statuses)
        self.assertIn("FAILED", statuses)

if __name__ == "__main__":
    unittest.main()

