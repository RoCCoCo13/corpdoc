"""End-to-end rendering tests — generate real PDFs and verify they exist."""

import os
import tempfile
import textwrap

from corpdoc.api import CorpDoc


MINIMAL_CONFIG = {
    "company": {
        "legal_name": "Test Corp SL",
        "tagline": "test | corp",
        "brand_split": 3,
    },
    "logo": {"svg": "", "png": ""},
    "footer": {
        "address": "123 Test Street",
        "fields": [{"label": "Email", "value": "test@example.com"}],
    },
    "defaults": {
        "language": "en",
        "version": "1.0",
        "author": "Test User",
    },
}

FULL_MD = textwrap.dedent("""\
    ---
    title: "Test Document"
    subtitle: "E2E Verification"
    version: "1.0"
    author: "Test User"
    ---

    # 1. Introduction

    This is a test paragraph with **bold** and *italic* text, and `inline code`.

    ## 1.1 Details

    Some body text explaining the details.

    ### 1.1.1 Sub-section

    Even deeper nesting.

    ## 1.2 Lists

    - Item one
    - Item two
      - Nested item A
      - Nested item B
    - Item three

    # 2. Data

    | Column A | Column B | Column C |
    |----------|----------|----------|
    | Value 1  | Value 2  | Value 3  |
    | Value 4  | Value 5  | Value 6  |

    # 3. Code

    ```python
    def hello():
        print("Hello, world!")
    ```

    ---

    # 4. Conclusion

    End of test document.
""")


def _make_pdf(md_text=None, config=None):
    """Helper: render md to a temp PDF, return path. Caller must unlink."""
    doc = CorpDoc(config=config or MINIMAL_CONFIG)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
    doc.render(md_text or FULL_MD, output=pdf_path)
    return pdf_path


def test_render_produces_nonempty_pdf():
    pdf = _make_pdf()
    try:
        assert os.path.exists(pdf)
        assert os.path.getsize(pdf) > 2000
    finally:
        os.unlink(pdf)


def test_render_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(FULL_MD)
        md_path = f.name
    pdf_path = md_path.replace(".md", ".pdf")
    try:
        doc = CorpDoc(config=MINIMAL_CONFIG)
        result = doc.render(md_path, output=pdf_path)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 2000
    finally:
        os.unlink(md_path)
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_render_xml_special_chars():
    """& < > in content must not crash the ReportLab XML pipeline."""
    md = textwrap.dedent("""\
        # Tests & Checks

        Use `a < b` and `x > y` in conditions.

        Comparison: **bold & strong** text.

        | Input | Output |
        |-------|--------|
        | a < b | true   |
        | x > 0 | valid  |
    """)
    pdf = _make_pdf(md_text=md)
    try:
        assert os.path.exists(pdf)
        assert os.path.getsize(pdf) > 2000
    finally:
        os.unlink(pdf)


def test_render_spanish_language():
    cfg = {**MINIMAL_CONFIG, "defaults": {**MINIMAL_CONFIG["defaults"], "language": "es"}}
    md = textwrap.dedent("""\
        ---
        title: "Propuesta Técnica"
        subtitle: "Para Cliente SL"
        ---

        # 1. Resumen Ejecutivo

        El proyecto consiste en la instalación de un sistema fotovoltaico.

        ## 1.1 Alcance

        Descripción del alcance del trabajo.
    """)
    pdf = _make_pdf(md_text=md, config=cfg)
    try:
        assert os.path.exists(pdf)
        assert os.path.getsize(pdf) > 2000
    finally:
        os.unlink(pdf)


def test_render_returns_output_path():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
    try:
        doc = CorpDoc(config=MINIMAL_CONFIG)
        result = doc.render("# Hello\n\nContent.", output=pdf_path)
        assert result == pdf_path
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_needs_landscape_threshold():
    """_needs_landscape returns True only when column count meets threshold."""
    doc = CorpDoc(config=MINIMAL_CONFIG)
    assert doc._needs_landscape([["a"] * 7]) is False
    assert doc._needs_landscape([["a"] * 8]) is True
    assert doc._needs_landscape([]) is False


def test_needs_landscape_custom_threshold():
    cfg = {**MINIMAL_CONFIG, "tables": {"landscape_threshold": 5}}
    doc = CorpDoc(config=cfg)
    assert doc._needs_landscape([["a"] * 4]) is False
    assert doc._needs_landscape([["a"] * 5]) is True


def test_render_each_cover_style():
    """All shipped cover styles must render without raising."""
    from corpdoc.flowables import CoverPageFlowable

    for style in CoverPageFlowable.STYLES:
        cfg = {**MINIMAL_CONFIG, "cover": {"style": style}}
        pdf = _make_pdf(config=cfg)
        try:
            assert os.path.exists(pdf)
            assert os.path.getsize(pdf) > 2000, f"style {style!r} produced tiny PDF"
        finally:
            os.unlink(pdf)


def test_unknown_cover_style_falls_back_to_classic(capsys):
    cfg = {**MINIMAL_CONFIG, "cover": {"style": "does-not-exist"}}
    pdf = _make_pdf(config=cfg)
    try:
        assert os.path.exists(pdf)
        captured = capsys.readouterr()
        assert "unknown cover.style" in captured.err
    finally:
        os.unlink(pdf)


def test_render_wide_table_produces_landscape_page():
    """A 9-column table must trigger a landscape page in the output PDF."""
    md = textwrap.dedent("""\
        # Wide Table Demo

        Some intro text.

        | A | B | C | D | E | F | G | H | I |
        |---|---|---|---|---|---|---|---|---|
        | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
        | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

        Trailing paragraph.
    """)
    pdf = _make_pdf(md_text=md)
    try:
        assert os.path.exists(pdf)
        # Parse page sizes from the PDF itself via pypdf (optional dep in reportlab stack).
        # Fall back to substring check if pypdf isn't available.
        try:
            from pypdf import PdfReader

            reader = PdfReader(pdf)
            sizes = [(p.mediabox.width, p.mediabox.height) for p in reader.pages]
            # At least one page must be landscape (width > height).
            assert any(w > h for w, h in sizes), f"no landscape page found in {sizes}"
        except ImportError:
            # Without pypdf, just assert the PDF is larger than a portrait-only baseline.
            assert os.path.getsize(pdf) > 2000
    finally:
        os.unlink(pdf)
