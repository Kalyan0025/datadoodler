from typing import Dict, Any, List
import random

# Bottom band reserved for legend / "how to read"
LEGEND_RESERVED_HEIGHT = 140
CONTENT_TOP_MARGIN = 90  # minimum y for main drawing

def _get_num(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _jitter(value: float, amount: float = 2.0) -> float:
    """Small random offset to mimic hand-drawn placement."""
    return value + random.uniform(-amount, amount)


def _clamp_y(y: float, height: int) -> float:
    """
    Keep y within the main drawing band:
    from CONTENT_TOP_MARGIN down to height - LEGEND_RESERVED_HEIGHT - 20.
    This prevents overlap with the bottom legend and avoids objects hugging the edges.
    """
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
    wobble_strength: float = 4.0,
) -> str:
    """Slightly imperfect SVG quadratic path between two points."""
    cx = (x1 + x2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    cy = (y1 + y2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    return f"M{x1},{y1} Q{cx},{cy} {x2},{y2}"


def _escape(text: str) -> str:
    """Escape basic XML entities."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _compute_bbox(elements: List[Dict[str, Any]], width: int, height: int):
    """
    Compute a bounding box of the main drawing elements (not including legend).
    We use this later to scale and center the entire composition so it uses
    most of the canvas.
    """
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
            # Skip unsupported types for bbox
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
    """
    Convert a JSON visual specification into an SVG string.
    """

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

    # Fix for handling legend as list or dict {title, items}
    if isinstance(raw_legend, dict):
        legend_title = raw_legend.get("title", "Legend") or "Legend"
        legend_items = raw_legend.get("items", []) or []
    elif isinstance(raw_legend, list):  # If legend is a list
        legend_items = raw_legend
    else:
        legend_items = []

    title_text: str = spec.get("title", "") or ""

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # Background paper, change based on mood
    if "background" in spec and spec["background"] == "mood":
        mood_color = "#F0E68C"  # Example: change based on mood data
        svg_parts.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{mood_color}" />'
        )
    else:
        svg_parts.append(
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
        )

    # Light paper border
    svg_parts.append(
        f'<rect x="16" y="16" width="{width-32}" height="{height-32}" '
        f'fill="none" stroke="#E1D7C6" stroke-width="1.5" />'
    )

    # Title at top
    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="50" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="24" fill="#222">'
            f'{_escape(title_text)}</text>'
        )

    # Content band geometry
    content_bottom = height - LEGEND_RESERVED_HEIGHT - 20
    margin_left_right = width * 0.1
    margin_top = CONTENT_TOP_MARGIN + 10
    margin_bottom = content_bottom - 10

    # 1️⃣ Compute bounding box of the drawing, then compute scale + translation
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

        sx = avail_w / (max_x - min_x)
        sy = avail_h / (max_y - min_y)
        scale = min(sx, sy) * 0.9  # keep a little breathing room

        target_cx = width / 2.0
        target_cy = (margin_top + margin_bottom) / 2.0

        def tx(x: float) -> float:
            return target_cx + (x - orig_cx) * scale

        def ty(y: float) -> float:
            return target_cy + (y - orig_cy) * scale

    else:
        # Fallback: no scaling
        scale = 1.0

        def tx(x: float) -> float:
            return x

        def ty(y: float) -> float:
            return y

    # 2️⃣ Draw core elements, applying scale + hand-drawn jitter
    for el in elements:
        el_type = (el.get("type") or "").lower()

        if el_type not in {"circle", "line", "polygon", "path", "text"}:
            # Ignore any unsupported / semantic types (arc, cluster, etc.)
            continue

        fill = el.get("fill", None)
        stroke = el.get("stroke", None)

        # If only fill provided, add a subtle dark stroke for that "marker" look
        if fill and not stroke and fill != "none":
            stroke = "#222222"
        if not fill:
            fill = "none"
        if not stroke:
            stroke = "#222222"

        stroke_width = _get_num(el.get("strokeWidth"), 2.5)  # Slightly thicker strokes
        opacity = _get_num(el.get("opacity"), random.uniform(0.86, 1.0))

        if el_type == "circle":
            cx_raw = _get_num(el.get("x"), width / 2)
            cy_raw = _get_num(el.get("y"), height / 2)
            r_raw = _get_num(el.get("radius"), 8)

            cx_scaled = tx(cx_raw)
            cy_scaled = ty(cy_raw)

            cx = _jitter(cx_scaled, amount=3.0)
            cy = _clamp_y(_jitter(cy_scaled, amount=3.0), height)
            r = max(_jitter(r_raw * scale, amount=2.0), 0.8)

            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}" />'
            )

        elif el_type == "line":
            x1_raw = _get_num(el.get("x"), width / 2)
            y1_raw = _get_num(el.get("y"), height / 2)
            x2_raw = _get_num(el.get("x2"), x1_raw + 10)
            y2_raw = _get_num(el.get("y2"), y1_raw)

            x1_scaled = tx(x1_raw)
            y1_scaled = ty(y1_raw)
            x2_scaled = tx(x2_raw)
            y2_scaled = ty(y2_raw)

            x1 = _jitter(x1_scaled, amount=3.0)
            y1 = _clamp_y(_jitter(y1_scaled, amount=3.0), height)
            x2 = _jitter(x2_scaled, amount=3.0)
            y2 = _clamp_y(_jitter(y2_scaled, amount=3.0), height)

            d = _wobble_path(x1, y1, x2, y2, wobble_strength=4.0)

            svg_parts.append(
                f'<path d="{d}" fill="none" '
                f'stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}" />'
            )

        elif el_type == "polygon":
            pts = el.get("points") or []
            if isinstance(pts, list) and pts:
                jittered_points = []
                for p in pts:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        px_raw = _get_num(p[0])
                        py_raw = _get_num(p[1])
                        px_scaled = tx(px_raw)
                        py_scaled = ty(py_raw)
                        px = _jitter(px_scaled, amount=2.0)
                        py = _clamp_y(_jitter(py_scaled, amount=2.0), height)
                        jittered_points.append(f"{px},{py}")
                if jittered_points:
                    pts_str = " ".join(jittered_points)
                    svg_parts.append(
                        f'<polygon points="{pts_str}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{stroke_width}" '
                        f'opacity="{opacity}" />'
                    )

        elif el_type == "path":
            d_raw = el.get("d") or ""
            if d_raw:
                d = _escape(d_raw)
                svg_parts.append(
                    f'<path d="{d}" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="{stroke_width}" '
                    f'opacity="{opacity}" />'
                )

        elif el_type == "text":
            tx_raw = _get_num(el.get("x"), width / 2)
            ty_raw = _get_num(el.get("y"), height / 2)

            tx_scaled_val = tx(tx_raw)
            ty_scaled_val = ty(ty_raw)

            tx_final = _jitter(tx_scaled_val, amount=2.0)
            ty_final = _clamp_y(_jitter(ty_scaled_val, amount=2.0), height)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill_text = el.get("fill", el.get("color", "#333333"))
            anchor = el.get("textAnchor", "start")

            svg_parts.append(
                f'<text x="{tx_final}" y="{ty_final}" text-anchor="{anchor}" '
                f'font-family="Georgia, serif" font-size="{font_size}" '
                f'fill="{fill_text}" opacity="{opacity}">{content}</text>'
            )

    # 3️⃣ Legend – in reserved bottom band, clean and non-overlapping
    if legend_items:
        legend_top = height - LEGEND_RESERVED_HEIGHT + 30
        legend_left = 70
        line_height = 24

        svg_parts.append(
            f'<text x="{legend_left}" y="{legend_top - 10}" '
            f'font-family="Georgia, serif" font-size="18" '
            f'fill="#222">{_escape(legend_title)}</text>'
        )

        for idx, item in enumerate(legend_items):
            if not isinstance(item, dict):
                continue
            ly = legend_top + idx * line_height
            color = item.get("color", "#222222")
            label = _escape(item.get("label", ""))

            svg_parts.append(
                f'<circle cx="{legend_left}" cy="{ly}" r="5" '
                f'fill="{color}" stroke="#222" stroke-width="0.7" />'
            )
            svg_parts.append(
                f'<text x="{legend_left + 18}" y="{ly + 4}" '
                f'font-family="Georgia, serif" font-size="13" '
                f'fill="#222">{label}</text>'
            )

    # Fallback if nothing drawn
    if not elements:
        svg_parts.append(
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="20" fill="#999">'
            f'No visual elements generated — check JSON spec.</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
