#!/usr/bin/env python3
"""Mechanical, judgement-free corrections for a skill directory.

Each fix has exactly one correct answer: append the missing eol line to an
existing `.gitattributes`, insert `## [Unreleased]` into a `CHANGELOG.md`
that already has a `# Changelog` header, and cover the Python bytecode
cache in a `.gitignore` that lacks it on a skill that ships `scripts/*.py`.
Never touches `SKILL.md`, `README.md`, or any Python source. Default is
dry-run: prints a unified diff and writes nothing. Pass `--apply` to write.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

EOL_LINE = "* text=auto eol=lf"
CHANGELOG_HEADER = "# Changelog"
UNRELEASED_HEADER = "## [Unreleased]"
GITIGNORE_PYTHON_LINES = ("__pycache__/", "*.py[cod]")

Change = tuple[Path, str, str]


def _diff(path: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
        )
    )


def _fix_gitattributes(skill_path: Path) -> Change | None:
    target = skill_path / ".gitattributes"
    if not target.exists():
        return None
    before = target.read_text(encoding="utf-8")
    if EOL_LINE in before.splitlines():
        return None
    after = before
    if after and not after.endswith("\n"):
        after += "\n"
    after += EOL_LINE + "\n"
    return target, before, after


def _fix_changelog(skill_path: Path) -> Change | None:
    target = skill_path / "CHANGELOG.md"
    if not target.exists():
        return None
    before = target.read_text(encoding="utf-8")
    lines = before.splitlines()
    if any(line.strip() == UNRELEASED_HEADER for line in lines):
        return None
    header_idx = next(
        (i for i, line in enumerate(lines[:10]) if line.strip().startswith(CHANGELOG_HEADER)),
        None,
    )
    if header_idx is None:
        return None
    new_lines = [*lines[: header_idx + 1], "", UNRELEASED_HEADER, *lines[header_idx + 1 :]]
    after = "\n".join(new_lines)
    if before.endswith("\n"):
        after += "\n"
    return target, before, after


def _is_python_skill(skill_path: Path) -> bool:
    scripts = skill_path / "scripts"
    return scripts.exists() and any(scripts.rglob("*.py"))


def _fix_gitignore(skill_path: Path) -> Change | None:
    target = skill_path / ".gitignore"
    if not target.exists() or not _is_python_skill(skill_path):
        return None
    before = target.read_text(encoding="utf-8")
    present = {line.strip() for line in before.splitlines()}
    missing = [line for line in GITIGNORE_PYTHON_LINES if line not in present]
    if not missing:
        return None
    after = before
    if after and not after.endswith("\n"):
        after += "\n"
    after += "\n".join(missing) + "\n"
    return target, before, after


FIXERS = (_fix_gitattributes, _fix_changelog, _fix_gitignore)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fix.py",
        description="Apply mechanical, judgement-free corrections to a skill directory.",
    )
    parser.add_argument("skill_path")
    parser.add_argument("--dry-run", action="store_true", help="print the diff and write nothing (default)")
    parser.add_argument("--apply", action="store_true", help="write the changes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    skill_path = Path(args.skill_path).expanduser().resolve()
    if not skill_path.is_dir():
        print(f"error: skill path is not a directory: {skill_path}", file=sys.stderr)
        return 2

    changes = [c for c in (fixer(skill_path) for fixer in FIXERS) if c is not None]

    for target, before, after in changes:
        print(_diff(target, before, after), end="")

    if args.apply:
        for target, _before, after in changes:
            target.write_text(after, encoding="utf-8", newline="\n")

    print(f"fix: {len(changes)} change(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
