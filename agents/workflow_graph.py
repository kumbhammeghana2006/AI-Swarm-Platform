from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from agents.swarm_state import SwarmState
from agents.base_agent import BaseAgent
from agents.planner_agent import PlannerAgent
from agents.researcher_agent import ResearcherAgent
from agents.coder_agent import CoderAgent
from agents.tester_agent import TesterAgent
from agents.reviewer_agent import ReviewerAgent
from agents.documentation_agent import DocumentationAgent

# Instantiate agent instances
planner_agent = PlannerAgent()
researcher_agent = ResearcherAgent()
coder_agent = CoderAgent()
tester_agent = TesterAgent()
reviewer_agent = ReviewerAgent()
documentation_agent = DocumentationAgent()
base_agent = BaseAgent()

VALID_TASK_TYPES = {
    "doc_only",
    "code_only",
    "testing_analysis",
    "research_explanation",
    "full_software"
}

def classifier_node(state: SwarmState) -> Dict[str, Any]:
    """Classifies user task into one of 5 supported categories, or uses explicit override_type if set."""
    task = state.get("task", "")
    existing_type = state.get("task_type")
    agents = list(state.get("agents_used") or [])
    if "Classifier" not in agents:
        agents.append("Classifier")

    # If override_type was provided and valid, skip LLM classification
    if existing_type in VALID_TASK_TYPES:
        logs = state.get("logs", [])
        logs.append(f"[Classifier Node] Task type override active: '{existing_type}'")
        return {
            "task_type": existing_type,
            "iteration_count": 0,
            "agents_used": agents,
            "logs": logs
        }
    
    system_prompt = (
        "You are the Dynamic Task Classifier in an AI Swarm platform.\n"
        "Analyze the user's task and classify it strictly into ONE of the following 5 categories:\n"
        "1. doc_only - User only wants documentation, guides, or API specs.\n"
        "2. code_only - User wants code generation/implementation without full software lifecycle planning.\n"
        "3. testing_analysis - User wants code testing, bug analysis, or code inspection.\n"
        "4. research_explanation - User wants research, explanation, or concept study.\n"
        "5. full_software - User wants full end-to-end software development (planning, research, coding, testing, review, docs).\n\n"
        "Respond ONLY with the category key: doc_only, code_only, testing_analysis, research_explanation, or full_software."
    )
    
    classification = base_agent.call_llm(system_prompt, f"Task: {task}", temperature=0.0).strip().lower()
    
    selected_type = "full_software"
    for cat in VALID_TASK_TYPES:
        if cat in classification:
            selected_type = cat
            break

    logs = state.get("logs", [])
    logs.append(f"[Classifier Node] Classified task as: '{selected_type}'")
    
    return {
        "task_type": selected_type,
        "iteration_count": 0,
        "agents_used": agents,
        "logs": logs
    }

def planner_node(state: SwarmState) -> Dict[str, Any]:
    """Generates execution plan using PlannerAgent."""
    task = state.get("task", "")
    plan = planner_agent.create_plan(task)
    
    agents = list(state.get("agents_used") or [])
    if "Planner" not in agents:
        agents.append("Planner")
        
    logs = state.get("logs", [])
    logs.append("[Planner Node] Created step-by-step execution plan.")
    
    return {
        "plan": plan,
        "agents_used": agents,
        "logs": logs
    }

def researcher_node(state: SwarmState) -> Dict[str, Any]:
    """Gathers context via local RAG and generates research notes."""
    task = state.get("task", "")
    plan = state.get("plan", "")
    res = researcher_agent.research(task, plan)
    
    agents = list(state.get("agents_used") or [])
    if "Researcher" not in agents:
        agents.append("Researcher")
        
    logs = state.get("logs", [])
    logs.append("[Researcher Node] Completed research & local RAG context retrieval.")
    
    return {
        "research_notes": res["research_notes"],
        "rag_context": res["rag_context"],
        "agents_used": agents,
        "logs": logs
    }

