#!/usr/bin/env python3
"""skill-audit Layer 1 runner.

Thin entry point: resolve the target path and profile, run the registered
Layer 1 checks via the vendored `auditlib` engine plus this repo's
skill-specific checks, write a schema-v2 JSON report, and print
`JSON_PATH=<abs-path>` as the last line of stdout so the invoking agent
(Layer 2) can pick it up.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import argparse  # noqa: E402
import os  # noqa: E402
import tomllib  # noqa: E402

from auditlib import registry  # noqa: E402
from auditlib.checks.artifacts import scorecard as artifact_scorecard_fn  # noqa: E402
from auditlib.config import AuditConfig, load_profile  # noqa: E402
from auditlib.context import TargetForLayer2, build_context  # noqa: E402
from auditlib.report import build_report, write_report  # noqa: E402
from auditlib.runner import build_layer2_targets, run_layer1  # noqa: E402
from auditlib.severity import CheckResult, Severity  # noqa: E402

TOOL_ROOT = SCRIPT_DIR.parent
TOOL_VERSION = "0.2.0"
PROFILE_ALIASES = {"public": "skill-public", "local": "skill-local"}
DEFAULT_PROFILE = "skill-local"
DEFAULT_MAX_LAYER2_BYTES = 262144


def _resolve_profile_name(skill_path: Path, cli_profile: str | None) -> str:
    if cli_profile:
        return PROFILE_ALIASES.get(cli_profile, cli_profile)

    config_path = skill_path / "skill-audit.toml"
    if config_path.exists():
        try:
            data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            data = {}
        declared = data.get("profile")
        if isinstance(declared, str) and declared:
            return PROFILE_ALIASES.get(declared, declared)

    return DEFAULT_PROFILE


def _entry_size(path: Path) -> int:
    try:
        if path.is_dir():
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        if path.is_file():
            return path.stat().st_size
    except OSError:
        pass
    return 0


def _apply_layer2_budget(targets: list[TargetForLayer2], max_bytes: int) -> list[CheckResult]:
    budget_findings: list[CheckResult] = []

    for target in targets:
        sizes = {f: _entry_size(Path(f)) for f in target.files}
        kept = list(target.files)
        dropped: list[str] = []

        while kept and sum(sizes[f] for f in kept) > max_bytes:
            largest = max(kept, key=lambda f: sizes[f])
            kept.remove(largest)
            dropped.append(largest)

        if dropped:
            target.files = kept
            budget_findings.append(
                CheckResult(
                    check=f"layer2.budget.{target.prompt_id}",
                    severity=Severity.INFO,
                    message=f"dropped {len(dropped)} input(s) from '{target.prompt_id}' to fit --max-layer2-bytes",
                    remediation="raise --max-layer2-bytes or trim the referenced file(s)",
                    evidence={"dropped": dropped},
                )
            )

    return budget_findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check.py",
        description="Audit a Claude Code skill against public-release standards.",
    )
    parser.add_argument("skill_path", help="path to the skill directory to audit")
    parser.add_argument(
        "--profile",
        choices=["skill-public", "skill-local", "public", "local"],
        default=None,
        help="profile to apply (default: skill-audit.toml's `profile`, else skill-local)",
    )
    parser.add_argument("--json-out", default=None, help="path to write the JSON report (default: a temp file)")
    parser.add_argument(
        "--max-layer2-bytes",
        type=int,
        default=DEFAULT_MAX_LAYER2_BYTES,
        help="drop the largest layer2 inputs per target until it fits this byte budget",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress the human-readable stderr preamble")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    skill_path = Path(args.skill_path).expanduser().resolve()
    if not skill_path.is_dir():
        print(f"error: skill path is not a directory: {skill_path}", file=sys.stderr)
        return 2

    profile_name = _resolve_profile_name(skill_path, args.profile)
    profile = load_profile(TOOL_ROOT / "profiles", profile_name)
    config = AuditConfig()

    ctx = build_context(
        repo_path=skill_path,
        profile=profile,
        config=config,
        offline=True,
        run_tests=False,
    )

    registry.discover("auditlib.checks")
    registry.discover("checks")

    findings_layer1 = run_layer1(ctx, profile)
    artifact_results = [r for r in findings_layer1 if r.check.startswith("artifacts.")]
    artifact_scorecard = artifact_scorecard_fn(artifact_results)

    prompt_dirs = [TOOL_ROOT / "prompts", TOOL_ROOT / "scripts" / "auditlib" / "prompts"]
    targets_for_layer2 = build_layer2_targets(ctx, profile, prompt_dirs)
    budget_findings = _apply_layer2_budget(targets_for_layer2, args.max_layer2_bytes)
    findings_layer1 = findings_layer1 + budget_findings

    report = build_report(
        tool_version=TOOL_VERSION,
        target_path=str(skill_path),
        target_name=skill_path.name,
        profile_name=profile.name,
        findings_layer1=findings_layer1,
        targets_for_layer2=targets_for_layer2,
        artifact_scorecard=artifact_scorecard,
    )
    report["tool"] = "skill-audit"
    report["kind"] = "skill"

    json_path = write_report(report, args.json_out, prefix="skill-audit")

    if not args.quiet:
        print(
            f"skill-audit: {skill_path.name} (profile={profile.name}) -> {report['gate']}",
            file=sys.stderr,
        )

    print(f"JSON_PATH={json_path}")

    if os.environ.get("SKILL_AUDIT_NEVER_EXIT_NONZERO") == "1":
        return 0
    return 0 if report["gate"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
