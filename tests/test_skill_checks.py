from __future__ import annotations

from pathlib import Path

from conftest import run_check


def _finding(report: dict, check_id: str) -> dict:
    return next(f for f in report["findings_layer1"] if f["check"] == check_id)


def _findings(report: dict, check_id: str) -> list[dict]:
    return [f for f in report["findings_layer1"] if f["check"] == check_id]


# --- skill_md.frontmatter ---


def test_skill_md_frontmatter_fails_when_missing(tmp_path: Path) -> None:
    root = tmp_path / "no-skill-md"
    root.mkdir()
    report = run_check(root)
    assert _finding(report, "skill_md.frontmatter")["severity"] == "FAIL"


def test_skill_md_frontmatter_passes_on_valid_description(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "skill_md.frontmatter")["severity"] == "OK"


def test_skill_md_frontmatter_fails_when_no_frontmatter_block(malformed_skill: Path) -> None:
    report = run_check(malformed_skill)
    assert _finding(report, "skill_md.frontmatter")["severity"] == "FAIL"


# --- skill_md.description_length ---


def test_description_length_info_when_too_short(tmp_path: Path) -> None:
    root = tmp_path / "short-desc"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: x\ndescription: short.\n---\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "skill_md.description_length")["severity"] == "INFO"


def test_description_length_ok_when_in_range(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "skill_md.description_length")["severity"] == "OK"


def test_description_length_warns_when_too_long(tmp_path: Path) -> None:
    root = tmp_path / "long-desc"
    root.mkdir()
    long_description = "x" * 1200
    (root / "SKILL.md").write_text(f"---\nname: x\ndescription: {long_description}\n---\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "skill_md.description_length")["severity"] == "WARN"


def test_description_length_warns_above_listing_budget(tmp_path: Path) -> None:
    root = tmp_path / "listing-desc"
    root.mkdir()
    (root / "SKILL.md").write_text(f"---\nname: x\ndescription: {'y' * 301}\n---\n", encoding="utf-8")
    finding = _finding(run_check(root), "skill_md.description_length")
    assert finding["severity"] == "WARN"
    assert "301" in finding["message"]


def test_description_length_ok_at_listing_budget(tmp_path: Path) -> None:
    root = tmp_path / "budget-desc"
    root.mkdir()
    (root / "SKILL.md").write_text(f"---\nname: x\ndescription: {'y' * 300}\n---\n", encoding="utf-8")
    assert _finding(run_check(root), "skill_md.description_length")["severity"] == "OK"


def _skill(tmp_path: Path, dirname: str, name: str, body: str = "") -> Path:
    root = tmp_path / dirname
    root.mkdir()
    (root / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: A skill used to exercise the SKILL.md checks.\n---\n\n{body}",
        encoding="utf-8",
    )
    return root


def test_skill_md_size_warns_above_500_lines(tmp_path: Path) -> None:
    root = _skill(tmp_path, "big", "big", "line\n" * 520)
    assert _finding(run_check(root), "skill_md.size")["severity"] == "WARN"


def test_skill_md_size_silent_on_base_skill(base_skill: Path) -> None:
    assert not _findings(run_check(base_skill), "skill_md.size")


def test_name_mismatch_with_directory_warns(tmp_path: Path) -> None:
    root = _skill(tmp_path, "audit", "skill-audit")
    assert _finding(run_check(root), "skill_md.name_matches_dir")["severity"] == "WARN"


def test_name_matches_directory_after_install_prefix(tmp_path: Path) -> None:
    root = _skill(tmp_path, "claude-skill-audit", "audit")
    assert not _findings(run_check(root), "skill_md.name_matches_dir")


def test_name_matches_base_skill_with_underscore_directory(base_skill: Path) -> None:
    assert not _findings(run_check(base_skill), "skill_md.name_matches_dir")


def test_claude_only_tools_without_alternative_is_info(tmp_path: Path) -> None:
    root = _skill(tmp_path, "porty", "porty", "Use AskUserQuestion, then run `/porty`.\n")
    finding = _finding(run_check(root), "skill_md.claude_only_tools")
    assert finding["severity"] == "INFO"
    assert "AskUserQuestion" in finding["message"]


def test_claude_only_tools_with_alternative_is_silent(tmp_path: Path) -> None:
    body = "Use AskUserQuestion; in Codex, agy or Cursor ask the question in chat.\n"
    root = _skill(tmp_path, "porty", "porty", body)
    assert not _findings(run_check(root), "skill_md.claude_only_tools")


# --- skill_layout.* ---


def test_skill_layout_root_python_warns(tmp_path: Path) -> None:
    root = tmp_path / "root-py"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: x\ndescription: A skill for testing.\n---\n", encoding="utf-8")
    (root / "stray.py").write_text("print('hi')\n", encoding="utf-8")
    report = run_check(root)
    assert _finding(report, "skill_layout.root_python")["severity"] == "WARN"


def test_skill_layout_root_python_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "skill_layout.root_python")["severity"] == "OK"


