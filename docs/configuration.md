# Configuration Reference

CorpDoc reads all branding from a single YAML file, conventionally named
`corpdoc.yml`. This file defines your company identity once — every document
you render afterwards uses it.

## Full example

```yaml
company:
  legal_name: "Acme Engineering SL"
  short_name: "Acme"
  tagline: "acme | engineering | solutions"
  tagline_prefix: "aes."
  brand_split: 3

logo:
  svg: "logo.svg"
  png: "logo.png"
  cover_scale: 1.00
  header_scale: 0.45

cover:
  style: "classic"   # classic | minimal | bold-band | split

footer:
  address: "Calle Principal 42, 28001 Madrid"
  fields:
    - label: "Director"
      value: "Jane Doe"
    - label: "VAT"
      value: "ESB12345678"
    - label: "E-Mail"
      value: "info@acme.com"
    - label: "Web"
      value: "www.acme.com"

defaults:
  language: "auto"
  version: "1.0"
  author: "Jane Doe"
  max_pages: 20      # optional: warn when the body is longer

sections:            # optional: front pages, all default to true
  cover: true
  version_history: true
  toc: true

fonts:               # optional
  family: "helvetica"   # helvetica | dejavu | mapping of TTF paths

tables:
  landscape_threshold: 8

mermaid:             # optional
  timeout: 30

# Optional: override auto-extracted colors
colors:
  primary: "#003d5c"
  accent: "#ff6b35"
  highlight: "#334155"
```

## Section reference

### `company`

Identity information used in the header, footer, and occasionally the cover.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `legal_name` | str | ✓ | Full legal name shown in the footer and brand-split styled |
| `short_name` | str | | Informal name (used for the PDF metadata) |
| `tagline` | str | | Shown in the header. Words get brand-split coloring |
| `tagline_prefix` | str | | Short italic prefix (e.g. "acme.") shown before the tagline |
| `brand_split` | int | | Chars of each word colored in accent. Default: 3 |

### `logo`

Paths to your logo files and their relative sizes. You may supply an SVG,
a PNG, or both — CorpDoc uses whichever is available.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `svg` | path | one of svg/png | SVG file. Enables automatic color extraction and renders natively via svglib |
| `png` | path | one of svg/png | PNG file. Used for embedding when present (preferred over SVG at render time for speed) |
| `cover_scale` | float | | Size of cover logo. 1.0 = default. Default: 1.0 |
| `header_scale` | float | | Header logo size relative to cover. Default: 0.45 |

**Resolution rules at render time:**

- Both SVG and PNG present → PNG wins (fastest, pixel-faithful).
- Only SVG present → SVG is rendered directly via svglib.
- Only PNG present → works, but you'll need to set colors manually (see below)
  since palette auto-extraction requires the SVG source.

**Paths are relative to the location of the YAML file**, not the Markdown
input. Use absolute paths if you prefer.

**SVG caveat:** svglib does not currently support SVG gradients or filters.
If your logo relies on either, export it to PNG or flatten those elements.

### `footer`

Controls the footer content on every page (except cover and version history).

| Key | Type | Description |
|-----|------|-------------|
| `address` | str | Shown on the first footer line, next to the company name |
| `fields` | list of `{label, value}` | Shown on subsequent lines with accent/primary split |

**Field styling:** The `label` is colored in your accent color, the `value`
in your primary color. This matches the style used in many corporate
letterhead designs.

### `defaults`

Document-level defaults. These can be overridden per-document in the
Markdown frontmatter.

