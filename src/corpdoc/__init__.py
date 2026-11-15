"""
CorpDoc — Professional Corporate PDF Generator from Markdown + Logo.

Turn a Markdown file and a corporate logo into a branded PDF with cover page,
version history, table of contents, headers, footers, auto-styled tables,
images and numbered lists.

Basic usage:
    from corpdoc import CorpDoc

    doc = CorpDoc(config='corpdoc.yml')
    doc.render('report.md', output='report.pdf')
"""

__version__ = "0.5.0"

from corpdoc.api import CorpDoc, RenderResult
from corpdoc.colors import extract_colors_from_svg, assign_roles

__all__ = ["CorpDoc", "RenderResult", "extract_colors_from_svg", "assign_roles", "__version__"]
