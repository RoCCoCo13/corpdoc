"""Tests for the markdown parser."""

from corpdoc.parser import parse_frontmatter, parse_blocks, inline, detect_language


def test_frontmatter_basic():
    md = """---
title: Test
version: 1.0
---
# Hello
"""
    meta, body = parse_frontmatter(md)
    assert meta["title"] == "Test"
    assert meta["version"] == "1.0"
    assert body.startswith("# Hello")


def test_frontmatter_none():
    md = "# Hello\n\nNo frontmatter."
    meta, body = parse_frontmatter(md)
    assert meta == {}
    assert body == md


def test_frontmatter_value_with_colon():
    md = """---
title: "Report: Q1 Results"
subtitle: "Client: ACME Corp"
---
Body."""
    meta, _ = parse_frontmatter(md)
    assert meta["title"] == "Report: Q1 Results"
    assert meta["subtitle"] == "Client: ACME Corp"


def test_frontmatter_date_value():
    md = """---
date: 2026-04-20
version: 1.0
---
Body."""
    meta, _ = parse_frontmatter(md)
    # Dates and numbers are coerced to strings for downstream consumers
    assert meta["date"] == "2026-04-20"
    assert meta["version"] == "1.0"


def test_frontmatter_malformed_does_not_crash():
    md = """---
title: "unterminated
---
Body."""
    meta, body = parse_frontmatter(md)
    # Malformed YAML → empty meta, body preserved
    assert meta == {}
    assert body.strip() == "Body."


def test_parse_heading():
    blocks = parse_blocks("# H1\n## H2\n### H3\n#### H4")
    levels = [b["level"] for b in blocks if b["type"] == "h"]
    assert levels == [1, 2, 3, 4]


def test_parse_paragraph():
    blocks = parse_blocks("Simple paragraph.\n\nAnother one.")
    paragraphs = [b for b in blocks if b["type"] == "p"]
    assert len(paragraphs) == 2


def test_parse_flat_list():
    md = "- item 1\n- item 2\n- item 3"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "list"
    assert len(blocks[0]["items"]) == 3
    assert all(i["level"] == 0 for i in blocks[0]["items"])


def test_parse_nested_list():
    md = "- top\n  - nested\n- top2"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "list"
    items = blocks[0]["items"]
    assert items[0]["level"] == 0
    assert items[1]["level"] == 1
    assert items[2]["level"] == 0


def test_parse_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "table"
    assert blocks[0]["rows"][0] == ["A", "B"]
    assert blocks[0]["rows"][1] == ["1", "2"]


def test_parse_mermaid():
    md = "```mermaid\nflowchart LR\n    A --> B\n```"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "mermaid"
    assert "flowchart" in blocks[0]["content"]


def test_parse_hr():
    md = "Text\n\n---\n\nMore text"
    blocks = parse_blocks(md)
    types = [b["type"] for b in blocks]
    assert "hr" in types


def test_inline_bold():
    assert "<b>" in inline("hello **world**")


def test_inline_italic():
    assert "<i>" in inline("hello *world*")


def test_inline_bold_italic():
    result = inline("***combo***")
    assert "<b>" in result and "<i>" in result


def test_inline_code():
    assert "Courier" in inline("use `pip install`")


def test_inline_xml_escape_ampersand():
    result = inline("cats & dogs")
    assert "&amp;" in result
    assert "&" not in result.replace("&amp;", "")


def test_inline_xml_escape_angle_brackets():
    result = inline("a < b and b > c")
    assert "&lt;" in result
    assert "&gt;" in result


def test_inline_xml_escape_in_code_span():
    result = inline("call `f(x) -> bool`")
    assert "&gt;" in result


def test_parse_blocks_xml_safe():
    """& < > in body text must not crash ReportLab XML rendering."""
    blocks = parse_blocks("Use `a < b` and `x > y`. A&B is valid.")
    para = next(b for b in blocks if b["type"] == "p")
    assert "&lt;" in para["text"]
    assert "&gt;" in para["text"]
    assert "&amp;" in para["text"]


def test_detect_language_english():
    text = "The quick brown fox jumps over the lazy dog. This is a test."
    assert detect_language(text) == "en"


def test_detect_language_spanish():
    text = (
        "El zorro marrón salta por encima del perro perezoso. Esto es una prueba para el sistema."
    )
    assert detect_language(text) == "es"


def test_detect_language_german():
    text = "Der braune Fuchs springt über den faulen Hund. Das ist ein Test für das System."
    assert detect_language(text) == "de"
