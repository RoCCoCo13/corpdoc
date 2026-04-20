"""
Command-line interface for CorpDoc.

Commands:
    corpdoc init       Create a new corpdoc.yml from a logo
    corpdoc render     Generate PDF from markdown + config
    corpdoc colors     Print the palette extracted from a logo
    corpdoc new        Scaffold a new markdown document
"""

import argparse
import os
import sys
from pathlib import Path

from corpdoc import __version__
from corpdoc.api import CorpDoc
from corpdoc.colors import extract_colors_from_svg, assign_roles


# Reconfigure stdout/stderr to UTF-8 so unicode glyphs render on Windows consoles
# that default to cp1252. Python 3.7+ exposes reconfigure(); guard for safety.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def cmd_init(args):
    """Create a new corpdoc.yml from a logo."""
    if not os.path.exists(args.logo):
        sys.exit(f"Error: logo file not found: {args.logo}")

    logo_path = Path(args.logo)
    suffix = logo_path.suffix.lower()

    # Extract colors for preview (SVG only — PNG palette extraction is out of scope)
    if suffix == ".svg":
        colors = extract_colors_from_svg(args.logo)
        palette = assign_roles(colors)
        print(f"Colors extracted from {args.logo}:")
        print(f"  Primary:   {palette['primary']}")
        print(f"  Secondary: {palette['secondary']}")
        print(f"  Accent:    {palette['accent']}")

    # Build logo section of the config depending on what the user supplied.
    # CorpDoc accepts SVG only, PNG only, or both — whichever is available
    # will be used at render time (PNG wins when both are present).
    if suffix == ".svg":
        sibling_png = logo_path.with_suffix(".png")
        png_value = str(sibling_png) if sibling_png.exists() else ""
        svg_value = args.logo
    elif suffix == ".png":
        sibling_svg = logo_path.with_suffix(".svg")
        svg_value = str(sibling_svg) if sibling_svg.exists() else ""
        png_value = args.logo
    else:
        sys.exit(f'Error: logo must be .svg or .png (got "{suffix}")')

    # Build a sensible default tagline using the short name
    short = args.name.split()[0] if args.name else "your-company"
    default_tagline = args.tagline or f"{short.lower()} | engineering | solutions"

    config = f"""# CorpDoc Configuration
# Edit the values below to match your company identity.

company:
  legal_name: "{args.name}"
  short_name: "{short}"
  tagline: "{default_tagline}"
  # Number of leading chars of each word colored in accent (brand-split effect)
  brand_split: 3

logo:
  # CorpDoc accepts SVG, PNG, or both. SVG enables automatic color extraction;
  # PNG is used for embedding when present. Leave a field empty to skip it.
  svg: "{svg_value}"
  png: "{png_value}"
  cover_scale: 1.00          # size of logo on cover page (1.0 = default)
  header_scale: 0.45         # size of logo in header (fraction of cover size)

cover:
  # Choose one of: classic | minimal | bold-band | split
  #   classic   — logo top, accent band bottom with title in white
  #   minimal   — small top-left logo, large centered title on white
  #   bold-band — full-page primary color, white logo + title stacked center
  #   split     — top half primary with logo, bottom half white with title
  style: "classic"

footer:
  address: ""
  fields:
    - label: "Director"
      value: ""
    - label: "E-Mail"
      value: ""
    - label: "Internet"
      value: ""

defaults:
  language: "auto"           # auto|en|es|de|fr
  version: "1.0"
  author: ""

tables:
  # Tables with this many columns (or more) are auto-rotated to a landscape
  # page so the content stays readable. Raise this value to disable.
  landscape_threshold: 8
"""

    out_path = Path(args.output)
    out_path.write_text(config, encoding="utf-8")
    print(f"\n✓ Configuration written to: {out_path}")

    print("\nNext steps:")
    print(f"  1. Edit {out_path} to fill in your company details")
    print(f"  2. Run: corpdoc render your-document.md --config {out_path}")


