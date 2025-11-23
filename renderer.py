# renderer.py
#
# MAX-DEAR-DATA VERSION (Option A)
# - Mood-based full-canvas background
# - Paper texture
# - Strong hand-drawn wobble
# - Dramatic clusters + halos
# - Better centering + use of full canvas
# - Smarter, less-cluttered legend (multi-column)
#

from typing import Dict, Any, List
import random

# Bottom band reserved for legend / "how to read"
LEGEND_RESERVED_HEIGHT = 150
CONTENT_TOP_MARGIN = 90  # minimum y for main drawing


# -------------------------
# Small helpers
# -------------------------


def _get_num(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _jitter(value: float, amount: float = 2.3) -> float:
    """Small random offset to mimic hand-drawn placement."""
    return value + random.uniform(-amount, amount)


def _clamp_y(y: float, height: int) -> float:
    """
    Keep y within the main drawing band:
    from CONTENT_TOP_MARGIN down to height - LEGEND_RESERVED_HEIGHT - 24.
    This prevents overlap with the bottom legend and avoids objects touching edges.
    """
    content_bottom = height - LEGEND_RESERVED_HEIGHT - 24
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
    Used to scale + center the whole composition so it uses most of the canvas.
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
            # Skip paths for bbox – radial grids/mandalas are scaffolding.
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


# -------------------------
# Main render function
# -------------------------


def render_visual_spec(spec: Dict[str, Any]) -> str:
    """
    Convert a JSON visual specification into an SVG string.

    Expected spec format (flexible):
      {
        "canvas": {
            "width": ...,
            "height": ...,
            "background": "#...",        # OR
            "background_color": "#..."
        },
        "elements": [...],
        "legend": [... ]                # OR {"title": "...", "items": [...]}
        "title": "..."
      }
    """

    canvas = spec.get("canvas", {}) or {}
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 800))

    # Accept both background and background_color; default to warm ivory.
    background = (
        canvas.get("background_color")
        or canvas.get("background")
        or "#F7F0E5"
    )

    elements: List[Dict[str, Any]] = spec.get("elements", []) or []

    # Legend can be either list or object with title + items
    legend_raw = spec.get("legend", []) or []
    if isinstance(legend_raw, dict):
        legend_title = legend_raw.get("title", "Legend")
        legend_items = legend_raw.get("items", []) or []
    else:
        legend_title = "Legend"
        legend_items = legend_raw

    # Title: prefer spec title, fallback to legend title if present
    title_text: str = spec.get("title") or legend_title or ""

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # --- defs: paper texture + soft shadow ---
    svg_parts.append(
        """
  <defs>
    <filter id="paperTexture" x="0" y="0" width="1" height="1">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="noStitch" result="noise"/>
      <feColorMatrix type="matrix" values="
        1 0 0 0 0
        0 1 0 0 0
        0 0 1 0 0
        0 0 0 0.18 0" in="noise" result="grain"/>
      <feBlend in="SourceGraphic" in2="grain" mode="soft-light"/>
    </filter>

    <filter id="softShadow" x="-0.05" y="-0.05" width="1.1" height="1.1">
      <feDropShadow dx="1.2" dy="1.4" stdDeviation="0.8" flood-color="#000000" flood-opacity="0.18"/>
    </filter>
  </defs>
"""
    )

    # Background paper
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="{background}" filter="url(#paperTexture)" />'
    )

    # Subtle inner margin frame (postcard border)
    frame_margin = 26
    frame_height = height - LEGEND_RESERVED_HEIGHT - frame_margin
    svg_parts.append(
        f'<rect x="{frame_margin}" y="{frame_margin}" '
        f'width="{width - 2*frame_margin}" '
        f'height="{frame_height - frame_margin}" '
        f'fill="none" stroke="#E0D6C6" stroke-width="1.4" '
        f'stroke-linecap="round" stroke-dasharray="3 5" opacity="0.9" />'
    )

    # Title at top
    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="58" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="27" '
            f'fill="#2A2520">'
            f'{_escape(title_text)}</text>'
        )

    # Content band geometry
    content_bottom = height - LEGEND_RESERVED_HEIGHT - 20
    margin_left_right = width * 0.08
    margin_top = CONTENT_TOP_MARGIN + 6
    margin_bottom = content_bottom - 8

    # --- 1) Compute bbox of drawing, then scale + translate to fill canvas ---
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
        scale = min(sx, sy) * 0.95  # use almost full available space

        target_cx = width / 2.0
        target_cy = (margin_top + margin_bottom) / 2.0

        def tx(x: float) -> float:
            return target_cx + (x - orig_cx) * scale

        def ty(y: float) -> float:
            return target_cy + (y - orig_cy) * scale

    else:
        # Fallback: identity
        scale = 1.0

        def tx(x: float) -> float:
            return x

        def ty(y: float) -> float:
            return y

    # --- 2) Draw main elements with jitter, halos, more drama ---

    for el in elements:
        el_type = (el.get("type") or "").lower()

        fill = el.get("fill", None)
        stroke = el.get("stroke", None)

        if fill and not stroke and fill != "none":
            stroke = "#3A312A"
        if not fill:
            fill = "none"
        if not stroke:
            stroke = "#3A312A"

        # Slightly thicker default lines for marker-feel
        stroke_width = _get_num(el.get("strokeWidth"), 2.4)
        opacity = _get_num(el.get("opacity"), random.uniform(0.82, 1.0))

        if el_type == "circle":
            cx_raw = _get_num(el.get("x"), width / 2)
            cy_raw = _get_num(el.get("y"), height / 2)
            r_raw = _get_num(el.get("radius"), 8)

            cx_scaled = tx(cx_raw)
            cy_scaled = ty(cy_raw)

            cx = _jitter(cx_scaled, amount=3.0)
            cy = _clamp_y(_jitter(cy_scaled, amount=3.0), height)
            r = max(
                _jitter(r_raw * (scale if scale > 0 else 1.0), amount=1.4),
                0.9,
            )

            # Halo / echo circle for more drama
            halo_r = r + random.uniform(2.0, 6.0)
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{halo_r}" '
                f'fill="none" stroke="{stroke}" stroke-width="{stroke_width * 0.6}" '
                f'opacity="{opacity * 0.3}" />'
            )

            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}" filter="url(#softShadow)" />'
            )

            # Micro drama dots around circle
            for _ in range(random.randint(1, 4)):
                angle = random.uniform(0, 6.283)
                dist = halo_r + random.uniform(3, 10)
                mx = cx + dist * 0.5 * random.uniform(0.8, 1.2) * (1 if random.random() < 0.5 else -1)
                my = cy + dist * 0.5 * random.uniform(0.8, 1.2) * (1 if random.random() < 0.5 else -1)
                my = _clamp_y(my, height)
                svg_parts.append(
                    f'<circle cx="{mx}" cy="{my}" r="1.4" '
                    f'fill="{fill if fill != "none" else stroke}" '
                    f'opacity="{opacity * 0.55}" />'
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
                f'opacity="{opacity}" stroke-linecap="round" />'
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
                        px = _jitter(px_scaled, amount=2.4)
                        py = _clamp_y(_jitter(py_scaled, amount=2.4), height)
                        jittered_points.append(f"{px},{py}")
                if jittered_points:
                    pts_str = " ".join(jittered_points)
                    # Fill + outline + softer shadow
                    svg_parts.append(
                        f'<polygon points="{pts_str}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{stroke_width}" '
                        f'opacity="{opacity}" filter="url(#softShadow)" />'
                    )
                    # Decorative inner lines for drama
                    if random.random() < 0.4:
                        svg_parts.append(
                            f'<polygon points="{pts_str}" fill="none" '
                            f'stroke="{stroke}" stroke-width="{stroke_width * 0.5}" '
                            f'opacity="{opacity * 0.5}" '
                            f'stroke-dasharray="3 4" />'
                        )

        elif el_type == "path":
            d_raw = el.get("d") or ""
            if d_raw:
                d = _escape(d_raw)
                svg_parts.append(
                    f'<path d="{d}" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="{stroke_width}" '
                    f'opacity="{opacity}" stroke-linecap="round" />'
                )

        elif el_type == "text":
            tx_raw = _get_num(el.get("x"), width / 2)
            ty_raw = _get_num(el.get("y"), height / 2)

            tx_scaled_val = tx(tx_raw)
            ty_scaled_val = ty(ty_raw)

            tx_final = _jitter(tx_scaled_val, amount=1.6)
            ty_final = _clamp_y(_jitter(ty_scaled_val, amount=1.6), height)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill_text = el.get("fill", "#3B332C")
            anchor = el.get("textAnchor", "start")

            svg_parts.append(
                f'<text x="{tx_final}" y="{ty_final}" text-anchor="{anchor}" '
                f'font-family="Georgia, serif" font-size="{font_size}" '
                f'fill="{fill_text}" opacity="{opacity}">{content}</text>'
            )

    # If nothing drawn, show friendly message
    if not elements:
        svg_parts.append(
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="20" fill="#999">'
            f'No visual elements generated — check JSON spec.</text>'
        )

    # --- 3) Legend – multi-column, de-cluttered at bottom ---

    if legend_items:
        legend_top = height - LEGEND_RESERVED_HEIGHT + 40
        legend_left = 70
        line_height = 24

        # Legend title
        svg_parts.append(
            f'<text x="{legend_left}" y="{legend_top - 16}" '
            f'font-family="Georgia, serif" font-size="18" '
            f'fill="#2A2520">{_escape(legend_title or "Legend")}</text>'
        )

        n_items = len(legend_items)
        # Decide 1 or 2 columns based on count
        if n_items <= 7:
            cols = 1
        else:
            cols = 2

        rows_per_col = (n_items + cols - 1) // cols
        col_width = (width - 2 * legend_left) / cols

        for idx, item in enumerate(legend_items):
            col_idx = idx // rows_per_col
            row_idx = idx % rows_per_col

            lx = legend_left + col_idx * col_width
            ly = legend_top + row_idx * line_height

            color = item.get("color", "#444444")
            label = _escape(item.get("label", ""))

            svg_parts.append(
                f'<circle cx="{lx}" cy="{ly}" r="5.2" '
                f'fill="{color}" stroke="#2A2520" stroke-width="0.7" />'
            )
            svg_parts.append(
                f'<text x="{lx + 16}" y="{ly + 4}" '
                f'font-family="Georgia, serif" font-size="13" '
                f'fill="#2A2520">{label}</text>'
            )

    svg_parts.append("</svg>")
    return "".join(svg_parts)
