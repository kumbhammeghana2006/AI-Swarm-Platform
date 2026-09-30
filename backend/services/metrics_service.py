from typing import List, Dict, Any, Optional
from backend.database.models import Task

def calculate_metrics_summary(tasks: List[Task], scope: str = "user") -> Dict[str, Any]:
    """
    Calculates empirical evaluation and benchmark metrics across a collection of Task records.
    Safely handles empty task sets (zero tasks) without division-by-zero errors.
    """
    total_tasks = len(tasks)
    if total_tasks == 0:
        return {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0,
            "avg_execution_time_seconds": 0.0,
            "avg_iteration_count": 0.0,
            "tester_pass_count": 0,
            "tester_fail_count": 0,
            "tester_na_count": 0,
            "tester_pass_rate": 0.0,
            "tester_fail_rate": 0.0,
            "agent_usage_frequency": {},
            "task_type_distribution": {},
            "configuration_distribution": {},
            "scope": scope
        }

    successful_tasks = 0
    failed_tasks = 0
    total_execution_time = 0.0
    tasks_with_execution_time = 0
    total_iterations = 0
    tasks_with_iterations = 0

    tester_pass_count = 0
    tester_fail_count = 0
    tester_na_count = 0

    agent_usage_frequency: Dict[str, int] = {}
    task_type_distribution: Dict[str, int] = {}
    configuration_distribution: Dict[str, int] = {}

    for task in tasks:
        # Task Type Distribution
        t_type = task.task_type or "unclassified"
        task_type_distribution[t_type] = task_type_distribution.get(t_type, 0) + 1

        # Status counts
        res = task.result
        if res:
            if res.execution_status == "SUCCESS" or task.status == "COMPLETED":
                successful_tasks += 1
            else:
                failed_tasks += 1

            # Execution time
            if res.execution_time_seconds is not None:
                total_execution_time += res.execution_time_seconds
                tasks_with_execution_time += 1

            # Iteration count
            if res.iteration_count is not None:
                total_iterations += res.iteration_count
                tasks_with_iterations += 1

            # Tester results
            t_res = (res.tester_result or "").upper()
            if t_res == "PASS":
                tester_pass_count += 1
            elif t_res == "FAIL":
                tester_fail_count += 1
            else:
                tester_na_count += 1

            # Agents Used Frequency
            if res.agents_used and isinstance(res.agents_used, list):
                for agent_name in res.agents_used:
                    if agent_name:
                        agent_usage_frequency[agent_name] = agent_usage_frequency.get(agent_name, 0) + 1

            # Configuration Type Distribution
            cfg = res.configuration_type or "multi_agent"
            configuration_distribution[cfg] = configuration_distribution.get(cfg, 0) + 1
        else:
            if task.status == "COMPLETED":
                successful_tasks += 1
            elif task.status == "FAILED":
                failed_tasks += 1

    success_rate = round((successful_tasks / total_tasks) * 100.0, 2)
    avg_exec_time = (
        round(total_execution_time / tasks_with_execution_time, 2)
        if tasks_with_execution_time > 0
        else 0.0
    )
    avg_iterations = (
        round(total_iterations / tasks_with_iterations, 2)
        if tasks_with_iterations > 0
        else 0.0
    )

    total_tested = tester_pass_count + tester_fail_count
    tester_pass_rate = (
        round((tester_pass_count / total_tested) * 100.0, 2)
        if total_tested > 0
        else 0.0
    )
    tester_fail_rate = (
        round((tester_fail_count / total_tested) * 100.0, 2)
        if total_tested > 0
        else 0.0
    )

    return {
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "failed_tasks": failed_tasks,
        "success_rate": success_rate,
        "avg_execution_time_seconds": avg_exec_time,
        "avg_iteration_count": avg_iterations,
        "tester_pass_count": tester_pass_count,
        "tester_fail_count": tester_fail_count,
        "tester_na_count": tester_na_count,
        "tester_pass_rate": tester_pass_rate,
        "tester_fail_rate": tester_fail_rate,
        "agent_usage_frequency": agent_usage_frequency,
        "task_type_distribution": task_type_distribution,
        "configuration_distribution": configuration_distribution,
        "scope": scope
    }
