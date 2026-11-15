"""
Custom ReportLab canvas with corporate header and footer.

Header: brand tagline (with split-color styling) on left, logo on right.
Footer: company legal info with key/value brand-split coloring, page numbers.
"""

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from corpdoc.fonts import BUILTIN_FONTS
from corpdoc.i18n import t


def brand_split_draw(canv, x, y, text, n, accent_hex, primary_hex, font="Helvetica", size=7):
    """
    Draw text on canvas with "brand split" coloring:
    First `n` chars of each word in accent, rest in primary.
    """
    cursor = x
    words = text.split()
    for wi, word in enumerate(words):
        if wi > 0:
            canv.setFont(font, size)
            canv.setFillColor(HexColor(primary_hex))
            canv.drawString(cursor, y, " ")
            cursor += canv.stringWidth(" ", font, size)

        head, tail = word[:n], word[n:]
        canv.setFont(font, size)
        canv.setFillColor(HexColor(accent_hex))
        canv.drawString(cursor, y, head)
        cursor += canv.stringWidth(head, font, size)

        if tail:
            canv.setFillColor(HexColor(primary_hex))
            canv.drawString(cursor, y, tail)
            cursor += canv.stringWidth(tail, font, size)

    return cursor


def brand_split_inline(text, n, accent_hex, primary_hex):
    """
    Return ReportLab-compatible XML string for brand-split text
    (use inside Paragraph).
    """
    words = text.split()
    parts = []
    for w in words:
        if len(w) <= n:
            parts.append(f'<font color="{accent_hex}">{w}</font>')
        else:
            parts.append(
                f'<font color="{accent_hex}">{w[:n]}</font>'
                f'<font color="{primary_hex}">{w[n:]}</font>'
            )
    return " ".join(parts)


