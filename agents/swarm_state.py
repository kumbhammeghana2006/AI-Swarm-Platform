from typing import TypedDict, List, Dict, Any, Optional

class SwarmState(TypedDict, total=False):
    """
    Shared state object passed between specialized agents in LangGraph workflow engine.
    """
    task: str
    task_type: str  # 'doc_only', 'code_only', 'testing_analysis', 'research_explanation', 'full_software'
    plan: str
    research_notes: str
    rag_context: str
    code: str
    test_results: str
    passed_tests: bool
    feedback: str
    iteration_count: int
    review_notes: str
    documentation: str
    final_output: str
    agents_used: List[str]
    logs: List[str]
    # Evaluation and ablation metrics fields
    configuration_type: str
    execution_time_seconds: float
    tester_result: str

