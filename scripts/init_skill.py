#!/usr/bin/env python3
"""Materialize examples/base_skill/ into a new skill directory.

Copies the reference skill, substitutes `base-skill` / `base_skill` with
the given name, and optionally writes a new `description:`. The generated
skill audits clean under `--profile skill-public`.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TOOL_ROOT = SCRIPT_DIR.parent
BASE_SKILL = TOOL_ROOT / "examples" / "base_skill"

SUBSTITUTE_FILES = ("SKILL.md", "README.md", "SETUP.md", "CHANGELOG.md", "pyproject.toml")


def _copy_tree(src: Path, dst: Path) -> None:
    for entry in sorted(src.rglob("*")):
        if "__pycache__" in entry.parts:
            continue
        target = dst / entry.relative_to(src)
        if entry.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(entry, target)


def _substitute_name(dst: Path, name: str) -> None:
    hyphen = name
    snake = name.replace("-", "_")
    for rel in SUBSTITUTE_FILES:
        target = dst / rel
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8")
        text = text.replace("base_skill", snake).replace("base-skill", hyphen)
        target.write_text(text, encoding="utf-8", newline="\n")


def _write_description(dst: Path, description: str) -> None:
    skill_md = dst / "SKILL.md"
    if not skill_md.exists():
        return
    lines = skill_md.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.lstrip()
        if not replaced and stripped.startswith("description:") and line[: len(line) - len(stripped)] == "":
            out.append(f"description: {description}\n")
            replaced = True
        else:
            out.append(line)
    skill_md.write_text("".join(out), encoding="utf-8", newline="\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="init_skill.py",
        description="Scaffold a new Claude Code skill from examples/base_skill/.",
    )
    parser.add_argument("--out", required=True, help="destination directory for the new skill")
    parser.add_argument("--name", default=None, help="skill name; replaces 'base-skill' / 'base_skill'")
    parser.add_argument("--description", default=None, help="value written to SKILL.md's `description:`")
    parser.add_argument("--force", action="store_true", help="allow writing into a non-empty directory")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    out_dir = Path(args.out).expanduser().resolve()
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        print(f"error: {out_dir} is not empty (pass --force to write into it anyway)", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    _copy_tree(BASE_SKILL, out_dir)

    if args.name:
        _substitute_name(out_dir, args.name)
    if args.description:
        _write_description(out_dir, args.description)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
