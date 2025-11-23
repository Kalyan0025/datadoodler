# visual_spec_generator.py

"""
Generate a Data Humanism visual specification using Gemini.

Takes a plain-text input string (already combined meta + raw data),
sends it to Gemini with a Dear Data–style system prompt, and returns
a Python dict representing the visual spec JSON.
"""

import json
import textwrap
from pathlib import Path
from typing import Any, Dict

from gemini_client import GeminiClient


# Path to the system prompt file
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"


def _load_system_prompt() -> str:
    """Load the Giorgia Lupi / Dear Data system prompt from file."""
    if not SYSTEM_PROMPT_PATH.exists():
        # Fallback minimal prompt if file is missing
        return textwrap.dedent(
            """
            You are a system that outputs ONLY valid JSON describing a visual
            specification with keys: canvas, elements, legend, title.
            Never include any explanation or markdown, only raw JSON.
            """
        ).strip()

    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def _extract_json_from_text(raw_text: str) -> Dict[str, Any]:
    """
    Gemini sometimes wraps JSON in text or ```json fences.
    This function tries to pull out the first valid JSON object.
    """
    text = raw_text.strip()

    # Remove markdown fences if present
    if text.startswith("```"):
        # e.g. ```json\n{...}\n```
        # Remove the first line (``` or ```json)
        parts = text.split("\n", 1)
        if len(parts) == 2:
            text = parts[1]
        # Remove trailing ```
        if text.endswith("```"):
            text = text[: -3].strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find first '{' and last '}' and try that slice
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # If still failing, raise a clear error
    raise ValueError("Could not extract valid JSON from Gemini response.")


def generate_visual_spec(input_data: str, gemini: GeminiClient) -> Dict[str, Any]:
    """
    Main entrypoint called from app.py.

    Parameters
    ----------
    input_data : str
        A combined string containing:
        - data type
        - short description
        - raw extracted data

    gemini : GeminiClient
        Configured Gemini client.

    Returns
    -------
    Dict[str, Any]
        Parsed visual specification ready for renderer.py
        with at least keys: canvas, elements, legend, title.
    """
    if not isinstance(input_data, str):
        # Safeguard: allow old-style dict input, but convert to text
        try:
            input_data = json.dumps(input_data, indent=2)
        except Exception:
            input_data = str(input_data)

    system_prompt = _load_system_prompt()

    # Build a concise user prompt for the model
    user_prompt = textwrap.dedent(
        f"""
        The following is user-provided data and context.

        Your task:
        - Understand the patterns, categories, sequences, and emotions.
        - Design a "Dear Data" style postcard visual specification.
        - Output ONLY a valid JSON object using the exact schema described
          in the system instructions (canvas, elements, legend, title).

        USER DATA START
        ---------------
        {input_data}
        ---------------
        USER DATA END
        """
    ).strip()

    # Call Gemini
    raw_response_text = gemini.generate(
        system_instruction=system_prompt,
        user_content=user_prompt,
    )

    # Parse the text into a JSON spec
    spec = _extract_json_from_text(raw_response_text)

    # Basic safety: ensure required top-level keys exist
    spec.setdefault("canvas", {"width": 1200, "height": 800, "background": "#FDFBF7"})
    spec.setdefault("elements", [])
    spec.setdefault("legend", [])
    spec.setdefault("title", "Data Humanism Visual")

    return spec
