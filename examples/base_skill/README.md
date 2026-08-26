# base-skill

The minimal reference skill that ships alongside `claude-skill-audit`. It
prints `ok` and exits zero. The point is the structure: every artifact
`skill-audit` looks for is present, and the skill passes
`check.py --profile skill-public` cleanly.

## What it is

A reference layout. Use `scripts/init_skill.py` to bootstrap a new skill
from it -- you get a directory that already passes the audit.

## Installation

```bash
git clone https://github.com/lucas-lima-s/claude-skill-audit.git
cd claude-skill-audit
uv run python scripts/init_skill.py --out ~/.claude/skills/your-new-skill \
  --name your-new-skill --description "What your-new-skill does."
```

## Usage

```bash
"$SKILLS_PYTHON" scripts/hello.py
```

Output:

```
ok
```

## License

[MIT](LICENSE).
