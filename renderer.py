# renderer.py

from typing import Dict, Any, List, Tuple
import random

# Bottom band reserved for legend / "how to read"
LEGEND_RESERVED_HEIGHT = 140
CONTENT_TOP_MARGIN = 90  # minimum y for main drawing


# ---------- small utilities ----------

def _get_num(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _jitter(value: float, amount: float = 1.6) -> float:
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
    wobble_strength: float = 3.0,
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


# ---------- bbox helpers (for scaling) ----------

def _expand_bbox(
    bbox: Tuple[float, float, float, float],
    xs: List[float],
    ys: List[float],
) -> Tuple[float, float, float, float]:
    """Expand running (min_x, min_y, max_x, max_y) bbox with new points."""
    min_x, min_y, max_x, max_y = bbox
    if not xs or not ys:
        return bbox

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

    return (min_x, min_y, max_x, max_y)


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

        # --- simple primitives we already supported ---
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

        # --- new high-level types from Gemini spec ---
        elif el_type == "cluster_area":
            x = _get_num(el.get("x"), width / 2)
            y = _get_num(el.get("y"), height / 2)
            w = _get_num(el.get("width"), 100)
            h = _get_num(el.get("height"), 60)
            xs = [x, x + w]
            ys = [y, y + h]

        elif el_type == "shape_cluster":
            area_center = el.get("area_center") or [width / 2, height / 2]
            cx = _get_num(area_center[0], width / 2)
            cy = _get_num(area_center[1], height / 2)
            pad = 50
            xs = [cx - pad, cx + pad]
            ys = [cy - pad, cy + pad]

        elif el_type == "visualization_unit":
            x = _get_num(el.get("x"), width / 2)
            y_start = _get_num(el.get("y_start"), height / 2)
            xs = [x - 30, x + 30]
            ys = [y_start, y_start + 140]

        else:
            # skip legend / title boxes / filters etc.
            continue

        (min_x, min_y, max_x, max_y) = _expand_bbox(
            (min_x, min_y, max_x, max_y), xs, ys
        )

    return min_x, min_y, max_x, max_y


# ---------- high-level custom renderers ----------

def _render_shape_cluster(
    svg_parts: List[str],
    el: Dict[str, Any],
    tx_fn,
    ty_fn,
    height: int,
):
    """Draw a cluster like imperfect triangles / spirals / squares / starbursts."""
    area_center = el.get("area_center") or [0, 0]
    cx_raw = _get_num(area_center[0])
    cy_raw = _get_num(area_center[1])

    cx = tx_fn(cx_raw)
    cy = _clamp_y(ty_fn(cy_raw), height)

    count = int(_get_num(el.get("count"), 3))
    color = el.get("color", "#333333")
    opacity = _get_num(el.get("opacity"), 0.85)

    shape = (el.get("shape") or "").lower()

    for _ in range(count):
        local_cx = _jitter(cx, 10)
        local_cy = _clamp_y(_jitter(cy, 10), height)

        if shape == "imperfect_triangle":
            size = random.uniform(10, 20)
            points = []
            for angle in [0, 120, 240]:
                rad = angle * 3.14159 / 180.0
                px = local_cx + size * random.uniform(0.9, 1.1) * \
                    (1.0 * (3.14159/180.0) * 0 + (1 if angle == 0 else 0))
                px = local_cx + size * random.uniform(0.9, 1.1) * \
                    (1.0 * (3.14159/180.0) * 0 + 0)  # simple-ish
            # Honestly, let's just make a small wobbly triangle manually:
            size = random.uniform(12, 22)
            pts = []
            for angle in [0, 120, 240]:
                rad = angle * 3.14159 / 180.0
                px = local_cx + size * random.uniform(0.9, 1.1) * (1.1 * (1 if angle == 0 else -0.5))
                py = local_cy + size * random.uniform(0.9, 1.1) * (0.6 if angle == 0 else 1.0)
                pts.append(f"{px},{py}")
            pts_str = " ".join(pts)
            svg_parts.append(
                f'<polygon points="{pts_str}" fill="none" stroke="{color}" '
                f'stroke-width="2" opacity="{opacity}" />'
            )

        elif shape == "soft_spiral":
            # Small spiral scribble
            turns = random.randint(2, 4)
            radius = random.uniform(8, 16)
            steps = 40
            path_points = []
            for i in range(steps):
                t = i / steps * turns * 6.28318
                r = radius * (i / steps)
                px = local_cx + r * 0.7 * (1 if i % 2 == 0 else 0.9) * \
                    (1.0 * (3.14159 / 180.0) + 0)
                # cheat a bit: swirl-ish circle
                path_points.append(
                    (
                        local_cx + r * 0.5 * random.uniform(0.9, 1.1)
                        * (1 if i % 2 == 0 else -1),
                        local_cy + r * 0.35 * random.uniform(0.9, 1.1)
                        * (1 if i % 3 == 0 else -1),
                    )
                )
            d = "M" + " L".join(f"{x},{y}" for x, y in path_points)
            svg_parts.append(
                f'<path d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="1.8" opacity="{opacity}" />'
            )

        elif shape == "wobbly_square":
            size = random.uniform(14, 22)
            pts = []
            for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                px = local_cx + dx * size + random.uniform(-2.5, 2.5)
                py = local_cy + dy * size + random.uniform(-2.5, 2.5)
                pts.append(f"{px},{py}")
            pts_str = " ".join(pts)
            svg_parts.append(
                f'<polygon points="{pts_str}" fill="{color}" '
                f'stroke="#333" stroke-width="1.4" opacity="{opacity}" />'
            )

        elif shape == "starburst":
            rays = random.randint(10, 14)
            outer = random.uniform(14, 22)
            inner = outer * 0.45
            pts = []
            for i in range(rays * 2):
                r = outer if i % 2 == 0 else inner
                angle = i / (rays * 2) * 6.28318
                px = local_cx + r * 0.9 * random.uniform(0.9, 1.1) * \
                    (1 if i % 2 == 0 else -1)
                py = local_cy + r * 0.6 * random.uniform(0.9, 1.1) * \
                    (1 if i % 3 == 0 else -1)
                pts.append(f"{px},{py}")
            pts_str = " ".join(pts)
            svg_parts.append(
                f'<polygon points="{pts_str}" fill="{color}" '
                f'stroke="#333" stroke-width="1.6" opacity="{opacity}" />'
            )


def _render_visualization_unit(
    svg_parts: List[str],
    el: Dict[str, Any],
    tx_fn,
    ty_fn,
    height: int,
):
    """
    Draw a little Dear-Data-style mini-panel for one day of data:
    - sleep: stacked jittered bar
    - coffee: concentric circles
    - mood: petal blob
    - interactions: scribble loops
    - steps_density: dotted cloud
    """
    x_raw = _get_num(el.get("x", 0))
    y_start_raw = _get_num(el.get("y_start", 0))

    x = tx_fn(x_raw)
    top = _clamp_y(ty_fn(y_start_raw), height)

    # panel height
    panel_h = 130

    data = el.get("data") or {}
    sleep = _get_num(data.get("sleep"), 0)       # 4–9
    coffee = _get_num(data.get("coffee"), 0)     # 0–3
    mood = _get_num(data.get("mood"), 0)         # 2–9
    interactions = _get_num(data.get("interactions"), 0)
    steps_density = _get_num(data.get("steps_density"), 0)

    # 1) Sleep – stacked bar to the left (blue)
    bar_w = 16
    bar_h = sleep * 6.0  # scale
    bar_x = x - 28
    bar_bottom = top + panel_h - 10
    bar_top = _clamp_y(bar_bottom - bar_h, height)

    svg_parts.append(
        f'<rect x="{_jitter(bar_x, 1.5)}" '
        f'y="{_jitter(bar_top, 1.5)}" '
        f'width="{bar_w}" height="{bar_bottom - bar_top}" '
        f'fill="#1B4F72" opacity="0.35" '
        f'stroke="#1B4F72" stroke-width="1.4" />'
    )

    # 2) Coffee – concentric circles near top middle (red-brown)
    cx = x
    cy = top + 20
    for n in range(int(coffee)):
        r = 3 + n * 3
        svg_parts.append(
            f'<circle cx="{_jitter(cx, 1.2)}" cy="{_jitter(cy, 1.2)}" r="{r}" '
            f'fill="none" stroke="#A93226" stroke-width="1.4" opacity="0.85" />'
        )

    # 3) Mood – petal blob on right (yellow/orange)
    mood_radius = 6 + mood * 1.5
    petal_cx = x + 24
    petal_cy = top + 40
    pts = []
    petals = 8
    for i in range(petals):
        angle = i / petals * 6.28318
        r = mood_radius * random.uniform(0.8, 1.1)
        px = petal_cx + r * 0.9 * (1 if i % 2 == 0 else -1)
        py = petal_cy + r * 0.6 * (1 if i % 3 == 0 else -1)
        pts.append(f"{px},{py}")
    pts_str = " ".join(pts)
    svg_parts.append(
        f'<polygon points="{pts_str}" fill="#F39C12" opacity="0.45" '
        f'stroke="#D68910" stroke-width="1.2" />'
    )

    # 4) Interactions – scribble loops (purple) in middle band
    loops = int(interactions)
    center_y = top + panel_h * 0.6
    for _ in range(loops):
        base_r = random.uniform(4, 8)
        cx_loop = _jitter(x, 6)
        cy_loop = _clamp_y(_jitter(center_y, 4), height)
        steps = 25
        pts_loop = []
        for i in range(steps):
            angle = i / steps * 6.28318 * random.uniform(0.8, 1.2)
            r = base_r * (0.7 + 0.3 * random.random())
            px = cx_loop + r * 0.9 * (1 if i % 2 == 0 else -1)
            py = cy_loop + r * 0.7 * (1 if i % 3 == 0 else -1)
            pts_loop.append(f"{px},{py}")
        d = "M" + " L".join(pts_loop)
        svg_parts.append(
            f'<path d="{d}" fill="none" stroke="#512E5F" '
            f'stroke-width="1.1" opacity="0.7" />'
        )

    # 5) Steps density – tiny dots as texture near bottom
    dots = int(steps_density)
    base_y = top + panel_h - 20
    for _ in range(dots):
        dx = random.uniform(-12, 12)
        dy = random.uniform(-8, 8)
        svg_parts.append(
            f'<circle cx="{x + dx}" cy="{_clamp_y(base_y + dy, height)}" r="0.9" '
            f'fill="#7F8C8D" opacity="0.6" />'
        )


# ---------- main render function ----------

def render_visual_spec(spec: Dict[str, Any]) -> str:
    """
    Convert a JSON visual specification into an SVG string.

    Expected spec format (flexible):
      {
        "canvas": {"width": ..., "height": ..., "background" or "background_color": "#..."},
        "elements": [...],
        "legend": [...]  OR  {"title": "...", "items": [...]},
        "title": "..."
      }
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
    legend_spec = spec.get("legend", None)
    title_text: str = spec.get("title", "") or ""

    # SVG shell (responsive)
    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # Light paper texture background (flat color, mood-based)
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
    )

    # Optional soft drop shadow for whole postcard
    svg_parts.append(
        '<defs>'
        '<filter id="softShadow" x="-0.05" y="-0.05" width="1.1" height="1.1">'
        '<feDropShadow dx="1.2" dy="1.4" stdDeviation="0.8" '
        'flood-color="#000000" flood-opacity="0.18"/>'
        '</filter>'
        '</defs>'
    )

    # Title at top (if Gemini doesn't already produce it as an element)
    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="50" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="24" fill="#222">'
            f'{_escape(title_text)}</text>'
        )

    # Main content group with subtle shadow
    svg_parts.append('<g filter="url(#softShadow)">')

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
        scale = min(sx, sy) * 0.95  # use most of the area

        target_cx = width / 2.0
        target_cy = (margin_top + margin_bottom) / 2.0

        def tx(x: float) -> float:
            return target_cx + (x - orig_cx) * scale

        def ty(y: float) -> float:
            return target_cy + (y - orig_cy) * scale

    else:
        # Fallback: identity transforms
        def tx(x: float) -> float:
            return x

        def ty(y: float) -> float:
            return y

    # 2️⃣ Draw elements (including new high-level ones)
    for el in elements:
        el_type = (el.get("type") or "").lower()

        # ---------- cluster area (subtle panel background) ----------
        if el_type == "cluster_area":
            x_raw = _get_num(el.get("x"), width / 2)
            y_raw = _get_num(el.get("y"), height / 2)
            w = _get_num(el.get("width"), 120)
            h = _get_num(el.get("height"), 60)

            x = tx(x_raw)
            y = _clamp_y(ty(y_raw), height)

            svg_parts.append(
                f'<rect x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" '
                f'rx="10" ry="10" fill="#FDF6E3" opacity="0.6" '
                f'stroke="#E0D3B8" stroke-width="1.4" />'
            )
            continue

        # ---------- shape cluster ----------
        if el_type == "shape_cluster":
            _render_shape_cluster(svg_parts, el, tx, ty, height)
            continue

        # ---------- timeline separator ----------
        if el_type == "timeline_separator":
            x_start_raw = _get_num(el.get("x_start"), 40)
            x_end_raw = _get_num(el.get("x_end"), width - 40)
            y_raw = _get_num(el.get("y"), height / 2)
            color = el.get("color", "#999999")
            stroke_w = _get_num(el.get("stroke_width"), 1.2)

            x1 = tx(x_start_raw)
            x2 = tx(x_end_raw)
            y = _clamp_y(ty(y_raw), height)

            d = _wobble_path(x1, y, x2, y, wobble_strength=2.0)
            svg_parts.append(
                f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke_w}" '
                f'stroke-dasharray="4 4" opacity="0.7" />'
            )
            continue

        # ---------- visualization unit (mini grid panel) ----------
        if el_type == "visualization_unit":
            _render_visualization_unit(svg_parts, el, tx, ty, height)
            continue

        # ---------- legend title box (background for bottom legend) ----------
        if el_type == "legend_title_box":
            # we draw this in the legend section later; skip here
            continue

        # ---------- standard primitives ----------

        fill = el.get("fill", None)
        stroke = el.get("stroke", None)

        # text elements from Gemini often use "color" key
        if not fill and "color" in el and el_type == "text":
            fill = el.get("color")

        if fill and not stroke and fill != "none" and el_type != "text":
            stroke = "#222222"
        if not fill:
            fill = "none"
        if not stroke and el_type != "text":
            stroke = "#222222"

        stroke_width = _get_num(el.get("strokeWidth"), 2.1)
        opacity = _get_num(el.get("opacity"), random.uniform(0.86, 1.0))

        if el_type == "circle":
            cx_raw = _get_num(el.get("x"), width / 2)
            cy_raw = _get_num(el.get("y"), height / 2)
            r_raw = _get_num(el.get("radius"), 8)

            cx_scaled = tx(cx_raw)
            cy_scaled = ty(cy_raw)

            cx = _jitter(cx_scaled, amount=2.3)
            cy = _clamp_y(_jitter(cy_scaled, amount=2.3), height)
            r = max(_jitter(r_raw, amount=1.0), 0.8)

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

            tx_val = tx(tx_raw)
            ty_val = ty(ty_raw)

            tx_final = _jitter(tx_val, amount=1.2)
            ty_final = _clamp_y(_jitter(ty_val, amount=1.2), height)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("font_size") or el.get("fontSize"), 14)
            fill_text = el.get("color", el.get("fill", "#333333"))
            anchor = el.get("textAnchor", "middle" if "title" in (el.get("style") or "") else "start")

            svg_parts.append(
                f'<text x="{tx_final}" y="{ty_final}" text-anchor="{anchor}" '
                f'font-family="Georgia, serif" font-size="{font_size}" '
                f'fill="{fill_text}" opacity="{opacity}">{content}</text>'
            )

    # close main group with shadow
    svg_parts.append("</g>")

    # 3️⃣ Legend – in reserved bottom band, clean and non-overlapping
    legend_items: List[Dict[str, Any]] = []
    legend_title = "Legend"

    if isinstance(legend_spec, dict):
        legend_title = legend_spec.get("title", "Legend")
        legend_items = legend_spec.get("items", []) or []
    elif isinstance(legend_spec, list):
        legend_items = legend_spec

    if legend_items:
        legend_top = height - LEGEND_RESERVED_HEIGHT + 30
        legend_left = 70
        line_height = 22

        # optional boxed background
        svg_parts.append(
            f'<rect x="{legend_left - 30}" y="{legend_top - 26}" '
            f'width="{width - 2 * (legend_left - 30)}" '
            f'height="{LEGEND_RESERVED_HEIGHT - 40}" '
            f'fill="rgba(253, 247, 239, 0.9)" stroke="#E0D3B8" stroke-width="1" />'
        )

        svg_parts.append(
            f'<text x="{legend_left}" y="{legend_top - 6}" '
            f'font-family="Georgia, serif" font-size="18" '
            f'fill="#222">{_escape(legend_title)}</text>'
        )

        for idx, item in enumerate(legend_items):
            ly = legend_top + 8 + idx * line_height
            color = item.get("color", "#222222")
            label = _escape(item.get("label", ""))
            shape_desc = item.get("shape")
            if shape_desc:
                label = f"{label} — {shape_desc}"

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
