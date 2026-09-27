from agents.base_agent import BaseAgent
from agents.rag_engine import LightweightRAG
from typing import Dict, Any

class ResearcherAgent(BaseAgent):
    """
    Researcher Agent queries local knowledge base via RAG and produces technical research notes.
    """

    def __init__(self, rag_engine: LightweightRAG = None):
        super().__init__()
        self.rag_engine = rag_engine or LightweightRAG()

    def research(self, task: str, plan: str = "") -> Dict[str, str]:
        rag_context = self.rag_engine.retrieve_context(task)

        system_prompt = (
            "You are the Researcher Agent in an AI Swarm platform. "
            "Your job is to analyze the user task and local knowledge base context, "
            "synthesizing technical research notes, required patterns, and key guidelines."
        )

        user_prompt = (
            f"User Task: {task}\n"
            f"Execution Plan: {plan if plan else 'N/A'}\n\n"
            f"Retrieved Knowledge Base Context:\n{rag_context}\n\n"
            "Please provide comprehensive, structured technical research notes to guide implementation."
        )

        research_notes = self.call_llm(system_prompt, user_prompt)
        return {
            "research_notes": research_notes,
            "rag_context": rag_context
        }