def coder_node(state: SwarmState) -> Dict[str, Any]:
    """Generates implementation code, incorporating feedback if in iteration loop."""
    task = state.get("task", "")
    plan = state.get("plan", "")
    research_notes = state.get("research_notes", "")
    feedback = state.get("feedback", "")
    current_iter = state.get("iteration_count", 0) + 1
    
    code = coder_agent.generate_code(
        task=task,
        plan=plan,
        research_notes=research_notes,
        feedback=feedback,
        iteration=current_iter
    )
    
    agents = list(state.get("agents_used") or [])
    if "Coder" not in agents:
        agents.append("Coder")
        
    logs = state.get("logs", [])
    logs.append(f"[Coder Node] Generated code (Iteration #{current_iter}).")
    
    return {
        "code": code,
        "iteration_count": current_iter,
        "agents_used": agents,
        "logs": logs
    }

def tester_node(state: SwarmState) -> Dict[str, Any]:
    """Evaluates code syntactically & logically."""
    task = state.get("task", "")
    code = state.get("code", "")
    
    # If testing_analysis workflow and no prior code was supplied in state, use state task as code reference
    if not code and state.get("task_type") == "testing_analysis":
        code = task
        
    res = tester_agent.test_code(task, code)
    
    agents = list(state.get("agents_used") or [])
    if "Tester" not in agents:
        agents.append("Tester")
        
    logs = state.get("logs", [])
    logs.append(f"[Tester Node] Test outcome: Passed={res['passed_tests']}.")
    
    return {
        "passed_tests": res["passed_tests"],
        "test_results": res["test_results"],
        "feedback": res["feedback"],
        "agents_used": agents,
        "logs": logs
    }

def reviewer_node(state: SwarmState) -> Dict[str, Any]:
    """Performs comprehensive code review."""
    task = state.get("task", "")
    code = state.get("code", "")
    test_results = state.get("test_results", "")
    
    review_notes = reviewer_agent.review(task, code, test_results)
    
    agents = list(state.get("agents_used") or [])
    if "Reviewer" not in agents:
        agents.append("Reviewer")
        
    logs = state.get("logs", [])
    logs.append("[Reviewer Node] Conducted code review.")
    
    return {
        "review_notes": review_notes,
        "agents_used": agents,
        "logs": logs
    }

def documentation_node(state: SwarmState) -> Dict[str, Any]:
    """Generates project documentation."""
    task = state.get("task", "")
    code = state.get("code", "")
    review_notes = state.get("review_notes", "")
    research_notes = state.get("research_notes", "")
    rag_context = state.get("rag_context", "")
    
    docs = documentation_agent.generate_docs(
        task=task,
        code=code,
        review_notes=review_notes,
        research_notes=research_notes,
        rag_context=rag_context
    )
    
    agents = list(state.get("agents_used") or [])
    if "Documentation" not in agents:
        agents.append("Documentation")
        
    logs = state.get("logs", [])
    logs.append("[Documentation Node] Generated documentation.")
    
    return {
        "documentation": docs,
        "agents_used": agents,
        "logs": logs
    }

def output_node(state: SwarmState) -> Dict[str, Any]:
    """Consolidates final output based on workflow type."""
    task_type = state.get("task_type", "full_software")
    output_sections = [f"# Swarm Platform Result [{task_type.upper()}]\n"]
    
    if state.get("plan"):
        output_sections.append(f"## Plan\n{state['plan']}\n")
    if state.get("research_notes"):
        output_sections.append(f"## Research Notes & RAG Context\n{state['research_notes']}\n")
    if state.get("code"):
        output_sections.append(f"## Generated Code\n{state['code']}\n")
    if state.get("test_results"):
        output_sections.append(f"## Test Results\n{state['test_results']}\n")
    if state.get("review_notes"):
        output_sections.append(f"## Code Review\n{state['review_notes']}\n")
    if state.get("documentation"):
        output_sections.append(f"## Documentation\n{state['documentation']}\n")
        
    final_output = "\n".join(output_sections)
    
    logs = state.get("logs", [])
    logs.append("[Output Node] Consolidated final output.")
    
    return {
        "final_output": final_output,
        "logs": logs
    }

