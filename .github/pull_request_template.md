## Summary

<!-- One or two sentences describing what changes and why. -->

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would change existing behavior)
- [ ] Documentation / tooling / chore (no user-visible code change)

## Checklist

- [ ] `ruff check src/ tests/` passes locally
- [ ] `ruff format --check src/ tests/` passes locally
- [ ] `pytest tests/ -v` passes locally
- [ ] `corpdoc render examples/corpdoc-sample/demo.md --config examples/corpdoc-sample/corpdoc.yml` still produces a valid PDF
- [ ] Added / updated tests for the change (where applicable)
- [ ] Updated `CHANGELOG.md` under `[Unreleased]`
- [ ] Updated relevant docs (`README.md`, `skill/SKILL.md`, `docs/`) if user-facing behavior changed

## Screenshots / output (if UI or PDF output changed)

<!-- Drop in a before/after screenshot of the rendered PDF, or a snippet of CLI output. -->

## Related issues

<!-- e.g. Closes #123, Refs #456. Delete if none. -->
