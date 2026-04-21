"""Tests for color extraction and role assignment."""

import os
import tempfile
from corpdoc.colors import (
    extract_colors_from_svg,
    assign_roles,
    luminance,
    saturation,
    lighten,
    darken,
)


SIMPLE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect fill="#ff0000" x="0" y="0" width="50" height="50"/>
    <rect fill="#00ff00" x="50" y="0" width="50" height="50"/>
    <circle fill="#0000ff" cx="50" cy="50" r="20"/>
</svg>
"""

STYLE_ATTR_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect style="fill:#b9885a;stroke:none" x="0" y="0" width="100" height="50"/>
    <rect style="fill:#2e1e19;stroke:none" x="0" y="50" width="100" height="50"/>
</svg>
"""


def _write_tmp_svg(content):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False)
    f.write(content)
    f.close()
    return f.name


def test_extract_simple_colors():
    path = _write_tmp_svg(SIMPLE_SVG)
    colors = extract_colors_from_svg(path)
    os.unlink(path)
    assert "#ff0000" in colors
    assert "#00ff00" in colors
    assert "#0000ff" in colors


def test_extract_from_style_attribute():
    """Colors defined inside style= attributes (not direct fill= attributes)."""
    path = _write_tmp_svg(STYLE_ATTR_SVG)
    colors = extract_colors_from_svg(path)
    os.unlink(path)
    assert "#b9885a" in colors
    assert "#2e1e19" in colors


def test_assign_roles_picks_darkest_as_primary():
    colors = ["#b9885a", "#2e1e19"]  # dark brown + bronze
    palette = assign_roles(colors)
    assert palette["primary"] == "#2e1e19"  # darker
    assert palette["secondary"] == "#b9885a"  # more saturated


def test_assign_roles_accent_differs_from_secondary_when_possible():
    # Three-color palette: dark + two saturated hues
    colors = ["#1a1a3c", "#2ec4b6", "#ff6b35"]  # navy + teal + coral
    palette = assign_roles(colors)
    assert palette["primary"] == "#1a1a3c"
    assert palette["secondary"] != palette["primary"]
    assert palette["accent"] != palette["primary"]
    assert palette["accent"] != palette["secondary"]


def test_assign_roles_accent_falls_back_to_secondary_with_two_colors():
    # Only two distinct usable colors — accent must fall back to secondary
    colors = ["#2e1e19", "#b9885a"]
    palette = assign_roles(colors)
    assert palette["accent"] == palette["secondary"]


def test_assign_roles_produces_all_keys():
    palette = assign_roles(["#ff5733", "#333333"])
    for key in ("primary", "secondary", "accent", "highlight", "light", "lighter", "text"):
        assert key in palette, f"Missing {key}"


def test_assign_roles_highlight_uses_fourth_distinct_color():
    """When the palette has 4+ colors, highlight picks one distinct from the first 3."""
    colors = ["#1F4129", "#C8A36A", "#1E293B", "#7A9E7E"]  # forest, camel, slate, sage
    palette = assign_roles(colors)
    assert palette["highlight"] not in (palette["primary"], palette["secondary"], palette["accent"])
    assert palette["highlight"] in colors


def test_assign_roles_highlight_falls_back_on_small_palette():
    """With only 2 colors the palette can't provide a distinct highlight — fallback kicks in."""
    palette = assign_roles(["#2e1e19", "#b9885a"])
    # Must still produce a usable highlight (darkened primary fallback).
    assert palette["highlight"]
    assert palette["highlight"].startswith("#")


def test_assign_roles_fallback_on_empty():
    palette = assign_roles([])
    # Should not crash, should give a sensible default
    assert palette["primary"]


def test_luminance():
    assert luminance("#000000") == 0
    assert luminance("#ffffff") == 255
    # Red should be lower luminance than green (perceptually darker)
    assert luminance("#ff0000") < luminance("#00ff00")


def test_saturation():
    assert saturation("#ffffff") == 0  # white has no saturation
    assert saturation("#000000") == 0  # black has no saturation
    assert saturation("#ff0000") == 1.0  # pure red is fully saturated


def test_lighten():
    assert lighten("#000000", 1.0) == "#ffffff"
    assert lighten("#000000", 0.0) == "#000000"
    # Midpoint should be grey
    result = lighten("#000000", 0.5)
    r = int(result[1:3], 16)
    assert 120 <= r <= 140


def test_darken():
    assert darken("#ffffff", 1.0) == "#000000"
    assert darken("#ffffff", 0.0) == "#ffffff"