# Dynamic Routing Functions
def route_after_classifier(state: SwarmState) -> str:
    task_type = state.get("task_type", "full_software")
    if task_type in ("doc_only", "research_explanation"):
        return "researcher_node"
    elif task_type in ("code_only", "full_software"):
        return "planner_node"
    elif task_type == "testing_analysis":
        return "tester_node"
    else:
        return "planner_node"

def route_after_planner(state: SwarmState) -> str:
    task_type = state.get("task_type", "full_software")
    if task_type == "code_only":
        return "coder_node"
    return "researcher_node"

def route_after_researcher(state: SwarmState) -> str:
    task_type = state.get("task_type", "full_software")
    if task_type in ("doc_only", "research_explanation"):
        return "documentation_node"
    return "coder_node"

def route_after_tester(state: SwarmState) -> str:
    passed = state.get("passed_tests", False)
    iteration_count = state.get("iteration_count", 1)
    task_type = state.get("task_type", "full_software")
    
    # Self-correction loop: retry up to max 3 iterations if tests failed
    if not passed and iteration_count < 3 and task_type in ("full_software", "code_only"):
        return "coder_node"
        
    if task_type in ("full_software", "code_only"):
        return "reviewer_node"
        
    return "output_node"

def route_after_reviewer(state: SwarmState) -> str:
    return "documentation_node"

# Build LangGraph StateGraph
builder = StateGraph(SwarmState)

builder.add_node("classifier_node", classifier_node)
builder.add_node("planner_node", planner_node)
builder.add_node("researcher_node", researcher_node)
builder.add_node("coder_node", coder_node)
builder.add_node("tester_node", tester_node)
builder.add_node("reviewer_node", reviewer_node)
builder.add_node("documentation_node", documentation_node)
builder.add_node("output_node", output_node)

# Add Edges
builder.add_edge(START, "classifier_node")

builder.add_conditional_edges(
    "classifier_node",
    route_after_classifier,
    {
        "researcher_node": "researcher_node",
        "planner_node": "planner_node",
        "tester_node": "tester_node"
    }
)

builder.add_conditional_edges(
    "planner_node",
    route_after_planner,
    {
        "coder_node": "coder_node",
        "researcher_node": "researcher_node"
    }
)

builder.add_conditional_edges(
    "researcher_node",
    route_after_researcher,
    {
        "documentation_node": "documentation_node",
        "coder_node": "coder_node"
    }
)

builder.add_edge("coder_node", "tester_node")

builder.add_conditional_edges(
    "tester_node",
    route_after_tester,
    {
        "coder_node": "coder_node",
        "reviewer_node": "reviewer_node",
        "output_node": "output_node"
    }
)

builder.add_conditional_edges(
    "reviewer_node",
    route_after_reviewer,
    {
        "documentation_node": "documentation_node"
    }
)

builder.add_edge("documentation_node", "output_node")
builder.add_edge("output_node", END)

# Compile Graph
swarm_app = builder.compile()

def run_swarm(task: str, override_type: str = None) -> SwarmState:
    """
    Main execution entry point for Swarm Orchestration.
    Supports override_type validation and direct bypass of LLM task classification.
    """
    if override_type is not None:
        if override_type not in VALID_TASK_TYPES:
            raise ValueError(
                f"Invalid override_type '{override_type}'. Must be one of: {sorted(list(VALID_TASK_TYPES))}"
            )

    initial_state: SwarmState = {
        "task": task,
        "agents_used": [],
        "logs": [f"[Swarm Engine] Starting workflow for task: '{task}'"]
    }
    if override_type:
        initial_state["task_type"] = override_type
        
    final_state = swarm_app.invoke(initial_state)
    return final_state
