import google.generativeai as genai


class GeminiClient:
    """
    Simple wrapper around Gemini Flash API.
    Reads API key from Streamlit secrets in app.py,
    initializes the model once, and exposes a clean
    .generate() method used by all other files.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)

        # Use Flash model (fastest + supports JSON reliably)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate(self, system_instruction: str, user_content: str):
        """
        Unified generate() method for all prompts.
        Takes system prompt + user content and returns text.
        """

        response = self.model.generate_content(
            contents=user_content,
            system_instruction=system_instruction
        )

        return response.text
