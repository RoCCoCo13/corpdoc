"""
Custom ReportLab Flowables for CorpDoc.

Provides:
- HRLine: horizontal rule with width percentage
- CoverPageFlowable: full cover with accent-filled bottom band
"""

from datetime import date

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Flowable


class HRLine(Flowable):
    """Horizontal rule with width as a percentage of available width."""

    def __init__(
        self, width_pct=100, thickness=1, color=HexColor("#333333"), space_before=0, space_after=0
    ):
        Flowable.__init__(self)
        self.wpct = width_pct / 100
        self.thickness = thickness
        self.color = color
        self.spaceBefore = space_before
        self.spaceAfter = space_after

    def wrap(self, aW, aH):
        self._w = aW * self.wpct
        return (self._w, self.thickness + self.spaceBefore + self.spaceAfter)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        y = self.spaceAfter + self.thickness / 2
        self.canv.line(0, y, self._w, y)


class CoverPageFlowable(Flowable):
    """
    Full-page cover:
    - Top 60%: white background with logo centered
    - Bottom 40%: accent color block with title and subtitle in white
    """

    def __init__(self, title, subtitle, meta, lang, logo, cover_scale, colors, company, defaults):
        Flowable.__init__(self)
        self.title = title
        self.subtitle = subtitle
        self.meta = meta
        self.lang = lang
        self.logo = logo
        self.cover_scale = cover_scale
        self.C = colors
        self.company = company
        self.defaults = defaults

    def wrap(self, aW, aH):
        return (aW, aH)

    def draw(self):
        canv = self.canv
        page_w, page_h = A4
        accent = HexColor(self.C["accent"])

        # Frame offsets (the flowable draws relative to its frame)
        frame_x = 2 * cm
        frame_y = 3.2 * cm

        # Bottom 40% accent block
        block_h = page_h * 0.40
        block_bottom_y = -frame_y
        block_top_y = block_bottom_y + block_h

        # Draw full-width accent block
        canv.setFillColor(accent)
        canv.rect(-frame_x, block_bottom_y, page_w, block_h, fill=1, stroke=0)

        # Logo centered in top half
        avail_w = page_w - 4 * cm
        if self.logo:
            iw, ih = self.logo.width, self.logo.height
            max_w = 200 * self.cover_scale
            sc = min(max_w / iw, 1)
            draw_w = iw * sc
            draw_h = ih * sc

            logo_x = (avail_w - draw_w) / 2
            logo_y = block_top_y - frame_y + (page_h - block_h) * 0.35
            try:
                self.logo.draw(canv, logo_x, logo_y, draw_w, draw_h)
            except Exception:
                pass

        # Title (white, centered, on accent block)
        cx = avail_w / 2
        title_y = block_top_y - 50

        canv.setFont("Helvetica-Bold", 24)
        canv.setFillColor(white)
        canv.drawCentredString(cx, title_y, self.title)

        # Subtitle (wraps if too long)
        if self.subtitle:
            canv.setFont("Helvetica", 13)
            canv.setFillColor(HexColor("#ffffff"))

            max_chars = 60
            if len(self.subtitle) > max_chars:
                words = self.subtitle.split()
                line1, line2 = [], []
                for w in words:
                    if len(" ".join(line1 + [w])) <= max_chars:
                        line1.append(w)
                    else:
                        line2.append(w)
                canv.drawCentredString(cx, title_y - 28, " ".join(line1))
                if line2:
                    canv.drawCentredString(cx, title_y - 44, " ".join(line2))
            else:
                canv.drawCentredString(cx, title_y - 28, self.subtitle)

        # Meta (version + date) near the bottom
        meta_y = block_bottom_y + 30
        canv.setFont("Helvetica", 8)
        canv.setFillColor(HexColor("#ffffffcc"))

        ver = self.meta.get("version", self.defaults.get("version", ""))
        fecha = self.meta.get("fecha", self.meta.get("date", str(date.today())))
        parts = []
        if ver:
            parts.append(f"v{ver}")
        if fecha:
            parts.append(str(fecha))
        if parts:
            canv.drawCentredString(cx, meta_y, "  |  ".join(parts))
