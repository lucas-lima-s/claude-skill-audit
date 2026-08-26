---
name: Bug report
about: Report a defect in the skill or its scripts
title: ""
labels: bug
---

## Reproduction

Step-by-step commands or natural-language phrases that triggered the
issue. Include the profile (`skill-public` / `skill-local`), the target
skill path, and any flags (`--profile`, `--json-out`, `--max-layer2-bytes`).

## Expected

What you expected to happen.

## Actual

What actually happened. If a check produced a false positive or false
negative, paste the relevant entry from `findings_layer1[]`.

## Environment

- OS:
- Python version (`python --version`):
- skill-audit version (`CHANGELOG.md`):
- Target skill (publicly available?):

## Logs

Attach relevant log output. **Sanitise paths** before pasting if the
target skill is private.
