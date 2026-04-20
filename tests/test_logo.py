"""Tests for the Logo resolver (PNG / SVG / both)."""

import os
import tempfile

from reportlab.pdfgen.canvas import Canvas

from corpdoc.logo import Logo


SIMPLE_SVG = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40" width="100" height="40">
  <rect x="0" y="0" width="100" height="40" fill="#1F4129"/>
</svg>
"""


def _write(content, suffix):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def _write_png_1x1():
    """Produce a valid 1x1 PNG so Pillow can open it."""
    from PIL import Image

    f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    f.close()
    Image.new("RGB", (10, 5), color=(200, 163, 106)).save(f.name, "PNG")
    return f.name


def test_logo_none_when_nothing_configured():
    logo = Logo({})
    assert not logo
    assert logo.kind is None


def test_logo_none_when_paths_missing():
    logo = Logo({"logo": {"svg": "/nope.svg", "png": "/nope.png"}})
    assert not logo


def test_logo_resolves_svg_only():
    svg = _write(SIMPLE_SVG, ".svg")
    try:
        logo = Logo({"logo": {"svg": svg}})
        assert logo
        assert logo.kind == "svg"
        assert logo.width > 0 and logo.height > 0
    finally:
        os.unlink(svg)


def test_logo_resolves_png_only():
    png = _write_png_1x1()
    try:
        logo = Logo({"logo": {"png": png}})
        assert logo
        assert logo.kind == "png"
        assert logo.width == 10 and logo.height == 5
    finally:
        os.unlink(png)


def test_logo_prefers_png_when_both_present():
    svg = _write(SIMPLE_SVG, ".svg")
    png = _write_png_1x1()
    try:
        logo = Logo({"logo": {"svg": svg, "png": png}})
        assert logo.kind == "png"
    finally:
        os.unlink(svg)
        os.unlink(png)


def test_logo_draw_svg_does_not_raise():
    svg = _write(SIMPLE_SVG, ".svg")
    try:
        logo = Logo({"logo": {"svg": svg}})
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            c = Canvas(pdf_path)
            logo.draw(c, 0, 0, 100, 40)
            c.save()
            assert os.path.getsize(pdf_path) > 500
        finally:
            os.unlink(pdf_path)
    finally:
        os.unlink(svg)


def test_logo_draw_png_does_not_raise():
    png = _write_png_1x1()
    try:
        logo = Logo({"logo": {"png": png}})
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            c = Canvas(pdf_path)
            logo.draw(c, 0, 0, 100, 40)
            c.save()
            assert os.path.getsize(pdf_path) > 500
        finally:
            os.unlink(pdf_path)
    finally:
        os.unlink(png)
