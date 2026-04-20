# Changelog

All notable changes to CorpDoc will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Native SVG rendering in PDFs via `svglib`. Logos can now be supplied as
  SVG, PNG, or both — CorpDoc picks the best available source.
- `corpdoc.i18n` module centralizing all localized strings.
- Logo resolver (`corpdoc.logo.Logo`) with a unified `draw()` API.
- Tests for the logo resolver and for the new frontmatter parser.

### Changed
- **Colors:** the CorpDoc brand palette moved from teal/coral to
  forest/camel (`#1F4129` + `#C8A36A`).
- **Frontmatter:** replaced the hand-rolled parser with `yaml.safe_load`.
  Values with colons, dates, and quoted strings now round-trip correctly.
- **Color role assignment:** `accent` now falls back to `secondary` only
  when the palette has fewer than three usable colors; previously they were
  always identical.
- **Config override:** the optional `colors:` block in `corpdoc.yml` now
  correctly overrides auto-extracted colors on a per-key basis (previously
  only applied when no SVG was present).
- CLI writes UTF-8 to stdout/stderr so unicode glyphs render on Windows.

### Removed
- Stray `=3.0` file at repo root (shell accident).
- Legacy `papyros-logo.svg` asset.

## [0.3.0] — 2026-04-19

### Added
- Full Python package structure (`src/corpdoc/`)
- CLI with commands: `init`, `render`, `colors`, `new`
- Cover page with accent color block and logo
- Separate version history page
- Automatic table of contents from headings
- Corporate header with logo and tagline
- Corporate footer with company info and page numbers
- Brand-split coloring for headers and footers
- Language detection (en, es, de, fr)
- Nested list support (2-space indentation)
- Auto-styled tables with zebra striping
- Mermaid diagram placeholder rendering
- `SKILL.md` for any LLM integration
- Example project (corpdoc-sample)

### Technical
- SVG color extraction with XML parsing
- Automatic role assignment (primary, secondary, accent)
- Configurable via YAML (`corpdoc.yml`)
- Zero-network runtime (fully offline)

## [0.2.0] — Internal prototype

Early version with hardcoded company info, monolithic script.

## [0.1.0] — Proof of concept

Initial implementation with basic Markdown → PDF conversion.
