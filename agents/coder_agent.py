from agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    """
    Coder Agent writes modular, clean, working implementation code.
    Supports self-correction iterations using feedback from Tester Agent, previous code,
    test results, and retrieved RAG context.
    """

    def generate_code(
        self,
        task: str,
        plan: str = "",
        research_notes: str = "",
        feedback: str = "",
        iteration: int = 1,
        previous_code: str = "",
        test_results: str = "",
        rag_context: str = ""
    ) -> str:
        system_prompt = (
            "You are the Coder Agent in an AI Swarm platform. "
            "Your job is to write high-quality, fully working, self-contained Python code "
            "or clean source files as requested. Return complete code with clear docstrings and error handling."
        )

        feedback_section = ""
        if feedback or iteration > 1:
            parts = [f"\n--- ATTENTION: THIS IS ITERATION #{iteration} (SELF-CORRECTION) ---"]
            if previous_code:
                parts.append(f"Previous Code Attempt:\n```python\n{previous_code}\n```")
            if test_results:
                parts.append(f"Tester Execution Results:\n{test_results}")
            if feedback:
                parts.append(f"Actionable Feedback to Fix:\n{feedback}")
            parts.append("Please address all reported errors, fix the defects, and output the corrected complete code.\n")
            feedback_section = "\n".join(parts)

        context_section = ""
        if rag_context:
            context_section = f"Knowledge Base & RAG Context:\n{rag_context}\n"

        user_prompt = (
            f"User Task: {task}\n"
            f"Plan: {plan if plan else 'N/A'}\n"
            f"Research Notes: {research_notes if research_notes else 'N/A'}\n"
            f"{context_section}"
            f"{feedback_section}\n"
            "Generate complete, clean, executable Python code."
        )

        return self.call_llm(system_prompt, user_prompt)

