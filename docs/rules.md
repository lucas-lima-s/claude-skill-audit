# Rules

One section per check id: what it checks, the severity it emits under each
profile, why it matters for a skill aiming at public release, and how to
fix it. `skill-public` and `skill-local` share the same set of enabled
checks and artifact rules; the only structural difference is
`downgrade_warn_to_info`, which turns every `WARN` this document lists into
`INFO` under `skill-local`. `FAIL` never downgrades under either profile.

## `artifacts.*`

Emitted by the vendored `artifacts` check, one finding per entry in the
active profile's `[artifacts]` table. The scorecard denominator is a
Python-shipping skill's full `14 / 14`; `pyproject` and `tests_dir`
require `python_code` and drop out, giving `12 / 12`, when the skill ships
no `*.py`.

| id | missing severity (`skill-public`) | requires |
|---|---|---|
| `artifacts.skill_md` | FAIL | -- |
| `artifacts.license` | INFO | -- |
| `artifacts.readme` | WARN | -- |
| `artifacts.setup` | WARN | -- |
| `artifacts.changelog` | INFO | -- |
| `artifacts.contributing` | INFO | -- |
| `artifacts.gitignore` | WARN | -- |
| `artifacts.gitattributes` | INFO | -- |
| `artifacts.pyproject` | WARN | `python_code` |
| `artifacts.ci_workflow` | INFO | -- |
| `artifacts.pr_template` | INFO | -- |
| `artifacts.issue_bug` | INFO | -- |
| `artifacts.issue_feature` | INFO | -- |
| `artifacts.tests_dir` | WARN | `python_code` |

Why it matters: a reader deciding whether to trust a skill looks for these
files before reading a line of code. `skill_md` is the only hard `FAIL`
because without it Claude Code cannot discover the skill at all.

Fix: add the missing file. `remediation` on the finding names the exact
path.

## `skill_md.frontmatter`

Checks that `SKILL.md` exists, has a `---`-delimited YAML frontmatter
block, and that the frontmatter has a non-empty `description:`. `FAIL`
under every profile -- this is the one check severity never downgrades via
`downgrade_warn_to_info` because it is already at the ceiling.

Why it matters: `description:` is the string Claude Code's trigger matching
runs against. No description, no discoverability.

Fix: add or restore the frontmatter block and a `description:` line.

## `skill_md.description_length`

`INFO` when the trimmed `description:` is under 40 characters (too short to
carry useful trigger phrases) or over 1024 (Claude Code truncates long
descriptions). `OK` otherwise.

Fix: expand a too-short description with concrete trigger phrases, or trim
a too-long one.

## `skill_md.allowed_tools`

`INFO` when the skill ships `scripts/*.py` but `SKILL.md` has no top-level
`allowed-tools:` key.

Why it matters: an undeclared `allowed-tools:` means the invoking agent has
no explicit scope for the `Bash(...)` calls the skill needs, which either
under- or over-grants permissions depending on the harness default.

Fix: add `allowed-tools:` listing the specific `Bash(*scripts/foo.py*)`
patterns (and any other tools) the skill actually invokes.

## `skill_layout.root_python`

`WARN` when one or more `*.py` files sit directly at the skill root instead
of under `scripts/`.

Why it matters: a root-level script is invisible to `runtime_stdlib.import`
and to anyone expecting the `scripts/` convention; it also usually means
the file was a scratch script that never got moved.

Fix: move the file(s) under `scripts/`.

## `skill_layout.tmp_tracked`

`INFO` when `scripts/_tmp/` or `data/_tmp/` is tracked in git.

