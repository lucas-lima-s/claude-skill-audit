from __future__ import annotations

from auditlib.context import CheckContext
from auditlib.registry import register
from auditlib.severity import CheckResult, Severity

MIN_DESCRIPTION_LENGTH = 40
MAX_DESCRIPTION_LENGTH = 1024


def _extract_frontmatter(content: str) -> str | None:
    if not content.startswith("---"):
        return None
    lines = content.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return None
    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            closing_idx = i
            break
    if closing_idx is None:
        return None
    return "\n".join(lines[1:closing_idx])


def _scalar_field(frontmatter: str, key: str) -> str | None:
    """Minimal YAML scalar extractor.

    Supports `key: value`, `key: "value"`, `key: 'value'`, folded form
    (`key: >` / `>-`) and literal form (`key: |` / `|-`) with an indented
    body. Does not descend into nested structures -- this check only
    needs top-level scalars.
    """
    lines = frontmatter.splitlines()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped.startswith(f"{key}:"):
            continue
        if line[: len(line) - len(stripped)] != "":
            continue
        rest = stripped[len(key) + 1 :].lstrip()
        if rest in {">", ">-", "|", "|-"}:
            collected: list[str] = []
            for follow in lines[i + 1 :]:
                if follow.startswith(" ") or follow.startswith("\t"):
                    collected.append(follow.strip())
                else:
                    break
            return " ".join(collected)
        if len(rest) >= 2 and rest[0] in "\"'" and rest[-1] == rest[0]:
            return rest[1:-1]
        return rest
    return None


def _has_top_level_field(frontmatter: str, key: str) -> bool:
    for line in frontmatter.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(f"{key}:") and line[: len(line) - len(stripped)] == "":
            return True
    return False


def _has_python_scripts(ctx: CheckContext) -> bool:
    return any(True for _ in ctx.iter_tracked("*.py"))


@register("skill_md")
def run(ctx: CheckContext) -> list[CheckResult]:
    content = ctx.read_text("SKILL.md")
    if content is None:
        return [
            CheckResult(
                check="skill_md.frontmatter",
                severity=Severity.FAIL,
                message="SKILL.md is missing -- without it the skill is not discoverable",
                remediation="add a SKILL.md with `---`-delimited frontmatter and a `description:`",
            )
        ]

    frontmatter = _extract_frontmatter(content)
    if frontmatter is None:
        return [
            CheckResult(
                check="skill_md.frontmatter",
                severity=Severity.FAIL,
                message="SKILL.md has no YAML frontmatter delimited by `---`",
                file="SKILL.md",
                line=1,
                remediation="wrap the frontmatter in `---` lines at the top of the file",
            )
        ]

    description = _scalar_field(frontmatter, "description")
    if description is None or description.strip() == "":
        return [
            CheckResult(
                check="skill_md.frontmatter",
                severity=Severity.FAIL,
                message="SKILL.md frontmatter has no non-empty `description:`",
                file="SKILL.md",
                remediation="add a non-empty `description:` to the frontmatter",
            )
        ]

    results = [
        CheckResult(
            check="skill_md.frontmatter",
            severity=Severity.OK,
            message="frontmatter OK; `description:` present and non-empty",
            file="SKILL.md",
        )
    ]

    length = len(description.strip())
    if length < MIN_DESCRIPTION_LENGTH:
        results.append(
            CheckResult(
                check="skill_md.description_length",
                severity=Severity.INFO,
                message=f"description is only {length} character(s); Claude Code may struggle to trigger on it",
                file="SKILL.md",
                remediation="expand the description with concrete trigger phrases",
            )
        )
    elif length > MAX_DESCRIPTION_LENGTH:
        results.append(
            CheckResult(
                check="skill_md.description_length",
                severity=Severity.INFO,
                message=f"description is {length} characters; Claude Code truncates long descriptions",
                file="SKILL.md",
                remediation="trim the description below 1024 characters",
            )
        )
    else:
        results.append(
            CheckResult(
                check="skill_md.description_length",
                severity=Severity.OK,
                message=f"description length ({length} chars) is within the recommended range",
                file="SKILL.md",
            )
        )

    if _has_python_scripts(ctx) and not _has_top_level_field(frontmatter, "allowed-tools"):
        results.append(
            CheckResult(
                check="skill_md.allowed_tools",
                severity=Severity.INFO,
                message="skill ships scripts/*.py but SKILL.md has no `allowed-tools:`",
                file="SKILL.md",
                remediation="declare `allowed-tools:` scoping the Bash invocations the skill needs",
            )
        )

    return results


__all__ = ["run"]
