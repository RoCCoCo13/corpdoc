"""A body that opens with a wide (landscape) table must not start with a blank page."""

import pytest
from test_render import MINIMAL_CONFIG

from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

WIDE_TABLE = (
    "| " + " | ".join("ABCDEFGHI") + " |\n|" + "---|" * 9 + "\n|" + " 1 |" * 9 + "\n\nEnd.\n"
)
NO_FRONT = {"sections": {"cover": False, "version_history": False, "toc": False}}


def _render(tmp_path, md, config=None):
    doc = CorpDoc(config=config or MINIMAL_CONFIG)
    out = str(tmp_path / "out.pdf")
    return doc, doc.render(md, output=out), out


def _page_texts(pdf):
    return [" ".join(p.extract_text().split()) for p in pypdf.PdfReader(pdf).pages]


def test_body_opening_with_a_landscape_table_has_no_blank_page(tmp_path):
    _, result, out = _render(tmp_path, WIDE_TABLE, {**MINIMAL_CONFIG, **NO_FRONT})

    pages = _page_texts(out)
    assert "A B C" in pages[0]  # the table is on the first page, not after a blank one
    assert result.total_pages == result.body_pages == len(pages) == 2
    box = pypdf.PdfReader(out).pages[0].mediabox
    assert box.width > box.height  # and that page is landscape


def test_body_opening_with_a_landscape_table_after_front_pages(tmp_path):
    _, result, out = _render(tmp_path, WIDE_TABLE)

    pages = _page_texts(out)
    assert len(pages) == 5 and "A B C" in pages[3]
    assert result.body_pages == 2
    boxes = [p.mediabox for p in pypdf.PdfReader(out).pages]
    assert [b.width > b.height for b in boxes] == [False, False, False, True, False]
