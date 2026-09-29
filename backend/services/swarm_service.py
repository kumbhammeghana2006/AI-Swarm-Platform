import sys
import os
import time
from typing import Dict, Any, Optional

# Ensure project root is in sys.path for importing Phase 1 agents module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.workflow_graph import run_swarm

def execute_swarm_task(
    task_text: str,
    override_type: Optional[str] = None,
    configuration_type: str = "multi_agent"
) -> Dict[str, Any]:
    """
    Executes existing Phase 1 LangGraph swarm workflow and captures measurable evaluation metrics.
    Reuses existing run_swarm() function without duplicating agent logic.
    """
    if configuration_type != "multi_agent":
        raise ValueError(
            f"Configuration type '{configuration_type}' is not supported by swarm_service. "
            "Only 'multi_agent' swarm execution is active in this milestone."
        )

    start_time = time.perf_counter()
    try:
        final_state = run_swarm(task=task_text, override_type=override_type)
        elapsed_time = round(time.perf_counter() - start_time, 4)

        # Tester result determination
        passed = final_state.get("passed_tests")
        if passed is True:
            tester_result = "PASS"
        elif passed is False:
            tester_result = "FAIL"
        else:
            tester_result = "N/A"

        agents_used = final_state.get("agents_used", [])
        iteration_count = final_state.get("iteration_count", 1)
        task_type = final_state.get("task_type", override_type)

        return {
            "success": True,
            "final_state": final_state,
            "final_output": final_state.get("final_output", ""),
            "iteration_count": iteration_count,
            "execution_time_seconds": elapsed_time,
            "tester_result": tester_result,
            "agents_used": agents_used,
            "configuration_type": configuration_type,
            "task_type": task_type
        }
    except ValueError as ve:
        raise ve
    except Exception as e:
        elapsed_time = round(time.perf_counter() - start_time, 4)
        err_str = str(e)
        return {
            "success": False,
            "error": err_str,
            "final_output": f"Swarm Execution Failed: LLM inference service is currently unavailable or rate limited. Details: {err_str}",
            "iteration_count": 0,
            "execution_time_seconds": elapsed_time,
            "tester_result": "FAIL",
            "agents_used": [],
            "configuration_type": configuration_type,
            "task_type": override_type
        }

