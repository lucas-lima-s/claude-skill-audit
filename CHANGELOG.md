# Changelog

All notable changes to `skill-audit` are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-08-25

### Changed

- Extracted the shared engine (severity model, config/profile loader,
  registry, runner, reporting, and the generic checks) into
  `claude-skill-repo-audit`'s `scripts/auditlib/`, vendored here verbatim
  under a sha256 checksum manifest (`scripts/auditlib/_vendor_manifest.json`)
  and a CI drift gate (`scripts/sync_auditlib.py --check`).
- Replaced the two hand-rolled profile modules with data-driven
  `profiles/skill-public.toml` and `profiles/skill-local.toml`
  (`[artifacts]`, `enabled_checks`, `layer2_prompts`,
  `downgrade_warn_to_info`). `--profile public` / `--profile local` are
  now accepted as compatibility aliases.
- Bumped the JSON report to **schema v2**: `tool`, `tool_version`, `kind`,
  `generated_at`, and a `findings_layer1[].evidence` field; see
  `docs/json_contract.md`.
- `requirements-dev.txt` + `black` replaced by `[dependency-groups].dev`
  and `ruff format` (both the tool itself and `examples/base_skill/`).
  `pyproject.format` now accepts either `[tool.ruff]` or `[tool.black]` --
  it only `FAIL`s when neither is configured.
- `scripts/report.py` renders **English only**
  ("`Polish scorecard: N / 14 artifacts present`", "`Summary:`");
  the source skill's pt-BR renderer strings are gone.

### Added

- `scripts/init_skill.py --out DIR [--name NAME] [--description TEXT]
  [--force]`: scaffolds a new skill from `examples/base_skill/`.
- `scripts/fix.py <skill-path> [--apply]`: mechanical, judgement-free
  corrections (`.gitattributes` eol line, `## [Unreleased]` header,
  Python-cache `.gitignore` coverage). Dry-run by default.
- `--max-layer2-bytes` (default `262144`) on `scripts/check.py`: drops the
  largest layer-2 inputs per target until it fits the budget and records
  a `layer2.budget.<prompt_id>` INFO finding naming what was skipped.
- `skill_md.description_length` and `skill_md.allowed_tools` checks.
- `skill_layout.*`: deterministic checks for root-level `*.py` files,
  tracked `_tmp/` scratch directories, and broken `scripts/*.py`
  references inside `SKILL.md`.
- `docs/rules.md`, replacing `docs/ground_truth.md`: one section per check
  id (what it checks, severity per profile, why it matters, how to fix),
  with no reference to any private skill or machine path.
- `docs/demo-light.svg` / `docs/demo-dark.svg` scorecard preview, rendered
  by `scripts/render_demo.py`.

### Removed

- `ROADMAP.md` and the `roadmap` artifact rule -- the scorecard should not
  reward a deferred-work document it audits against. Its five open items
  are now either implemented (`--init`, `--fix`, `--max-layer2-bytes`) or
  retired along with the document they depended on
  (`docs/ground_truth.md`'s auto-validation idea).
- `requirements-dev.txt` (repo and `examples/base_skill/`).

## [0.1.0] - 2026-05-01

### Initial release

- **Layer 1 -- deterministic checks** in `scripts/check.py` orchestrating:
  - `detect.py`: presence of 14 expected artifacts (LICENSE, README,
    SETUP, ROADMAP, CHANGELOG, CONTRIBUTING, `.gitignore`,
    `.gitattributes`, `pyproject.toml`, `requirements-dev.txt`, a
    `.github` workflow, PR/issue templates, a tests directory).
  - `skill_md.py`: validates that `SKILL.md` exists and has a non-empty
    `description:` in its YAML frontmatter (the only hard `FAIL`).
  - `gitattributes.py`, `gitignore.py`, `pyproject.py`, `ci_workflow.py`,
    `changelog_format.py`: validate format when the file is present.
  - `requirements_dev.py`: tolerant parser accepting comments, blank
    lines, requirement specifiers, environment markers, `-r`, `-c`,
    `--index-url`. Lines outside the supported subset emit `WARN`, never
    `FAIL`.
  - `python_style.py`: AST checks for `from __future__ import annotations`
    and deprecated `typing.List`/`Dict`/`Optional` aliases. `WARN` in
    `scripts/`, `INFO` in `tests/`.
  - `runtime_stdlib.py`: AST imports cross-referenced against stdlib,
    local modules, `requirements-dev.txt`, `SETUP.md`, and a
    `skill-audit.toml` allowlist. Severity caps at `WARN`.
  - `hardcoded_paths.py`: regex over `scripts/`, `tests/`, `*.md`,
    `*.toml`, `*.yml`, normalizing separators and drive letters before
    matching. `FAIL` on any literal hit.
- **Layer 2 -- judgement passes** delegated to the invoking agent:
  `readme_quality`, `setup_completeness`, `changelog_significance`,
  `language_coherence`, `aspiration_to_base_skill`. Capped at `WARN`.
- **JSON contract (schema v1)**: `schema_version`, `skill_path`,
  `profile`, `scorecard`, `findings_layer1`, `targets_for_layer2`,
  `findings_layer2`. Exposed as `JSON_PATH=<abs-path>` on the last line of
  stdout.
- **Profiles**: `--profile public` (full severity) and `--profile local`
  (`WARN`-on-absence downgraded to `INFO`). Default `local`.
- **Reference structure**: `examples/base_skill/`, a functional
  hello-world skill passing `skill-audit --profile public` cleanly.

[Unreleased]: https://github.com/lucas-lima-s/claude-skill-audit/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/lucas-lima-s/claude-skill-audit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lucas-lima-s/claude-skill-audit/releases/tag/v0.1.0
