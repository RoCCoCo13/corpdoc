# Changelog

All notable changes to CorpDoc will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.4.1] — 2026-04-25

### Fixed
- README image references switched from repo-relative paths to absolute
  `raw.githubusercontent.com` URLs so the logo and the cover preview render
  correctly on the PyPI project page (PyPI serves the README from its own
  domain and cannot resolve `assets/...` paths against the GitHub repo).

## [0.4.0] — 2026-04-25

First public release on PyPI.

### Added
- Native SVG rendering in PDFs via `svglib`. Logos can now be supplied as
  SVG, PNG, or both — CorpDoc picks the best available source.
- `corpdoc.i18n` module centralizing all localized strings.
- Logo resolver (`corpdoc.logo.Logo`) with a unified `draw()` API.
- **Auto-landscape wide tables:** tables whose column count meets
  `tables.landscape_threshold` (default 8) now render on a rotated A4 page
  so content stays readable instead of being squeezed. Configurable per
  project via `corpdoc.yml`. Demo includes a 9-column cost-breakdown table
  that exercises the feature.
- **Configurable cover styles** via `cover.style` in `corpdoc.yml`:
  `classic` (default), `minimal`, `bold-band`, `split`. Unknown style names
  fall back to `classic` with a warning. `CoverPageFlowable` now dispatches
  per style rather than hard-coding one layout.
- **Fourth color role: `highlight`.** Palettes now expose a 4th tone picked
  from the next darkest color distinct from `primary`/`secondary`/`accent`,
  with a darkened-primary fallback for two-color logos. Used for `H3`
  headings and the divider rule on the `split` cover style. Overridable via
  `colors.highlight` in `corpdoc.yml`.
- Tests for the logo resolver, the new frontmatter parser, the `highlight`
  role (distinctness + fallback), and for landscape table rotation
  (verified via `pypdf`).
- **Pastel cover surfaces with white logo card.** The `bold-band` and
  `split` covers now fill their colored areas with a pastel tint of the
  primary (lightened 78%) — derived from the logo, not hard-coded — and
  render the logo on a white rounded card so the wordmark stays readable
  regardless of which colors the logo uses.
- **Edge-bleed fix on cover blocks.** Edge-to-edge color blocks
  (classic band, bold-band fill, split top half) now overshoot every page
  edge by 1 cm, eliminating the thin white strip on the bottom-left caused
  by ReportLab's default 6 pt frame padding.
- `SECURITY.md` with private reporting via GitHub Security Advisory + email.
- `pip-audit` job in CI: fails the build on any vulnerability in a CorpDoc
  runtime or dev dependency.
- `dependabot.yml` for weekly version updates of pip and GitHub Actions.

### Changed
- **Colors:** the CorpDoc brand palette moved from teal/coral to
  forest/camel/slate (`#1F4129` + `#C8A36A` + `#1E293B`). Slate powers the
  new `highlight` role so documents render with three visible brand tones.
- **Logo refresh:** the wordmark is now a tight `CorpDoc` (capital `C` and
  `D`, no gap) with `Corp` in forest and `Doc` in camel. The document-tile
  mark uses all three brand colors.
- **Frontmatter:** replaced the hand-rolled parser with `yaml.safe_load`.
  Values with colons, dates, and quoted strings now round-trip correctly.
- **Color role assignment:** `accent` now falls back to `secondary` only
  when the palette has fewer than three usable colors; previously they were
  always identical.
- **Config override:** the optional `colors:` block in `corpdoc.yml` now
  correctly overrides auto-extracted colors on a per-key basis (previously
  only applied when no SVG was present).
- CLI writes UTF-8 to stdout/stderr so unicode glyphs render on Windows.
- **Release pipeline:** PyPI publishing migrated from API-token auth to
  Trusted Publishing (OIDC). No long-lived secret in the repo.

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
