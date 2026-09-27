import unittest
from unittest.mock import patch
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.rag_engine import LightweightRAG
from agents.swarm_state import SwarmState
from agents.workflow_graph import (
    route_after_classifier,
    route_after_planner,
    route_after_researcher,
    route_after_tester,
    route_after_reviewer,
    run_swarm
)
from agents.planner_agent import PlannerAgent
from agents.coordinator_agent import CoordinatorAgent

class TestPhase1Swarm(unittest.TestCase):

    def setUp(self):
        self.rag = LightweightRAG()

    def test_rag_retrieval(self):
        """Test local RAG engine indexes documents and retrieves relevant context."""
        context = self.rag.retrieve_context("FastAPI REST API")
        self.assertIn("FastAPI", context)
        
        context_python = self.rag.retrieve_context("Python best practices docstring")
        self.assertTrue(len(context_python) > 0)

    def test_classifier_routing(self):
        """Test classifier conditional routing for all 5 categories."""
        # doc_only -> researcher_node
        self.assertEqual(route_after_classifier({"task_type": "doc_only"}), "researcher_node")

        # code_only -> planner_node
        self.assertEqual(route_after_classifier({"task_type": "code_only"}), "planner_node")

        # testing_analysis -> tester_node
        self.assertEqual(route_after_classifier({"task_type": "testing_analysis"}), "tester_node")

        # research_explanation -> researcher_node
        self.assertEqual(route_after_classifier({"task_type": "research_explanation"}), "researcher_node")

        # full_software -> planner_node
        self.assertEqual(route_after_classifier({"task_type": "full_software"}), "planner_node")

    def test_planner_routing(self):
        """Test planner routing for code_only vs full_software."""
        self.assertEqual(route_after_planner({"task_type": "code_only"}), "coder_node")
        self.assertEqual(route_after_planner({"task_type": "full_software"}), "researcher_node")

    def test_researcher_routing(self):
        """Test researcher conditional routing."""
        self.assertEqual(route_after_researcher({"task_type": "doc_only"}), "documentation_node")
        self.assertEqual(route_after_researcher({"task_type": "research_explanation"}), "documentation_node")
        self.assertEqual(route_after_researcher({"task_type": "full_software"}), "coder_node")

    def test_tester_routing(self):
        """Test tester conditional routing and max 3 iteration limit."""
        # full_software + FAIL + iteration 1 -> coder_node
        self.assertEqual(route_after_tester({"passed_tests": False, "iteration_count": 1, "task_type": "full_software"}), "coder_node")

        # full_software + FAIL + iteration 2 -> coder_node
        self.assertEqual(route_after_tester({"passed_tests": False, "iteration_count": 2, "task_type": "full_software"}), "coder_node")

        # full_software + FAIL + iteration 3 -> reviewer_node (caps at max 3 iterations)
        self.assertEqual(route_after_tester({"passed_tests": False, "iteration_count": 3, "task_type": "full_software"}), "reviewer_node")

        # full_software + PASS -> reviewer_node
        self.assertEqual(route_after_tester({"passed_tests": True, "iteration_count": 1, "task_type": "full_software"}), "reviewer_node")

        # code_only + PASS -> reviewer_node
        self.assertEqual(route_after_tester({"passed_tests": True, "iteration_count": 1, "task_type": "code_only"}), "reviewer_node")

        # code_only + FAIL + iteration < 3 -> coder_node
        self.assertEqual(route_after_tester({"passed_tests": False, "iteration_count": 1, "task_type": "code_only"}), "coder_node")
        self.assertEqual(route_after_tester({"passed_tests": False, "iteration_count": 2, "task_type": "code_only"}), "coder_node")

        # testing_analysis -> output_node
        self.assertEqual(route_after_tester({"passed_tests": True, "iteration_count": 1, "task_type": "testing_analysis"}), "output_node")
        self.assertEqual(route_after_tester({"passed_tests": False, "iteration_count": 1, "task_type": "testing_analysis"}), "output_node")

    def test_reviewer_routing(self):
        """Test reviewer conditional routing (code_only and full_software both route to documentation_node)."""
        self.assertEqual(route_after_reviewer({"task_type": "code_only"}), "documentation_node")
        self.assertEqual(route_after_reviewer({"task_type": "full_software"}), "documentation_node")

    @patch("agents.base_agent.BaseAgent.call_llm")
    def test_documentation_agent_context_usage(self, mock_call_llm):
        """Test DocumentationAgent accepts and incorporates research notes and RAG context."""
        mock_call_llm.return_value = "Mocked Documentation Output"
        from agents.documentation_agent import DocumentationAgent
        from agents.workflow_graph import documentation_node

        doc_agent = DocumentationAgent()
        docs = doc_agent.generate_docs(
            task="Write API docs",
            code="def foo(): pass",
            review_notes="Code looks good",
            research_notes="Sample research notes",
            rag_context="Sample RAG context"
        )
        self.assertTrue(len(docs) > 0)

        # Test documentation_node execution with research context in SwarmState
        state = {
            "task": "Write API docs",
            "code": "def foo(): pass",
            "review_notes": "Code looks good",
            "research_notes": "Sample research notes",
            "rag_context": "Sample RAG context",
            "logs": []
        }
        res = documentation_node(state)
        self.assertIn("documentation", res)
        self.assertTrue(len(res["documentation"]) > 0)

    @patch("agents.base_agent.BaseAgent.call_llm")
    def test_override_type_behavior(self, mock_call_llm):
        """Test override_type bypasses LLM classification and raises ValueError for invalid keys without requiring HF API credits."""
        mock_call_llm.return_value = "Mocked LLM Response"
        # Valid override_type
        result = run_swarm("Write a function to add numbers", override_type="doc_only")
        self.assertEqual(result.get("task_type"), "doc_only")
        self.assertIn("documentation", result)
        self.assertIn("research_notes", result)

        # Invalid override_type raises ValueError
        with self.assertRaises(ValueError):
            run_swarm("Some task", override_type="invalid_category")

    def test_existing_agents_preserved(self):
        """Test existing PlannerAgent and CoordinatorAgent instantiate cleanly."""
        planner = PlannerAgent()
        self.assertTrue(hasattr(planner, "create_plan"))

        coordinator = CoordinatorAgent()
        self.assertTrue(hasattr(coordinator, "coordinate"))

if __name__ == "__main__":
    unittest.main()

