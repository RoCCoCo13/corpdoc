---
name: corpdoc
description: >
  Generate professional corporate PDFs from Markdown. Use this skill whenever
  the user asks to create a formal document, offer, technical report, proposal,
  memo, or any business deliverable that needs to look branded and professional.
  The user will have a Markdown file that gets converted to PDF via the corpdoc
  CLI. Your job is to produce Markdown content with the correct structure and
  frontmatter — CorpDoc handles all visual formatting (cover, colors, logo,
  headers, footers, tables) automatically from a config file.
version: 0.3.0
license: MIT
---

# CorpDoc Skill — Generate Corporate PDFs with Any AI

CorpDoc converts Markdown to professional branded PDFs. It handles cover pages,
version control, table of contents, headers/footers with corporate info, and
auto-styled tables. Your job as the AI is to produce correct Markdown. The
corpdoc CLI does everything visual.

---

## When to use this skill

Trigger on any request like:
- "write an offer for client X"
- "generate a technical report about..."
- "draft a memo / proposal / technical document"
- "create a project report for..."
- Anything that needs a branded, formal PDF deliverable

## When NOT to use this skill

- Casual notes, emails, chat messages
- Code documentation / READMEs
- Slides or presentations (CorpDoc is for documents, not decks)
- Spreadsheets

---

## Agentic information-gathering (IMPORTANT)

Before producing Markdown, you must have enough context. If the user has not
provided everything below, **ask them in a single grouped message** — not one
question at a time. Prefer giving reasonable defaults they can approve.

### Minimum required information

1. **Document type** — offer, report, memo, proposal, technical document,
   generic
2. **Document title** — the H1 heading
3. **Subtitle** — usually the client name or project name (shown under the
   title on the cover)
4. **Content** — what goes in the body. Either:
   - Ask the user to describe the content, OR
   - Offer to draft a full outline they can review before you flesh it out
5. **Language** — detected automatically from content (en, es, de, fr), but
   confirm if there are mixed signals

### Optional but recommended

- Reference / document ID (e.g. "OT-2026-0042")
- Version number (default: 1.0)
- Document date (default: today)
- Author name
- Document status (Draft, Review, Final, Release)
- Confidentiality (Public, Internal, Confidential, Restricted)

### Config-level info (only ask once per company)

These go in `corpdoc.yml`, not in the Markdown. If the user doesn't have a
config yet, help them create one by asking:

- Company legal name (e.g. "Acme Engineering SL")
- Tagline for header (e.g. "acme | engineering | solutions")
- Logo path (SVG or PNG; SVG is preferred because CorpDoc extracts brand
  colors from it automatically and renders it natively via svglib)
- Footer fields: address, Director, CIF/VAT, registry, email, website
- `brand_split` (default: 3) — how many leading chars of each word get the
  accent color in headers and footers

**If the user doesn't have a config file yet, tell them to run:**

```bash
corpdoc init --logo logo.svg --name "Acme Engineering SL"
```

Then edit the generated `corpdoc.yml` to fill in the footer details.

---

## Output format — how to structure the Markdown

Every document you produce must be valid Markdown with optional YAML
frontmatter. The corpdoc CLI renders it to PDF.

### 1. Optional YAML frontmatter

Put between two `---` lines at the very top of the file:

```yaml
---
title: "Clear Document Title"
subtitle: "Client name or project description"
reference: "REF-2026-001"
version: "1.0"
date: 2026-04-19
author: "Your Name"
status: "Draft"              # Draft | Review | Final | Release
---
```

**If you omit the frontmatter**, CorpDoc uses the first H1 as the title and the
first H2 (if it comes right after) as the subtitle. This is perfectly fine.

### 2. Body structure

Use standard Markdown:

```markdown
# Main Title (becomes cover title if no frontmatter)
## Subtitle (becomes cover subtitle if right after H1)

# 1. First Section

Body text here. Supports **bold**, *italic*, ***bold italic***, and `inline code`.

## 1.1 Subsection

More content.

### 1.1.1 Sub-subsection

Even more specific content.
```

### 3. Lists — nested lists need 2-space indent

```markdown
- Top-level item
  - Sub-item (2 spaces before the dash)
  - Another sub-item
- Another top-level item
  - With a sub-item
```

### 4. Tables

Use standard Markdown tables. CorpDoc styles them automatically:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data     | Data     | Data     |
| More     | More     | More     |
```

Tables with up to 6 columns render at standard size. Tables with 7+ columns
automatically switch to a smaller font. Tables longer than a page break across
pages with the header row repeated.

### 5. Diagrams (Mermaid)

```markdown
​```mermaid
flowchart LR
    A[Start] --> B[Process] --> C[End]
​```
```

### 6. Code blocks

```markdown
​```python
def example():
    return "Hello"
​```
```

### 7. Horizontal rules

Use `---` on its own line to separate major sections.

---

## Templates per document type

### Offer / Proposal

```markdown
---
title: "Proposal: [What you're proposing]"
subtitle: "Client: [Client Name]"
reference: "OFR-YYYY-NNN"
version: "1.0"
date: YYYY-MM-DD
status: "Draft"
---

# 1. Executive Summary

One paragraph summarizing what you're offering, the value proposition,
and the total investment.

# 2. Client Context and Needs

Briefly describe the client's situation and the problem being solved.
This shows you understand their needs.

