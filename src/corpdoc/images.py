"""
Block images for the document body.

A Markdown paragraph that contains only an image is drawn as a figure:
scaled down to the frame width (never upscaled), aspect ratio preserved,
capped to the usable page height, with the alt text as a centred caption.

Only local files are read. Remote URLs are never fetched.
"""

import os
import re

from PIL import Image as PILImage
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, Spacer
from svglib.svglib import svg2rlg

from corpdoc._util import warn, xml_escape

_REMOTE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://|^data:", re.IGNORECASE)

# Vertical space kept free around a figure, on top of the caption height.
_SPACE_BEFORE = 2 * mm
_CAPTION_GAP = 1.5 * mm
_SPACE_AFTER = 3 * mm


def fit_size(width, height, max_width, max_height):
    """
    Scale (width, height) down to fit inside (max_width, max_height),
    keeping the aspect ratio. Never scales up.
    """
    factor = min(1.0, max_width / width, max_height / height)
    return (width * factor, height * factor)


def resolve_path(src, base_dir):
    """Resolve an image `src` against `base_dir` (absolute paths are kept)."""
    if os.path.isabs(src):
        return src
    return os.path.normpath(os.path.join(base_dir or os.getcwd(), src))


def _placeholder(reason, src, alt, styles):
    label = f"[ {reason}: {src} ]"
    if alt:
        label += f" {alt}"
    return [Paragraph(xml_escape(label), styles["CPlaceholder"])]


def _load_svg(path, max_w, max_h, scale):
    drawing = svg2rlg(path)
    if drawing is None or drawing.width <= 0 or drawing.height <= 0:
        raise ValueError("not a valid SVG")
    w, h = fit_size(drawing.width * scale, drawing.height * scale, max_w, max_h)
    factor = w / drawing.width
    if factor != 1:
        drawing.scale(factor, factor)
        drawing.width, drawing.height = w, h
    drawing.hAlign = "CENTER"
    return drawing


def _load_raster(path, max_w, max_h, scale):
    # One pixel is treated as one point (ReportLab's convention).
    with PILImage.open(path) as im:
        im.verify()
        px_w, px_h = im.size
    if px_w <= 0 or px_h <= 0:
        raise ValueError("image has no size")
    w, h = fit_size(px_w * scale, px_h * scale, max_w, max_h)
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    return img


def build_image_flowables(src, alt, base_dir, max_width, max_height, styles, scale=1.0):
    """
    Build the flowables for one block image.

    Args:
        src: Path from the Markdown source (relative to `base_dir`, or absolute).
        alt: Alt text, rendered as a centred caption when not empty.
        base_dir: Directory relative paths are resolved against.
        max_width: Frame width available to the image, in points.
        max_height: Usable page height for image + caption, in points.
        styles: CorpDoc style sheet (needs `CCaption` and `CPlaceholder`).
        scale: Factor applied to the natural size before fitting (e.g. 0.5
            for a bitmap rendered at 2x).

    Returns:
        A list of flowables. On a missing or unreadable file a warning is
        printed to stderr and a visible placeholder paragraph is returned.
    """
    if _REMOTE_RE.match(src):
        warn(f"remote images are not supported (nothing is downloaded): {src}")
        return _placeholder("Remote image not embedded", src, alt, styles)

    path = resolve_path(src, base_dir)
    if not os.path.isfile(path):
        warn(f"image not found: {src} (looked in {path})")
        return _placeholder("Image not found", src, alt, styles)

    caption = Paragraph(xml_escape(alt), styles["CCaption"]) if alt else None
    reserved = _SPACE_BEFORE + _SPACE_AFTER
    if caption is not None:
        reserved += caption.wrap(max_width, max_height)[1] + _CAPTION_GAP
    image_max_h = max(max_height - reserved, max_height / 4)

    loader = _load_svg if path.lower().endswith(".svg") else _load_raster
    try:
        figure = loader(path, max_width, image_max_h, scale)
    except Exception as exc:  # noqa: BLE001 - PIL / svglib / lxml raise many unrelated types
        warn(f"image could not be read: {src} ({exc.__class__.__name__}: {exc})")
        return _placeholder("Image could not be read", src, alt, styles)

    parts = [Spacer(1, _SPACE_BEFORE), figure]
    if caption is not None:
        parts += [Spacer(1, _CAPTION_GAP), caption]
    return [KeepTogether(parts), Spacer(1, _SPACE_AFTER)]