def cmd_render(args):
    """Generate PDF from markdown."""
    if not os.path.exists(args.md):
        sys.exit(f"Error: markdown file not found: {args.md}")
    if not os.path.exists(args.config):
        sys.exit(f"Error: config file not found: {args.config}")

    print(f"Rendering {args.md}...")
    doc = CorpDoc(config=args.config)
    print(f"  Primary:   {doc.colors['primary']}")
    print(f"  Secondary: {doc.colors['secondary']}")

    output = args.output or Path(args.md).with_suffix(".pdf")
    result = doc.render(args.md, output=str(output))
    print(f"\n✓ PDF generated: {result}")


def cmd_colors(args):
    """Print the palette extracted from a logo."""
    if not os.path.exists(args.logo):
        sys.exit(f"Error: logo file not found: {args.logo}")

    raw = extract_colors_from_svg(args.logo)
    palette = assign_roles(raw)

    print(f"\nColors extracted from: {args.logo}")
    print("─" * 60)
    print(f"Raw colors found: {raw}")
    print("─" * 60)
    print("Role assignments:")
    for role in ["primary", "secondary", "accent", "light", "lighter"]:
        color = palette[role]
        # ANSI color block
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        block = f"\033[48;2;{r};{g};{b}m      \033[0m"
        print(f"  {block}  {color}   ({role})")


def cmd_new(args):
    """Scaffold a new markdown document."""
    templates = {
        "generic": """# {title}
## {subtitle}

Write your content here.

## Section 1

Your content.

## Section 2

More content.
""",
        "offer": """# {title}
## {subtitle}

Brief executive summary of the offer.

## 1. Scope

Describe the scope of work.

## 2. Approach

Describe the proposed approach.

## 3. Deliverables

| Item | Description | Quantity |
|------|-------------|----------|
| A    | ...         | 1        |

## 4. Timeline

Describe the timeline.

## 5. Budget

Describe the budget and payment terms.
""",
        "report": """# {title}
## {subtitle}

## 1. Executive Summary

Brief summary of findings.

## 2. Methodology

Describe the approach.

## 3. Results

Present the data.

## 4. Conclusions

Summarize conclusions.

## 5. Recommendations

List recommendations.
""",
    }

    template = templates.get(args.type, templates["generic"])
    content = template.format(
        title=args.title or "Document Title",
        subtitle=args.subtitle or "Subtitle or client name",
    )

    out_path = Path(args.output)
    out_path.write_text(content, encoding="utf-8")
    print(f"✓ New {args.type} document created: {out_path}")
    print(f"  Edit the file and run: corpdoc render {out_path} --config corpdoc.yml")


def main():
    parser = argparse.ArgumentParser(
        prog="corpdoc", description="CorpDoc — Professional Corporate PDF Generator"
    )
    parser.add_argument("-V", "--version", action="version", version=f"corpdoc {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Create a new corpdoc.yml from a logo")
    p_init.add_argument(
        "--logo",
        required=True,
        help="Path to your logo (.svg or .png — SVG preferred for color extraction)",
    )
    p_init.add_argument("--name", required=True, help="Company legal name")
    p_init.add_argument("--tagline", default="", help="Header tagline (optional)")
    p_init.add_argument("--output", default="corpdoc.yml", help="Output config path")
    p_init.set_defaults(func=cmd_init)

    # render
    p_render = sub.add_parser("render", help="Generate PDF from markdown + config")
    p_render.add_argument("md", help="Markdown file")
    p_render.add_argument("--config", default="corpdoc.yml", help="Config YAML path")
    p_render.add_argument("--output", default="", help="Output PDF path")
    p_render.set_defaults(func=cmd_render)

    # colors
    p_colors = sub.add_parser("colors", help="Show palette extracted from a logo")
    p_colors.add_argument("logo", help="SVG logo file")
    p_colors.set_defaults(func=cmd_colors)

    # new
    p_new = sub.add_parser("new", help="Create a new document skeleton")
    p_new.add_argument("type", choices=["generic", "offer", "report"], help="Document type")
    p_new.add_argument("--title", default="", help="Document title")
    p_new.add_argument("--subtitle", default="", help="Document subtitle")
    p_new.add_argument("--output", default="document.md", help="Output .md path")
    p_new.set_defaults(func=cmd_new)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
