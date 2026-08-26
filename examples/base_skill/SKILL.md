---
name: base-skill
description: Reference skill that ships with claude-skill-audit as a functional example. Triggered by "run base-skill" / "rode a base-skill". Prints `ok` and exits.
argument-hint: (none)
allowed-tools:
  - Bash(*scripts/hello.py*)
---

# base-skill -- minimal reference

This skill exists as a working example of every artifact `skill-audit`
checks for. It does the simplest thing imaginable: prints `ok`. The point
is the surrounding structure, not the behaviour.

## Invocation

```
"$SKILLS_PYTHON" scripts/hello.py
```

## What this skill demonstrates

- A minimal `SKILL.md` with a non-empty frontmatter `description:` and an
  `allowed-tools:` entry.
- A `README.md`, `SETUP.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`,
  `.gitignore`, `.gitattributes`, `pyproject.toml`, a CI workflow, PR and
  issue templates, and a `tests/` directory -- all in their canonical
  shapes.
- A `scripts/hello.py` with `from __future__ import annotations`,
  `pathlib.Path`, no hardcoded paths, no third-party imports.

Running `skill-audit` against this directory under `--profile
skill-public` reports a perfect scorecard.
