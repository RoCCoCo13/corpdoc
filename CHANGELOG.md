# Changelog

All notable changes to CorpDoc will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.5.0] — 2026-11-15

Existing documents render as before: every new behaviour is additive or
opt-in. The exceptions are the things that were not rendered at all until now
— numbered lists, block images, link targets, a third list level — and
Mermaid diagrams on machines where `mmdc` is installed.
Two bug fixes also change existing output: the table of contents is now
filled, and words at wrapped source lines are no longer glued together
(see Fixed).

### Added
- **Images.** A paragraph that contains only an image is drawn as a figure:
  PNG and JPG through ReportLab, SVG through svglib. It is scaled down to the
  frame width (never upscaled), keeps its aspect ratio, is capped to the
  usable page height, and shows its alt text as a centred caption. Relative
  paths resolve against the Markdown file's directory; `render()` takes a new
  optional `base_dir` for Markdown passed as a string (default: current
  directory). A missing, unreadable or remote image prints a warning and
  renders a visible placeholder instead of failing. Images inside a line of
  text keep printing their alt text.
- **Optional front pages.** New config block `sections` with `cover`,
  `version_history` and `toc` (all default to `true`), and the same keys in
  the document frontmatter, which override the config. Header, footer and
  page numbering follow the pages that are present.
- **Page count.** `corpdoc render` prints total and body pages (body = pages
  after cover / version history / table of contents). `render()` now returns
  a `RenderResult`: still the output path (a `str` subclass), plus
  `total_pages`, `body_pages`, `max_pages` and `over_limit`. The counts are
  also set on the `CorpDoc` object.
- **Page limit.** Optional `max_pages` (`defaults.max_pages` in the config,
  overridable in the frontmatter) for the body pages. Exceeding it prints a
  warning; the new `corpdoc render --strict` flag exits with code 1 instead.
- **Numbered lists.** Ordered lists render "1.", "2.", … honouring the start
  number and restarting in each nested list. Previously every item got a
  bullet.
- **Unicode fonts (opt-in).** New config `fonts.family`: `"helvetica"`
  (default, unchanged), `"dejavu"`, or a mapping of TTF paths. `"dejavu"`
  uses DejaVu Sans and DejaVu Sans Mono, bundled in the package (unmodified
  DejaVu 2.37, licence included as `corpdoc/fonts/LICENSE-DejaVu.txt`), in
  every style including cover, header and footer.
- **Warning for characters the fonts cannot show.** With the default family,
  one warning per render lists characters that the built-in fonts cannot
  encode and that therefore appear as a box (for example `₂`). The check
  covers the text that is actually drawn, with the font that draws it
  (regular, bold, italic, monospace), including custom font families.
- **Clickable links.** Links to `http(s)`, `ftp`, `mailto` and `tel` targets
  are emitted as real PDF links, with the URL escaped. Their look is
  unchanged. Anchor and relative links stay plain text.
- **Three list levels** instead of two (new `CBullet3` style).
- **Local Mermaid rendering.** If the Mermaid CLI executable `mmdc` is on
  `PATH`, diagrams are rendered to PNG in a temporary directory and embedded
  as images, with a timeout (`mermaid.timeout`, default 30 s) and cleanup.
  Without `mmdc`, or on failure, the previous text block is kept and a
  warning is printed. `mermaid.enabled: false` keeps the text block silently.
  Up to four diagrams are rendered at the same time; if `mmdc` times out or
  cannot be started, the remaining diagrams are not attempted.
- **Concurrent renders.** One `CorpDoc` object can render several documents
  at the same time (for example from a thread pool).

### Changed
- `corpdoc init` writes the new `sections` and `fonts` blocks (with their
  defaults) into the generated config.
- The sample document and its PDFs exercise images, numbered lists, links,
  three-level lists and the DejaVu family.
- `CorpDoc(config=...)` raises `TypeError` instead of `ValueError` when the
  config is neither a path nor a dict.
- Linting uses ruff's default rule set, with the ruff version pinned in
  `pyproject.toml` and used by CI.

### Removed
- The `mermaid` extra (`requests`, `cairosvg`). It was never used by the
  code. Diagrams are rendered locally only; there is no Kroki or other HTTP
  path, and CorpDoc makes no network calls at render time.

### Fixed
- **Table of contents was empty.** The contents page showed only a
  placeholder text because the document was built in a single pass. It now
  lists the H1–H3 headings with the page numbers printed in the footers.
- **Words glued at line breaks.** A line break inside a paragraph, list item
  or table cell in the Markdown source ("line one⏎line two") rendered as
  "line oneline two". It now renders as a space. Paragraphs become slightly
  longer where this happened, so page breaks can shift.
- Headings containing `&` or `<` were mangled in the table of contents.
- A wide table at the very start of the body left a blank page before it,
  which also counted towards `max_pages`.
- A config `sections` that is not a mapping crashed the render; it now
  prints a warning and uses the defaults.
- A code block without a language (a bare ` ``` ` fence, or an indented code
  block) crashed the render with `KeyError: 'attrs'`.
- The alt text of an inline image was dropped instead of printed (mistune v3
  stores it as child tokens).
- The Mermaid text block garbled diagram sources containing `&` or `<`.
- A logo that cannot be read or drawn is now reported with a warning. Before,
  the problem was swallowed and the logo was silently left out.
- A truncated SVG logo (zero size) is rejected with a warning instead of
  failing later.

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
