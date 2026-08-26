from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS

NON_ENGLISH_RE = re.compile(r"artefatos|Camada|achados", re.IGNORECASE)


def _write_report(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "report.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _run_report(json_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "report.py"), "--json", str(json_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_report_renders_scorecard_and_summary(base_skill: Path, tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check.py"),
            str(base_skill),
            "--profile",
            "skill-public",
            "--json-out",
            str(tmp_path / "base.json"),
        ],
        check=False,
    )
    result = _run_report(tmp_path / "base.json")
    assert result.returncode == 0
    assert re.search(r"^Polish scorecard: \d+ / 14 artifacts present$", result.stdout, re.MULTILINE)
    assert "Summary:" in result.stdout


def test_report_is_english_only(malformed_skill: Path, tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check.py"),
            str(malformed_skill),
            "--profile",
            "skill-public",
            "--json-out",
            str(tmp_path / "malformed.json"),
        ],
        check=False,
    )
    result = _run_report(tmp_path / "malformed.json")
    assert not NON_ENGLISH_RE.search(result.stdout)


def test_report_exits_one_on_fail(malformed_skill: Path, tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check.py"),
            str(malformed_skill),
            "--profile",
            "skill-public",
            "--json-out",
            str(tmp_path / "malformed.json"),
        ],
        check=False,
    )
    result = _run_report(tmp_path / "malformed.json")
    assert result.returncode == 1


def test_report_exits_two_on_missing_file(tmp_path: Path) -> None:
    result = _run_report(tmp_path / "does-not-exist.json")
    assert result.returncode == 2


def test_report_exits_two_on_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    result = _run_report(path)
    assert result.returncode == 2


def test_report_exits_two_on_unsupported_schema_version(tmp_path: Path) -> None:
    path = _write_report(tmp_path, {"schema_version": 1})
    result = _run_report(path)
    assert result.returncode == 2


def test_report_exits_zero_on_clean_report(base_skill: Path, tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check.py"),
            str(base_skill),
            "--profile",
            "skill-public",
            "--json-out",
            str(tmp_path / "base.json"),
        ],
        check=False,
    )
    result = _run_report(tmp_path / "base.json")
    assert result.returncode == 0
