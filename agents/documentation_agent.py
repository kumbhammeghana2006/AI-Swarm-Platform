from agents.base_agent import BaseAgent

class DocumentationAgent(BaseAgent):
    """
    Documentation Agent generates technical documentation, API guides, setup instructions, and summaries.
    """

    def generate_docs(
        self,
        task: str,
        code: str = "",
        review_notes: str = "",
        research_notes: str = "",
        rag_context: str = ""
    ) -> str:
        system_prompt = (
            "You are the Documentation Agent in an AI Swarm platform. "
            "Your job is to generate clean, comprehensive user and developer documentation. "
            "Include an overview, setup guide, API/Usage reference, example usage, and key takeaways."
        )

        user_prompt = (
            f"User Task: {task}\n\n"
            f"Research Notes:\n{research_notes if research_notes else 'N/A'}\n\n"
            f"RAG Context:\n{rag_context if rag_context else 'N/A'}\n\n"
            f"Code:\n{code if code else 'N/A'}\n\n"
            f"Review Notes:\n{review_notes if review_notes else 'N/A'}\n\n"
            "Produce comprehensive markdown documentation."
        )

        return self.call_llm(system_prompt, user_prompt)
