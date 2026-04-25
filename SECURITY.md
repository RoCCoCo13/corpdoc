# Security Policy

CorpDoc generates PDFs from Markdown. The most likely real-world risk is a
malicious YAML config or SVG/PNG logo that triggers a parser fault rather
than network/auth issues, but we take any potential vulnerability seriously.

## Supported versions

The latest minor release is the only branch that receives security fixes.
Pre-release / alpha tags are not supported.

| Version | Supported          |
|---------|--------------------|
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security reports.**

Report privately via either channel:

- **GitHub Security Advisories** — preferred. Open a draft advisory at
  <https://github.com/RoCCoCo13/corpdoc/security/advisories/new>. This keeps
  the report private until a fix is published.
- **Email** — `roccoco13@gmail.com` with subject `[corpdoc-security] <short title>`.

Include, if possible:

- Affected version(s) and platform.
- A minimal reproducer (config + Markdown + logo).
- The observed impact (crash, file read outside intended scope, etc.).
- Any suggested fix.

## What to expect

- **Acknowledgement:** within 5 working days.
- **Triage:** within 14 days. We'll either accept the report and start work
  on a fix, or explain why we consider it out of scope.
- **Fix:** target 30 days for high-severity issues. Lower-severity issues
  may be batched into the next release.
- **Disclosure:** after a fix ships, we publish a GitHub Security Advisory
  crediting the reporter (unless they prefer to remain anonymous).

## Scope

In scope:

- Code execution, file read/write outside the paths explicitly given to the
  CLI, denial of service via crafted inputs (SVG/PNG/Markdown/YAML).
- Vulnerabilities in CorpDoc's own source code or default configuration.
- Supply-chain issues in our release workflow.

Out of scope:

- Vulnerabilities in third-party dependencies (please report those upstream
  to ReportLab, Pillow, mistune, PyYAML, or svglib directly). We will of
  course bump the affected dependency once a fix is available.
- Issues that require an attacker to already control the operator's
  `corpdoc.yml`, logo files, or Markdown source — CorpDoc trusts the user
  who runs it. Wrapping CorpDoc as a service that processes untrusted input
  is the integrator's responsibility (see notes in the README about
  defusedxml/lxml and `PIL.Image.MAX_IMAGE_PIXELS`).

## Hall of fame

Reporters who follow this policy will be credited here once their report
results in a published advisory.
