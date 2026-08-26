# Setup -- `skill-audit`

Two-layer audit for Claude Code skills. Layer 1 runs `scripts/check.py` in
Python; Layer 2 is delegated to the agent invoking the skill.

Supported on Windows, Linux, and macOS via Python 3.11+.

## Requirements

- Python 3.11+ available via `$SKILLS_PYTHON` (preferred) or `python` /
  `python3` on `PATH`. Python 3.11+ is required because Layer 1 uses
  `tomllib` (stdlib since 3.11) and `sys.stdlib_module_names` (stdlib
  since 3.10).
- Optional: [`uv`](https://docs.astral.sh/uv/) for dependency management
  and running the dev tooling (`uv sync`, `uv run pytest`).
- Claude Code, when running through the `SKILL.md` flow.

No third-party runtime dependencies. Dev dependencies (`ruff`, `pytest`)
live under `[dependency-groups].dev` in `pyproject.toml` and are installed
only when you work on the skill itself, not when you use it.

## Recognised environment variables

| Variable | Purpose |
|---|---|
| `SKILLS_PYTHON` | Preferred Python interpreter the skill invokes for `scripts/check.py`. |
| `SKILL_AUDIT_HOME` | The directory this skill was cloned into. Used in `SKILL.md`'s invocation snippets so no user-specific path shape is hardcoded. |
| `TEMP` / `env:TEMP` | Where the JSON report is written by `scripts/check.py` when `--json-out` is not passed. |
| `SKILL_AUDIT_NEVER_EXIT_NONZERO` | Test hook; when set to `1`, `check.py` always returns exit code 0. |

The skill itself does not write any environment variable. It only reads
the host environment to discover paths.

## Configuration

Per-skill configuration lives at `<target-skill>/skill-audit.toml`
(optional). Keys:

```toml
profile = "skill-public"  # or "skill-local" (aliases: "public" / "local")

[runtime_stdlib.allowlist]
yaml = "pyyaml"
cv2 = "opencv-python"
```

- `profile` overrides the default profile when the user does not pass
  `--profile`. Default-default is `skill-local` (less noise on personal
  skills).
- `runtime_stdlib.allowlist` maps an import name to its distribution name
  in the dev dependency group. Only needed when the import name and the
  package name differ (e.g. `import yaml` from `pyyaml`).

## Profile resolution chain

`--profile` (CLI) > `<target-skill>/skill-audit.toml`'s `profile` >
`skill-local` (the default). `public` and `local` are accepted as aliases
for `skill-public` and `skill-local` for backward compatibility.

## Running standalone

```bash
"$SKILLS_PYTHON" scripts/check.py ~/.claude/skills/foo --profile skill-public

# stdout's last line is `JSON_PATH=<abs-path>`.
"$SKILLS_PYTHON" scripts/report.py --json <abs-path>
```

`check.py` writes the JSON report to a temp file by default; override the
path with `--json-out`. `--max-layer2-bytes` (default `262144`) caps the
total size of the input files listed per `targets_for_layer2` entry,
dropping the largest ones and recording an INFO finding when it does.

See [`docs/json_contract.md`](docs/json_contract.md) for the full report
shape.

## Layout

```
~/.claude/skills/skill-audit/
  SKILL.md                  - skill entry point
  SETUP.md                  - this file
  README.md                 - public-facing summary
  CHANGELOG.md              - Keep a Changelog
  CONTRIBUTING.md           - dev setup, commit policy
  pyproject.toml            - uv + ruff config
  skill-audit.toml          - self-config (profile = skill-public)
  profiles/                 - skill-public.toml, skill-local.toml
  prompts/                  - aspiration_to_base_skill.md
  scripts/
    check.py                - Layer 1 entry (writes JSON, prints JSON_PATH=)
    report.py               - markdown renderer
    init_skill.py           - --init scaffolder
    fix.py                  - --fix mechanical corrections
    sync_auditlib.py        - re-vendor + drift gate
    render_demo.py          - regenerates docs/demo-*.svg
    auditlib/               - vendored engine, do not hand-edit
    checks/                 - skill-specific checks
  tests/                    - pytest suite
  examples/
    base_skill/             - functional reference skill
  docs/
    rules.md                 - rule rationale
    json_contract.md         - schema v2
    layer2_prompts.md        - five LLM prompts
```

## Profiles in practice

- `--profile skill-public`: full severity. Use when the target skill is
  (or is about to be) public on GitHub. Missing `LICENSE`, `README.md`,
  `SETUP.md`, `.gitignore` produce `WARN`.
- `--profile skill-local`: lower noise. `WARN`-on-absence is downgraded to
  `INFO` for files that are publication conveniences (CI, CHANGELOG, etc.).

When the user does not pass `--profile`, the skill reads
`<target-skill>/skill-audit.toml`. If neither informs a profile,
`skill-local` is assumed.

## Working with the JSON contract

See [`docs/json_contract.md`](docs/json_contract.md) for the full schema.
The agent applying Layer 2 mutates only `findings_layer2[]`. Severity in
Layer 2 caps at `WARN` -- the exit code from `report.py` only goes to `1`
on `findings_layer1[].severity == "FAIL"`.
