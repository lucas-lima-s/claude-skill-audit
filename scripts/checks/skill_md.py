from __future__ import annotations

import re
from pathlib import Path

from auditlib.context import CheckContext
from auditlib.registry import register
from auditlib.severity import CheckResult, Severity

MIN_DESCRIPTION_LENGTH = 40
LISTING_DESCRIPTION_LENGTH = 300
MAX_DESCRIPTION_LENGTH = 1024
MAX_SKILL_MD_LINES = 500
INSTALL_PREFIXES = ("claude-skill-", "skill-")
CLAUDE_ONLY_PATTERNS = (
    re.compile(r"\bAgent tool\b"),
    re.compile(r"\bAskUserQuestion\b"),
    re.compile(r"\bTodoWrite\b"),
    re.compile(r"\b(?:EnterPlanMode|ExitPlanMode)\b"),
    re.compile(r"\bplan mode\b", re.IGNORECASE),
    re.compile(r"\bSkill tool\b"),
    re.compile(r"`/[a-z][a-z0-9-]*(?::[a-z0-9-]+)?`"),
)
OTHER_AGENT_MARKERS = re.compile(r"\b(?:Codex|agy|Antigravity|Cursor|other agents?)\b", re.IGNORECASE)


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
    if length > LISTING_DESCRIPTION_LENGTH:
        truncated = length > MAX_DESCRIPTION_LENGTH
        detail = "agents truncate long descriptions" if truncated else "it crowds the skill listing"
        results.append(
            CheckResult(
                check="skill_md.description_length",
                severity=Severity.WARN,
                message=f"description is {length} characters (target {LISTING_DESCRIPTION_LENGTH}); {detail}",
                file="SKILL.md",
                remediation="keep what the skill does and when, main trigger first; drop implementation detail",
            )
        )
    elif length < MIN_DESCRIPTION_LENGTH:
        results.append(
            CheckResult(
                check="skill_md.description_length",
                severity=Severity.INFO,
                message=f"description is only {length} character(s); Claude Code may struggle to trigger on it",
                file="SKILL.md",
                remediation="expand the description with concrete trigger phrases",
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

    results.extend(_size_result(content))
    results.extend(_name_result(ctx, frontmatter))
    results.extend(_portability_result(content))
    return results


def _size_result(content: str) -> list[CheckResult]:
    lines = len(content.splitlines())
    if lines <= MAX_SKILL_MD_LINES:
        return []
    return [
        CheckResult(
            check="skill_md.size",
            severity=Severity.WARN,
            message=f"SKILL.md has {lines} lines (target {MAX_SKILL_MD_LINES}); it is loaded on every invocation",
            file="SKILL.md",
            remediation="keep the routing logic in SKILL.md and move long sections to references/",
        )
    ]


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _name_result(ctx: CheckContext, frontmatter: str) -> list[CheckResult]:
    name = _scalar_field(frontmatter, "name")
    if not name:
        return []
    directory = _normalized(Path(ctx.repo_path).resolve().name)
    candidates = {directory}
    for prefix in INSTALL_PREFIXES:
        if directory.startswith(prefix):
            candidates.add(directory.removeprefix(prefix))
    if _normalized(name) in candidates:
        return []
    return [
        CheckResult(
            check="skill_md.name_matches_dir",
            severity=Severity.WARN,
            message=f"frontmatter `name: {name}` does not match the skill directory `{Path(ctx.repo_path).name}`",
            file="SKILL.md",
            remediation="align `name:` with the directory the skill is installed under, so triggers match the command",
        )
    ]


def _portability_result(content: str) -> list[CheckResult]:
    hits = sorted({m.group(0) for pattern in CLAUDE_ONLY_PATTERNS for m in pattern.finditer(content)})
    if not hits or OTHER_AGENT_MARKERS.search(content):
        return []
    return [
        CheckResult(
            check="skill_md.claude_only_tools",
            severity=Severity.INFO,
            message="SKILL.md relies on Claude Code-only tools with no note for other agents: " + ", ".join(hits),
            file="SKILL.md",
            remediation="say what Codex, agy or Cursor do instead (sequential steps, a plain question in chat)",
        )
    ]


__all__ = ["run"]
