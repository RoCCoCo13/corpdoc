"""Tests for optional front pages (cover / version history / table of contents)."""

import pytest
from test_render import MINIMAL_CONFIG

from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

BODY = "# Body Heading\n\nBody paragraph.\n"


def _pages(tmp_path, md=BODY, sections=None):
    cfg = dict(MINIMAL_CONFIG)
    if sections is not None:
        cfg["sections"] = sections
    out = tmp_path / "out.pdf"
    CorpDoc(config=cfg).render(md, output=str(out))
    return [p.extract_text() for p in pypdf.PdfReader(out).pages]


def _frontmatter(**keys):
    lines = "\n".join(f"  {k}: {v}" for k, v in keys.items())
    return f"---\ntitle: Doc\nsections:\n{lines}\n---\n\n{BODY}"


def test_defaults_keep_all_three_front_pages(tmp_path):
    pages = _pages(tmp_path)
    assert len(pages) == 4
    assert "Version History" in pages[1]
    assert "Table of Contents" in pages[2]
    assert "Body paragraph." in pages[3]
    assert "Page 2 of 2" in pages[3]


def test_explicit_true_matches_defaults(tmp_path):
    pages = _pages(tmp_path, sections={"cover": True, "version_history": True, "toc": True})
    assert len(pages) == 4


def test_config_disables_cover(tmp_path):
    pages = _pages(tmp_path, sections={"cover": False})
    assert len(pages) == 3
    assert "Version History" in pages[0]
    assert "Table of Contents" in pages[1]
    # Only the version-history page is left unnumbered.
    assert "Page 2 of 2" in pages[2]


def test_config_disables_version_history(tmp_path):
    pages = _pages(tmp_path, sections={"version_history": False})
    assert len(pages) == 3
    assert not any("Version History" in p for p in pages)
    assert "Table of Contents" in pages[1]


def test_config_disables_toc(tmp_path):
    pages = _pages(tmp_path, sections={"toc": False})
    assert len(pages) == 3
    assert not any("Table of Contents" in p for p in pages)
    assert "Page 1 of 1" in pages[2]


def test_all_disabled_leaves_only_the_body_with_header_and_footer(tmp_path):
    pages = _pages(tmp_path, sections={"cover": False, "version_history": False, "toc": False})
    assert len(pages) == 1
    assert "Body paragraph." in pages[0]
    assert "Page 1 of 1" in pages[0]
    assert "Test Street" in pages[0]  # footer is drawn on the first page


def test_frontmatter_overrides_config(tmp_path):
    md = _frontmatter(cover="false", toc="false")
    pages = _pages(tmp_path, md=md)
    assert len(pages) == 2
    assert "Version History" in pages[0]

    md = _frontmatter(cover="true")
    pages = _pages(tmp_path, md=md, sections={"cover": False, "toc": False})
    assert len(pages) == 3  # cover re-enabled by frontmatter, toc still off from config
    assert "Version History" in pages[1]


def test_frontmatter_accepts_top_level_keys_and_yaml_booleans(tmp_path):
    md = f"---\ntitle: Doc\ncover: no\nversion_history: off\ntoc: False\n---\n\n{BODY}"
    assert len(_pages(tmp_path, md=md)) == 1


@pytest.mark.parametrize("bad", [["cover"], "cover", 3, True])
def test_config_sections_that_is_not_a_mapping_warns_and_uses_defaults(tmp_path, capsys, bad):
    out = tmp_path / "out.pdf"
    CorpDoc(config={**MINIMAL_CONFIG, "sections": bad}).render("# T\n\nBody.\n", output=str(out))

    assert len(pypdf.PdfReader(out).pages) == 4  # cover, version history, TOC, body
    assert "sections" in capsys.readouterr().err
