from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

from auditlib.checks.dev_deps import dev_dependency_names
from auditlib.context import CheckContext
from auditlib.registry import register
from auditlib.severity import CheckResult, Severity

STDLIB = frozenset(sys.stdlib_module_names)
SCAN_PREFIXES = ("scripts/", "tests/")


def _local_top_level_modules(ctx: CheckContext) -> set[str]:
    """Top-level Python module names directly under `scripts/` and `tests/`.

    A directory with `__init__.py` (e.g. `scripts/auditlib/`,
    `scripts/checks/`) or a bare `<dir>/<name>.py` file (e.g.
    `tests/conftest.py`) both count, so the vendored `auditlib` package and
    the test suite's own `conftest` helper never register as undeclared
    dependencies.
    """
    out: set[str] = set()
    for sub in ("scripts", "tests"):
        directory = Path(ctx.repo_path) / sub
        if not directory.exists():
            continue
        for entry in directory.iterdir():
            if entry.is_dir() and (entry / "__init__.py").exists():
                out.add(entry.name)
            elif entry.is_file() and entry.suffix == ".py":
                out.add(entry.stem)
    return out


def _read_allowlist(ctx: CheckContext) -> dict[str, str]:
    text = ctx.read_text("skill-audit.toml")
    if text is None:
        return {}
    try:
        cfg = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    section = cfg.get("runtime_stdlib", {})
    if not isinstance(section, dict):
        return {}
    allow = section.get("allowlist", {})
    if not isinstance(allow, dict):
        return {}
    return {str(k).lower(): str(v).lower() for k, v in allow.items()}


def _is_type_checking_guard(test: ast.expr) -> bool:
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
        return True
    return False


def _top_level_imports(tree: ast.Module) -> list[tuple[str, int]]:
    """Yield (top_module_name, lineno) for absolute imports outside TYPE_CHECKING blocks."""
    out: list[tuple[str, int]] = []

    def visit(node: ast.AST, in_type_checking: bool) -> None:
        if isinstance(node, ast.If) and _is_type_checking_guard(node.test):
            for child in node.body:
                visit(child, True)
            for child in node.orelse:
                visit(child, in_type_checking)
            return
        if isinstance(node, ast.Import) and not in_type_checking:
            for alias in node.names:
                out.append((alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom) and not in_type_checking:
            if node.level == 0 and node.module:
                out.append((node.module.split(".")[0], node.lineno))
        else:
            for child in ast.iter_child_nodes(node):
                visit(child, in_type_checking)

    for node in tree.body:
        visit(node, False)
    return out


def _matches_declared(import_name: str, declared: set[str], allowlist: dict[str, str]) -> bool:
    name = import_name.lower()
    if name in declared:
        return True
    if name in allowlist and allowlist[name] in declared:
        return True
    return False


@register("runtime_stdlib")
def run(ctx: CheckContext) -> list[CheckResult]:
    base = Path(ctx.repo_path)
    py_files = [
        p for p in ctx.iter_tracked("*.py") if str(p.relative_to(base)).replace("\\", "/").startswith(SCAN_PREFIXES)
    ]
    if not py_files:
        return []

    local_modules = _local_top_level_modules(ctx)
    declared = dev_dependency_names(ctx)
    setup_text = (ctx.read_text("SETUP.md") or "").lower()
    allowlist = _read_allowlist(ctx)

    seen: dict[str, str] = {}
    for py_file in py_files:
        try:
            text = py_file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text, filename=str(py_file))
        except (OSError, SyntaxError):
            continue
        rel = str(py_file.relative_to(base)).replace("\\", "/")
        for top_name, lineno in _top_level_imports(tree):
            seen.setdefault(top_name, f"{rel}:{lineno}")

    findings: list[CheckResult] = []
    for top_name, location in sorted(seen.items()):
        if top_name in STDLIB:
            continue
        if top_name in local_modules:
            continue
        if _matches_declared(top_name, declared, allowlist):
            continue
        if top_name.lower() in setup_text:
            continue
        file_part, _, line_part = location.partition(":")
        findings.append(
            CheckResult(
                check="runtime_stdlib.import",
                severity=Severity.WARN,
                message=(
                    f"import `{top_name}` is not declared as a dev dependency, "
                    "in SETUP.md, or in skill-audit.toml's allowlist"
                ),
                file=file_part,
                line=int(line_part) if line_part.isdigit() else None,
                remediation=(
                    "declare it in [dependency-groups].dev, mention it in SETUP.md, "
                    "or add it to [runtime_stdlib.allowlist]"
                ),
            )
        )

    if not findings:
        findings.append(
            CheckResult(
                check="runtime_stdlib.import",
                severity=Severity.OK,
                message="all non-stdlib imports are accounted for",
            )
        )
    return findings


__all__ = ["run"]
