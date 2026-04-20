# AI Integration Guide

CorpDoc is built to be driven by AI. This guide shows how to wire it up with
the most popular LLM interfaces.

## The core idea

1. **Your AI** generates CorpDoc-compatible Markdown
2. **CorpDoc** renders the Markdown to a branded PDF

The bridge between them is [`skill/SKILL.md`](../skill/SKILL.md) — a single
file that teaches any LLM how to produce correct output.

## How to feed the SKILL.md to your AI

### Claude (via Claude.ai or API)

1. Copy the full contents of `skill/SKILL.md`
2. Paste it as the **first message** in a new conversation, prefixed with
   "Here are your instructions for the CorpDoc skill:"
3. Then send your actual request

Or, if you're using Claude Projects, add `SKILL.md` as a project knowledge
file once and Claude will apply it to every conversation in that project.

### ChatGPT / GPT-4 / GPT-5

1. Create a **Custom GPT** and paste `SKILL.md` into the "Instructions" field
2. Optional: upload example Markdown files and their rendered PDFs as
   knowledge

Or paste `SKILL.md` into the system prompt via the API.

### Gemini / Gemini Advanced

Paste `SKILL.md` at the start of the conversation as context. Gemini's large
context window makes this easy.

### Local models (Ollama, LM Studio, etc.)

Set `SKILL.md` as the system prompt in your model's config. For a quick test:

```bash
ollama run llama3.1 < skill/SKILL.md
```

Then start your request after the skill loads.

### API integrations (programmatic)

```python
import anthropic

client = anthropic.Anthropic()

with open('skill/SKILL.md') as f:
    skill = f.read()

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    system=skill,
    messages=[{
        "role": "user",
        "content": "Draft an offer for a 500kW solar PV installation at ACME Industrial."
    }]
)

markdown = response.content[0].text

# Save and render
with open('offer.md', 'w') as f:
    f.write(markdown)

import subprocess
subprocess.run(['corpdoc', 'render', 'offer.md', '--config', 'corpdoc.yml'])
```

## Workflow patterns

### Pattern 1: Single-shot generation

You know exactly what you want. Give the AI all the info in one prompt:

> "Generate a CorpDoc Markdown for a technical offer. Project: HVAC
> installation in 2000 m² warehouse. Client: ClienteCorp. Budget: €45,000.
> Timeline: 6 weeks. Include sections for scope, timeline, team, and
> payment terms. Reference: OFR-2026-0043."

The AI produces complete Markdown. You save and render.

### Pattern 2: Agentic refinement

Start with a brief prompt and let the AI ask clarifying questions:

> "I need to write an offer for a new client. Can you help?"

A well-configured AI (with the SKILL.md) will ask for:
- Document type
- Client details
- Project scope and budget
- Any missing reference/version numbers

Once it has enough info, it produces the Markdown.

### Pattern 3: Iterative drafting

Generate an outline first, review it, then fill in:

> "First, give me the Markdown structure (headings only) for a technical
> report on our Q1 performance. After I approve, we'll fill in the content."

Useful for longer documents where you want control over the structure.

### Pattern 4: Batch generation

Produce multiple variations:

> "Generate three versions of this offer: one conservative (lowest scope),
> one standard, and one premium. Same client, same base project."

CorpDoc renders all three. You send the client the one that fits.

## The full automation loop (for power users)

If you run a home server (Ollama + agent framework), you can make this fully
automatic:

```
Telegram message → Agent receives request → Local LLM generates Markdown
                       → corpdoc render → PDF sent back via Telegram
```

Sample agent logic (pseudocode):

```python
@telegram_bot.command("/offer")
def handle_offer_request(ctx):
    brief = ctx.text
    md = ollama.generate(system=SKILL_MD, prompt=brief)
    with open('/tmp/offer.md', 'w') as f:
        f.write(md)
    subprocess.run(['corpdoc', 'render', '/tmp/offer.md',
                    '--config', '/home/user/corpdoc.yml',
                    '--output', '/tmp/offer.pdf'])
    ctx.send_document('/tmp/offer.pdf')
```

From message to PDF in your hand: 30 seconds.

## Tips for better AI output

1. **Give examples.** If you have a previous offer you liked, include it in
   the prompt as "format like this one, but for this new project."
2. **Be specific about numbers.** Amounts, durations, team sizes — the AI
   will invent them if you don't specify.
3. **Name your sections.** If you want specific H1s, list them: "Include
   sections: Scope, Timeline, Budget, Team, Next Steps."
4. **Mind the language.** If you want the document in Spanish, write your
   prompt in Spanish. CorpDoc auto-detects the output language.
5. **Review before rendering.** The AI handles 95% of the structure, but
   skim the Markdown for factual accuracy before running `corpdoc render`.

## Troubleshooting

**The AI keeps adding HTML tags or layout instructions.**
Re-emphasize the "DON'T" section of SKILL.md. Specifically say: "Pure
Markdown only. No HTML. No layout instructions."

**The output references sections or fields that don't exist in my config.**
Share your `corpdoc.yml` with the AI (copy the content, not the file) so
it knows what fields are available.

**Tables come out badly formatted.**
Ask the AI to re-check that every table has a `|---|---|` separator line
under the header, and that cells don't contain pipe characters.
