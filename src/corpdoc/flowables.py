"""
Custom ReportLab Flowables for CorpDoc.

Provides:
- HRLine: horizontal rule with width percentage
- CoverPageFlowable: full cover page with pluggable styles.

Cover styles
------------
The cover is selected per-document via `cover.style` in corpdoc.yml. The
following styles ship out of the box:

- `classic`   — Logo centered top, accent band on the bottom 40% with the
                title and subtitle in white. (Default.)
- `minimal`   — Logo small, top-left. Title large and centered, with a thin
                accent rule underneath. Everything in primary color on a
                clean white page.
- `bold-band` — Full-page accent background. Logo + title + subtitle stacked
                and centered in white. Maximum brand impact.
- `split`     — Top half filled with primary color (logo in white inside),
                bottom half white with the title in primary. Corporate-modern
                look popular in consulting decks.
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
    Full-page cover. The concrete look is chosen via `style`.

    Draws relative to its containing frame (frame at (2 cm, 3.2 cm) with
    width page_w - 4 cm and height page_h - 5.4 cm), but uses negative
    offsets to paint past the frame edges when a style asks for
    edge-to-edge color (classic, bold-band, split).
    """

    # Canonical list of shipped styles. `CorpDoc.render` validates against this.
    STYLES = ("classic", "minimal", "bold-band", "split")

    def __init__(
        self,
        title,
        subtitle,
        meta,
        lang,
        logo,
        cover_scale,
        colors,
        company,
        defaults,
        style="classic",
        cover_cfg=None,
    ):
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
        self.style = style if style in self.STYLES else "classic"
        self.cover_cfg = cover_cfg or {}

    def wrap(self, aW, aH):
        return (aW, aH)

    def draw(self):
        dispatch = {
            "classic": self._draw_classic,
            "minimal": self._draw_minimal,
            "bold-band": self._draw_bold_band,
            "split": self._draw_split,
        }
        dispatch[self.style]()

    # ─────────────────────────────────────────────────────────────
    # Shared helpers
    # ─────────────────────────────────────────────────────────────

    def _meta_line(self):
        """Return the 'vX.Y  |  YYYY-MM-DD' string, or '' if both missing."""
        ver = self.meta.get("version", self.defaults.get("version", ""))
        fecha = self.meta.get("fecha", self.meta.get("date", str(date.today())))
        parts = []
        if ver:
            parts.append(f"v{ver}")
        if fecha:
            parts.append(str(fecha))
        return "  |  ".join(parts)

    def _draw_logo(self, canv, cx, cy, max_w, tint=None):
        """
        Draw the logo centered on (cx, cy) with max width max_w, preserving
        aspect ratio. `tint` is unused (kept for future white-tint variants).
        Returns (draw_w, draw_h) actually used.
        """
        if not self.logo:
            return (0, 0)
        iw, ih = self.logo.width, self.logo.height
        if iw <= 0 or ih <= 0:
            return (0, 0)
        sc = min(max_w / iw, 1)
        dw, dh = iw * sc, ih * sc
        try:
            self.logo.draw(canv, cx - dw / 2, cy - dh / 2, dw, dh)
        except Exception:
            pass
        return (dw, dh)

    def _wrap_subtitle(self, text, max_chars=60):
        """Split subtitle into 1 or 2 lines by word boundary."""
        if len(text) <= max_chars:
            return [text]
        words, line1, line2 = text.split(), [], []
        for w in words:
            if len(" ".join(line1 + [w])) <= max_chars:
                line1.append(w)
            else:
                line2.append(w)
        return [" ".join(line1), " ".join(line2)] if line2 else [" ".join(line1)]

    # ─────────────────────────────────────────────────────────────
    # Style: classic
    # ─────────────────────────────────────────────────────────────

    def _draw_classic(self):
        canv = self.canv
        page_w, page_h = A4
        accent = HexColor(self.C["accent"])

        frame_x = 2 * cm
        frame_y = 3.2 * cm

        block_h = page_h * 0.40
        block_bottom_y = -frame_y
        block_top_y = block_bottom_y + block_h

        canv.setFillColor(accent)
        canv.rect(-frame_x, block_bottom_y, page_w, block_h, fill=1, stroke=0)

        avail_w = page_w - 4 * cm
        cx = avail_w / 2

        # Logo centered in top portion (above the accent band).
        logo_y = block_top_y + (page_h - block_h) * 0.35 - frame_y
        self._draw_logo(canv, cx, logo_y, 200 * self.cover_scale)

        # Title (white on accent band).
        title_y = block_top_y - 50
        canv.setFont("Helvetica-Bold", 24)
        canv.setFillColor(white)
        canv.drawCentredString(cx, title_y, self.title)

        if self.subtitle:
            canv.setFont("Helvetica", 13)
            canv.setFillColor(white)
            for i, ln in enumerate(self._wrap_subtitle(self.subtitle)):
                canv.drawCentredString(cx, title_y - 28 - i * 16, ln)

        meta = self._meta_line()
        if meta:
            canv.setFont("Helvetica", 8)
            canv.setFillColor(HexColor("#ffffffcc"))
            canv.drawCentredString(cx, block_bottom_y + 30, meta)

    # ─────────────────────────────────────────────────────────────
    # Style: minimal
    # ─────────────────────────────────────────────────────────────

    def _draw_minimal(self):
        canv = self.canv
        page_w, page_h = A4
        primary = HexColor(self.C["primary"])
        accent = HexColor(self.C["accent"])

        frame_y = 3.2 * cm
        avail_w = page_w - 4 * cm

        # Small logo top-left. Translate to frame-relative coordinates:
        # top of page is at frame_inner_top = page_h - 2.2*cm - frame_y.
        logo_top_y = page_h - 2.2 * cm - frame_y - 10
        if self.logo:
            iw, ih = self.logo.width, self.logo.height
            max_w = 100 * self.cover_scale
            sc = min(max_w / iw, 1) if iw > 0 else 1
            dw, dh = iw * sc, ih * sc
            try:
                self.logo.draw(canv, 0, logo_top_y - dh, dw, dh)
            except Exception:
                pass

        # Title: large, centered, vertical ~60% of page.
        cx = avail_w / 2
        title_y = page_h * 0.55 - frame_y
        canv.setFont("Helvetica-Bold", 32)
        canv.setFillColor(primary)
        canv.drawCentredString(cx, title_y, self.title)

        # Accent rule under title.
        rule_y = title_y - 16
        canv.setStrokeColor(accent)
        canv.setLineWidth(1.5)
        canv.line(cx - 60, rule_y, cx + 60, rule_y)

        if self.subtitle:
            canv.setFont("Helvetica", 14)
            canv.setFillColor(HexColor("#555555"))
            for i, ln in enumerate(self._wrap_subtitle(self.subtitle)):
                canv.drawCentredString(cx, rule_y - 26 - i * 18, ln)

        meta = self._meta_line()
        if meta:
            canv.setFont("Helvetica", 9)
            canv.setFillColor(HexColor("#888888"))
            canv.drawCentredString(cx, -frame_y + 30, meta)

    # ─────────────────────────────────────────────────────────────
    # Style: bold-band
    # ─────────────────────────────────────────────────────────────

    def _draw_bold_band(self):
        canv = self.canv
        page_w, page_h = A4
        primary = HexColor(self.C["primary"])

        frame_x = 2 * cm
        frame_y = 3.2 * cm
        avail_w = page_w - 4 * cm
        cx = avail_w / 2

        # Full page primary color.
        canv.setFillColor(primary)
        canv.rect(-frame_x, -frame_y, page_w, page_h, fill=1, stroke=0)

        # Logo centered upper third.
        self._draw_logo(
            canv,
            cx,
            page_h * 0.68 - frame_y,
            220 * self.cover_scale,
        )

        # Title in white, centered.
        title_y = page_h * 0.42 - frame_y
        canv.setFont("Helvetica-Bold", 30)
        canv.setFillColor(white)
        canv.drawCentredString(cx, title_y, self.title)

        if self.subtitle:
            canv.setFont("Helvetica", 14)
            canv.setFillColor(HexColor("#ffffffdd"))
            for i, ln in enumerate(self._wrap_subtitle(self.subtitle)):
                canv.drawCentredString(cx, title_y - 32 - i * 18, ln)

        meta = self._meta_line()
        if meta:
            canv.setFont("Helvetica", 9)
            canv.setFillColor(HexColor("#ffffffaa"))
            canv.drawCentredString(cx, -frame_y + 30, meta)

    # ─────────────────────────────────────────────────────────────
    # Style: split
    # ─────────────────────────────────────────────────────────────

    def _draw_split(self):
        canv = self.canv
        page_w, page_h = A4
        primary = HexColor(self.C["primary"])
        accent = HexColor(self.C["accent"])

        frame_x = 2 * cm
        frame_y = 3.2 * cm
        avail_w = page_w - 4 * cm
        cx = avail_w / 2

        # Top half filled with primary.
        top_h = page_h * 0.55
        canv.setFillColor(primary)
        canv.rect(-frame_x, page_h - top_h - frame_y, page_w, top_h, fill=1, stroke=0)

        # Thin accent rule at the split line.
        split_y = page_h - top_h - frame_y
        canv.setStrokeColor(accent)
        canv.setLineWidth(3)
        canv.line(-frame_x, split_y, page_w - frame_x, split_y)

        # Logo centered in upper (primary) half.
        self._draw_logo(canv, cx, page_h - top_h * 0.5 - frame_y, 200 * self.cover_scale)

        # Title in primary, centered in lower (white) half.
        title_y = split_y - 60
        canv.setFont("Helvetica-Bold", 26)
        canv.setFillColor(primary)
        canv.drawCentredString(cx, title_y, self.title)

        if self.subtitle:
            canv.setFont("Helvetica", 13)
            canv.setFillColor(HexColor("#444444"))
            for i, ln in enumerate(self._wrap_subtitle(self.subtitle)):
                canv.drawCentredString(cx, title_y - 26 - i * 16, ln)

        meta = self._meta_line()
        if meta:
            canv.setFont("Helvetica", 9)
            canv.setFillColor(HexColor("#888888"))
            canv.drawCentredString(cx, -frame_y + 30, meta)
