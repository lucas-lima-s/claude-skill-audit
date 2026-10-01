#!/usr/bin/env python3
"""Render a skill-audit JSON report as markdown.

Thin wrapper over `auditlib.report.load_and_validate` + `render_markdown`.
English output only -- see docs/rules.md for what each check id means.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from auditlib.report import load_and_validate, render_markdown  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="report.py", description="Render a skill-audit JSON report as markdown.")
    parser.add_argument("--json", required=True, help="path to the report JSON written by check.py")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    path = Path(args.json).expanduser()

    if not path.exists():
        print(f"error: report file not found: {path}", file=sys.stderr)
        return 2

    try:
        report = load_and_validate(str(path))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {path}: {exc}", file=sys.stderr)
        return 2
    except SystemExit:
        print(f"error: unsupported schema_version in {path} (expected 2)", file=sys.stderr)
        return 2

    rendered = render_markdown(report)
    rendered = rendered.replace("repo-audit: ", "skill-audit: ", 1)
    print(rendered)

    layer1 = report.get("findings_layer1", [])
    has_fail = any(str(f.get("severity", "")).upper() == "FAIL" for f in layer1)
    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
