"""Tests for Unicode coverage: built-in fonts vs. the opt-in DejaVu family."""

import os
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


# ── The warning looks at what is drawn, with the font that draws it ───────


def _only_in_sans():
    """A character DejaVu Sans can draw and DejaVu Sans Mono cannot."""
    from reportlab.pdfbase.ttfonts import TTFont

    from corpdoc.fonts import FONT_DIR

    sans = TTFont("ProbeSans", os.path.join(FONT_DIR, "DejaVuSans.ttf")).face.charToGlyph
    mono = TTFont("ProbeMono", os.path.join(FONT_DIR, "DejaVuSansMono.ttf")).face.charToGlyph
    return next(chr(c) for c in range(0x2100, 0x2C00) if c in sans and c not in mono)


def _sans_with(**variants):
    from corpdoc.fonts import FONT_DIR

    family = {"regular": os.path.join(FONT_DIR, "DejaVuSans.ttf")}
    family.update({k: os.path.join(FONT_DIR, v) for k, v in variants.items()})
    return {**MINIMAL_CONFIG, "fonts": {"family": family}}


def _warning(tmp_path, capsys, md, config=MINIMAL_CONFIG, **kw):
    CorpDoc(config=config).render(md, output=str(tmp_path / "o.pdf"), **kw)
    return capsys.readouterr().err


def test_warning_covers_the_bold_face_used_by_headings(tmp_path, capsys):
    ch = _only_in_sans()
    config = _sans_with(bold="DejaVuSansMono.ttf")

    assert "boxes" not in _warning(tmp_path, capsys, f"# Title\n\nBody {ch}.\n", config)
    err = _warning(tmp_path, capsys, f"# Title {ch}\n\nBody.\n", config)
    assert "boxes" in err and f"U+{ord(ch):04X}" in err
    assert "boxes" in _warning(tmp_path, capsys, f"# Title\n\nSome **bold {ch}** text.\n", config)


def test_warning_covers_the_mono_face_used_by_code(tmp_path, capsys):
    ch = _only_in_sans()
    config = _sans_with(mono="DejaVuSansMono.ttf")

    assert "boxes" in _warning(tmp_path, capsys, f"# T\n\n```\nx = {ch}\n```\n", config)
    assert "boxes" in _warning(tmp_path, capsys, f"# T\n\nInline `{ch}` code.\n", config)
    assert "boxes" not in _warning(tmp_path, capsys, f"# T\n\nPlain {ch} text.\n", config)


def test_no_warning_for_text_that_is_never_drawn_with_a_pdf_font(tmp_path, capsys, monkeypatch):
    from PIL import Image as PILImage

    from corpdoc import mermaid

    def fake_run(cmd, **kwargs):
        PILImage.new("RGB", (200, 100), (240, 240, 255)).save(cmd[cmd.index("-o") + 1])
        return __import__("subprocess").CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(mermaid.shutil, "which", lambda name: "/fake/bin/mmdc")
    monkeypatch.setattr(mermaid.subprocess, "run", fake_run)
    PILImage.new("RGB", (60, 30), (200, 30, 30)).save(tmp_path / "图.png")

    md = "# T\n\n```mermaid\nflowchart LR\n    A[日本語] --> B[中文]\n```\n\n![Figure](图.png)\n"
    err = _warning(tmp_path, capsys, md, base_dir=str(tmp_path))
    assert err == ""


def test_warning_when_a_diagram_falls_back_to_text(tmp_path, capsys, monkeypatch):
    from corpdoc import mermaid

    monkeypatch.setattr(mermaid.shutil, "which", lambda name: None)
    md = "# T\n\n```mermaid\nflowchart LR\n    A[日本語] --> B\n```\n"
    err = _warning(tmp_path, capsys, md)
    assert "boxes" in err and "U+65E5" in err


def test_warning_covers_captions_tables_and_the_cover(tmp_path, capsys):
    from PIL import Image as PILImage

    PILImage.new("RGB", (60, 30), (200, 30, 30)).save(tmp_path / "a.png")
    cases = [
        "# T\n\n![Water H₂O](a.png)\n",
        "# T\n\n| A | B |\n|---|---|\n| H₂O | 1 |\n",
        "# T\n\n- item\n  - nested H₂O\n",
        "---\ntitle: Report on H₂O\n---\n\n# T\n\nBody.\n",
    ]
    for md in cases:
        err = _warning(tmp_path, capsys, md, base_dir=str(tmp_path))
        assert err.count("boxes") == 1 and "U+2082" in err, md
