from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS, run_check

EXPECTED_PROMPT_IDS = (
    "readme_quality",
    "setup_completeness",
    "changelog_significance",
    "language_coherence",
    "aspiration_to_base_skill",
)


def test_required_keys_present(base_skill: Path) -> None:
    report = run_check(base_skill)
    for key in (
        "schema_version",
        "tool",
        "tool_version",
        "kind",
        "target_path",
        "target_name",
        "profile",
        "gate",
        "scorecard",
        "findings_layer1",
        "targets_for_layer2",
        "findings_layer2",
    ):
        assert key in report


def test_schema_version_and_tool(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert report["schema_version"] == 2
    assert report["tool"] == "skill-audit"


def test_json_path_is_last_line_of_stdout(base_skill: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check.py"), str(base_skill), "--profile", "skill-public"],
        capture_output=True,
        text=True,
        check=False,
    )
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line.startswith("JSON_PATH=")


def test_exit_code_zero_when_clean(base_skill: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check.py"), str(base_skill), "--profile", "skill-public"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_exit_code_one_on_fail(malformed_skill: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check.py"), str(malformed_skill), "--profile", "skill-public"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1


def test_exit_code_two_on_bad_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check.py"), str(missing)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2


def test_never_exit_nonzero_env_forces_zero(malformed_skill: Path) -> None:
    env = dict(os.environ, SKILL_AUDIT_NEVER_EXIT_NONZERO="1")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check.py"), str(malformed_skill), "--profile", "skill-public"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0


def test_layer2_targets_populated_with_existing_prompt_files(base_skill: Path) -> None:
    report = run_check(base_skill)
    targets = report["targets_for_layer2"]
    assert len(targets) == 5
    ids = tuple(t["prompt_id"] for t in targets)
    assert ids == EXPECTED_PROMPT_IDS
    for target in targets:
        assert Path(target["prompt_file"]).is_file()


def test_findings_layer2_starts_empty(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert report["findings_layer2"] == []


def test_max_layer2_bytes_emits_budget_info(base_skill: Path) -> None:
    report = run_check(base_skill, max_layer2_bytes="1")
    hits = [f for f in report["findings_layer1"] if f["check"].startswith("layer2.budget")]
    assert hits
    assert all(f["severity"] == "INFO" for f in hits)