Why it matters: these directories exist specifically to hold one-off,
disposable scripts and data (see the portfolio convention in this
project's own tooling); tracking them defeats the purpose and clutters the
history.

Fix: `git rm -r --cached scripts/_tmp data/_tmp` and add both to
`.gitignore`.

## `skill_layout.broken_script_ref`

`WARN` when `SKILL.md` mentions a `scripts/...py` path that does not exist
on disk. The check parses `scripts/[\w./-]+?\.py` occurrences out of the
raw text and stats each one.

Why it matters: a stale path in the skill's own entry point means the
documented invocation will fail the moment someone follows it.

Fix: correct the path, or remove the reference if the script was deleted.

## `gitattributes.eol`

`WARN` when `.gitattributes` exists but lacks a `* text=auto eol=lf` line.

Why it matters: without a normalizing eol rule, a contributor on a
different OS can silently flip line endings across an entire file,
producing a diff that is 100% noise.

Fix: add `* text=auto eol=lf` to `.gitattributes`, or run
`scripts/fix.py <path> --apply`.

## `gitattributes.linguist`

`INFO` when a tracked file matches a generated-asset glob (`docs/*.svg`,
`*.min.js`, `dist/**`) without a `linguist-generated` or
`linguist-vendored` attribute.

Why it matters: without the attribute, GitHub's language detection and PR
diffs treat generated files as authored source.

Fix: add e.g. `docs/*.svg linguist-generated=true` to `.gitattributes`.

## `gitignore.coverage`

`WARN` per missing family: Python bytecode cache, a Python virtualenv, a
`.env` dotenv file, `node_modules` (only when `package.json` exists), log
files, and a `.history/` directory -- each only when applicable to the
skill (e.g. the virtualenv rule only fires on a Python skill).

Why it matters: an uncovered family is exactly the kind of thing that ends
up committed by accident on someone's first `git add .`.

Fix: add the missing pattern; `scripts/fix.py` covers the Python-cache case
automatically.

## `pyproject.format`

Only runs when `pyproject.toml` exists. `FAIL` when the TOML is invalid, or
when neither `[tool.ruff]` nor `[tool.black]` is configured (either
formatter is accepted -- see the note below). `WARN` when a linter is
configured but no formatter signal is found (`[tool.ruff.format]`,
`[tool.black]`, or a CI step invoking one), and when `uv.lock` is committed
without a `[tool.uv]` section or a `[build-system]`. `INFO` when
`project.requires-python` is absent.

Why it matters: this repo's own baseline is ruff-as-formatter, so the rule
deliberately does not require `[tool.black]` -- it only fails when no
tooling is configured at all, which is the actual publish-readiness
signal.

Fix: add `[tool.ruff]` (and `[tool.ruff.format]` if you want ruff as the
formatter too), or `[tool.black]`; add `requires-python`.

## `dev_deps.declared`

Only runs on a Python skill. `INFO` when no dev dependency group is found
at all (checks `[dependency-groups].dev` first, then
`project.optional-dependencies.dev`, then `requirements-dev.txt`). `WARN`
when `tests/` exists but `pytest` is not declared, and per malformed line
in a legacy `requirements-dev.txt`.

Fix: declare `[dependency-groups] dev = [...]` in `pyproject.toml`
(preferred) or fix the `requirements-dev.txt` line.

## `ci_workflow.matrix`

Only runs when `.github/workflows/*.yml` exists. `WARN` when no workflow
declares both an OS runner token (`ubuntu-*`/`windows-*`/`macos-*`) and a
language-version token (`python-version`/`node-version`/...). `OK`
otherwise.

Fix: add an `os` x `python-version` (or equivalent) matrix.

## `ci_workflow.parser_limit`

`WARN` when a workflow uses a matrix `include:` block or a YAML anchor
(`<<: *`). This scanner is line/regex-based (no PyYAML dependency, to keep
the vendored engine stdlib-only) and does not expand either construct.

This is a documented, deliberate gap rather than a bug: encoding a real
YAML parser would add a runtime dependency to a tool whose entire value
proposition is "clone and run with zero install step." Keep the primary
matrix free of `include:`/anchors, or accept the `WARN`.

## `ci_workflow.shallow_clone`

`WARN` when a workflow checks out with `actions/checkout` but no
`fetch-depth: 0`, on a repo that also runs a history-scanning check
(`git_history` or `secrets`). Neither of those checks is enabled in
`skill-public`/`skill-local` (they belong to `claude-skill-repo-audit`'s
own profiles), so this finding never fires from `skill-audit` itself --
it is inherited from the shared engine and documented here for
completeness, in case a future profile enables it.

## `changelog.format`

Only runs when `CHANGELOG.md` exists. `WARN` when the first 10 lines lack a
`# Changelog` header, or when no `## [Unreleased]` section exists anywhere
in the file. `OK` when both are present.

Fix: add the header and/or the section; `scripts/fix.py` inserts
`## [Unreleased]` automatically when a `# Changelog` header is already
there.

## `python_style.future`

`WARN` (in `scripts/`) or `INFO` (in `tests/`) when a `.py` file's first
statement is not `from __future__ import annotations`. `examples/` and
`tests/fixtures/` are excluded entirely.

Fix: add the import as the module's first statement.

## `python_style.typing_aliases`

`WARN` when a file imports a deprecated `typing` alias (`List`, `Dict`,
`Tuple`, `Set`, `FrozenSet`, `Type`, `Optional`, `Union`).

Fix: use builtin generics (`list[str]`, `dict[str, Any]`) and `X | None` /
`X | Y` unions instead.

## `python_style.parse`

`WARN` when a `.py` file fails to parse as valid Python (a `SyntaxError`).

Fix: fix the syntax error.

## `runtime_stdlib.import`

Walks every `.py` file under `scripts/` and `tests/`, collects top-level
absolute imports (excluding `TYPE_CHECKING`-guarded and relative imports),
and flags any import that is not: a stdlib module (`sys.stdlib_module_names`),
a local top-level module directly under `scripts/` or `tests/` (this is how
the vendored `scripts/auditlib/` package, this repo's own `scripts/checks/`
package, and a `tests/conftest.py` helper are all recognised as local
rather than undeclared), declared in
the dev dependency group (via `auditlib.checks.dev_deps.dev_dependency_names`,
so a `[dependency-groups].dev` entry counts the same as a legacy
`requirements-dev.txt` line), mentioned in `SETUP.md`, or mapped through
`skill-audit.toml`'s `[runtime_stdlib.allowlist]`. Severity caps at `WARN`;
emits a single `OK` when nothing is unaccounted for.

Fix: declare the dependency, mention it in `SETUP.md`, or add an allowlist
entry when the import name differs from the distribution name (e.g.
`import yaml` from `pyyaml`).

## `hardcoded_paths.literal`

`FAIL` on any line matching a Windows drive letter immediately followed by
a per-user profile segment, a bare per-user path rooted at `/`, a per-user
path under `/home/`, or a drive letter followed by a common workspace
segment (`projects`, `dev`, `work`, `repos`), across `*.py`, `*.md`,
`*.toml`, `*.yml`, `*.yaml`, `*.json`, `*.ps1`, `*.sh` -- see
`scripts/auditlib/checks/hardcoded_paths.py`'s `PATTERNS` for the exact
regexes. Lines containing an
environment-variable placeholder (`$HOME`, `$USERPROFILE`, `$TEMP`,
`%USERPROFILE%`, `${{ runner.temp }}`, ...) or the literal marker
`repo-audit: allow-path` are suppressed.

Why it matters: a machine-specific path is the single most common way a
personal skill accidentally becomes unusable -- or embarrassing -- the
moment someone else clones it.

Fix: replace the literal with an environment variable, a relative path, or
a CI-provided temp directory.

## `layer2.budget.<prompt_id>`

Emitted by `scripts/check.py` itself (not the vendored engine): `INFO` when
one or more inputs were dropped from a `targets_for_layer2` entry to fit
`--max-layer2-bytes` (default 262144). The `evidence.dropped` list names
what was skipped.

This is not a publish-readiness signal about the audited skill -- it is a
budget-exceeded notice about the audit run itself, so it never affects the
scorecard or the gate.

## Layer 2 prompts

`readme_quality`, `setup_completeness`, `changelog_significance`,
`language_coherence`, and `aspiration_to_base_skill` are judgement passes
delegated to the invoking agent; see `docs/layer2_prompts.md` for what each
one reads and looks for. All five cap severity at `WARN` by contract --
`auditlib.layer2.merge_layer2` demotes any `FAIL` an agent emits, with a
note appended to the message.

## What is deliberately not checked

- **Tool version pins** (`ruff>=0.6` vs `ruff>=0.7`, a specific Python
  patch version). Version pinning is the skill author's call; the audit
  only checks that a tool is configured at all.
- **Internal layout under `scripts/`.** Beyond the root-vs-`scripts/`
  distinction (`skill_layout.root_python`), how a skill organizes its own
  helpers is not standardized -- a one-script skill and a
  ten-module skill are equally valid.
- **i18n / locale mechanisms.** A skill's own translation scheme (a `t()`
  helper, a `config.default.json`) is a feature of that skill, not a
  public-skill standard this tool enforces.
- **Telemetry conventions** (log rotation, a `cache/runs.jsonl` file, retry
  policy). Domain decisions specific to what the skill does at runtime.
- **Secret scanning and git-history identity checks.** Those live in
  `claude-skill-repo-audit`'s `secrets` and `git_history` checks, which are
  not enabled in `skill-public`/`skill-local` -- a skill directory audited
  in isolation, outside its own git history, is not the right scope for
  those checks. Run `claude-skill-repo-audit` itself when publishing a
  skill as its own repository.
