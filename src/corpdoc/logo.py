"""
Logo resolver and renderer.

CorpDoc accepts the logo in either PNG or SVG (or both). When both are
configured and present, PNG wins because it's faster to embed and pixel-faithful
to whatever the designer exported. When only SVG is available it's rendered
natively via svglib, so there's no need for an external conversion step.
"""

import os

from PIL import Image as PILImage
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from corpdoc._util import warn


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

    __slots__ = ("_drawing", "_warned", "height", "kind", "path", "width")

    def __init__(self, cfg):
        self.kind = None
        self.path = None
        self.width = None
        self.height = None
        self._drawing = None
        self._warned = False

        logo_cfg = (cfg or {}).get("logo", {}) or {}
        png = logo_cfg.get("png", "") or ""
        svg = logo_cfg.get("svg", "") or ""

        if png and os.path.exists(png):
            try:
                with PILImage.open(png) as im:
                    size = im.size
            except Exception as exc:  # noqa: BLE001 - PIL raises many unrelated types
                warn(f"logo could not be read: {png} ({exc.__class__.__name__}: {exc})")
            else:
                self.kind = "png"
                self.path = png
                self.width, self.height = size
                return

        if svg and os.path.exists(svg):
            try:
                drawing = svg2rlg(svg)
            except Exception as exc:  # noqa: BLE001 - svglib / lxml raise many unrelated types
                warn(f"logo could not be read: {svg} ({exc.__class__.__name__}: {exc})")
                return
            if drawing is None or drawing.width <= 0 or drawing.height <= 0:
                warn(f"logo could not be read: {svg} (not a valid SVG)")
                return
            self.kind = "svg"
            self.path = svg
            self.width = drawing.width
            self.height = drawing.height
            self._drawing = drawing

    def __bool__(self):
        return self.kind is not None

    def draw(self, canvas, x, y, width, height):
        """
        Draw the logo onto a ReportLab canvas at (x, y) scaled to (width, height).

        A logo that cannot be drawn never fails the render: the problem is
        reported once on stderr and the logo is left out.
        """
        try:
            self._draw(canvas, x, y, width, height)
        except Exception as exc:  # noqa: BLE001 - a broken logo must not break the document
            if not self._warned:
                self._warned = True
                warn(f"logo could not be drawn: {self.path} ({exc.__class__.__name__}: {exc})")

    def _draw(self, canvas, x, y, width, height):
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
            try:
                canvas.translate(x, y)
                canvas.scale(sx, sy)
                renderPDF.draw(self._drawing, canvas, 0, 0)
            finally:
                canvas.restoreState()