def test_skill_layout_tmp_tracked_ok_when_untracked(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "skill_layout.tmp_tracked")["severity"] == "OK"


def test_skill_layout_broken_script_ref_warns(tmp_path: Path) -> None:
    root = tmp_path / "broken-ref"
    root.mkdir()
    (root / "SKILL.md").write_text(
        "---\nname: x\ndescription: A skill for testing.\n---\n\nRun `scripts/missing.py`.\n",
        encoding="utf-8",
    )
    report = run_check(root)
    assert _finding(report, "skill_layout.broken_script_ref")["severity"] == "WARN"


def test_skill_layout_broken_script_ref_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    assert _finding(report, "skill_layout.broken_script_ref")["severity"] == "OK"


# --- runtime_stdlib.import ---


def test_runtime_stdlib_warns_on_undeclared_import(tmp_path: Path) -> None:
    root = tmp_path / "undeclared-import"
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: x\ndescription: A skill for testing.\n---\n", encoding="utf-8")
    (root / "scripts" / "main.py").write_text(
        "from __future__ import annotations\n\nimport definitely_not_a_real_package\n",
        encoding="utf-8",
    )
    report = run_check(root)
    hits = _findings(report, "runtime_stdlib.import")
    assert any(f["severity"] == "WARN" for f in hits)


def test_runtime_stdlib_ok_when_allowlisted(tmp_path: Path) -> None:
    root = tmp_path / "allowlisted-import"
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: x\ndescription: A skill for testing.\n---\n", encoding="utf-8")
    (root / "scripts" / "main.py").write_text(
        "from __future__ import annotations\n\nimport totally_custom_dep\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        '[dependency-groups]\ndev = ["totally-custom-dep"]\n',
        encoding="utf-8",
    )
    (root / "skill-audit.toml").write_text(
        '[runtime_stdlib.allowlist]\ntotally_custom_dep = "totally-custom-dep"\n',
        encoding="utf-8",
    )
    report = run_check(root)
    hits = _findings(report, "runtime_stdlib.import")
    assert all(f["severity"] == "OK" for f in hits)


def test_runtime_stdlib_ignores_type_checking_imports(tmp_path: Path) -> None:
    root = tmp_path / "type-checking-import"
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: x\ndescription: A skill for testing.\n---\n", encoding="utf-8")
    (root / "scripts" / "main.py").write_text(
        "from __future__ import annotations\n\n"
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    import never_installed_type_only_dep\n",
        encoding="utf-8",
    )
    report = run_check(root)
    hits = _findings(report, "runtime_stdlib.import")
    assert all(f["severity"] == "OK" for f in hits)


def test_runtime_stdlib_ok_on_base_skill(base_skill: Path) -> None:
    report = run_check(base_skill)
    hits = _findings(report, "runtime_stdlib.import")
    assert hits and all(f["severity"] == "OK" for f in hits)
