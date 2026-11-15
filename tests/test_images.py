"""Tests for block images (PNG / JPG / SVG) in the document body."""

import os

import pytest
from PIL import Image as PILImage
from test_render import MINIMAL_CONFIG

from corpdoc.api import CorpDoc
from corpdoc.parser import inline, parse_blocks

pypdf = pytest.importorskip("pypdf")

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100">'
    '<rect width="200" height="100" fill="#336699"/></svg>'
)


def _png(path, size=(300, 150), color=(200, 30, 30)):
    PILImage.new("RGB", size, color).save(path)
    return path


def _pdf_text(pdf):
    return "\n".join(p.extract_text() for p in pypdf.PdfReader(pdf).pages)


def _pdf_image_count(pdf):
    return sum(len(p.images) for p in pypdf.PdfReader(pdf).pages)


# ── Parser ────────────────────────────────────────────────────────────────


def test_image_only_paragraph_becomes_image_block():
    blocks = parse_blocks("Intro.\n\n![Sales chart](img/chart.png)\n\nOutro.")
    assert [b["type"] for b in blocks] == ["p", "image", "p"]
    assert blocks[1] == {"type": "image", "src": "img/chart.png", "alt": "Sales chart"}


def test_image_block_src_is_url_decoded():
    blocks = parse_blocks("![x](my%20folder/a%20b.png)")
    assert blocks[0]["src"] == "my folder/a b.png"


def test_inline_image_in_text_paragraph_keeps_alt_text():
    blocks = parse_blocks("See the ![company logo](logo.png) above.")
    assert [b["type"] for b in blocks] == ["p"]
    assert blocks[0]["text"] == "See the company logo above."
    assert inline("icon: ![check mark](c.png)") == "icon: check mark"


# ── Rendering ─────────────────────────────────────────────────────────────


def test_png_is_embedded_with_caption(tmp_path):
    _png(tmp_path / "chart.png")
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\n![Quarterly revenue](chart.png)\n", encoding="utf-8")
    out = tmp_path / "out.pdf"

    CorpDoc(config=MINIMAL_CONFIG).render(str(md), output=str(out))

    assert _pdf_image_count(out) == 1
    assert "Quarterly revenue" in _pdf_text(out)


def test_jpg_is_embedded(tmp_path):
    PILImage.new("RGB", (120, 80), (10, 120, 10)).save(tmp_path / "photo.jpg")
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\n![Photo](photo.jpg)\n", encoding="utf-8")
    out = tmp_path / "out.pdf"

    CorpDoc(config=MINIMAL_CONFIG).render(str(md), output=str(out))

    assert _pdf_image_count(out) == 1


def test_relative_path_resolves_against_markdown_dir_not_cwd(tmp_path, monkeypatch, capsys):
    docs = tmp_path / "docs"
    (docs / "img").mkdir(parents=True)
    _png(docs / "img" / "a.png")
    md = docs / "doc.md"
    md.write_text("# T\n\n![A](img/a.png)\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    out = tmp_path / "out.pdf"

    CorpDoc(config=MINIMAL_CONFIG).render(str(md), output=str(out))

    assert _pdf_image_count(out) == 1
    assert "Warning" not in capsys.readouterr().err


def test_string_input_uses_base_dir(tmp_path, monkeypatch):
    assets = tmp_path / "assets"
    assets.mkdir()
    _png(assets / "a.png")
    monkeypatch.chdir(tmp_path)
    doc = CorpDoc(config=MINIMAL_CONFIG)

    # Default base_dir is the current directory → "a.png" is not found there.
    doc.render("# T\n\n![A](a.png)\n", output=str(tmp_path / "miss.pdf"))
    assert _pdf_image_count(tmp_path / "miss.pdf") == 0

    doc.render("# T\n\n![A](a.png)\n", output=str(tmp_path / "hit.pdf"), base_dir=str(assets))
    assert _pdf_image_count(tmp_path / "hit.pdf") == 1


def test_missing_image_warns_and_renders_placeholder(tmp_path, capsys):
    out = tmp_path / "out.pdf"
    result = CorpDoc(config=MINIMAL_CONFIG).render(
        "# T\n\n![Diagram](nope/missing.png)\n\nAfter.", output=str(out), base_dir=str(tmp_path)
    )

    assert os.path.exists(result)
    err = capsys.readouterr().err
    assert "Warning" in err and "missing.png" in err
    text = _pdf_text(out)
    assert "missing.png" in text  # visible placeholder
    assert "After." in text
    assert _pdf_image_count(out) == 0


def test_unreadable_image_warns_and_renders_placeholder(tmp_path, capsys):
    (tmp_path / "broken.png").write_bytes(b"this is not a png")
    (tmp_path / "broken.svg").write_text("<svg", encoding="utf-8")
    out = tmp_path / "out.pdf"

    CorpDoc(config=MINIMAL_CONFIG).render(
        "# T\n\n![A](broken.png)\n\n![B](broken.svg)\n", output=str(out), base_dir=str(tmp_path)
    )

    err = capsys.readouterr().err
    assert "broken.png" in err and "broken.svg" in err
    assert "broken.png" in _pdf_text(out)


def test_remote_image_is_never_fetched(tmp_path, capsys):
    out = tmp_path / "out.pdf"
    CorpDoc(config=MINIMAL_CONFIG).render(
        "# T\n\n![Remote](https://example.com/a.png)\n", output=str(out)
    )
    assert "remote" in capsys.readouterr().err.lower()
    assert _pdf_image_count(out) == 0


def test_svg_is_drawn_as_vector(tmp_path):
    from reportlab.graphics.shapes import Drawing

    from corpdoc.images import build_image_flowables

    (tmp_path / "d.svg").write_text(SVG, encoding="utf-8")
    doc = CorpDoc(config=MINIMAL_CONFIG)
    flowables = build_image_flowables("d.svg", "Vector", str(tmp_path), 400, 600, doc.styles)
    drawings = _find(flowables, Drawing)
    assert len(drawings) == 1
    assert (drawings[0].width, drawings[0].height) == (200, 100)

    out = tmp_path / "out.pdf"
    doc.render("# T\n\n![Vector](d.svg)\n", output=str(out), base_dir=str(tmp_path))
    assert "Vector" in _pdf_text(out)


# ── Scaling ───────────────────────────────────────────────────────────────


def _find(flowables, cls):
    found = []
    for f in flowables:
        if isinstance(f, cls):
            found.append(f)
        found.extend(_find(getattr(f, "_content", []) or [], cls))
    return found


def test_fit_size_rules():
    from corpdoc.images import fit_size

    assert fit_size(100, 50, 400, 600) == (100, 50)  # never upscaled
    assert fit_size(800, 400, 400, 600) == (400, 200)  # scaled to width, ratio kept
    w, h = fit_size(400, 2400, 400, 600)  # capped to page height, ratio kept
    assert h == 600 and w == pytest.approx(100)


def test_wide_and_tall_images_fit_the_page(tmp_path):
    """Oversized images must not overflow the frame (ReportLab would raise LayoutError)."""
    _png(tmp_path / "wide.png", size=(3000, 500))
    _png(tmp_path / "tall.png", size=(500, 4000))
    out = tmp_path / "out.pdf"

    CorpDoc(config=MINIMAL_CONFIG).render(
        "# T\n\n![Wide](wide.png)\n\n![Tall with a caption](tall.png)\n",
        output=str(out),
        base_dir=str(tmp_path),
    )

    assert _pdf_image_count(out) == 2
