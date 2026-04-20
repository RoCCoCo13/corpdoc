# Quickstart

From zero to your first branded PDF in 5 minutes.

## 1. Install

```bash
pip install corpdoc
```

You should now have the `corpdoc` command available:

```bash
corpdoc --version
# corpdoc 0.3.0
```

## 2. Prepare your logo

CorpDoc accepts your logo as **SVG**, **PNG**, or both. You don't need to
convert between formats — svglib renders SVGs directly into the PDF.

- **SVG** is preferred because CorpDoc parses the XML to extract brand colors
  automatically. If your SVG uses gradients or filters, flatten them first
  (svglib doesn't support those) or also provide a PNG.
- **PNG** is used when present at render time; it's faster and pixel-faithful
  to whatever your designer exported.

If you only have a PNG, CorpDoc still works but you'll need to declare the
colors manually in `corpdoc.yml` (see below).

## 3. Create the config

```bash
corpdoc init --logo logo.svg --name "Acme Engineering SL"
```

This creates `corpdoc.yml` with:
- Brand colors extracted from `logo.svg` (you'll see them printed)
- Company name populated
- Placeholder footer fields for you to fill in

Open `corpdoc.yml` and edit the `footer.fields` section to include your
address, director, VAT number, email, and website.

## 4. Preview your palette

Confirm the extracted colors look right:

```bash
corpdoc colors logo.svg
```

You'll see color swatches in your terminal (if your terminal supports true
color). The tool assigns roles automatically:
- **Primary** — used for body text, headings, table headers
- **Secondary / accent** — used for lines, the cover band, highlights

If CorpDoc picks wrong colors (e.g. your logo has 20 gradient stops and it
chose a weird one), you can override them in `corpdoc.yml`:

```yaml
colors:
  primary: "#003d5c"
  accent: "#ff6b35"
```

## 5. Write a document

Create `test.md`:

```markdown
---
title: "Quick Test"
subtitle: "First CorpDoc Document"
version: "1.0"
status: "Draft"
---

# 1. Introduction

This is a test. If you can read this in a nicely branded PDF, CorpDoc is
working.

# 2. Test Table

| Item | Value |
|------|-------|
| A    | 1     |
| B    | 2     |
| C    | 3     |

# 3. Done

That's all.
```

## 6. Render

```bash
corpdoc render test.md --config corpdoc.yml
```

You get `test.pdf`. Open it and you should see:
1. Cover page with your logo and title
2. Version history page (with room for future versions)
3. Table of contents
4. Three sections of body content

## 7. Use with AI

Copy the contents of `skill/SKILL.md` (or the whole file) into your AI of
choice as a system prompt or attached file. Then say something like:

> "Generate a CorpDoc-compatible Markdown offer for installing 50kW solar
> panels at ACME's warehouse. Budget €60,000."

The AI will produce Markdown that renders correctly with CorpDoc.

## Next steps

- Read [configuration.md](configuration.md) for all `corpdoc.yml` options
- Read [ai-integration.md](ai-integration.md) for effective AI workflows
- Browse the `examples/` folder for real-world samples
