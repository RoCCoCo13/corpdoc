"""Tests for Unicode coverage: built-in fonts vs. the opt-in DejaVu family."""

import re
from pathlib import Path

import pytest
from test_render import FULL_MD, MINIMAL_CONFIG

import corpdoc
from corpdoc.api import CorpDoc

pypdf = pytest.importorskip("pypdf")

SYMBOLS = "Σ ≤ ≥ → ² ₂"
MD = f"""---
title: "Unicode {SYMBOLS}"
---

# Heading {SYMBOLS}

Body {SYMBOLS} with **bold {SYMBOLS}** and *italic {SYMBOLS}* and `code {SYMBOLS}`.

- item {SYMBOLS}

| Column |
|--------|
| cell {SYMBOLS} |

```
block {SYMBOLS}
```
"""
BODY_ONLY = {"sections": {"cover": False, "version_history": False, "toc": False}}
FONT_DIR = Path(corpdoc.__file__).parent / "fonts"


def _render(tmp_path, md=MD, **cfg):
    out = tmp_path / "out.pdf"
    CorpDoc(config={**MINIMAL_CONFIG, **cfg}).render(md, output=str(out))
    return pypdf.PdfReader(out)


def _text(reader):
    return "\n".join(p.extract_text() for p in reader.pages)


def _font_names(reader):
    names = set()
    for page in reader.pages:
        for font in page["/Resources"].get("/Font", {}).values():
            names.add(str(font.get_object()["/BaseFont"]).split("+")[-1].lstrip("/"))
    return names


# ── Current behaviour of the built-in fonts (characterisation) ────────────


def test_builtin_fonts_keep_symbol_font_characters_but_lose_subscripts(tmp_path):
    """
    Helvetica/Courier are WinAnsi-encoded. ReportLab substitutes the Symbol
    font for Σ ≤ ≥ →, and ² is part of WinAnsi, so those survive. A
    character in none of the built-in fonts (₂) is NOT kept: it is replaced
    by a filled box (■).
    """
    text = _text(_render(tmp_path, md="# T\n\nA Σ B ≤ C ≥ D → E ² F ₂ G\n", **BODY_ONLY))
    for ch in "Σ≤≥→²":
        assert ch in text, f"{ch!r} unexpectedly missing with built-in fonts"
    assert "₂" not in text
    assert "F ■ G" in text


def test_default_family_still_uses_only_builtin_fonts(tmp_path):
    names = _font_names(_render(tmp_path, md=FULL_MD))
    assert "Helvetica" in names and "Helvetica-Bold" in names
    assert not any("DejaVu" in n for n in names)
    names = _font_names(_render(tmp_path, md=FULL_MD, fonts={"family": "helvetica"}))
    assert not any("DejaVu" in n for n in names)


# ── DejaVu (opt-in) ───────────────────────────────────────────────────────


def test_dejavu_renders_every_symbol_everywhere(tmp_path):
    reader = _render(tmp_path, fonts={"family": "dejavu"}, **BODY_ONLY)
    text = _text(reader)
    assert "■" not in text
    for where in ("Heading", "Body", "bold", "italic", "code", "item", "cell", "block"):
        assert re.search(rf"{where}\s+Σ\s+≤\s+≥\s+→\s+²\s+₂", text), f"symbols lost in: {where}"


def test_dejavu_is_used_in_every_style_including_front_pages(tmp_path):
    names = _font_names(_render(tmp_path, md=MD + "\n" + FULL_MD, fonts={"family": "dejavu"}))
    assert {
        "DejaVuSans",
        "DejaVuSans-Bold",
        "DejaVuSans-Oblique",
        "DejaVuSansMono",
    } <= names
    leftovers = {n for n in names if not n.startswith("DejaVu")}
    assert not leftovers, f"built-in fonts still used: {leftovers}"


def test_dejavu_bold_italic_is_registered(tmp_path):
    names = _font_names(
        _render(tmp_path, md="# T\n\n***both***\n", fonts={"family": "dejavu"}, **BODY_ONLY)
    )
    assert "DejaVuSans-BoldOblique" in names


def test_dejavu_title_with_symbols_on_cover(tmp_path):
    reader = _render(tmp_path, fonts={"family": "dejavu"})
    assert "₂" in reader.pages[0].extract_text()


def test_bundled_fonts_and_licence_ship_in_the_package():
    for name in (
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans-Oblique.ttf",
        "DejaVuSans-BoldOblique.ttf",
        "DejaVuSansMono.ttf",
        "LICENSE-DejaVu.txt",
    ):
        assert (FONT_DIR / name).is_file(), name
    assert "Bitstream Vera Fonts Copyright" in (FONT_DIR / "LICENSE-DejaVu.txt").read_text(
        encoding="utf-8"
    )
    pyproject = (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    package_data = pyproject.split("[tool.setuptools.package-data]")[1].split("[")[1]
    assert "fonts/*.ttf" in package_data and "fonts/*.txt" in package_data


# ── Custom TTFs ───────────────────────────────────────────────────────────


def test_custom_ttf_paths(tmp_path):
    custom = {
        "regular": str(FONT_DIR / "DejaVuSans-Oblique.ttf"),
        "bold": str(FONT_DIR / "DejaVuSans-BoldOblique.ttf"),
    }
    reader = _render(tmp_path, fonts={"family": custom}, **BODY_ONLY)
    names = _font_names(reader)
    assert "DejaVuSans-Oblique" in names and "DejaVuSans-BoldOblique" in names
    assert "Helvetica" not in names
    assert re.search(r"Body\s+Σ\s+≤\s+≥\s+→\s+²\s+₂", _text(reader))


def test_missing_custom_font_falls_back_with_warning(tmp_path, capsys):
    reader = _render(
        tmp_path, md=FULL_MD, fonts={"family": {"regular": str(tmp_path / "nope.ttf")}}
    )
    assert "nope.ttf" in capsys.readouterr().err
    assert "Helvetica" in _font_names(reader)


def test_unknown_family_falls_back_with_warning(tmp_path, capsys):
    reader = _render(tmp_path, md=FULL_MD, fonts={"family": "comic-sans"})
    err = capsys.readouterr().err
    assert "comic-sans" in err and "Warning" in err
    assert "Helvetica" in _font_names(reader)


# ── Warning for characters the built-in fonts cannot encode ───────────────


def test_default_family_warns_once_per_render(tmp_path, capsys):
    _render(tmp_path, md="# CO₂ report\n\nCO₂ and H₂O and 你好.\n\nMore CO₂.\n")
    err = capsys.readouterr().err
    lines = [line for line in err.splitlines() if "cannot" in line]
    assert len(lines) == 1
    assert "₂" in lines[0] and "U+2082" in lines[0]
    assert "dejavu" in lines[0]


def test_no_warning_for_characters_the_builtin_fonts_can_draw(tmp_path, capsys):
    _render(tmp_path, md="# Año – “quotes” €\n\nΣ ≤ ≥ → ² é ü ß ñ • — …\n")
    assert "cannot" not in capsys.readouterr().err


def test_no_warning_with_dejavu(tmp_path, capsys):
    _render(tmp_path, md="# CO₂\n\nH₂O Σ ≤ ≥ →\n", fonts={"family": "dejavu"})
    assert capsys.readouterr().err == ""
