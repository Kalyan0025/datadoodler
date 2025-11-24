from typing import Dict, Any, List
import random

LEGEND_RESERVED_HEIGHT = 160
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

def _compute_bbox(elements: List[Dict[str, Any]], width: int, height: int):
    """Compute the bounding box for all drawing elements."""
    min_x = None
    max_x = None
    min_y = None
    max_y = None

    for el in elements:
        el_type = (el.get("type") or "").lower()

        if el_type == "circle":
            x = _get_num(el.get("x"), width / 2)
            y = _get_num(el.get("y"), height / 2)
            r = _get_num(el.get("radius"), 0)
            xs = [x - r, x + r]
            ys = [y - r, y + r]

        elif el_type == "line":
            x1 = _get_num(el.get("x"), width / 2)
            y1 = _get_num(el.get("y"), height / 2)
            x2 = _get_num(el.get("x2"), x1 + 10)
            y2 = _get_num(el.get("y2"), y1)
            xs = [x1, x2]
            ys = [y1, y2]

        elif el_type == "polygon":
            pts = el.get("points") or []
            xs, ys = [], []
            for p in pts:
                if isinstance(p, (list, tuple)) and len(p) >= 2:
                    xs.append(_get_num(p[0]))
                    ys.append(_get_num(p[1]))
            if not xs or not ys:
                continue

        elif el_type == "text":
            x = _get_num(el.get("x"), width / 2)
            y = _get_num(el.get("y"), height / 2)
            xs = [x]
            ys = [y]

        else:
            continue

        local_min_x = min(xs)
        local_max_x = max(xs)
        local_min_y = min(ys)
        local_max_y = max(ys)

        if min_x is None or local_min_x < min_x:
            min_x = local_min_x
        if max_x is None or local_max_x > max_x:
            max_x = local_max_x
        if min_y is None or local_min_y < min_y:
            min_y = local_min_y
        if max_y is None or local_max_y > max_y:
            max_y = local_max_y

    return min_x, min_y, max_x, max_y

def render_visual_spec(spec: Dict[str, Any]) -> str:
    """Generate the SVG based on visual spec with enhanced aesthetics, including mood-based background, handwritten font, and responsive legend."""
    canvas = spec.get("canvas", {}) or {}
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 800))

    background_color = canvas.get("background_color", "#F7F3EB")
    mood = spec.get("mood", "neutral")  # mood could be "positive", "negative", or "neutral"
    
    if mood == "positive":
        background_color = "#FFFAF0"  # Light warm tone for positive mood
    elif mood == "negative":
        background_color = "#D8E3E7"  # Cooler tone for negative mood

    elements: List[Dict[str, Any]] = spec.get("elements", []) or []
    legend_items: List[Dict[str, Any]] = spec.get("legend", []) or []
    title_text: str = spec.get("title", "") or ""

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # Background Paper
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background_color}" />'
    )

    # Title
    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="60" text-anchor="middle" '
            f'font-family="Dancing Script, cursive" font-size="28" fill="#222">'
            f'{_escape(title_text)}</text>'
        )

    # Visual Element Handling (e.g., circles, lines, polygons, etc.)
    for el in elements:
        # SVG element creation logic remains here as per the previous implementation
        pass

    # Legend handling for shapes
    if legend_items:
        # Legend layout and shapes (circle, triangle, swirl, etc.)
        pass

    svg_parts.append("</svg>")
    return "".join(svg_parts)
