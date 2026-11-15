"""Tests for page counting and the optional `max_pages` limit."""

import sys

import pytest
from test_render import MINIMAL_CONFIG

from corpdoc import cli
from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

ONE_PAGE = "# Heading\n\nShort body.\n"
THREE_PAGES = "# Heading\n\n" + "\n\n".join(f"Paragraph {i}. " + "word " * 120 for i in range(40))


def _cfg(**defaults):
    return {**MINIMAL_CONFIG, "defaults": {**MINIMAL_CONFIG["defaults"], **defaults}}


def _render(tmp_path, md, config=None):
    doc = CorpDoc(config=config or MINIMAL_CONFIG)
    out = str(tmp_path / "out.pdf")
    return doc, doc.render(md, output=out), out


def test_render_still_returns_the_output_path(tmp_path):
    _, result, out = _render(tmp_path, ONE_PAGE)
    assert result == out
    assert isinstance(result, str)
    assert str(result) == out


def test_counts_are_exposed_on_result_and_on_the_object(tmp_path):
    doc, result, out = _render(tmp_path, THREE_PAGES)
    real_total = len(pypdf.PdfReader(out).pages)

    assert result.total_pages == real_total
    assert result.body_pages == real_total - 3  # cover + version history + TOC
    assert result.body_pages >= 2
    assert (doc.total_pages, doc.body_pages) == (result.total_pages, result.body_pages)
    assert result.max_pages is None
    assert result.over_limit is False


def test_body_pages_follow_disabled_sections(tmp_path):
    cfg = {**MINIMAL_CONFIG, "sections": {"cover": False, "toc": False}}
    _, result, _ = _render(tmp_path, ONE_PAGE, cfg)
    assert (result.total_pages, result.body_pages) == (2, 1)

    cfg = {**MINIMAL_CONFIG, "sections": {"cover": False, "version_history": False, "toc": False}}
    _, result, _ = _render(tmp_path, ONE_PAGE, cfg)
    assert (result.total_pages, result.body_pages) == (1, 1)


def test_landscape_table_pages_count_as_body(tmp_path):
    md = (
        "# T\n\n| "
        + " | ".join("ABCDEFGHI")
        + " |\n|"
        + "---|" * 9
        + "\n|"
        + " 1 |" * 9
        + "\n\nEnd."
    )
    _, result, out = _render(tmp_path, md)
    assert result.body_pages == len(pypdf.PdfReader(out).pages) - 3 == 3


def test_no_limit_means_no_warning(tmp_path, capsys):
    _render(tmp_path, THREE_PAGES)
    assert "max_pages" not in capsys.readouterr().err


def test_config_max_pages_exceeded_warns(tmp_path, capsys):
    _, result, out = _render(tmp_path, THREE_PAGES, _cfg(max_pages=1))
    err = capsys.readouterr().err
    assert "Warning" in err and "max_pages" in err
    assert result.over_limit is True
    assert result.max_pages == 1
    assert len(pypdf.PdfReader(out).pages) == result.total_pages  # PDF is still written


def test_limit_applies_to_body_pages_not_total(tmp_path, capsys):
    # 4 pages in total, but only one of them is body.
    _, result, _ = _render(tmp_path, ONE_PAGE, _cfg(max_pages=1))
    assert result.total_pages == 4
    assert result.over_limit is False
    assert "max_pages" not in capsys.readouterr().err


def test_frontmatter_max_pages_overrides_config(tmp_path, capsys):
    md = "---\ntitle: T\nmax_pages: 1\n---\n\n" + THREE_PAGES
    _, result, _ = _render(tmp_path, md, _cfg(max_pages=50))
    assert result.max_pages == 1 and result.over_limit is True

    md = "---\ntitle: T\nmax_pages: 50\n---\n\n" + THREE_PAGES
    _, result, _ = _render(tmp_path, md, _cfg(max_pages=1))
    assert result.max_pages == 50 and result.over_limit is False


def test_invalid_max_pages_is_ignored_with_warning(tmp_path, capsys):
    _, result, _ = _render(tmp_path, ONE_PAGE, _cfg(max_pages="lots"))
    assert result.max_pages is None
    assert "max_pages" in capsys.readouterr().err


# ── CLI ───────────────────────────────────────────────────────────────────


def _run_cli(tmp_path, monkeypatch, md, *extra, max_pages=None):
    import yaml

    cfg_path = tmp_path / "corpdoc.yml"
    cfg = _cfg(max_pages=max_pages) if max_pages is not None else MINIMAL_CONFIG
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    md_path = tmp_path / "doc.md"
    md_path.write_text(md, encoding="utf-8")
    out = tmp_path / "doc.pdf"
    argv = ["corpdoc", "render", str(md_path), "--config", str(cfg_path), "--output", str(out)]
    monkeypatch.setattr(sys, "argv", [*argv, *extra])
    return out


def test_cli_prints_total_and_body_pages(tmp_path, monkeypatch, capsys):
    _run_cli(tmp_path, monkeypatch, ONE_PAGE)
    cli.main()
    out = capsys.readouterr().out
    assert "Pages: 4 total, 1 body" in out


def test_cli_over_limit_warns_but_exits_zero_by_default(tmp_path, monkeypatch, capsys):
    pdf = _run_cli(tmp_path, monkeypatch, THREE_PAGES, max_pages=1)
    cli.main()  # must not raise SystemExit
    assert "max_pages" in capsys.readouterr().err
    assert pdf.exists()


def test_cli_strict_exits_non_zero_when_over_limit(tmp_path, monkeypatch, capsys):
    pdf = _run_cli(tmp_path, monkeypatch, THREE_PAGES, "--strict", max_pages=1)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code not in (0, None)
    assert pdf.exists()


def test_cli_strict_passes_when_within_limit(tmp_path, monkeypatch):
    _run_cli(tmp_path, monkeypatch, ONE_PAGE, "--strict", max_pages=5)
    cli.main()


# ── Review fixes ──────────────────────────────────────────────────────────


def test_invalid_frontmatter_max_pages_falls_back_to_config(tmp_path, capsys):
    md = "---\nmax_pages: 12 pages\n---\n" + ONE_PAGE
    _, result, _ = _render(tmp_path, md, _cfg(max_pages=20))

    assert result.max_pages == 20
    assert "max_pages" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["1.0", "1", '"1"', " 1 "])
def test_max_pages_accepts_whole_numbers_in_any_spelling(tmp_path, capsys, value):
    md = f"---\nmax_pages: {value}\n---\n" + ONE_PAGE
    _, result, _ = _render(tmp_path, md)

    assert result.max_pages == 1
    assert "must be" not in capsys.readouterr().err


@pytest.mark.parametrize("value", ["1.5", "0", "-2", "true"])
def test_max_pages_rejects_non_positive_and_fractional_values(tmp_path, capsys, value):
    md = f"---\nmax_pages: {value}\n---\n" + ONE_PAGE
    _, result, _ = _render(tmp_path, md)

    assert result.max_pages is None
    assert "max_pages" in capsys.readouterr().err
