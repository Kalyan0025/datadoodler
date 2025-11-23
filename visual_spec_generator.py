# visual_spec_generator.py

"""
Generate a Data Humanism visual specification using Gemini.

Flow:
1. Build a Dear Data style user prompt from the combined input text.
2. Call Gemini with the main system prompt → get raw text.
3. Try to extract JSON.
4. If extraction fails, call Gemini again in "JSON repair" mode to fix it.
5. Return a valid spec dict (canvas, elements, legend, title).
"""

import json
import textwrap
from pathlib import Path
from typing import Any, Dict

from gemini_client import GeminiClient


SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"


# ---------------------------------------------------------
# Helpers: load system prompt and extract JSON from text
# ---------------------------------------------------------
def _load_system_prompt() -> str:
    """Load the Giorgia Lupi / Dear Data system prompt from file."""
    if not SYSTEM_PROMPT_PATH.exists():
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
    Try to pull a JSON object out of model text.
    Handles ```json fences and leading/trailing prose.
    Raises ValueError if nothing JSON-like can be parsed.
    """
    text = raw_text.strip()

    # Strip markdown fences
    if text.startswith("```"):
        parts = text.split("\n", 1)
        if len(parts) == 2:
            text = parts[1]
        if text.endswith("```"):
            text = text[:-3].strip()

    # 1) Direct attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2) Slice between first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from Gemini response.")


# ---------------------------------------------------------
# JSON repair: second-pass call to Gemini
# ---------------------------------------------------------
def _repair_json_with_gemini(
    raw_text: str,
    gemini: GeminiClient,
) -> Dict[str, Any]:
    """
    Use Gemini itself to repair non-JSON or broken JSON output.

    We pass the raw text and ask for:
      - ONLY a valid JSON object
      - matching the required schema
    """
    repair_system = textwrap.dedent(
        """
        You are a JSON repair assistant.

        You are given some text that SHOULD have been a JSON object describing
        a visual specification, but may contain extra commentary, markdown
        fences, or invalid JSON.

        Your job:
        - Read the provided text.
        - Infer the intended JSON object if possible.
        - Output ONLY a single JSON object with this structure:

          {
            "canvas": { "width": number, "height": number, "background": "#hex" },
            "elements": [ ... ],
            "legend": [ ... ],
            "title": "..."
          }

        Rules:
        - No markdown fences.
        - No explanation.
        - No prose.
        - Just the JSON.
        """
    ).strip()

    repair_user = textwrap.dedent(
        f"""
        Here is the previous (possibly invalid) output:

        ---- START RAW TEXT ----
        {raw_text}
        ---- END RAW TEXT ----

        Convert this into a single valid JSON object following the schema.
        """
    ).strip()

    repaired_text = gemini.generate(
        system_instruction=repair_system,
        user_content=repair_user,
    )

    # Now try to extract JSON from the repaired text
    return _extract_json_from_text(repaired_text)


# ---------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------
def generate_visual_spec(input_data: str, gemini: GeminiClient) -> Dict[str, Any]:
    """
    Called from app.py.

    input_data:
        Combined string containing:
        - data type
        - short description
        - raw text / parsed file contents

    Returns:
        A dict with at least: canvas, elements, legend, title.
    """

    # Backwards safety: if someone passes a dict, stringify it
    if not isinstance(input_data, str):
        try:
            input_data = json.dumps(input_data, indent=2)
        except Exception:
            input_data = str(input_data)

    system_prompt = _load_system_prompt()

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

    # 1) First call: ask Gemini to design the spec
    raw_response_text = gemini.generate(
        system_instruction=system_prompt,
        user_content=user_prompt,
    )

    # 2) Try parsing the first response
    try:
        spec = _extract_json_from_text(raw_response_text)
    except ValueError:
        # 3) JSON failed → second-pass repair call
        try:
            spec = _repair_json_with_gemini(raw_response_text, gemini)
        except Exception:
            # 4) If even repair fails, build a minimal but valid fallback
            spec = {
                "canvas": {
                    "width": 1200,
                    "height": 800,
                    "background": "#FDFBF7",
                },
                "elements": [],
                "legend": [
                    {
                        "label": "Model output could not be parsed as JSON "
                                 "even after repair.",
                        "shape": "circle",
                        "color": "#999999",
                        "styleNotes": "fallback / parsing error",
                    }
                ],
                "title": "Fallback visual – JSON could not be repaired",
                "_raw_model_text": raw_response_text,
            }

    # 5) Final safety: ensure required keys exist
    spec.setdefault("canvas", {"width": 1200, "height": 800, "background": "#FDFBF7"})
    spec.setdefault("elements", [])
    spec.setdefault("legend", [])
    spec.setdefault("title", "Data Humanism Visual")

    return spec
