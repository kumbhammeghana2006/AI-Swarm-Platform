from agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    """
    Coder Agent writes modular, clean, working implementation code.
    Supports self-correction iterations using feedback from Tester Agent.
    """

    def generate_code(
        self,
        task: str,
        plan: str = "",
        research_notes: str = "",
        feedback: str = "",
        iteration: int = 1
    ) -> str:
        system_prompt = (
            "You are the Coder Agent in an AI Swarm platform. "
            "Your job is to write high-quality, fully working, self-contained Python code "
            "or clean source files as requested. Return complete code with clear docstrings and error handling."
        )

        feedback_section = ""
        if feedback:
            feedback_section = (
                f"\n--- ATTENTION: THIS IS ITERATION #{iteration} (SELF-CORRECTION) ---\n"
                f"Previous test/execution feedback to fix:\n{feedback}\n"
                "Please fix all reported issues and return the corrected complete code.\n"
            )

        user_prompt = (
            f"User Task: {task}\n"
            f"Plan: {plan if plan else 'N/A'}\n"
            f"Research Notes: {research_notes if research_notes else 'N/A'}\n"
            f"{feedback_section}\n"
            "Generate complete, clean, executable Python code."
        )

        return self.call_llm(system_prompt, user_prompt)
