## Summary

<!-- What does this change do, and why? -->

## Checks

- [ ] `uv run pytest -q` passes
- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `scripts/sync_auditlib.py --check` passes (never hand-edit `scripts/auditlib/`)
- [ ] `CHANGELOG.md` has an `## [Unreleased]` entry
- [ ] No hardcoded paths -- only env vars (`SKILLS_PYTHON`, `TEMP`, `env:TEMP`) or paths relative to the skill directory
- [ ] Docs are in English (SKILL.md's `description:` may keep pt-BR trigger phrases)
