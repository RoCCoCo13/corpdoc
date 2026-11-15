"""Tests for ordered lists, three-level nesting and their rendering."""

import pytest
from test_render import MINIMAL_CONFIG

from corpdoc.api import CorpDoc
from corpdoc.parser import parse_blocks

pypdf = pytest.importorskip("pypdf")


def _body_text(tmp_path, md):
    out = tmp_path / "out.pdf"
    cfg = {**MINIMAL_CONFIG, "sections": {"cover": False, "version_history": False, "toc": False}}
    CorpDoc(config=cfg).render(md, output=str(out))
    return "\n".join(p.extract_text() for p in pypdf.PdfReader(out).pages)


def _markers(blocks):
    doc = CorpDoc(config=MINIMAL_CONFIG)
    return [p.getPlainText().split()[0] for p in doc._build_body(blocks) if hasattr(p, "frags")]


# ── Ordered lists (item 4) ────────────────────────────────────────────────


def test_parser_carries_ordered_flag_and_numbers():
    block = parse_blocks("1. one\n2. two\n3. three")[0]
    assert block["type"] == "list"
    assert block["ordered"] is True
    assert block["start"] == 1
    assert [(i["ordered"], i["number"]) for i in block["items"]] == [
        (True, 1),
        (True, 2),
        (True, 3),
    ]


def test_parser_honours_start_number():
    block = parse_blocks("5. five\n6. six")[0]
    assert block["start"] == 5
    assert [i["number"] for i in block["items"]] == [5, 6]


def test_unordered_list_items_are_flagged_unordered():
    block = parse_blocks("- a\n- b")[0]
    assert block["ordered"] is False
    assert all(i["ordered"] is False for i in block["items"])
    # Existing keys are untouched
    assert [(i["text"], i["level"]) for i in block["items"]] == [("a", 0), ("b", 0)]


def test_nested_ordered_list_restarts_numbering():
    md = "1. first\n   1. inner a\n   2. inner b\n2. second\n   1. inner c\n3. third"
    items = parse_blocks(md)[0]["items"]
    assert [(i["level"], i["number"]) for i in items] == [
        (0, 1),
        (1, 1),
        (1, 2),
        (0, 2),
        (1, 1),
        (0, 3),
    ]


def test_mixed_nesting_keeps_each_list_kind():
    md = "1. first\n   - bullet\n2. second\n\n- top\n  1. num a\n  2. num b"
    blocks = parse_blocks(md)
    assert [i["ordered"] for i in blocks[0]["items"]] == [True, False, True]
    assert [i["ordered"] for i in blocks[1]["items"]] == [False, True, True]
    assert [i.get("number") for i in blocks[1]["items"]] == [None, 1, 2]


def test_ordered_list_renders_numbers_not_bullets():
    assert _markers(parse_blocks("1. one\n2. two\n3. three")) == ["1.", "2.", "3."]
    assert _markers(parse_blocks("7. seven\n8. eight")) == ["7.", "8."]


def test_second_paragraph_of_a_numbered_item_is_not_renumbered():
    blocks = parse_blocks("1. one\n\n   more about one\n\n2. two")
    assert [i["number"] for i in blocks[0]["items"]] == [1, None, 2]
    assert _markers(blocks) == ["1.", "more", "2."]


def test_unordered_list_still_renders_bullets():
    assert _markers(parse_blocks("- a\n- b")) == ["•", "•"]


def test_legacy_list_items_without_ordered_key_render_bullets():
    """Blocks built by hand (plain strings / dicts without 'ordered') keep working."""
    blocks = [{"type": "list", "items": ["plain", {"text": "dict", "level": 1}]}]
    assert _markers(blocks) == ["•", "•"]


def test_numbers_reach_the_pdf(tmp_path):
    text = _body_text(tmp_path, "# T\n\n1. alpha\n2. beta\n   1. gamma\n3. delta\n")
    text = " ".join(text.split())
    assert "1. alpha 2. beta 1. gamma 3. delta" in text
