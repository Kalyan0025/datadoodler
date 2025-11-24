from typing import Dict, Any, List
import random

LEGEND_RESERVED_HEIGHT = 160
CONTENT_TOP_MARGIN = 90  

BACKGROUND_COLORS = {
    "calm": "#F7F3EB",  
    "intense": "#FBEDE4",  
    "sad": "#F3F5FA"  
}

def _get_num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _jitter(value: float, amount: float = 1.6) -> float:
    return value + random.uniform(-amount, amount)

def _clamp_y(y: float, height: int) -> float:
    content_bottom = height - LEGEND_RESERVED_HEIGHT - 20
    if y < CONTENT_TOP_MARGIN:
        return CONTENT_TOP_MARGIN
    if y > content_bottom:
        return content_bottom
    return y

def _wobble_path(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    wobble_strength: float = 3.0,
) -> str:
    cx = (x1 + x2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    cy = (y1 + y2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    return f"M{x1},{y1} Q{cx},{cy} {x2},{y2}"

def _escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def _compute_bbox(elements: List[Dict[str, Any]], width: int, height: int):
    min_x, max_x, min_y, max_y = None, None, None, None

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
    canvas = spec.get("canvas", {}) or {}
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 800))

    background = (
        canvas.get("background")
        or canvas.get("background_color")
        or "#FDFBF7"
    )

    elements: List[Dict[str, Any]] = spec.get("elements", []) or []

    raw_legend = spec.get("legend") or []
    legend_items: List[Dict[str, Any]]
    legend_title = "Legend"

    if isinstance(raw_legend, dict):
        legend_title = raw_legend.get("title", "Legend") or "Legend"
        legend_items = raw_legend.get("items", []) or []
    else:
        legend_items = raw_legend

    title_text: str = spec.get("title", "") or ""

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
    )

    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="50" text-anchor="middle" '
            f'font-family="Dancing Script, cursive" font-size="24" fill="#222">'
            f'{_escape(title_text)}</text>'
        )

    content_bottom = height - LEGEND_RESERVED_HEIGHT - 20
    margin_left_right = width * 0.1
    margin_top = CONTENT_TOP_MARGIN + 10
    margin_bottom = content_bottom - 10

    min_x, min_y, max_x, max_y = _compute_bbox(elements, width, height)

    if (
        min_x is not None
        and max_x is not None
        and min_y is not None
        and max_y is not None
        and max_x > min_x
        and max_y > min_y
    ):
        orig_cx = (min_x + max_x) / 2.0
        orig_cy = (min_y + max_y) / 2.0

        avail_w = (width - 2 * margin_left_right)
        avail_h = (margin_bottom - margin_top)

        sx = avail_w / (max_
