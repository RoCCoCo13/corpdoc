"""The table of contents lists the document headings with their pages."""

import pytest
from test_render import MINIMAL_CONFIG

from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

MD = (
    "# Introduction\n\nText.\n\n## Background\n\nText.\n\n"
    "# Second chapter\n\nText.\n\n### Deep detail\n\nText.\n"
)


def _pages(pdf):
    return [" ".join(p.extract_text().split()) for p in pypdf.PdfReader(pdf).pages]


def test_toc_lists_headings(tmp_path):
    out = tmp_path / "out.pdf"
    CorpDoc(config=MINIMAL_CONFIG).render(MD, output=str(out))

    pages = _pages(out)
    toc_page = pages[2]  # cover, version history, TOC, body
    assert "Placeholder for table of contents" not in toc_page
    for heading in ("Introduction", "Background", "Second chapter", "Deep detail"):
        assert heading in toc_page


def test_toc_does_not_change_the_page_count(tmp_path):
    out = tmp_path / "out.pdf"
    result = CorpDoc(config=MINIMAL_CONFIG).render(MD, output=str(out))

    assert result.total_pages == len(_pages(out)) == 4
    assert result.body_pages == 1


def test_toc_with_images_and_long_body(tmp_path):
    """Flowables are laid out more than once; nothing may break on the second pass."""
    from PIL import Image as PILImage

    PILImage.new("RGB", (300, 150), (200, 30, 30)).save(tmp_path / "a.png")
    md = "".join(
        f"# Chapter {i}\n\n![Figure {i}](a.png)\n\n" + "Text. " * 400 + "\n\n" for i in range(6)
    )
    out = tmp_path / "out.pdf"
    result = CorpDoc(config=MINIMAL_CONFIG).render(md, output=str(out), base_dir=str(tmp_path))

    pages = _pages(out)
    assert "Chapter 5" in pages[2]
    assert sum(len(p.images) for p in pypdf.PdfReader(out).pages) == 6
    assert result.total_pages == len(pages)


def test_no_toc_section_still_renders(tmp_path):
    out = tmp_path / "out.pdf"
    CorpDoc(config=MINIMAL_CONFIG).render("---\ntoc: false\n---\n" + MD, output=str(out))
    assert "Introduction" in " ".join(_pages(out))


def test_toc_does_not_list_itself_and_uses_footer_page_numbers(tmp_path):
    out = tmp_path / "out.pdf"
    CorpDoc(config=MINIMAL_CONFIG).render(MD + "\n# Table tail\n", output=str(out))

    toc_page, body_page = _pages(out)[2:4]
    assert toc_page.count("Table of Contents") == 1  # the title only
    # The body is the 4th sheet but is numbered "2" in its footer (cover and
    # version history carry no number); the TOC must print the same number.
    assert "Page 2 of 2" in body_page
    assert "4" not in toc_page.replace("Page 1 of 2", "")