| Key | Type | Description |
|-----|------|-------------|
| `language` | `"auto"` \| `"en"` \| `"es"` \| `"de"` \| `"fr"` | Controls footer labels and version-history headers |
| `version` | str | Default version if the document frontmatter doesn't specify one |
| `author` | str | Default author name |
| `max_pages` | int | Optional page limit for the document body. Not set by default (no limit). See [Page count and page limit](#page-count-and-page-limit). |

### `sections` (optional)

Chooses which front pages are generated before the body.

| Key | Type | Description |
|-----|------|-------------|
| `cover` | bool | Cover page. Default: `true`. |
| `version_history` | bool | Version history page. Default: `true`. |
| `toc` | bool | Table of contents. Default: `true`. |

A document can override any of the three in its frontmatter (see
[Document-level frontmatter](#document-level-frontmatter)); the frontmatter
wins over the config. Leaving the block out keeps all three pages, exactly
as in earlier versions.

Header, footer and page numbers follow what is present: the cover and the
version history carry no header or footer and are not numbered, so "Page 1"
is the first page after them.

### `fonts` (optional)

| Key | Type | Description |
|-----|------|-------------|
| `family` | `"helvetica"` \| `"dejavu"` \| mapping | Font family for the whole document. Default: `"helvetica"`. |

- **`helvetica`** (default) — the PDF built-in fonts Helvetica and Courier.
  Nothing is embedded, files stay small. They cover Western European text;
  Greek letters and common maths operators (Σ, ≤, ≥, →, ±) also work because
  the built-in Symbol font is used for them. Characters outside these fonts —
  subscripts such as ₂, most superscripts, Cyrillic, CJK — are drawn as a
  filled box (■). CorpDoc prints one warning per render listing the affected
  characters.
- **`dejavu`** — DejaVu Sans (regular, bold, oblique, bold-oblique) and
  DejaVu Sans Mono. The fonts ship inside the package, so nothing has to be
  installed, and only the glyphs a document uses are embedded in the PDF.
  They cover Greek, Cyrillic, maths operators, arrows, superscripts and
  subscripts, and are applied everywhere: body, headings, tables, table of
  contents, code, cover, header and footer. Text is slightly wider than in
  Helvetica, so page breaks can move.
- **Custom TTF files** — give `family` a mapping of paths:

  ```yaml
  fonts:
    family:
      regular: "fonts/Inter-Regular.ttf"       # required
      bold: "fonts/Inter-Bold.ttf"             # optional
      italic: "fonts/Inter-Italic.ttf"         # optional
      bold_italic: "fonts/Inter-BoldItalic.ttf" # optional
      mono: "fonts/JetBrainsMono-Regular.ttf"  # optional
  ```

  A missing `bold`, `italic` or `bold_italic` falls back to `regular`; a
  missing `mono` falls back to the bundled DejaVu Sans Mono. Only TrueType
  (`.ttf`) files are supported. Make sure the font's licence allows
  embedding.

An unknown family name or an unreadable font file prints a warning and falls
back to `helvetica`; the render does not fail.

The DejaVu fonts are redistributed unmodified under their own licence
(Bitstream Vera / Arev), included in the package as
`corpdoc/fonts/LICENSE-DejaVu.txt`.

### `cover` (optional)

Selects the look of the first page.

| Key | Type | Description |
|-----|------|-------------|
| `style` | `"classic"` \| `"minimal"` \| `"bold-band"` \| `"split"` | Cover layout. Default: `"classic"`. |

Style reference:

- **`classic`** — logo centered in the top half, accent-colored band filling
  the bottom 40% of the page, with the title and subtitle printed in white
  on top of it. The default, and what every existing CorpDoc PDF uses.
- **`minimal`** — small logo anchored top-left, title large and centered
  around the 55% vertical line with a thin accent rule below it. Everything
  on a clean white page in the primary color. Best for internal memos and
  short documents.
- **`bold-band`** — the whole page is painted in the primary brand color;
  logo, title and subtitle are stacked and centered in white. Maximum brand
  impact. Good for sales decks and proposals.
- **`split`** — top 55% of the page filled with primary color (logo
  centered inside, in whatever color the logo already has), thin accent
  rule at the split line, bottom 45% white with the title in primary.
  A clean corporate-modern layout.

Unknown style names fall back to `classic` and emit a warning on stderr.

### `tables` (optional)

Controls automatic handling of wide tables.

| Key | Type | Description |
|-----|------|-------------|
| `landscape_threshold` | int | Tables with this many columns or more are rendered on an automatically rotated landscape A4 page. Default: `8`. Set very high to disable. |

When a table triggers the threshold, CorpDoc inserts a page break, switches the
page template to landscape for that one page, renders the table at full
landscape width, then switches back. Header/footer on the landscape page
adapt automatically.

### `mermaid` (optional)

Mermaid code blocks are rendered to an image when the Mermaid CLI is
installed and its `mmdc` executable is on `PATH`
(`npm install -g @mermaid-js/mermaid-cli`). Rendering happens entirely on
your machine, in a temporary directory that is removed afterwards. CorpDoc
never sends diagram content to an external service.

If `mmdc` is not found, fails, or takes too long, the diagram source is
printed as a styled text block (the behaviour of earlier versions) and a
warning is shown.

| Key | Type | Description |
|-----|------|-------------|
| `enabled` | bool | Set to `false` to always print the source as text, without looking for `mmdc` and without a warning. Default: `true`. |
| `timeout` | number | Seconds allowed per diagram before `mmdc` is stopped. Default: `30`. |
| `puppeteer_config` | path | Passed to `mmdc -p`. Needed in some containers and CI runners, where the headless browser must be started with `--no-sandbox`. |

### `colors` (optional override)

If the automatic color extraction doesn't pick the right colors, override
them explicitly:

```yaml
colors:
  primary: "#003d5c"
  secondary: "#00a8e8"
  accent: "#ff6b35"
  highlight: "#334155"
```

Any keys you set here override the automatic extraction. Keys you don't
specify remain auto-derived from the SVG.

**Role reference** — what each color actually paints in the output:

| Role | Used for |
|------|----------|
| `primary` | Body text, H1/H2 headings, footer company name, TOC level-1 entries, table header background |
| `secondary` | Table outer borders, divider rules, brand-split secondary tone |
| `accent` | Cover accent band, H1 underline rule, footer labels, zebra striping on tables |
| `highlight` | 4th tone — H3 headings, thin rule on the `split` cover style. Gives documents more visual rhythm when the logo provides a 4th color. |

## Document-level frontmatter

Each Markdown file can have its own frontmatter that overrides defaults:

```yaml
---
title: "Document Title"
subtitle: "Subtitle shown under title"
reference: "DOC-2026-001"
version: "1.2"
date: 2026-04-19
author: "Author Name"
status: "Final"
confidentiality: "Internal"
max_pages: 12            # overrides defaults.max_pages
sections:                # overrides the config's sections block
  cover: true
  version_history: false
  toc: false
---
```

None of these are strictly required. If `title` is missing, CorpDoc uses the
first `# H1` heading. If `subtitle` is missing and an `## H2` follows the
H1 directly, that becomes the subtitle.

Under `sections`, list only the keys you want to change. The three keys are
also accepted at the top level of the frontmatter (`toc: false`).

## Page count and page limit

After every render, the CLI prints the size of the document:

```
✓ PDF generated: report.pdf
  Pages: 14 total, 11 body
```

*Body* pages are the pages after the cover, version history and table of
contents.

`max_pages` (in `defaults`, or in the frontmatter of one document) sets a
limit for the body. When the body is longer, CorpDoc still writes the PDF and
prints a warning. To fail instead — for example in CI — add `--strict`:

```bash
corpdoc render report.md --config corpdoc.yml --strict
```

With `--strict`, a body over the limit ends the command with exit code 1.

From Python, the counts are on the value returned by `render()`. It is still
the output path (a `str`), with extra attributes:

```python
result = CorpDoc(config="corpdoc.yml").render("report.md", output="report.pdf")
print(result)               # report.pdf
print(result.total_pages)   # 14
print(result.body_pages)    # 11
print(result.max_pages)     # 12, or None when no limit is set
print(result.over_limit)    # False
```

## Images

A Markdown paragraph that contains only an image is drawn as a figure:

```markdown
![Figure 1: Monthly output, 2025](img/output-2025.png)
```

- PNG, JPG and SVG are supported.
- The image is scaled down to the text width when it is wider, never
  enlarged, and always keeps its proportions. Very tall images are reduced
  to fit on one page. One pixel counts as one point (1/72 inch), so an image
  about 1300 px wide fills the text width at roughly 200 dpi.
- The alt text is printed as a centred caption below the image. Leave it
  empty for no caption.
- Relative paths are resolved against the folder of the Markdown file. When
  `render()` is given Markdown text instead of a file, pass
  `base_dir="path/to/folder"`; the default is the current directory.
- A missing or unreadable file does not stop the render: a warning is
  printed and a visible placeholder box appears where the image would be.
- Remote images (`https://...`) are never downloaded; they get the same
  placeholder.
- An image inside a line of text is not drawn; its alt text is printed
  instead.
- SVG files are drawn as vectors through svglib, with the same limits as SVG
  logos (no gradients or filters).

## Lists and links

- Ordered lists (`1.`, `2.`, …) are numbered, honour their start number and
  restart in every nested list. Bullet lists are unchanged.
- Lists keep three levels of nesting; deeper levels are drawn like the third.
- Links to `http(s)://`, `ftp://`, `mailto:` and `tel:` targets are clickable
  in the PDF. They keep the look of the surrounding text. Links to anchors
  (`#section`) and relative files are printed as plain text.
