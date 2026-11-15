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
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
        f.write(content)
    return f.name


def _write_png_1x1():
    """Produce a valid 1x1 PNG so Pillow can open it."""
    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        pass
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


# ── Problems are reported, not swallowed ──────────────────────────────────


def test_unreadable_png_logo_warns(tmp_path, capsys):
    bad = tmp_path / "logo.png"
    bad.write_bytes(b"this is not a png")

    logo = Logo({"logo": {"png": str(bad)}})

    assert not logo
    err = capsys.readouterr().err
    assert "Warning" in err and "logo.png" in err


def test_unreadable_svg_logo_warns(tmp_path, capsys):
    bad = tmp_path / "logo.svg"
    bad.write_text("<svg", encoding="utf-8")

    logo = Logo({"logo": {"svg": str(bad)}})

    assert not logo
    err = capsys.readouterr().err
    assert "Warning" in err and "logo.svg" in err


def test_unreadable_png_falls_back_to_svg_with_warning(tmp_path, capsys):
    bad = tmp_path / "logo.png"
    bad.write_bytes(b"this is not a png")
    svg = _write(SIMPLE_SVG, ".svg")
    try:
        logo = Logo({"logo": {"png": str(bad), "svg": svg}})
        assert logo.kind == "svg"
        assert "logo.png" in capsys.readouterr().err
    finally:
        os.unlink(svg)


def test_readable_logo_prints_nothing(capsys):
    svg = _write(SIMPLE_SVG, ".svg")
    try:
        assert Logo({"logo": {"svg": svg}})
        assert capsys.readouterr().err == ""
    finally:
        os.unlink(svg)


def test_draw_failure_warns_once_and_does_not_raise(tmp_path, capsys):
    png = _write_png_1x1()
    try:
        logo = Logo({"logo": {"png": png}})
    finally:
        os.unlink(png)  # the file disappears between loading and drawing
    canvas = Canvas(str(tmp_path / "out.pdf"))

    logo.draw(canvas, 0, 0, 10, 5)
    logo.draw(canvas, 0, 0, 10, 5)

    err = capsys.readouterr().err
    assert err.count("Warning") == 1 and "logo" in err.lower()


def test_render_with_a_logo_that_cannot_be_drawn_still_produces_the_pdf(tmp_path, capsys):
    from test_render import MINIMAL_CONFIG

    from corpdoc.api import CorpDoc

    png = _write_png_1x1()
    doc = CorpDoc(config={**MINIMAL_CONFIG, "logo": {"png": png}})
    os.unlink(png)
    out = tmp_path / "out.pdf"

    doc.render("# T\n\nBody.\n\n# Two\n\nMore.\n", output=str(out))

    assert out.exists()
    assert capsys.readouterr().err.count("logo") == 1  # once, not once per page
