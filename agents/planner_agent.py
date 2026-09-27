import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

token = os.getenv("HF_TOKEN")

client = InferenceClient(
    token=token
)


class PlannerAgent:

    def __init__(self):
        self.client = client

    def create_plan(self, task):

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Planner Agent in a multi-agent AI system. "
                        "Your job is to analyze the user's task and break it "
                        "into clear, logical, actionable steps."
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
    planner = PlannerAgent()
    task = "Build a student management REST API"
    plan = planner.create_plan(task)
    print("\nGenerated Plan:\n")
    print(plan)
