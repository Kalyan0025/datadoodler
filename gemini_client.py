# gemini_client.py

import os
from typing import Optional
import google.generativeai as genai


class GeminiClient:
    """
    Simple wrapper around Google Generative AI Gemini model.

    Usage:
        gemini = GeminiClient(api_key=...)
        text = gemini.generate(system_instruction="...", user_content="...")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/gemini-1.5-flash"
    ):
        # Allow passing key directly or via environment
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to Streamlit secrets or environment.")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name

    def generate(self, system_instruction: str, user_content: str) -> str:
        """
        Call Gemini with a system instruction and user content.
        Returns plain text (model's text output).
        """

        # ✅ system_instruction belongs here, when creating the model
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

        # ✅ generate_content only takes the content (string or list), no system_instruction kwarg
        response = model.generate_content(user_content)

        # Basic safety: return text or raise a clear error
        if not hasattr(response, "text") or response.text is None:
            raise RuntimeError("Gemini returned an empty response or no .text field.")

        return response.text
