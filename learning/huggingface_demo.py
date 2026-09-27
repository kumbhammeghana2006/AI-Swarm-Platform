from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient
load_dotenv()
token = os.getenv("HF_TOKEN")
print("HF token loaded:", token is not None)
client = InferenceClient(
    token=token
)
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Explain what an AI agent is in simple words."
        }
    ],
)
print(response.choices[0].message.content)