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


def _jitter(value: float, amount: float = 1.6) -> float:
def _jitter(value: float, amount: float = 2.0) -> float:
    """Small random offset to mimic hand-drawn placement."""
    return value + random.uniform(-amount, amount)

@@ -37,7 +37,7 @@
    y1: float,
    x2: float,
    y2: float,
    wobble_strength: float = 3.0,
    wobble_strength: float = 4.0,
) -> str:
    """Slightly imperfect SVG quadratic path between two points."""
    cx = (x1 + x2) / 2.0 + random.uniform(-wobble_strength, wobble_strength)
@@ -162,10 +162,16 @@
        f'style="max-width:100%; height:auto; display:block; margin:0 auto;">'
    ]

    # Background paper
    svg_parts.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
    )
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
@@ -246,7 +252,7 @@
        if not stroke:
            stroke = "#222222"

        stroke_width = _get_num(el.get("strokeWidth"), 2.0)
        stroke_width = _get_num(el.get("strokeWidth"), 2.5)  # Slightly thicker strokes
        opacity = _get_num(el.get("opacity"), random.uniform(0.86, 1.0))

        if el_type == "circle":
@@ -257,9 +263,9 @@
            cx_scaled = tx(cx_raw)
            cy_scaled = ty(cy_raw)

            cx = _jitter(cx_scaled, amount=2.3)
            cy = _clamp_y(_jitter(cy_scaled, amount=2.3), height)
            r = max(_jitter(r_raw * scale, amount=1.0), 0.8)
            cx = _jitter(cx_scaled, amount=3.0)
            cy = _clamp_y(_jitter(cy_scaled, amount=3.0), height)
            r = max(_jitter(r_raw * scale, amount=2.0), 0.8)

            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
@@ -278,12 +284,12 @@
            x2_scaled = tx(x2_raw)
            y2_scaled = ty(y2_raw)

            x1 = _jitter(x1_scaled, amount=2.0)
            y1 = _clamp_y(_jitter(y1_scaled, amount=2.0), height)
            x2 = _jitter(x2_scaled, amount=2.0)
            y2 = _clamp_y(_jitter(y2_scaled, amount=2.0), height)
            x1 = _jitter(x1_scaled, amount=3.0)
            y1 = _clamp_y(_jitter(y1_scaled, amount=3.0), height)
            x2 = _jitter(x2_scaled, amount=3.0)
            y2 = _clamp_y(_jitter(y2_scaled, amount=3.0), height)

            d = _wobble_path(x1, y1, x2, y2, wobble_strength=3.0)
            d = _wobble_path(x1, y1, x2, y2, wobble_strength=4.0)

            svg_parts.append(
                f'<path d="{d}" fill="none" '
@@ -301,8 +307,8 @@
                        py_raw = _get_num(p[1])
                        px_scaled = tx(px_raw)
                        py_scaled = ty(py_raw)
                        px = _jitter(px_scaled, amount=1.8)
                        py = _clamp_y(_jitter(py_scaled, amount=1.8), height)
                        px = _jitter(px_scaled, amount=2.0)
                        py = _clamp_y(_jitter(py_scaled, amount=2.0), height)
                        jittered_points.append(f"{px},{py}")
                if jittered_points:
                    pts_str = " ".join(jittered_points)
@@ -329,8 +335,8 @@
            tx_scaled_val = tx(tx_raw)
            ty_scaled_val = ty(ty_raw)

            tx_final = _jitter(tx_scaled_val, amount=1.2)
            ty_final = _clamp_y(_jitter(ty_scaled_val, amount=1.2), height)
            tx_final = _jitter(tx_scaled_val, amount=2.0)
            ty_final = _clamp_y(_jitter(ty_scaled_val, amount=2.0), height)

            content = _escape(el.get("text") or "")
            font_size = _get_num(el.get("fontSize"), 14)
