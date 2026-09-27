import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

class BaseAgent:
    """
    Base Agent class providing shared Hugging Face InferenceClient communication logic.
    Loads HF_TOKEN securely from environment.
    """

    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        token = os.getenv("HF_TOKEN")
        if not token:
            raise ValueError("HF_TOKEN is missing from environment variables.")
        self.client = InferenceClient(token=token)
        self.model_name = model_name

    def call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Invokes Hugging Face InferenceClient chat completion safely."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Mask sensitive info if any exception occurs
            err_msg = str(e)
            print(f"[BaseAgent Error] LLM invocation failed: {err_msg}")
            raise RuntimeError("LLM request failed. Please check network or HF_TOKEN permissions.") from None
