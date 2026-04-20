# CorpDoc AI Skill

This folder contains `SKILL.md` — a single file that teaches any LLM how to
generate CorpDoc-compatible Markdown documents.

## What's a skill?

A skill is a self-contained instruction file for AI models. It describes:

- When the AI should use the skill (what kinds of requests trigger it)
- What output format the AI should produce
- Rules and constraints specific to the task
- Example interactions

You give the `SKILL.md` to your AI once, and from then on, the AI produces
correctly-structured CorpDoc Markdown whenever you ask for a formal document.

## How to use it

### With Claude

- **claude.ai:** Paste `SKILL.md` contents at the start of a new conversation,
  or attach it as a Project file.
- **API:** Pass it as the `system` parameter.

### With ChatGPT

- **Custom GPT:** Paste `SKILL.md` into the "Instructions" field.
- **API:** Pass it as the `system` role message.

### With Gemini

- Paste at the start of the conversation as context.

### With local models (Ollama, LM Studio)

- Set as the system prompt in your model's Modelfile or config.

See [`docs/ai-integration.md`](../docs/ai-integration.md) for detailed setup
instructions and example workflows.

## File

- [`SKILL.md`](SKILL.md) — the full skill definition

## Testing your setup

A good test prompt after loading the skill:

> "Generate a CorpDoc Markdown document for a technical offer. Project: solar
> PV installation 500 kWp. Client: Test Corp. Budget: €300,000. Timeline: 8
> weeks."

The AI should produce Markdown that starts with YAML frontmatter and contains
numbered sections like `# 1. Scope`, `# 2. Timeline`, etc. No HTML tags, no
layout instructions, no inline styling.

If you get that, you're ready.
