from __future__ import annotations

import re
from pathlib import Path

from auditlib.context import CheckContext
from auditlib.registry import register
from auditlib.severity import CheckResult, Severity

SCRIPT_REF_RE = re.compile(r"scripts/[\w./-]+?\.py")
TMP_DIR_NAMES = ("scripts/_tmp", "data/_tmp")


def _root_python_files(ctx: CheckContext) -> list[str]:
    base = Path(ctx.repo_path)
    return sorted(entry.name for entry in base.iterdir() if entry.is_file() and entry.suffix == ".py")


def _tracked_tmp_dirs(ctx: CheckContext) -> list[str]:
    hits: set[str] = set()
    for tracked in ctx.tracked_files:
        rel = tracked.replace("\\", "/")
        for tmp_dir in TMP_DIR_NAMES:
            if rel == tmp_dir or rel.startswith(f"{tmp_dir}/"):
                hits.add(tmp_dir)
    return sorted(hits)


def _referenced_script_paths(ctx: CheckContext) -> list[str]:
    text = ctx.read_text("SKILL.md") or ""
    return sorted(set(SCRIPT_REF_RE.findall(text)))


@register("skill_layout")
def run(ctx: CheckContext) -> list[CheckResult]:
    results: list[CheckResult] = []

    root_files = _root_python_files(ctx)
    if root_files:
        results.append(
            CheckResult(
                check="skill_layout.root_python",
                severity=Severity.WARN,
                message=f"{len(root_files)} *.py file(s) sit at the skill root instead of under scripts/",
                file=root_files[0],
                remediation="move top-level Python files under scripts/",
                evidence={"files": root_files},
            )
        )
    else:
        results.append(
            CheckResult(
                check="skill_layout.root_python",
                severity=Severity.OK,
                message="no *.py files at the skill root",
            )
        )

    tmp_dirs = _tracked_tmp_dirs(ctx)
    if tmp_dirs:
        results.append(
            CheckResult(
                check="skill_layout.tmp_tracked",
                severity=Severity.INFO,
                message=f"{', '.join(tmp_dirs)} is tracked in git",
                remediation="gitignore scripts/_tmp/ and data/_tmp/ -- they are scratch space, not canonical artifacts",
                evidence={"dirs": tmp_dirs},
            )
        )
    else:
        results.append(
            CheckResult(
                check="skill_layout.tmp_tracked",
                severity=Severity.OK,
                message="no scripts/_tmp/ or data/_tmp/ tracked",
            )
        )

    if ctx.exists("SKILL.md"):
        missing = [ref for ref in _referenced_script_paths(ctx) if not ctx.exists(ref)]
        if missing:
            results.append(
                CheckResult(
                    check="skill_layout.broken_script_ref",
                    severity=Severity.WARN,
                    message=f"SKILL.md references {len(missing)} script path(s) that do not exist on disk",
                    file="SKILL.md",
                    remediation="fix the path or remove the reference",
                    evidence={"paths": missing},
                )
            )
        else:
            results.append(
                CheckResult(
                    check="skill_layout.broken_script_ref",
                    severity=Severity.OK,
                    message="every scripts/*.py path referenced in SKILL.md exists on disk",
                    file="SKILL.md",
                )
            )

    return results


__all__ = ["run"]
