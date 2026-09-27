import sys
import os
from typing import Dict, Any, Optional

# Ensure project root is in sys.path for importing Phase 1 agents module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.workflow_graph import run_swarm

def execute_swarm_task(task_text: str, override_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes existing Phase 1 LangGraph swarm workflow.
    Reuses existing run_swarm() function without duplicating agent logic.
    """
    try:
        final_state = run_swarm(task=task_text, override_type=override_type)
        return {
            "success": True,
            "final_state": final_state,
            "final_output": final_state.get("final_output", ""),
            "iteration_count": final_state.get("iteration_count", 1)
        }
    except ValueError as ve:
        raise ve
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "final_output": f"Swarm Execution Failed: {str(e)}",
            "iteration_count": 0
        }
