# gemini_client.py

import os
from typing import Optional
import google.generativeai as genai


class GeminiClient:
    """
    Wrapper around Google Gemini Flash for Data Humanism visual generation.

    Usage:
        gemini = GeminiClient(api_key=...)
        text = gemini.generate(system_instruction="...", user_content="...")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/gemini-flash-latest"
    ):
        # Load API key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Add it in Streamlit secrets.")

        # Configure client
        genai.configure(api_key=self.api_key)
        self.model_name = model_name

    def generate(self, system_instruction: str, user_content: str) -> str:
        """
        Ask Gemini to generate text based on a system instruction and user content.
        Returns the model's raw text output.
        """

        # System instructions must be set at model creation time
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

        # Only the user content goes here
        response = model.generate_content(user_content)

        # Validate output
        if not hasattr(response, "text") or response.text is None:
            raise RuntimeError("Gemini did not return a valid .text output.")

        return response.text
