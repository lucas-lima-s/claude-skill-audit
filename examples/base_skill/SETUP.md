# Setup -- base-skill

Reference skill. Prints `ok`.

## Requirements

- Python 3.11+ available via `$SKILLS_PYTHON` (preferred) or `python` /
  `python3` on `PATH`.

No third-party runtime dependencies. Dev dependencies (`ruff`, `pytest`)
are declared under `[dependency-groups].dev` in `pyproject.toml` and are
installed only when you work on the skill itself (`uv sync`), not when you
use it.

## Recognised environment variables

| Variable              | Purpose                                                   |
|------------------------|------------------------------------------------------------|
| `SKILLS_PYTHON`        | Python interpreter the skill expects to be invoked with.  |
| `USERPROFILE`/`HOME`   | Resolved by Python's `Path.expanduser()` if needed.       |

## Running

```bash
"$SKILLS_PYTHON" scripts/hello.py
```

## Layout

```
.
- SKILL.md                  - frontmatter + body
- README.md
- SETUP.md                  - this file
- CHANGELOG.md
- CONTRIBUTING.md
- LICENSE
- .gitignore
- .gitattributes
- pyproject.toml
- scripts/
  - hello.py                - prints `ok`
- tests/
  - test_hello.py
```
