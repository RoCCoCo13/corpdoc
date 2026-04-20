"""
Main CorpDoc API.

Usage:
    from corpdoc import CorpDoc

    # From config file
    doc = CorpDoc(config='corpdoc.yml')
    doc.render('input.md', output='output.pdf')

    # From explicit config
    doc = CorpDoc(config={
        'company': {'legal_name': 'Acme Inc.', 'tagline': 'acme | engineering'},
        'logo': {'svg': 'logo.svg', 'png': 'logo.png'},
        'footer': {'address': '...', 'fields': [...]},
    })
    doc.render('input.md', output='output.pdf')
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from corpdoc.colors import extract_colors_from_svg, assign_roles
from corpdoc.parser import parse_frontmatter, parse_blocks, detect_language
from corpdoc.styles import build_styles
from corpdoc.flowables import HRLine, CoverPageFlowable
from corpdoc.canvas import CorpCanvas
from corpdoc.i18n import t
from corpdoc.logo import Logo


class CorpDocTemplate(BaseDocTemplate):
    """
    BaseDocTemplate subclass with two page templates (portrait A4 and
    landscape A4) so wide tables can auto-switch orientation mid-document.
    Heading paragraphs are fed into the real TableOfContents flowable via
    ReportLab's notify mechanism.
    """

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        sname = flowable.style.name
        if sname == "CH1":
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
        elif sname == "CH2":
            self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))
        elif sname == "CH3":
            self.notify("TOCEntry", (2, flowable.getPlainText(), self.page))


class CorpDoc:
    """
    Main entry point for rendering Markdown to corporate PDF.

    Args:
        config: Either a path to a YAML config file, or a dict with the
                same structure.

    The config must contain (at minimum):
        company:
          legal_name: str
          tagline: str              # shown in header
          brand_split: int          # chars to color in accent (default: 3)
        logo:
          svg: path                 # used for color extraction
          png: path                 # used for PDF embedding
          cover_scale: float        # default: 1.0
          header_scale: float       # default: 0.45
        footer:
          address: str
          fields:                   # list of {label, value} dicts
            - label: Director
              value: Name
        defaults:
          language: "auto"|en|es|de|fr   # default: auto
          version: "1.0"
          author: str
    """

    def __init__(self, config):
        if isinstance(config, (str, Path)):
            import yaml

            with open(config, "r", encoding="utf-8") as f:
                self.cfg = yaml.safe_load(f)
        elif isinstance(config, dict):
            self.cfg = config
        else:
            raise ValueError("config must be a path or a dict")

        # Extract colors from SVG logo, then let any explicit `colors:` block
        # in the config override the auto-derived values on a per-key basis.
        svg_path = self.cfg.get("logo", {}).get("svg")
        if svg_path and os.path.exists(svg_path):
            raw = extract_colors_from_svg(svg_path)
            self.colors = assign_roles(raw)
        else:
            self.colors = assign_roles(["#333333"])

        explicit = self.cfg.get("colors") or {}
        if explicit:
            self.colors = {**self.colors, **explicit}

        self.logo = Logo(self.cfg)

        # Warn early if a logo was configured but nothing resolved
        logo_cfg = self.cfg.get("logo", {}) or {}
        if (logo_cfg.get("png") or logo_cfg.get("svg")) and not self.logo:
            print(
                "Warning: logo was configured but neither PNG nor SVG could be "
                "loaded — PDF will render without logo.",
                file=sys.stderr,
            )

        self.styles = build_styles(self.colors)

    def render(self, md_input, output="output.pdf"):
        """
        Render a Markdown file or string to PDF.

        Args:
            md_input: Path to .md file, or markdown text as string.
            output: Output PDF path.

        Returns:
            Path to the generated PDF.
        """
        if os.path.exists(str(md_input)):
            md_text = Path(md_input).read_text(encoding="utf-8")
        else:
            md_text = str(md_input)

        meta, body = parse_frontmatter(md_text)
        blocks = parse_blocks(body)

        lang_cfg = self.cfg.get("defaults", {}).get("language", "auto")
        lang = detect_language(body) if lang_cfg == "auto" else lang_cfg

        title = self._extract_title(meta, blocks)
        subtitle = self._extract_subtitle(meta, blocks)

        left_m, right_m, top_m, bottom_m = 2 * cm, 2 * cm, 2.2 * cm, 3.2 * cm
        portrait_size = A4
        landscape_size = landscape(A4)

        doc = CorpDocTemplate(
            output,
            pagesize=portrait_size,
            leftMargin=left_m,
            rightMargin=right_m,
            topMargin=top_m,
            bottomMargin=bottom_m,
            title=title,
            author=meta.get("autor", meta.get("author", "")),
        )

        def _make_frame(pw, ph, frame_id):
            return Frame(
                left_m,
                bottom_m,
                pw - left_m - right_m,
                ph - top_m - bottom_m,
                id=frame_id,
            )

        doc.addPageTemplates(
            [
                PageTemplate(
                    id="portrait",
                    frames=[_make_frame(*portrait_size, "portrait_frame")],
                    pagesize=portrait_size,
                ),
                PageTemplate(
                    id="landscape",
                    frames=[_make_frame(*landscape_size, "landscape_frame")],
                    pagesize=landscape_size,
                ),
            ]
        )

        elements = []
        elements.extend(self._build_cover(title, subtitle, meta, lang))
        elements.extend(self._build_version_history(meta, lang))
        elements.extend(self._build_toc(lang))
        elements.extend(self._build_body(blocks))

        corp_data = self._build_corp_data(lang)

        def canvas_maker(filename, pagesize=A4, **kw):
            return CorpCanvas(filename, pagesize=pagesize, _corp=corp_data, **kw)

        doc.build(elements, canvasmaker=canvas_maker)
        return output

    # ─────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────

    @staticmethod
    def _plain(xml_text):
        """Strip ReportLab XML tags to get plain text (for PDF metadata, TOC)."""
        return re.sub(r"<[^>]+>", "", xml_text)

    def _extract_title(self, meta, blocks):
        t = meta.get("titulo", meta.get("title", ""))
        if t:
            return t
        for b in blocks:
            if b["type"] == "h" and b["level"] == 1:
                return self._plain(b["text"])
        for b in blocks:
            if b["type"] == "h":
                return self._plain(b["text"])
        return "Document"

    def _extract_subtitle(self, meta, blocks):
        s = meta.get("subtitulo", meta.get("subtitle", ""))
        if s:
            return s
        if len(blocks) >= 2:
            if blocks[0]["type"] == "h" and blocks[0]["level"] == 1:
                if blocks[1]["type"] == "h" and blocks[1]["level"] == 2:
                    return self._plain(blocks[1]["text"])
        return ""

    def _build_corp_data(self, lang):
        company = self.cfg.get("company", {})
        footer = self.cfg.get("footer", {})
        logo = self.cfg.get("logo", {})

        data = dict(self.colors)
        data["logo"] = self.logo
        data["lang"] = lang
        data["brand_split"] = company.get("brand_split", 3)
        data["tagline"] = company.get("tagline", "")
        data["tagline_prefix"] = company.get("tagline_prefix", "")
        data["company_legal"] = company.get("legal_name", "")
        data["address"] = footer.get("address", "")
        data["fields"] = footer.get("fields", [])
        data["header_scale"] = logo.get("header_scale", 0.45)
        return data

    # ─────────────────────────────────────────────────
    # Page builders
    # ─────────────────────────────────────────────────

    def _build_cover(self, title, subtitle, meta, lang):
        return [
            CoverPageFlowable(
                title=title,
                subtitle=subtitle,
                meta=meta,
                lang=lang,
                logo=self.logo,
                cover_scale=self.cfg.get("logo", {}).get("cover_scale", 1.0),
                colors=self.colors,
                company=self.cfg.get("company", {}),
                defaults=self.cfg.get("defaults", {}),
            ),
            PageBreak(),
        ]

    def _build_version_history(self, meta, lang):
        els = []
        c = self.colors
        S = self.styles

        h = t(lang, "version_history_headers")
        els.append(Paragraph(t(lang, "version_history_title"), S["VerH"]))

        defaults = self.cfg.get("defaults", {})
        ver = meta.get("version", defaults.get("version", "1.0"))
        fecha = meta.get("fecha", meta.get("date", str(date.today())))
        author = meta.get("autor", meta.get("author", defaults.get("author", "")))

        data = [
            [
                Paragraph(h[0], S["THead"]),
                Paragraph(h[1], S["THead"]),
                Paragraph(h[2], S["THead"]),
                Paragraph(h[3], S["THead"]),
            ],
            [
                Paragraph(ver, S["TCell"]),
                Paragraph(str(fecha), S["TCell"]),
                Paragraph(author or "—", S["TCell"]),
                Paragraph(t(lang, "initial_version"), S["TCell"]),
            ],
        ]
        for _ in range(3):
            data.append([Paragraph("", S["TCell"])] * 4)

        avail = A4[0] - 4 * cm
        tbl = Table(
            data, colWidths=[avail * 0.12, avail * 0.18, avail * 0.25, avail * 0.45], repeatRows=1
        )

        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor(c["primary"])),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
                    ("BOX", (0, 0), (-1, -1), 1, HexColor(c["secondary"])),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        els.append(tbl)
        els.append(PageBreak())
        return els

    def _build_toc(self, lang):
        c = self.colors
        S = self.styles

        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle(
                "TOCEntry1",
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=HexColor(c["primary"]),
                leftIndent=0,
                firstLineIndent=0,
                spaceBefore=2 * mm,
                spaceAfter=1 * mm,
            ),
            ParagraphStyle(
                "TOCEntry2",
                fontName="Helvetica",
                fontSize=10,
                textColor=HexColor(c["text"]),
                leftIndent=8 * mm,
                firstLineIndent=0,
                spaceAfter=0.5 * mm,
            ),
            ParagraphStyle(
                "TOCEntry3",
                fontName="Helvetica",
                fontSize=9,
                textColor=HexColor("#666666"),
                leftIndent=16 * mm,
                firstLineIndent=0,
                spaceAfter=0.5 * mm,
            ),
        ]

        return [
            Paragraph(t(lang, "toc_title"), S["CH1"]),
            Spacer(1, 4 * mm),
            toc,
            Spacer(1, 4 * mm),
            HRLine(100, 0.5, HexColor(c["secondary"]), 2 * mm, 4 * mm),
            PageBreak(),
        ]

    def _build_body(self, blocks):
        els = []
        S = self.styles
        c = self.colors

        for b in blocks:
            tp = b["type"]
            if tp == "h":
                lvl = min(b["level"], 4)
                els.append(Paragraph(b["text"], S[f"CH{lvl}"]))
                if lvl == 1:
                    els.append(HRLine(35, 2, HexColor(c["accent"]), 0, 3 * mm))
            elif tp == "p":
                els.append(Paragraph(b["text"], S["CBody"]))
            elif tp == "list":
                for item in b["items"]:
                    text = item["text"] if isinstance(item, dict) else item
                    level = item.get("level", 0) if isinstance(item, dict) else 0
                    style = S["CBullet2"] if level > 0 else S["CBullet"]
                    els.append(Paragraph(f"•  {text}", style))
                els.append(Spacer(1, 2 * mm))
            elif tp == "table":
                if self._needs_landscape(b["rows"]):
                    els.append(NextPageTemplate("landscape"))
                    els.append(PageBreak())
                    els.extend(self._build_table(b["rows"], page_width=landscape(A4)[0]))
                    els.append(NextPageTemplate("portrait"))
                    els.append(PageBreak())
                else:
                    els.extend(self._build_table(b["rows"]))
            elif tp == "mermaid":
                content = b["content"].replace("\n", "<br/>")
                els.append(Paragraph(f"<b>[ Diagram ]</b><br/><br/>{content}", S["CMermaid"]))
            elif tp == "code":
                content = (
                    b["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                content = content.replace("\n", "<br/>").replace(" ", "&nbsp;")
                els.append(Paragraph(content, S["CCode"]))
            elif tp == "hr":
                els.append(HRLine(100, 0.5, HexColor(c["secondary"]), 4 * mm, 4 * mm))
        return els

    def _needs_landscape(self, rows):
        """
        A table is rendered on a landscape page when its column count
        exceeds the configured threshold (default: 8).
        """
        threshold = self.cfg.get("tables", {}).get("landscape_threshold", 8)
        return bool(rows) and len(rows[0]) >= threshold

    def _build_table(self, rows, page_width=None):
        if not rows:
            return []
        S = self.styles
        c = self.colors
        n = len(rows[0])
        wide = n > 6
        cs = S["TCellSm" if wide else "TCell"]
        hs = S["THeadSm" if wide else "THead"]

        data = [
            [Paragraph(cell, hs if ri == 0 else cs) for cell in row] for ri, row in enumerate(rows)
        ]

        pw = page_width if page_width is not None else A4[0]
        avail = pw - 4 * cm
        tbl = Table(data, colWidths=[avail / n] * n, repeatRows=1)

        style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(c["primary"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
            ("BOX", (0, 0), (-1, -1), 0.8, HexColor(c["secondary"])),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), HexColor(c["lighter"])))
        tbl.setStyle(TableStyle(style))
        return [Spacer(1, 2 * mm), tbl, Spacer(1, 3 * mm)]
