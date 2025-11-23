# renderer.py

from typing import Dict, Any, List


def _get_num(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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

    # Start SVG – make it responsive (scaled to container width)
    svg_parts = [
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

        if el_type == "circle":
            cx = _get_num(el.get("x"), width / 2)
            cy = _get_num(el.get("y"), height / 2)
            r = max(_get_num(el.get("radius"), 4), 0.5)
            fill = el.get("fill", "none")
            stroke = el.get("stroke", "#222222")
            sw = _get_num(el.get("strokeWidth"), 1)
            opacity = _get_num(el.get("opacity"), 1.0)

            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                f'opacity="{opacity}" />'
            )

        elif el_type == "line":
            x1 = _get_num(el.get("x"), width / 2)
            y1 = _get_num(el.get("y"), height / 2)
            x2 = _get_num(el.get("x2"), x1 + 10)
            y2 = _get_num(el.get("y2"), y1)
            stroke = el.get("stroke", "#222222")
            sw = _get_num(el.get("strokeWidth"), 1)
            opacity = _get_num(el.get("opacity"), 1.0)

            svg_parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" />'
            )

        elif el_type == "polygon":
            pts = el.get("points") or []
            if isinstance(pts, list) and pts:
                pts_str = " ".join(
                    f'{_get_num(p[0])},{_get_num(p[1])}'
                    for p in pts
                    if isinstance(p, (list, tuple)) and len(p) >= 2
                )
                fill = el.get("fill", "none")
                stroke = el.get("stroke", "#222222")
                sw = _get_num(el.get("strokeWidth"), 1)
                opacity = _get_num(el.get("opacity"), 1.0)

                svg_parts.append(
                    f'<polygon points="{pts_str}" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" />'
                )

        elif el_type == "path":
            d = el.get("d") or ""
            if d:
                fill = el.get("fill", "none")
                stroke = el.get("stroke", "#222222")
                sw = _get_num(el.get("strokeWidth"), 1.0)
                opacity = _get_num(el.get("opacity"), 1.0)

                svg_parts.append(
                    f'<path d="{_escape(d)}" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" />'
                )

        elif el_type == "text":
            tx = _get_num(el.get("x"), width / 2)
            ty = _get_num(el.get("y"), height / 2)
            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
            fill = el.get("fill", "#222222")
            anchor = el.get("textAnchor", "start")

            svg_parts.append(
                f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" '
                f'font-family="Georgia, serif" font-size="{font_size}" '
                f'fill="{fill}">{content}</text>'
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
