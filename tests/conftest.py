from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = TOOL_ROOT / "scripts"
PYTHON = sys.executable


def run_check(target: Path, profile: str = "skill-public", **extra_args: str) -> dict:
    """Shell `check.py` against `target` and return the parsed JSON report.

    Asserts the JSON_PATH contract along the way: the last line of stdout
    always starts with `JSON_PATH=`.
    """
    args = [PYTHON, str(SCRIPTS / "check.py"), str(target), "--profile", profile]
    for key, value in extra_args.items():
        args.extend([f"--{key.replace('_', '-')}", str(value)])
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line.startswith("JSON_PATH="), f"unexpected stdout: {result.stdout!r}"
    json_path = Path(last_line.split("=", 1)[1])
    report = json.loads(json_path.read_text(encoding="utf-8"))
    report["_returncode"] = result.returncode
    return report


@pytest.fixture
def base_skill() -> Path:
    return TOOL_ROOT / "examples" / "base_skill"


@pytest.fixture
def bare_skill(tmp_path: Path) -> Path:
    """A skill with only the absolute minimum (SKILL.md with a description)."""
    root = tmp_path / "bare"
    root.mkdir()
    (root / "SKILL.md").write_text(
        "---\nname: bare\ndescription: A minimal skill for testing.\n---\n\n# bare\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def malformed_skill(tmp_path: Path) -> Path:
    """A skill with files present but malformed (triggers FAIL paths)."""
    root = tmp_path / "malformed"
    root.mkdir()
    (root / "SKILL.md").write_text("no frontmatter here\n", encoding="utf-8")

    # [tool.ruff] partially configured, [tool.black] absent -> pyproject.format FAIL
    # is reserved for "no tooling at all"; here we test the true FAIL path by
    # omitting [tool] entirely.
    (root / "pyproject.toml").write_text(
        '[project]\nname = "broken"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    (root / "scripts").mkdir()
    # Build the leak content from chunks so the literal path never appears in
    # this source file's text (prevents a false positive on self-audit).
    drive = "C:"  # repo-audit: allow-path
    leak_path = drive + "/Users/lucas/secret"  # repo-audit: allow-path
    leak_content = 'from __future__ import annotations\nP = "' + leak_path + '"\n'
    (root / "scripts" / "leak.py").write_text(leak_content, encoding="utf-8")
    return root


__all__ = ["run_check", "base_skill", "bare_skill", "malformed_skill", "TOOL_ROOT", "SCRIPTS", "PYTHON"]
