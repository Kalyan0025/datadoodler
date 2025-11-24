from typing import Dict, Any, List
import random

LEGEND_RESERVED_HEIGHT = 140
CONTENT_TOP_MARGIN = 90  

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
    """Slightly imperfect SVG quadratic path between two points for hand-drawn feel."""
    cx = (x1 + x2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    cy = (y1 + y2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    return f"M{x1},{y1} Q{cx},{cy} {x2},{y2}"

def _escape(text: str) -> str:
    """Escape basic XML entities for SVG compatibility."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def render_visual_spec(spec: Dict[str, Any]) -> str:
    """Generate the SVG based on visual spec with enhanced aesthetics, including mood-based background, handwritten font, and responsive legend."""
    canvas_width = 1200
    canvas_height = 800

    # Background colors for different moods
    mood_colors = {
        "Positive": "#FFEB3B",  # Yellow for happy
        "Neutral": "#F3F4F7",  # Light gray for neutral
        "Negative": "#B3B3B3"  # Cool gray for negative
    }
    background_color = mood_colors.get(spec.get("mood", "Neutral"), "#F3F4F7")

    elements: List[Dict[str, Any]] = []

    # Example visual: mood represented as color
    elements.append({
        "type": "circle",
        "x": canvas_width / 2,
        "y": canvas_height / 2,
        "radius": spec.get("hours_worked", 8) * 5,  # Adjust circle size based on hours worked
        "fill": background_color
    })

    # Add energy level as text
    elements.append({
        "type": "text",
        "x": canvas_width / 2,
        "y": canvas_height / 2 + 50,
        "text": f"Energy: {spec.get('energy', 'Medium')}",
        "fontSize": 24,
        "fill": "#333333"
    })

    # Generate SVG for elements
    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {canvas_width} {canvas_height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # Background Paper
    svg_parts.append(
        f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="{background_color}" />'
    )

    # Render each visual element
    for el in elements:
        el_type = (el.get("type") or "").lower()

        if el_type == "circle":
            cx = _get_num(el.get("x"), canvas_width / 2)
            cy = _get_num(el.get("y"), canvas_height / 2)
            r = _get_num(el.get("radius"), 50)
            fill = el.get("fill", "none")
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" />'
            )

        elif el_type == "text":
            tx = _get_num(el.get("x"), canvas_width / 2)
            ty = _get_num(el.get("y"), canvas_height / 2)
            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill_text = el.get("fill", "#333333")
            svg_parts.append(
                f'<text x="{tx}" y="{ty}" font-family="Dancing Script, cursive" font-size="{font_size}" '
                f'fill="{fill_text}">{content}</text>'
            )

    svg_parts.append("</svg>")

    return "".join(svg_parts)
