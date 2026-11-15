"""
Font families for CorpDoc.

Three choices, selected with `fonts.family` in the config:

- "helvetica" (default) — the PDF built-in fonts Helvetica and Courier.
  Nothing is embedded. Coverage is WinAnsi (Western European) plus what
  ReportLab substitutes from the Symbol font; anything else is drawn as a
  filled box.
- "dejavu" — DejaVu Sans / DejaVu Sans Mono, bundled with the package and
  embedded (subset) in the PDF. Wide Unicode coverage: Greek, Cyrillic,
  maths operators, arrows, super- and subscripts.
- a mapping of TTF paths — `regular` is required; `bold`, `italic`,
  `bold_italic` and `mono` are optional.

Every consumer reads font names from the dict returned by `resolve_fonts`:
    {"regular", "bold", "italic", "bold_italic", "mono", "builtin"}
"""

import os
import unicodedata
import zlib

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError, TTFont

from corpdoc._util import warn

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

BUILTIN_FONTS = {
    "regular": "Helvetica",
    "bold": "Helvetica-Bold",
    "italic": "Helvetica-Oblique",
    "bold_italic": "Helvetica-BoldOblique",
    "mono": "Courier",
    "builtin": True,
}

_DEJAVU_FILES = {
    "regular": "DejaVuSans.ttf",
    "bold": "DejaVuSans-Bold.ttf",
    "italic": "DejaVuSans-Oblique.ttf",
    "bold_italic": "DejaVuSans-BoldOblique.ttf",
    "mono": "DejaVuSansMono.ttf",
}

_VARIANTS = ("regular", "bold", "italic", "bold_italic", "mono")


def _register(name, path):
    """Register a TTF under `name` (idempotent) and return the name."""
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, path))
    return name


def _register_families(fonts):
    """Tell ReportLab which faces <b> and <i> map to inside paragraphs."""
    pdfmetrics.registerFontFamily(
        fonts["regular"],
        normal=fonts["regular"],
        bold=fonts["bold"],
        italic=fonts["italic"],
        boldItalic=fonts["bold_italic"],
    )
    mono = fonts["mono"]
    if mono != BUILTIN_FONTS["mono"]:
        pdfmetrics.registerFontFamily(mono, normal=mono, bold=mono, italic=mono, boldItalic=mono)


def _dejavu():
    fonts = {
        variant: _register(filename[:-4], os.path.join(FONT_DIR, filename))
        for variant, filename in _DEJAVU_FILES.items()
    }
    fonts["builtin"] = False
    _register_families(fonts)
    return fonts


def _custom(paths):
    regular = paths.get("regular")
    if not regular:
        raise ValueError("fonts.family needs a 'regular' TTF path")

    def load(path):
        path = os.path.abspath(str(path))
        if not os.path.isfile(path):
            raise FileNotFoundError(f"font file not found: {path}")
        # The registered name is tied to the file, so two configs pointing
        # at different files never collide inside one process.
        stem = os.path.splitext(os.path.basename(path))[0]
        tag = zlib.crc32(path.encode("utf-8")) & 0xFFFF
        return _register(f"CorpDoc-{stem}-{tag:04x}", path)

    fonts = {"regular": load(regular)}
    for variant in ("bold", "italic", "bold_italic"):
        fonts[variant] = load(paths[variant]) if paths.get(variant) else fonts["regular"]
    if paths.get("mono"):
        fonts["mono"] = load(paths["mono"])
    else:
        # Courier would bring back the WinAnsi limitation, so default to the
        # bundled Unicode monospace face.
        fonts["mono"] = _register("DejaVuSansMono", os.path.join(FONT_DIR, _DEJAVU_FILES["mono"]))
    fonts["builtin"] = False
    _register_families(fonts)
    return fonts


def resolve_fonts(cfg):
    """
    Resolve `cfg["fonts"]["family"]` to a dict of registered font names.

    Any problem (unknown family, missing or invalid font file) prints a
    warning and falls back to the built-in fonts, so a render never fails
    because of the font configuration.
    """
    family = ((cfg or {}).get("fonts") or {}).get("family", "helvetica")
    try:
        if isinstance(family, dict):
            unknown = sorted(set(family) - set(_VARIANTS))
            if unknown:
                warn(f"fonts.family: ignoring unknown keys {unknown}; valid: {list(_VARIANTS)}")
            return _custom(family)
        name = str(family or "helvetica").strip().lower()
        if name == "dejavu":
            return _dejavu()
        if name != "helvetica":
            warn(
                f"unknown fonts.family '{family}'. Falling back to 'helvetica'. "
                "Valid: helvetica, dejavu, or a mapping of TTF paths."
            )
    except (OSError, ValueError, TTFError) as exc:
        warn(f"fonts.family could not be loaded ({exc}). Falling back to 'helvetica'.")
    return dict(BUILTIN_FONTS)


def _can_draw(font):
    """Return a predicate telling whether `font` has a glyph for a character."""
    if isinstance(font, TTFont):
        glyphs = font.face.charToGlyph
        return lambda ch: ord(ch) in glyphs

    # Built-in (Type 1) fonts: ReportLab tries the font's own encoding, then
    # its substitution fonts (Symbol, ZapfDingbats).
    encodings = [f.encName for f in [font, *font.substitutionFonts]]

    def can_draw(ch):
        for enc in encodings:
            try:
                ch.encode(enc)
            except (UnicodeError, LookupError):
                continue
            return True
        return False

    return can_draw


def unsupported_chars(text, fonts=None, role="regular"):
    """
    Return the characters of `text` that the `role` font ("regular", "bold",
    "italic", "bold_italic" or "mono") cannot draw, in order of first
    appearance. Whitespace and invisible format characters are ignored.
    """
    fonts = fonts or BUILTIN_FONTS
    can_draw = _can_draw(pdfmetrics.getFont(fonts[role]))
    missing = []
    for ch in dict.fromkeys(text):
        if ord(ch) < 128 or ch.isspace() or unicodedata.category(ch) in ("Cf", "Cc"):
            continue
        if not can_draw(ch):
            missing.append(ch)
    return missing


def warn_unsupported(text, fonts):
    """
    Print a single warning if `text` has characters the fonts cannot draw.

    `text` is a string (checked against the regular font) or a mapping of
    font role -> strings drawn with that font.
    """
    by_role = {"regular": [text]} if isinstance(text, str) else text
    found = {}
    for role, chunks in by_role.items():
        for ch in unsupported_chars("".join(chunks), fonts, role):
            found.setdefault(ch, None)
    missing = list(found)
    if not missing:
        return
    shown = ", ".join(f"{ch} (U+{ord(ch):04X})" for ch in missing[:8])
    more = f" and {len(missing) - 8} more" if len(missing) > 8 else ""
    if fonts.get("builtin"):
        hint = 'the built-in fonts cannot encode them. Set fonts.family: "dejavu" in the config.'
    else:
        hint = "the configured font cannot draw them (it has no glyph for them)."
    warn(f"{len(missing)} character(s) will show as boxes: {shown}{more} — {hint}")
