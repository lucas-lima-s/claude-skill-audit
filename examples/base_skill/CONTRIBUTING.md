# Contributing

This is a minimal reference skill; changes should stay minimal too.

## Setup

```bash
uv sync
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## Commit policy

Conventional Commits, English subject lines. Update `CHANGELOG.md` under
`[Unreleased]` for any user-visible change.
