from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS, run_check


def _finding(report: dict, check_id: str) -> dict:
    return next(f for f in report["findings_layer1"] if f["check"] == check_id)


def _run_without_profile_flag(target: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check.py"), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line.startswith("JSON_PATH=")
    return json.loads(Path(last_line.split("=", 1)[1]).read_text(encoding="utf-8"))


def test_legacy_public_alias_matches_skill_public(bare_skill: Path) -> None:
    a = run_check(bare_skill, profile="skill-public")
    b = run_check(bare_skill, profile="public")
    assert a["scorecard"] == b["scorecard"]
    assert a["findings_layer1"] == b["findings_layer1"]
    assert a["profile"] == b["profile"] == "skill-public"


def test_legacy_local_alias_matches_skill_local(bare_skill: Path) -> None:
    a = run_check(bare_skill, profile="skill-local")
    b = run_check(bare_skill, profile="local")
    assert a["scorecard"] == b["scorecard"]
    assert a["findings_layer1"] == b["findings_layer1"]
    assert a["profile"] == b["profile"] == "skill-local"


def test_skill_audit_toml_pins_profile(tmp_path: Path) -> None:
    root = tmp_path / "pinned"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: x\ndescription: A skill for testing.\n---\n", encoding="utf-8")
    (root / "skill-audit.toml").write_text('profile = "skill-public"\n', encoding="utf-8")

    report = _run_without_profile_flag(root)
    assert report["profile"] == "skill-public"
    assert _finding(report, "artifacts.readme")["severity"] == "WARN"


def test_default_profile_is_skill_local_without_pin(tmp_path: Path) -> None:
    root = tmp_path / "unpinned"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: x\ndescription: A skill for testing.\n---\n", encoding="utf-8")

    report = _run_without_profile_flag(root)
    assert report["profile"] == "skill-local"
