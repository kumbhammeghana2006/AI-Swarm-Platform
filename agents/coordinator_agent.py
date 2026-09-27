import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

token = os.getenv("HF_TOKEN")

client = InferenceClient(
    token=token
)


class CoordinatorAgent:

    def __init__(self):
        self.client = client
    def coordinate(self, task):

      response = self.client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Coordinator Agent in a multi-agent AI system. "
                        "Your job is to analyze the user's task and decide which "
                        "specialized agents are needed to complete it. "
                        "Available agents are: Planner, Researcher, RAG, Coder, "
                        "Analyst, Tester, Reviewer, and Documentation. "
                        "Return the selected agents and briefly explain what "
                        "each selected agent should do."
                )
            },
            {
                "role": "user",
                "content": task
            }
        ],
    )

      return response.choices[0].message.content

if __name__ == "__main__":
    coordinator = CoordinatorAgent()
    task = "Build a FastAPI student management REST API"
    decision = coordinator.coordinate(task)
    print("\nCoordinator Decision:\n")
    print(decision)