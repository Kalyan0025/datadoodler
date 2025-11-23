# renderer.py

from typing import Dict, Any, List
import random


def _get_num(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _jitter(value: float, amount: float = 2.0) -> float:
    """Apply a small random offset to mimic hand-drawn placement."""
    return value + random.uniform(-amount, amount)


def _wobble_path(x1: float, y1: float, x2: float, y2: float, wobble_strength: float = 4.0) -> str:
    """
    Generate a slightly imperfect SVG quadratic path between two points.
    This mimics a hand-drawn line with a little wobble.
    """
    cx = (x1 + x2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    cy = (y1 + y2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
    return f"M{x1},{y1} Q{cx},{cy} {x2},{y2}"


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

    canvas = spec.get("canvas", {})
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 800))
    background = canvas.get("background", "#FDFBF7")

    elements: List[Dict[str, Any]] = spec.get("elements", []) or []
    legend: List[Dict[str, Any]] = spec.get("legend", []) or []
    title_text: str = spec.get("title", "") or ""

    # Start SVG – responsive
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

    # Optional title at top
    if title_text:
        svg_parts.append(
            f'<text x="{width / 2}" y="40" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="26" '
            f'fill="#222">{_escape(title_text)}</text>'
        )

    # Core elements
    for el in elements:
        el_type = (el.get("type") or "").lower()

        # Normalize some common fields
        fill = el.get("fill", "none")
        stroke = el.get("stroke", "#222222")
        # Use thicker, marker-like defaults if not specified
        stroke_width = _get_num(el.get("strokeWidth"), 2.0)
        # Slight opacity variation for hand-drawn ink feel
        opacity = _get_num(el.get("opacity"), random.uniform(0.85, 1.0))

        if el_type == "circle":
            cx_raw = _get_num(el.get("x"), width / 2)
            cy_raw = _get_num(el.get("y"), height / 2)
            r_raw = _get_num(el.get("radius"), 6)

            # Jitter center and radius slightly for hand-drawn feel
            cx = _jitter(cx_raw, amount=3.0)
            cy = _jitter(cy_raw, amount=3.0)
            r = max(_jitter(r_raw, amount=1.5), 0.5)

            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" '
                f'opacity="{opacity}" />'
            )

        elif el_type == "line":
            # Instead of a perfect line, render a wobbly path
            x1_raw = _get_num(el.get("x"), width / 2)
            y1_raw = _get_num(el.get("y"), height / 2)
            x2_raw = _get_num(el.get("x2"), x1_raw + 10)
            y2_raw = _get_num(el.get("y2"), y1_raw)

            # Slight jitter on endpoints
            x1 = _jitter(x1_raw, amount=2.5)
            y1 = _jitter(y1_raw, amount=2.5)
            x2 = _jitter(x2_raw, amount=2.5)
            y2 = _jitter(y2_raw, amount=2.5)

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
                        px = _jitter(_get_num(p[0]), amount=2.0)
                        py = _jitter(_get_num(p[1]), amount=2.0)
                        jittered_points.append(f"{px},{py}")
                if jittered_points:
                    pts_str = " ".join(jittered_points)
                    svg_parts.append(
                        f'<polygon points="{pts_str}" fill="{fill}" '
                        f'stroke="{stroke}" stroke-width="{stroke_width}" '
                        f'opacity="{opacity}" />'
                    )

        elif el_type == "path":
            # Use provided path but allow slight opacity + stroke adjustments
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
            tx = _jitter(tx_raw, amount=1.5)
            ty = _jitter(ty_raw, amount=1.5)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill_text = el.get("fill", "#222222")
            anchor = el.get("textAnchor", "start")

            svg_parts.append(
                f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                f'font-family="Georgia, serif" font-size="{font_size}" '
                f'fill="{fill_text}" opacity="{opacity}">{content}</text>'
            )

    # Simple legend at bottom-left
    if legend:
        legend_x = 40
        legend_y = height - 120
        line_height = 22

        svg_parts.append(
            f'<text x="{legend_x}" y="{legend_y - 10}" '
            f'font-family="Georgia, serif" font-size="16" '
            f'fill="#222">Legend</text>'
        )

        for idx, item in enumerate(legend):
            ly = legend_y + idx * line_height
            color = item.get("color", "#222222")
            label = _escape(item.get("label", ""))

            svg_parts.append(
                f'<circle cx="{legend_x}" cy="{ly}" r="5" '
                f'fill="{color}" stroke="#222" stroke-width="0.5" />'
            )
            svg_parts.append(
                f'<text x="{legend_x + 14}" y="{ly + 4}" '
                f'font-family="Georgia, serif" font-size="13" '
                f'fill="#222">{label}</text>'
            )

    # Fallback message if no elements
    if not elements:
        svg_parts.append(
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="20" fill="#999999">'
            f'No visual elements generated — check JSON spec.</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def _escape(text: str) -> str:
    """Escape basic XML entities."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
