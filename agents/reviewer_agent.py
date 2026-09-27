from agents.base_agent import BaseAgent

class ReviewerAgent(BaseAgent):
    """
    Reviewer Agent performs code reviews covering structure, performance, security, and best practices.
    """

    def review(self, task: str, code: str, test_results: str = "") -> str:
        system_prompt = (
            "You are the Reviewer Agent in an AI Swarm platform. "
            "Your job is to conduct a detailed code review focusing on: "
            "1. Code architecture and readability "
            "2. Security vulnerabilities and input validation "
            "3. Performance optimizations "
            "4. Adherence to Python standards (PEP 8, type hints, docstrings)."
        )

        user_prompt = (
            f"User Task: {task}\n\n"
            f"Code to Review:\n{code}\n\n"
            f"Tester Results:\n{test_results if test_results else 'N/A'}\n\n"
            "Provide structured code review notes with recommendations."
        )

        return self.call_llm(system_prompt, user_prompt)
