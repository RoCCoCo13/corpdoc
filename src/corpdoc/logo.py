"""
Logo resolver and renderer.

CorpDoc accepts the logo in either PNG or SVG (or both). When both are
configured and present, PNG wins because it's faster to embed and pixel-faithful
to whatever the designer exported. When only SVG is available it's rendered
natively via svglib, so there's no need for an external conversion step.
"""

import os

from PIL import Image as PILImage
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


class Logo:
    """
    Resolved logo, ready to be drawn onto a ReportLab canvas.

    Usage:
        logo = Logo(cfg)
        if logo:
            logo.draw(canvas, x, y, width, height)

    Selection rules:
        - PNG present → use PNG (fast path, via canvas.drawImage).
        - PNG missing but SVG present → use SVG (rendered via svglib).
        - Neither present → Logo is falsy; draw() is a no-op.
    """

    __slots__ = ("kind", "path", "width", "height", "_drawing")

    def __init__(self, cfg):
        self.kind = None
        self.path = None
        self.width = None
        self.height = None
        self._drawing = None

        logo_cfg = (cfg or {}).get("logo", {}) or {}
        png = logo_cfg.get("png", "") or ""
        svg = logo_cfg.get("svg", "") or ""

        if png and os.path.exists(png):
            try:
                with PILImage.open(png) as im:
                    self.kind = "png"
                    self.path = png
                    self.width, self.height = im.size
                return
            except Exception:
                pass

        if svg and os.path.exists(svg):
            try:
                drawing = svg2rlg(svg)
            except Exception:
                drawing = None
            if drawing is not None:
                self.kind = "svg"
                self.path = svg
                self.width = drawing.width
                self.height = drawing.height
                self._drawing = drawing

    def __bool__(self):
        return self.kind is not None

    def draw(self, canvas, x, y, width, height):
        """Draw the logo onto a ReportLab canvas at (x, y) scaled to (width, height)."""
        if self.kind == "png":
            canvas.drawImage(
                self.path,
                x,
                y,
                width=width,
                height=height,
                preserveAspectRatio=True,
                mask="auto",
            )
        elif self.kind == "svg":
            sx = width / self.width
            sy = height / self.height
            canvas.saveState()
            canvas.translate(x, y)
            canvas.scale(sx, sy)
            renderPDF.draw(self._drawing, canvas, 0, 0)
            canvas.restoreState()
