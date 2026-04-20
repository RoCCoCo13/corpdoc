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

# Optional: override auto-extracted colors
colors:
  primary: "#003d5c"
  accent: "#ff6b35"
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

### `colors` (optional override)

If the automatic color extraction doesn't pick the right colors, override
them explicitly:

```yaml
colors:
  primary: "#003d5c"
  secondary: "#00a8e8"
  accent: "#ff6b35"
```

Any keys you set here override the automatic extraction. Keys you don't
specify remain auto-derived from the SVG.

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
---
```

None of these are strictly required. If `title` is missing, CorpDoc uses the
first `# H1` heading. If `subtitle` is missing and an `## H2` follows the
H1 directly, that becomes the subtitle.
