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

def _adjust_legend(legend: List[Dict[str, Any]], canvas_width: int) -> List[Dict[str, Any]]:
    """Arrange the legend horizontally or vertically based on available space."""
    legend_area = canvas_width - 40  # 40px padding for edges
    
    if len(legend) < 5:
        space_per_item = legend_area / len(legend)
        x_position = 20  # Initial offset
        for item in legend:
            item['x'] = x_position
            item['y'] = 850  # Fixed y position for bottom legend
            x_position += space_per_item
    else:
        space_per_item = (canvas_width - 40) / len(legend)
        y_position = 850
        for item in legend:
            item['x'] = 40  # Fixed x position for vertical legend
            item['y'] = y_position
            y_position += space_per_item

    return legend

def render_visual_spec(spec: Dict[str, Any]) -> str:
    """Convert a JSON visual specification into an SVG string."""
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
            f'font-family="Dancing Script, cursive" font-size="24" fill="#222"> '
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

        sx = avail_w / (max_x - min_x)
        sy = avail_h / (max_y - min_y)
        scale = min(sx, sy) * 0.9

        target_cx = width / 2.0
        target_cy = (margin_top + margin_bottom) / 2.0

        def tx(x: float) -> float:
            return target_cx + (x - orig_cx) * scale

        def ty(y: float) -> float:
            return target_cy + (y - orig_cy) * scale

    else:
        scale = 1.0

        def tx(x: float) -> float:
            return x

        def ty(y: float) -> float:
            return y

    for el in elements:
        el_type = (el.get("type") or "").lower()

        if el_type not in {"circle", "line", "polygon", "path", "text"}:
            continue

        fill = el.get("fill", None)
        stroke = el.get("stroke", None)

        if fill and not stroke and fill != "none":
            stroke = "#222222"
        if not fill:
            fill = "none"
        if not stroke:
            stroke = "#222222"

        stroke_width = _get_num(el.get("strokeWidth"), 2.0)
        opacity = _get_num(el.get("opacity"), random.uniform(0.86, 1.0))

        if el_type == "circle":
            cx_raw = _get_num(el.get("x"), width / 2)
            cy_raw = _get_num(el.get("y"), height / 2)
            r_raw = _get_num(el.get("radius"), 8)

            cx_scaled = tx(cx_raw)
            cy_scaled = ty(cy_raw)

            cx = _jitter(cx_scaled, amount=2.3)
            cy = _clamp_y(_jitter(cy_scaled, amount=2.3), height)
            r = max(_jitter(r_raw * scale, amount=1.0), 0.8)

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

            x1 = _jitter(x1_scaled, amount=2.0)
            y1 = _clamp_y(_jitter(y1_scaled, amount=2.0), height)
            x2 = _jitter(x2_scaled, amount=2.0)
            y2 = _clamp_y(_jitter(y2_scaled, amount=2.0), height)

            d = _wobble_path(x1, y1, x2, y2, wobble_strength=3.0)

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
                        px = _jitter(px_scaled, amount=1.8)
                        py = _clamp_y(_jitter(py_scaled, amount=1.8), height)
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

            tx_final = _jitter(tx_scaled_val, amount=1.2)
            ty_final = _clamp_y(_jitter(ty_scaled_val, amount=1.2), height)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill_text = el.get("fill", el.get("color", "#333333"))
            anchor = el.get("textAnchor", "start")

            svg_parts.append(
                f'<text x="{tx_final}" y="{ty_final}" text-anchor="{anchor}" '
                f'font-family="Dancing Script, cursive" font-size="{font_size}" '
                f'fill="{fill_text}" opacity="{opacity}">{content}</text>'
            )

    if legend_items:
        legend_top = height - LEGEND_RESERVED_HEIGHT + 30
        legend_left = 70
        line_height = 24

        svg_parts.append(
            f'<text x="{legend_left}" y="{legend_top - 10}" '
            f'font-family="Dancing Script, cursive" font-size="18" '
            f'fill="#222">{_escape(legend_title)}</text>'
        )

        for idx, item in enumerate(legend_items):
            if not isinstance(item, dict):
                continue
            ly = legend_top + idx * line_height
            color = item.get("color", "#222222")
            label = _escape(item.get("label", ""))

            shape = item.get("shape", "circle")  # Shape variation
            if shape == "circle":
                svg_parts.append(
                    f'<circle cx="{legend_left}" cy="{ly}" r="5" '
                    f'fill="{color}" stroke="#222" stroke-width="0.7" />'
                )
            elif shape == "triangle":
                svg_parts.append(
                    f'<polygon points="{legend_left-5},{ly+7} {legend_left+5},{ly+7} {legend_left},{ly-5}" '
                    f'fill="{color}" stroke="#222" stroke-width="0.7" />'
                )

            svg_parts.append(
                f'<text x="{legend_left + 18}" y="{ly + 4}" '
                f'font-family="Dancing Script, cursive" font-size="13" '
                f'fill="#222">{label}</text>'
            )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
