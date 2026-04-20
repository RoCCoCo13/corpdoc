"""
Color extraction and role assignment from SVG logos.

Extracts hex colors from SVG files by parsing XML attributes (fill, stroke)
and inline styles. Then assigns semantic roles (primary, secondary, accent)
based on luminance and saturation.
"""

import re
from xml.etree import ElementTree as ET
from collections import Counter


HEX_PATTERN = re.compile(r"#([0-9a-fA-F]{3,8})\b")
RGB_PATTERN = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")


def extract_colors_from_svg(svg_path):
    """
    Extract all hex colors used in an SVG file, ordered by frequency.

    Parses XML for fill, stroke, stop-color, and style attributes. Also
    scans embedded <style> blocks for colors.

    Args:
        svg_path: Path to .svg file

    Returns:
        List of hex color strings (e.g. ['#1a2b3c', '#b9885a'])
        ordered by frequency of appearance.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()
    colors = Counter()

    for elem in root.iter():
        # Direct color attributes
        for attr in ("fill", "stroke", "stop-color", "color", "flood-color"):
            val = elem.get(attr, "")
            if val and val not in ("none", "transparent", "currentColor"):
                for m in HEX_PATTERN.finditer(val):
                    colors[_normalize_hex("#" + m.group(1))] += 1
                for m in RGB_PATTERN.finditer(val):
                    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    colors[f"#{r:02x}{g:02x}{b:02x}"] += 1

        # Inline style attribute
        style = elem.get("style", "")
        if style:
            for m in HEX_PATTERN.finditer(style):
                colors[_normalize_hex("#" + m.group(1))] += 1

    # Embedded <style> blocks
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "style" and elem.text:
            for m in HEX_PATTERN.finditer(elem.text):
                colors[_normalize_hex("#" + m.group(1))] += 1

    return [c for c, _ in sorted(colors.items(), key=lambda x: -x[1])]


def _normalize_hex(color):
    """Convert #RGB to #RRGGBB, lowercase."""
    color = color.lower()
    if len(color) == 4:
        return f"#{color[1] * 2}{color[2] * 2}{color[3] * 2}"
    return color


def luminance(hex_color):
    """Perceived brightness (0-255) using ITU-R BT.601 weighting."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def saturation(hex_color):
    """HSV saturation (0.0 - 1.0)."""
    h = hex_color.lstrip("#")
    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) / mx if mx > 0 else 0


def lighten(hex_color, factor):
    """Lighten a color by mixing with white. factor: 0.0-1.0."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def darken(hex_color, factor):
    """Darken a color by mixing with black. factor: 0.0-1.0."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def assign_roles(colors):
    """
    Assign semantic roles to a list of extracted colors.

    Strategy:
        - primary: darkest color (best for body text, headings)
        - secondary: most saturated color distinct from primary (headings, text highlights)
        - accent: next most saturated color distinct from primary and secondary
                  (lines, cover band). Falls back to secondary if the palette
                  only has two usable colors.
        - light: primary lightened 88% (for subtle backgrounds)
        - lighter: secondary lightened 92% (for zebra rows)

    Args:
        colors: List of hex color strings.

    Returns:
        Dict with keys: primary, secondary, accent, light, lighter, text.
    """
    # Filter out near-white and near-black
    filtered = [c for c in colors if 20 < luminance(c) < 240]
    if not filtered:
        filtered = colors if colors else ["#333333"]

    by_lum = sorted(filtered, key=luminance)
    by_sat = sorted(filtered, key=saturation, reverse=True)

    primary = by_lum[0]

    # Secondary: most saturated color that is not primary
    secondary = next(
        (c for c in by_sat if c != primary),
        by_lum[1] if len(by_lum) > 1 else lighten(primary, 0.3),
    )

    # Accent: next most saturated distinct from both
    accent = next(
        (c for c in by_sat if c != primary and c != secondary),
        secondary,
    )

    return {
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "light": lighten(primary, 0.88),
        "lighter": lighten(secondary, 0.92),
        "text": "#333333",
    }


def extract_and_assign(svg_path):
    """Convenience: extract colors and assign roles in one call."""
    colors = extract_colors_from_svg(svg_path)
    return assign_roles(colors)
