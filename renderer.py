from typing import Dict, Any, List


def _scale(val: float, max_val: float) -> float:
    """Scale normalized coordinate (0–1) into absolute SVG space."""
    try:
        return float(val) * float(max_val)
    except:
        return 0.0


def _render_circle(shape: Dict[str, Any], width: int, height: int) -> str:
    cx = _scale(shape.get("cx", 0.5), width)
    cy = _scale(shape.get("cy", 0.5), height)
    r = shape.get("r", 0.02) * min(width, height)

    fill = shape.get("fill", "none")
    stroke = shape.get("stroke", "#222")
    stroke_width = shape.get("strokeWidth", 1)

    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'


def _render_line(shape: Dict[str, Any], width: int, height: int) -> str:
    x1 = _scale(shape.get("x1", 0.2), width)
    y1 = _scale(shape.get("y1", 0.2), height)
    x2 = _scale(shape.get("x2", 0.8), width)
    y2 = _scale(shape.get("y2", 0.8), height)

    stroke = shape.get("stroke", "#222")
    stroke_width = shape.get("strokeWidth", 1)

    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}" />'


def _render_path(shape: Dict[str, Any], width: int, height: int) -> str:
    """
    Handle freeform SVG paths.
    Gemini sends normalized coordinates inside the `d` string.
    We scale numbers in order: x,y,x,y,...
    """
    raw_d = shape.get("d", "")
    if not raw_d:
        return ""

    # Scale numbers sequentially (x then y then x then y...)
    import re
    nums = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_d)

    scaled_nums = []
    is_x = True
    for n in nums:
        v = float(n)
        if is_x:
            scaled_nums.append(str(v * width))
        else:
            scaled_nums.append(str(v * height))
        is_x = not is_x

    # Rebuild the path by replacing numbers one-by-one
    def repl(match):
        return scaled_nums.pop(0)

    scaled_d = re.sub(r"[-+]?\d*\.\d+|[-+]?\d+", repl, raw_d)

    stroke = shape.get("stroke", "#222")
    fill = shape.get("fill", "none")
    stroke_width = shape.get("strokeWidth", 1)

    return f'<path d="{scaled_d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'


def _render_polygon(shape: Dict[str, Any], width: int, height: int) -> str:
    points = shape.get("points", [])
    svg_points = " ".join(
        f"{_scale(x, width)},{_scale(y, height)}" for x, y in points
    )

    fill = shape.get("fill", "none")
    stroke = shape.get("stroke", "#222")
    stroke_width = shape.get("strokeWidth", 1)

    return f'<polygon points="{svg_points}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'


def _render_text(shape: Dict[str, Any], width: int, height: int) -> str:
    text = shape.get("text", "")
    x = _scale(shape.get("x", 0.1), width)
    y = _scale(shape.get("y", 0.1), height)
    size = shape.get("fontSize", shape.get("size", 14))
    fill = shape.get("fill", "#222")
    font_family = "Georgia, serif"

    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-family="{font_family}">{text}</text>'


def render_svg_from_spec(spec: Dict[str, Any]) -> str:
    """
    Convert the visual_spec (JSON from Gemini) into an SVG string.
    """

    canvas = spec.get("canvas", {})
    width = int(canvas.get("width", 1200))
    height = int(canvas.get("height", 800))
    background = canvas.get("background", "#ffffff")

    svg_parts: List[str] = []

    # SVG header
    svg_parts.append(
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    # Background
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
    )

    # Render shapes
    for shape in spec.get("shapes", []):
        t = shape.get("type")
        if t == "circle":
            svg_parts.append(_render_circle(shape, width, height))
        elif t == "line":
            svg_parts.append(_render_line(shape, width, height))
        elif t == "path":
            svg_parts.append(_render_path(shape, width, height))
        elif t == "polygon":
            svg_parts.append(_render_polygon(shape, width, height))
        elif t == "text":
            svg_parts.append(_render_text(shape, width, height))
        else:
            continue

    # Render labels (optional)
    for label in spec.get("labels", []):
        svg_parts.append(_render_text(label, width, height))

    # Close SVG
    svg_parts.append("</svg>")

    return "\n".join(svg_parts)
