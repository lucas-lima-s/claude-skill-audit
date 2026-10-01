from __future__ import annotations

from pathlib import Path

from conftest import run_check


def _finding(report: dict, check_id: str) -> dict:
    return next(f for f in report["findings_layer1"] if f["check"] == check_id)


def _findings(report: dict, check_id: str) -> list[dict]:
    return [f for f in report["findings_layer1"] if f["check"] == check_id]


# --- artifacts.* / profile downgrade ---


def test_artifacts_readme_warns_under_public(bare_skill: Path) -> None:
    report = run_check(bare_skill, profile="skill-public")
    assert _finding(report, "artifacts.readme")["severity"] == "WARN"


def test_artifacts_readme_downgrades_to_info_under_local(bare_skill: Path) -> None:
    report = run_check(bare_skill, profile="skill-local")
    assert _finding(report, "artifacts.readme")["severity"] == "INFO"


def test_artifacts_present_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert report["scorecard"]["present"] == report["scorecard"]["total"] == 14


# --- gitattributes.eol ---


def test_gitattributes_eol_warns_when_missing(tmp_path: Path) -> None:
    root = tmp_path / "no-eol"
    root.mkdir()
    (root / ".gitattributes").write_text("*.png binary\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "gitattributes.eol")["severity"] == "WARN"


def test_gitattributes_eol_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert not _findings(report, "gitattributes.eol")


# --- gitignore.coverage ---


def test_gitignore_coverage_warns_on_empty_file(tmp_path: Path) -> None:
    root = tmp_path / "empty-gitignore"
    root.mkdir()
    (root / ".gitignore").write_text("", encoding="utf-8")
    report = run_check(root)
    hits = _findings(report, "gitignore.coverage")
    assert any("log files" in f["message"] for f in hits)


def test_gitignore_coverage_clean_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert not _findings(report, "gitignore.coverage")


# --- pyproject.format ---


def test_pyproject_format_ok_with_ruff_and_format_section(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "pyproject.format")["severity"] == "OK"


def test_pyproject_format_warns_with_linter_but_no_formatter(tmp_path: Path) -> None:
    root = tmp_path / "ruff-only"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "x"\nrequires-python = ">=3.11"\n\n[tool.ruff]\nline-length = 120\n',
        encoding="utf-8",
    )
    report = run_check(root)
    assert _finding(report, "pyproject.format")["severity"] == "WARN"


def test_pyproject_format_fails_with_no_tooling(malformed_skill: Path) -> None:
    report = run_check(malformed_skill)
    assert _finding(report, "pyproject.format")["severity"] == "FAIL"


def test_pyproject_format_fails_on_broken_toml(tmp_path: Path) -> None:
    root = tmp_path / "broken-toml"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project\nname = x\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "pyproject.format")["severity"] == "FAIL"


# --- dev_deps.declared ---


def test_dev_deps_declared_via_dependency_groups(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "dev_deps.declared")["severity"] == "OK"


def test_dev_deps_declared_via_requirements_dev_txt(tmp_path: Path) -> None:
    root = tmp_path / "legacy-reqs"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    (root / "requirements-dev.txt").write_text("pytest>=8.0\n", encoding="utf-8")
    (root / "tests").mkdir()
    report = run_check(root)
    assert _finding(report, "dev_deps.declared")["severity"] == "OK"


# --- ci_workflow.matrix ---


def test_ci_workflow_matrix_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "ci_workflow.matrix")["severity"] == "OK"


def test_ci_workflow_matrix_warns_when_incomplete(tmp_path: Path) -> None:
    root = tmp_path / "bad-ci"
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    report = run_check(root)
    assert _finding(report, "ci_workflow.matrix")["severity"] == "WARN"


# --- changelog.format ---


def test_changelog_format_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "changelog.format")["severity"] == "OK"


def test_changelog_format_warns_without_unreleased(tmp_path: Path) -> None:
    root = tmp_path / "no-unreleased"
    root.mkdir()
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0] - 2026-01-01\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "changelog.format")["severity"] == "WARN"


# --- python_style.future / .typing_aliases ---


def test_python_style_future_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert not [f for f in _findings(report, "python_style.future") if f["severity"] != "OK"]


def test_python_style_future_warns_when_missing(tmp_path: Path) -> None:
    root = tmp_path / "no-future"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "python_style.future")["severity"] == "WARN"


def test_python_style_typing_aliases_warns_on_deprecated_import(tmp_path: Path) -> None:
    root = tmp_path / "deprecated-typing"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "main.py").write_text(
        "from __future__ import annotations\n\nfrom typing import List\n\nx: List[int] = []\n",
        encoding="utf-8",
    )
    report = run_check(root)
    assert _finding(report, "python_style.typing_aliases")["severity"] == "WARN"


def test_python_style_typing_aliases_clean_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert not _findings(report, "python_style.typing_aliases")


# --- hardcoded_paths.literal ---


def test_hardcoded_paths_detects_windows_literal(malformed_skill: Path) -> None:
    hits = run_check(malformed_skill)["findings_layer1"]
    matches = [f for f in hits if f["check"] == "hardcoded_paths.literal"]
    assert matches and all(f["severity"] == "FAIL" for f in matches)


def test_hardcoded_paths_clean_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert not _findings(report, "hardcoded_paths.literal")


def test_hardcoded_paths_detects_regex_encoded_home(tmp_path: Path) -> None:
    root = tmp_path / "regex-home"
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: regex-home\ndescription: A skill for testing.\n---\n", encoding="utf-8")
    slash_class = "[" + ("\\" * 2) + "/]+"
    payload = 'PATTERN = r"C:' + slash_class + "Users" + slash_class + 'someone"\n'
    (root / "scripts" / "hygiene.py").write_text(payload, encoding="utf-8")
    hits = _findings(run_check(root), "hardcoded_paths.literal")
    assert hits and all(f["severity"] == "FAIL" for f in hits)
