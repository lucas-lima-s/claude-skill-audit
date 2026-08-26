from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS, run_check


def test_init_skill_scaffolds_and_audits_clean(tmp_path: Path) -> None:
    out = tmp_path / "new-skill"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "init_skill.py"),
            "--out",
            str(out),
            "--name",
            "my-skill",
            "--description",
            "Does one thing.",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert out.is_dir()

    report = run_check(out, profile="skill-public")
    assert report["scorecard"]["fail"] == 0


def test_init_skill_leaves_no_base_skill_leftovers(tmp_path: Path) -> None:
    out = tmp_path / "no-leftovers"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "init_skill.py"),
            "--out",
            str(out),
            "--name",
            "my-skill",
        ],
        check=False,
    )
    for rel in ("SKILL.md", "README.md", "SETUP.md", "CHANGELOG.md", "pyproject.toml"):
        text = (out / rel).read_text(encoding="utf-8")
        assert "base-skill" not in text
        assert "base_skill" not in text


def test_init_skill_refuses_nonempty_dir_without_force(tmp_path: Path) -> None:
    out = tmp_path / "occupied"
    out.mkdir()
    (out / "existing.txt").write_text("hi\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "init_skill.py"), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2


def test_init_skill_force_writes_into_nonempty_dir(tmp_path: Path) -> None:
    out = tmp_path / "occupied-forced"
    out.mkdir()
    (out / "existing.txt").write_text("hi\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "init_skill.py"), "--out", str(out), "--force"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert (out / "SKILL.md").is_file()


def _fixme_dir(tmp_path: Path) -> Path:
    root = tmp_path / "fixme"
    root.mkdir()
    (root / ".gitattributes").write_text("*.png binary\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0] - 2026-01-01\n\n- initial\n", encoding="utf-8")
    return root


def test_fix_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = _fixme_dir(tmp_path)
    before_attrs = (root / ".gitattributes").stat().st_mtime_ns
    before_changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "fix.py"), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "fix: 2 change(s)" in result.stdout

    assert (root / ".gitattributes").stat().st_mtime_ns == before_attrs
    assert (root / "CHANGELOG.md").read_text(encoding="utf-8") == before_changelog


def test_fix_apply_writes_both_corrections(tmp_path: Path) -> None:
    root = _fixme_dir(tmp_path)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "fix.py"), str(root), "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "* text=auto eol=lf" in (root / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "## [Unreleased]" in (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()


def test_fix_apply_is_idempotent(tmp_path: Path) -> None:
    root = _fixme_dir(tmp_path)
    subprocess.run([sys.executable, str(SCRIPTS / "fix.py"), str(root), "--apply"], check=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "fix.py"), str(root), "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "fix: 0 change(s)" in result.stdout


def test_fix_never_touches_python_source(tmp_path: Path) -> None:
    root = _fixme_dir(tmp_path)
    (root / "scripts").mkdir()
    script = root / "scripts" / "keep_me.py"
    script.write_text("print('unchanged')\n", encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPTS / "fix.py"), str(root), "--apply"], check=False)
    assert script.read_text(encoding="utf-8") == "print('unchanged')\n"
