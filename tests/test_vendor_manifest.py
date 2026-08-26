from __future__ import annotations

import subprocess
import sys

from conftest import SCRIPTS, TOOL_ROOT, run_check


def _run_sync_check() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "sync_auditlib.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_vendor_manifest_clean_on_committed_tree() -> None:
    result = _run_sync_check()
    assert result.returncode == 0
    assert "auditlib: 0 drifted files" in result.stdout


def test_vendor_manifest_catches_tampering() -> None:
    target = TOOL_ROOT / "scripts" / "auditlib" / "severity.py"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n")
        result = _run_sync_check()
        assert result.returncode == 1
        assert "scripts/auditlib/severity.py" in result.stdout
    finally:
        target.write_bytes(original)

    assert _run_sync_check().returncode == 0


def test_dogfood_self_audit_has_zero_fail() -> None:
    report = run_check(TOOL_ROOT, profile="skill-public")
    assert report["scorecard"]["fail"] == 0
