# Contributing to CorpDoc

Thanks for your interest in making CorpDoc better. This guide covers how to
set up a dev environment and submit changes.

## Getting started

```bash
git clone https://github.com/RoCCoCo13/corpdoc.git
cd corpdoc
pip install -e ".[dev]"
```

Run the examples to verify your setup:

```bash
cd examples/corpdoc-sample
python -m corpdoc.cli render demo.md --config corpdoc.yml
```

You should get `corpdoc-demo.pdf`.

## Running tests

```bash
pytest
```

## Code style

- Python 3.10+ syntax
- `ruff` for linting (`ruff check src/`)
- Type hints welcome but not required
- Docstrings for public APIs (Google style)

## How to contribute

1. **Open an issue first** for non-trivial changes, so we can discuss the
   design before you spend time implementing.
2. **Fork the repo**, create a branch from `main`.
3. **Make your change**, add tests if applicable.
4. **Update the CHANGELOG** under an `## [Unreleased]` section.
5. **Open a pull request** with a clear description of what and why.

## Areas where we'd love help

### Document templates
We want a gallery of battle-tested templates in `templates/`:
- Commercial offer / proposal
- Technical report
- Memorandum
- Consulting SOW
- Legal brief
- Academic paper
- Invoice / quotation

### Languages
We currently detect en / es / de / fr. Pull requests welcome for:
- Portuguese (pt)
- Italian (it)
- Dutch (nl)
- Polish (pl)

Add your stop-word list to `parser.py::detect_language` and page-label
translations to `corpdoc/i18n.py::LANGUAGES`.

### Diagram rendering
Current Mermaid handling is a styled text placeholder. Real rendering via
Kroki.io or a local mermaid-cli fallback would be great.

### Integrations
- VS Code extension (run `corpdoc render` from the command palette)
- Obsidian plugin (render current note)
- GitHub Action (auto-render on push)
- Pre-commit hook

## Code of conduct

Be kind. Assume good faith. No harassment. If you wouldn't say it at a
professional meeting, don't say it here.

## License

By contributing, you agree your contributions will be licensed under MIT.
