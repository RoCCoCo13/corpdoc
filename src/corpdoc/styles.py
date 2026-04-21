"""
Paragraph and table styles for CorpDoc.

All styles are derived from the brand colors dictionary. Call `build_styles(colors)`
to get a dict-like object of all named styles.
"""

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm


def build_styles(colors):
    """
    Build the full style sheet for a CorpDoc document.

    Args:
        colors: dict with keys primary, secondary, accent, light, lighter, text.

    Returns:
        A ReportLab StyleSheet with all CorpDoc styles registered.
    """
    base = getSampleStyleSheet()
    c = colors
    P = ParagraphStyle

    def add(style):
        base.add(style)

    # Title / subtitle (cover page fallback — actual cover is drawn on canvas)
    add(
        P(
            "CTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=HexColor(c["primary"]),
            spaceAfter=4 * mm,
            alignment=TA_LEFT,
            leading=34,
        )
    )
    add(
        P(
            "CSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=14,
            textColor=HexColor(c["secondary"]),
            spaceAfter=10 * mm,
            alignment=TA_LEFT,
        )
    )

    # Headings
    add(
        P(
            "CH1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            textColor=HexColor(c["primary"]),
            spaceBefore=10 * mm,
            spaceAfter=4 * mm,
        )
    )
    add(
        P(
            "CH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=HexColor(c["primary"]),
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
        )
    )
    add(
        P(
            "CH3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=HexColor(c.get("highlight", c["secondary"])),
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
        )
    )
    add(
        P(
            "CH4",
            parent=base["Heading4"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=HexColor(c["text"]),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        )
    )

    # Body and lists
    add(
        P(
            "CBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=HexColor(c["text"]),
            leading=14,
            spaceAfter=3 * mm,
            alignment=TA_JUSTIFY,
        )
    )
    add(
        P(
            "CBullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=HexColor(c["text"]),
            leading=14,
            spaceAfter=1.5 * mm,
            leftIndent=8 * mm,
            bulletIndent=3 * mm,
        )
    )
    add(
        P(
            "CBullet2",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=HexColor("#555555"),
            leading=13,
            spaceAfter=1 * mm,
            leftIndent=16 * mm,
            bulletIndent=11 * mm,
        )
    )

    # Code
    add(
        P(
            "CCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            textColor=HexColor("#2d2d2d"),
            backColor=HexColor("#f5f5f5"),
            leftIndent=5 * mm,
            rightIndent=5 * mm,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
            leading=11,
            borderPadding=5,
        )
    )

    # Table cells
    add(
        P(
            "TCell",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=HexColor(c["text"]),
            leading=11,
            alignment=TA_LEFT,
        )
    )
    add(P("THead", fontName="Helvetica-Bold", fontSize=8.5, textColor=white, leading=11))
    add(
        P(
            "TCellSm",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=HexColor(c["text"]),
            leading=10,
            alignment=TA_LEFT,
        )
    )
    add(P("THeadSm", fontName="Helvetica-Bold", fontSize=7.5, textColor=white, leading=10))

    # Meta (cover / version page)
    add(
        P(
            "CMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=HexColor(c["text"]),
            leading=15,
            spaceAfter=1 * mm,
        )
    )

    # TOC entries
    add(
        P(
            "TOC1",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=HexColor(c["primary"]),
            spaceBefore=2 * mm,
            spaceAfter=1 * mm,
        )
    )
    add(
        P(
            "TOC2",
            fontName="Helvetica",
            fontSize=10,
            textColor=HexColor(c["text"]),
            leftIndent=8 * mm,
            spaceAfter=0.5 * mm,
        )
    )
    add(
        P(
            "TOC3",
            fontName="Helvetica",
            fontSize=9,
            textColor=HexColor("#666666"),
            leftIndent=16 * mm,
            spaceAfter=0.5 * mm,
        )
    )

    # Mermaid placeholder
    add(
        P(
            "CMermaid",
            fontName="Courier",
            fontSize=8.5,
            textColor=HexColor(c["primary"]),
            backColor=HexColor(c["lighter"]),
            leftIndent=5 * mm,
            rightIndent=5 * mm,
            spaceBefore=4 * mm,
            spaceAfter=4 * mm,
            leading=12,
            borderPadding=8,
            borderWidth=1,
            borderColor=HexColor(c["secondary"]),
        )
    )

    # Version history heading
    add(
        P(
            "VerH",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=HexColor(c["primary"]),
            spaceBefore=6 * mm,
            spaceAfter=6 * mm,
        )
    )

    return base
