import json
from pathlib import Path
from typing import Dict, Any


PROMPT_PATH = Path("prompts/system_prompt.txt")


def _load_system_prompt() -> str:
    """
    Load the main Data Humanism / Giorgia Lupi-style system prompt
    from prompts/system_prompt.txt.
    """
    if not PROMPT_PATH.exists():
        # Fallback minimal safety if file missing
        return (
            "You are a visual designer inspired by Giorgia Lupi and Data Humanism. "
            "Given a small or large human dataset in text form, you design a unique, "
            "hand-drawn-style visualization as a JSON specification for an SVG drawing. "
            "Only output valid JSON."
        )

    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_user_prompt(input_data: Dict[str, Any]) -> str:
    """
    Build the 'user' side content for Gemini using the unified input_data.
    We let Gemini see:
      - what kind of data this is (dream/memory/routine/etc.)
      - source type (file/text)
      - a meta description
      - the raw text/table description
    """
    pieces = []

    pieces.append("You are given a single dataset to visualize in a Data Humanism / Dear Data style.\n")

    pieces.append("Here is the meta description of the dataset:\n")
    pieces.append(input_data.get("meta_description", "") + "\n")

    pieces.append("\nHere is the raw data (or its textual representation):\n")
    pieces.append(input_data.get("raw_text", ""))

    # We explicitly label the logical type (dream/memory/etc.)
    data_kind = input_data.get("data_kind", "mixed")
    pieces.append(f"\n\nData kind label for this visualization: {data_kind}\n")

    # Final instruction to Gemini:
    pieces.append(
        "\nNow, based on this dataset, design a unique visualization using the JSON schema I defined "
        "in the system instructions. Remember: Dear Data, Giorgia Lupi, no dashboards, no axes, no bar charts. "
        "Use circles, lines, paths, repetition, spacing, color, small legends, and metaphors."
    )

    return "".join(pieces)


def generate_visual_spec(input_data: Dict[str, Any], gemini) -> Dict[str, Any]:
    """
    Main function used by app.py.
    Calls Gemini with the system prompt + user prompt, expects JSON back.

    Returns:
      visual_spec (dict) that the renderer can turn into SVG.
    """
    system_prompt = _load_system_prompt()
    user_prompt = _build_user_prompt(input_data)

    raw_response = gemini.generate(
        system_instruction=system_prompt,
        user_content=user_prompt
    )

    # Gemini is instructed to return ONLY JSON.
    # We parse it here. If something goes wrong, we raise a clean error.
    try:
        visual_spec = json.loads(raw_response)
    except json.JSONDecodeError as e:
        # Simple fallback: wrap the error in a minimal visual spec
        # so the app doesn't crash hard.
        visual_spec = {
            "canvas": {
                "width": 1200,
                "height": 800,
                "background": "#ffffff"
            },
            "layout": {
                "type": "error",
                "description": "Failed to parse JSON from model. Showing error message instead."
            },
            "palette": {},
            "shapes": [],
            "labels": [
                {
                    "text": "Error parsing visual specification",
                    "x": 0.1,
                    "y": 0.2,
                    "size": 20,
                    "style": "title"
                },
                {
                    "text": f"Raw model response started with: {raw_response[:200]}",
                    "x": 0.1,
                    "y": 0.3,
                    "size": 12,
                    "style": "note"
                }
            ],
            "legend": [
                "The model did not return valid JSON.",
                "Check the system prompt or response format."
            ]
        }

    return visual_spec
