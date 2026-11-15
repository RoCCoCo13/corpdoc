"""Tests for clickable links."""

import pytest
from test_render import MINIMAL_CONFIG

from corpdoc.api import CorpDoc
from corpdoc.parser import inline, parse_blocks

pypdf = pytest.importorskip("pypdf")


def _link_uris(tmp_path, md):
    out = tmp_path / "out.pdf"
    cfg = {**MINIMAL_CONFIG, "sections": {"cover": False, "version_history": False, "toc": False}}
    CorpDoc(config=cfg).render(md, output=str(out))
    uris = []
    reader = pypdf.PdfReader(out)
    for page in reader.pages:
        for annot in page.get("/Annots", []):
            action = annot.get_object().get("/A", {})
            if "/URI" in action:
                uris.append(action["/URI"])
    return uris, "\n".join(p.extract_text() for p in reader.pages)


def test_link_keeps_url_as_href():
    assert inline("see [the docs](https://example.com/docs)") == (
        'see <a href="https://example.com/docs">the docs</a>'
    )


def test_link_text_keeps_inline_formatting():
    assert inline("[**bold** link](https://example.com)") == (
        '<a href="https://example.com"><b>bold</b> link</a>'
    )


def test_autolink_and_mailto():
    assert inline("<https://example.com/a>") == (
        '<a href="https://example.com/a">https://example.com/a</a>'
    )
    assert 'href="mailto:me@example.com"' in inline("[mail](mailto:me@example.com)")


def test_url_is_escaped_for_xml():
    xml = inline("[q](https://example.com/?a=1&b=2&c=<x>&d=\"y\"&e='z')")
    href = xml.split('href="')[1].split('"')[0]
    assert "&amp;b=2" in href
    assert "<" not in href and ">" not in href and "'" not in href
    assert xml.count('"') == 2  # only the attribute delimiters


def test_non_web_targets_stay_plain_text():
    """Anchors, relative paths and script URLs cannot be resolved inside the PDF."""
    for target in ("#section", "other.md", "../a/b.pdf", "javascript:alert(1)", "file:///etc/x"):
        assert inline(f"[label]({target})") == "label", target


def test_links_in_lists_and_tables():
    blocks = parse_blocks("- [a](https://a.example)\n\n| x |\n|---|\n| [b](https://b.example) |")
    assert 'href="https://a.example"' in blocks[0]["items"][0]["text"]
    assert 'href="https://b.example"' in blocks[1]["rows"][1][0]


def test_links_are_clickable_in_the_pdf(tmp_path):
    md = (
        "# T\n\nVisit [our site](https://example.com/?a=1&b=2) or "
        "[write us](mailto:hi@example.com). See [below](#below).\n\n"
        "- [listed](https://example.org/list)\n"
    )
    uris, text = _link_uris(tmp_path, md)
    assert uris == [
        "https://example.com/?a=1&b=2",
        "mailto:hi@example.com",
        "https://example.org/list",
    ]
    assert "our site" in text and "below" in text


def test_hostile_url_does_not_break_rendering(tmp_path):
    md = '# T\n\n[x](https://example.com/"><b>&<a href="y">) and [y](https://example.com/%22%3E)\n'
    uris, text = _link_uris(tmp_path, md)
    assert all(u.startswith("https://example.com/") for u in uris)
    assert "and" in text