class CorpCanvas(canvas.Canvas):
    """
    Canvas that draws corporate header and footer on every page except
    the leading unnumbered pages: cover and version history, when present
    (`_corp["unnumbered_pages"]`, default 2).
    """

    def __init__(self, *args, **kwargs):
        self._corp = kwargs.pop("_corp", {})
        super().__init__(*args, **kwargs)
        self._page_states = []
        self.page_count = 0

    def showPage(self):
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._page_states)
        for state in self._page_states:
            self.__dict__.update(state)
            self._draw_header_footer(total)
            canvas.Canvas.showPage(self)
        # Set after the loop: restoring each page state rewinds __dict__.
        self.page_count = total
        canvas.Canvas.save(self)

    def _draw_header_footer(self, total_pages):
        pn = self._pageNumber
        corp = self._corp
        # Skip cover and version history (whichever of them are enabled)
        skip = corp.get("unnumbered_pages", 2)
        if pn <= skip:
            return

        w, h = self._pagesize
        accent = corp.get("accent", "#b9885a")
        primary = corp.get("primary", "#2e1e19")
        lang = corp.get("lang", "en")
        split_n = corp.get("brand_split", 3)

        # ── HEADER ──
        self._draw_header(w, h, corp, accent, primary, split_n)

        # ── FOOTER ──
        self._draw_footer(w, h, corp, accent, primary, split_n, pn - skip, total_pages - skip, lang)

    def _draw_header(self, w, h, corp, accent, primary, split_n):
        fonts = corp.get("fonts") or BUILTIN_FONTS
        # Logo right-aligned
        logo = corp.get("logo")
        header_scale = corp.get("header_scale", 0.45)
        if logo:
            iw, ih = logo.width, logo.height
            # Base size 170pt * scale
            target_w = 170 * header_scale
            sc = target_w / iw
            dw, dh = iw * sc, ih * sc
            logo.draw(self, w - 2 * cm - dw, h - 0.6 * cm - dh, dw, dh)

        # Tagline (left)
        tagline = corp.get("tagline", "")
        if tagline:
            # Short prefix in italic (e.g. "jes.")
            prefix = corp.get("tagline_prefix", "")
            x_cursor = 2 * cm
            if prefix:
                self.setFont(fonts["italic"], 8)
                self.setFillColor(HexColor(accent))
                self.drawString(x_cursor, h - 1.3 * cm, prefix)
                x_cursor += self.stringWidth(prefix, fonts["italic"], 8) + 8

            brand_split_draw(
                self, x_cursor, h - 1.3 * cm, tagline, split_n, accent, primary, fonts["regular"], 7
            )

        # Header accent line
        self.setStrokeColor(HexColor(accent))
        self.setLineWidth(0.4)
        self.line(2 * cm, h - 1.6 * cm, w - 2 * cm, h - 1.6 * cm)

    def _draw_footer(self, w, h, corp, accent, primary, split_n, pn, total, lang):
        footer_y = 2.6 * cm
        fonts = corp.get("fonts") or BUILTIN_FONTS

        # Footer accent line
        self.setStrokeColor(HexColor(accent))
        self.setLineWidth(1.0)
        self.line(2 * cm, footer_y, w - 2 * cm, footer_y)

        cx = w / 2

        # Line 1: Company name (brand-split) + address
        company_name = corp.get("company_legal", "")
        address = corp.get("address", "")

        if company_name:
            line1 = company_name
            if address:
                line1 += f"    |    {address}"
            total_w = self.stringWidth(line1, fonts["regular"], 6.5)
            start_x = cx - total_w / 2

            end_x = brand_split_draw(
                self,
                start_x,
                footer_y - 12,
                company_name,
                split_n,
                accent,
                primary,
                fonts["regular"],
                6.5,
            )
            if address:
                self.setFont(fonts["regular"], 6.5)
                self.setFillColor(HexColor(primary))
                self.drawString(end_x, footer_y - 12, f"    |    {address}")

        # Additional fields (key/value pairs, grouped per line)
        fields = corp.get("fields", [])
        field_lines = self._group_fields(fields)

        for li, fline in enumerate(field_lines):
            y_pos = footer_y - 23 - (li * 11)
            full_text = "    |    ".join(f"{f['label']}: {f['value']}" for f in fline)
            total_w = self.stringWidth(full_text, fonts["regular"], 6.5)
            cur_x = cx - total_w / 2

            for fi, fld in enumerate(fline):
                if fi > 0:
                    self.setFont(fonts["regular"], 6.5)
                    self.setFillColor(HexColor("#999999"))
                    sep = "    |    "
                    self.drawString(cur_x, y_pos, sep)
                    cur_x += self.stringWidth(sep, fonts["regular"], 6.5)

                # Label in accent
                label = fld["label"] + ": "
                self.setFont(fonts["regular"], 6.5)
                self.setFillColor(HexColor(accent))
                self.drawString(cur_x, y_pos, label)
                cur_x += self.stringWidth(label, fonts["regular"], 6.5)

                # Value in primary
                val = fld["value"]
                self.setFillColor(HexColor(primary))
                self.drawString(cur_x, y_pos, val)
                cur_x += self.stringWidth(val, fonts["regular"], 6.5)

        # Page number (language-aware, right-aligned)
        footer_bottom = footer_y - 23 - (len(field_lines) * 11)
        pg = t(lang, "page")
        of = t(lang, "of")

        self.setFont(fonts["regular"], 7)
        self.setFillColor(HexColor("#aaaaaa"))
        # pn / total already exclude the unnumbered front pages
        self.drawRightString(w - 2 * cm, footer_bottom, f"{pg} {pn} {of} {total}")

    @staticmethod
    def _group_fields(fields):
        """Group fields into lines of approx 90 chars max."""
        lines = []
        current = []
        for fld in fields:
            current.append(fld)
            combined = "    |    ".join(f"{f['label']}: {f['value']}" for f in current)
            if len(combined) > 90 or len(current) >= 3:
                lines.append(current)
                current = []
        if current:
            lines.append(current)
        return lines
