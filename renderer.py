from typing import Dict, Any, List
import random

# Bottom band reserved for legend / "how to read"
LEGEND_RESERVED_HEIGHT = 140
CONTENT_TOP_MARGIN = 90  # minimum y for main drawing

# Dynamic background color mapping based on mood
BACKGROUND_COLORS = {
    "calm": "#F7F3EB",  # warm cream
    "intense": "#FBEDE4",  # warmer tinted paper
    "sad": "#F3F5FA"  # cooler paper
}

def _get_num(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _jitter(value: float, amount: float = 2.0) -> float:
    """Add a small random offset to mimic hand-drawn placement."""
    return value + random.uniform(-amount, amount)

def _clamp_y(y: float, height: int) -> float:
    """Ensure y value stays within the visual content boundaries."""
    content_bottom = height - LEGEND_RESERVED_HEIGHT - 20
    if y < CONTENT_TOP_MARGIN:
        return CONTENT_TOP_MARGIN
    if y > content_bottom:
        return content_bottom
    return y

def _wobble_path(x1: float, y1: float, x2: float, y2: float, wobble_strength: float = 3.0) -> str:
    """Slightly imperfect SVG path generation."""
    return f"M{x1},{y1} C{x1 + random.uniform(-wobble_strength, wobble_strength)},{y1 + random.uniform(-wobble_strength, wobble_strength)} {x2 + random.uniform(-wobble_strength, wobble_strength)},{y2 + random.uniform(-wobble_strength, wobble_strength)} {x2},{y2}"

def render_elements(elements: List[Dict[str, Any]], canvas_width: int, canvas_height: int, mood: str = 'calm') -> str:
    """Render the visual elements onto the canvas with adjustments for drama, size, and aesthetics."""
    canvas = {
        "width": canvas_width,
        "height": canvas_height,
        "background": BACKGROUND_COLORS.get(mood, BACKGROUND_COLORS["calm"])  # Set background color based on mood
    }
    
    rendered_elements = []
    for element in elements:
        if element['type'] == 'circle':
            element['radius'] = element['radius'] * 1.5  # Increase size for drama
            element['opacity'] = random.uniform(0.7, 1.0)  # Add randomness to opacity for more organic feel
            element['x'] = _jitter(element['x'])
            element['y'] = _clamp_y(element['y'], canvas_height)
            rendered_elements.append(element)
        elif element['type'] == 'line':
            element['strokeWidth'] = 3  # Thicker lines for more emphasis
            rendered_elements.append(element)
        elif element['type'] == 'polygon':
            element['opacity'] = 0.9  # More solid shapes for clarity
            rendered_elements.append(element)
        elif element['type'] == 'path':
            element['d'] = _wobble_path(element['x'], element['y'], element['x2'], element['y2'])  # Wobbly paths for hand-drawn effect
            rendered_elements.append(element)
        elif element['type'] == 'text':
            element['fontSize'] = 20  # Increase font size for readability and emphasis
            element['fill'] = "#333333"  # Darker text for better contrast
            element['textAnchor'] = 'middle'  # Ensure the text is centered properly
            rendered_elements.append(element)

    return {
        "canvas": canvas,
        "elements": rendered_elements,
        "legend": [
            {"label": "Energetic Moments", "color": "#F5A623"},
            {"label": "Calm Moments", "color": "#7FB77E"}
        ],
        "title": "Visual Journal of the Day"
    }
