"""
CorpDoc — Professional Corporate PDF Generator from Markdown + Logo.

Turn a Markdown file and a corporate logo into a branded PDF with cover page,
version history, table of contents, headers, footers, and auto-styled tables.

Basic usage:
    from corpdoc import CorpDoc

    doc = CorpDoc(config='corpdoc.yml')
    doc.render('report.md', output='report.pdf')
"""

__version__ = "0.3.0"

from corpdoc.api import CorpDoc
from corpdoc.colors import extract_colors_from_svg, assign_roles

__all__ = ["CorpDoc", "extract_colors_from_svg", "assign_roles", "__version__"]