# 3. Proposed Solution

## 3.1 Overview

High-level description of the solution.

## 3.2 Scope of Work

Detailed breakdown of what's included:

- **Phase 1: [Name]**
  - Deliverable A
  - Deliverable B
- **Phase 2: [Name]**
  - Deliverable C

## 3.3 Out of Scope

What is explicitly NOT included (manage expectations).

# 4. Timeline

| Phase | Duration | Milestone |
|-------|----------|-----------|
| Kickoff | 1 week | Kick-off meeting |
| Phase 1 | N weeks | First delivery |
| Phase 2 | N weeks | Final delivery |

# 5. Investment

| Item | Description | Amount |
|------|-------------|--------|
| Phase 1 | ... | €X,XXX |
| Phase 2 | ... | €X,XXX |
| **Total (excl. VAT)** | | **€XX,XXX** |

Payment terms: [e.g. 30% upfront, 40% at milestone, 30% on delivery]

# 6. Team

Brief bio of the team members involved.

# 7. Next Steps

How to move forward (e.g. "Sign and return by DATE").
```

### Technical Report

```markdown
---
title: "[Topic] Analysis Report"
subtitle: "Prepared for [Client]"
reference: "RPT-YYYY-NNN"
version: "1.0"
status: "Final"
---

# 1. Executive Summary

Key findings and recommendations in 3–5 bullets.

# 2. Objectives

What this report set out to investigate.

# 3. Methodology

How the analysis was conducted. Include relevant data sources, tools,
and methods.

# 4. Findings

## 4.1 Finding Area 1

Evidence-based findings. Use tables to present data:

| Metric | Baseline | Observed | Target |
|--------|----------|----------|--------|
| ...    | ...      | ...      | ...    |

## 4.2 Finding Area 2

...

# 5. Analysis

Interpretation of the findings.

# 6. Conclusions

Synthesis of what the findings mean.

# 7. Recommendations

Actionable next steps, prioritized.
```

### Memo / Internal Document

```markdown
---
title: "[Short descriptive title]"
subtitle: "Internal memorandum"
reference: "MEMO-YYYY-NNN"
status: "Internal"
---

# Summary

One-paragraph summary at the top.

# Background

Context for the memo.

# Key Points

- Point 1
- Point 2
- Point 3

# Recommendations

Clear, actionable recommendations.

# Next Steps

Who does what, by when.
```

---

## Hard rules — DO and DON'T

### DO

- Always produce valid Markdown
- Use `#`, `##`, `###`, `####` for headings (max 4 levels)
- Use `-` for bullets (not `*`)
- Indent sub-bullets with exactly 2 spaces
- Use frontmatter for professional documents
- Keep tables ≤ 8 columns where possible
- Use meaningful section numbers in H1s (e.g. "# 1. Introduction")
- Match the language of the user (CorpDoc detects en/es/de/fr)
- Leave a blank line before and after each heading and table

### DON'T

- Don't add HTML tags — CorpDoc only accepts pure Markdown
- Don't try to specify fonts, colors, or layout in the Markdown — these come
  from `corpdoc.yml`
- Don't use exotic Unicode characters for bullets (·, •, ▪) — use `-`
- Don't embed images directly in the Markdown unless the user provides them
- Don't create cover pages in the content — CorpDoc generates them
- Don't write "Table of Contents" manually — CorpDoc generates it
- Don't write "Page 1 of N" — CorpDoc handles pagination
- Don't use heading levels deeper than `####` — they won't render distinctly

---

## How the user renders your output

After you produce the Markdown, the user runs:

```bash
corpdoc render document.md --config corpdoc.yml
```

This produces `document.pdf` with:
- Cover page (logo, title, subtitle, accent color block)
- Version history page
- Auto-generated table of contents
- Branded header on every page (logo right, tagline left)
- Branded footer on every page (company legal info, page numbers)
- Styled body with brand-colored headings and tables

The user doesn't need to touch layout. Your Markdown is the deliverable.

---

## Agentic checklist before you hand off

Before sending the final Markdown to the user, verify:

- [ ] Frontmatter has at minimum `title` and `subtitle`
- [ ] H1 headings follow a logical numbering scheme (`# 1.`, `# 2.`, ...)
- [ ] Tables have header rows separated by `|---|---|` line
- [ ] Nested lists use 2-space indentation
- [ ] No HTML, no raw CSS, no layout instructions
- [ ] Content is complete and in the right language
- [ ] Amounts/dates/units formatted consistently (e.g., "€12,500.00", "2026-04-19")

If any of these fail, fix it before showing the output to the user.

---

## Example end-to-end interaction

**User:** "Write an offer for installing 50kW solar PV at ClienteCorp's
warehouse in Madrid. Budget around €60k."

**You (AI with this skill):**

1. Check: do they have a `corpdoc.yml`? If not, tell them to run
   `corpdoc init --logo their-logo.svg --name "Their Company SL"` first.
2. Ask the 2–3 missing pieces at most (reference number, preferred date,
   their company name if not set up yet).
3. Produce the Markdown using the "Offer / Proposal" template, filled with
   realistic technical content for a 50kW PV installation.
4. Remind them: `corpdoc render offer.md --config corpdoc.yml` will produce
   the final PDF.

That's it. Stay focused on content quality. CorpDoc makes it look professional.
