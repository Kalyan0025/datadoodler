# renderer.py

from typing import Dict, Any, List
import random


LEGEND_RESERVED_HEIGHT = 140   # bottom band reserved for legend
CONTENT_TOP_MARGIN = 90        # minimum y for main drawing


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


def render_visual_spec(spec: Dict[str, Any]) -> str:
    """
    Convert a JSON visual specification into an SVG string.

    Expected spec format:
      {
        "canvas": {"width": ..., "height": ..., "background": "#..."},
        "elements": [...],
        "legend": [...],
        "title": "..."
      }
    """

    canvas = spec.get("canvas", {}) or {}
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 800))

    background = canvas.get("background") or "#FDFBF7"

    elements: List[Dict[str, Any]] = spec.get("elements", []) or []
    legend: List[Dict[str, Any]] = spec.get("legend", []) or []
    title_text: str = spec.get("title", "") or ""

    svg_parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # Background
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
    )

    # Title
    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="60" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="26" fill="#222">'
            f'{_escape(title_text)}</text>'
        )

    # Main drawing band boundaries
    content_bottom = height - LEGEND_RESERVED_HEIGHT - 20

    # Core elements
    for el in elements:
        el_type = (el.get("type") or "").lower()

        fill = el.get("fill", None)
        stroke = el.get("stroke", None)

        if fill and not stroke and fill != "none":
            stroke = "#222222"
        if not fill:
            fill = "none"
        if not stroke:
            stroke = "#222222"

        stroke_width = _get_num(el.get("strokeWidth"), 2.1)
        opacity = _get_num(el.get("opacity"), random.uniform(0.86, 1.0))

        if el_type == "circle":
            cx_raw = _get_num(el.get("x"), width / 2)
            cy_raw = _get_num(el.get("y"), height / 2)
            r_raw = _get_num(el.get("radius"), 8)

            cx = _jitter(cx_raw, amount=2.3)
            cy = _clamp_y(_jitter(cy_raw, amount=2.3), height)
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

            x1 = _jitter(x1_raw, amount=2.0)
            y1 = _clamp_y(_jitter(y1_raw, amount=2.0), height)
            x2 = _jitter(x2_raw, amount=2.0)
            y2 = _clamp_y(_jitter(y2_raw, amount=2.0), height)

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
                        px = _jitter(_get_num(p[0]), amount=1.8)
                        py = _clamp_y(_jitter(_get_num(p[1]), amount=1.8), height)
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
                # Try to clamp using a simple transform if needed is complex; for now assume
                # path designed within band by model.
                svg_parts.append(
                    f'<path d="{d}" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="{stroke_width}" '
                    f'opacity="{opacity}" />'
                )

        elif el_type == "text":
            tx_raw = _get_num(el.get("x"), width / 2)
            ty_raw = _get_num(el.get("y"), height / 2)

            tx = _jitter(tx_raw, amount=1.2)
            ty = _clamp_y(_jitter(ty_raw, amount=1.2), height)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill_text = el.get("fill", "#333333")
            anchor = el.get("textAnchor", "start")

            svg_parts.append(
                f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                f'font-family="Georgia, serif" font-size="{font_size}" '
                f'fill="{fill_text}" opacity="{opacity}">{content}</text>'
            )

    # Legend – in reserved bottom band
    if legend:
        legend_top = height - LEGEND_RESERVED_HEIGHT + 30
        legend_left = 70
        line_height = 26

        svg_parts.append(
            f'<text x="{legend_left}" y="{legend_top - 10}" '
            f'font-family="Georgia, serif" font-size="18" '
            f'fill="#222">Legend</text>'
        )

        for idx, item in enumerate(legend):
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
