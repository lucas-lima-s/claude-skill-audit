# Contributing

Thanks for considering a contribution. The skill is small and stdlib-only
at runtime; the bar to set up a dev environment is low.

## Local setup

```sh
git clone https://github.com/lucas-lima-s/claude-skill-audit.git
cd claude-skill-audit
uv sync
```

## Run the test suite

```sh
uv run pytest -q
```

Tests are self-contained (no external services, no Claude API calls).

## Lint and format

```sh
uv run ruff check .
uv run ruff format .
```

Both are configured in `pyproject.toml` (line length 120, target Python
3.11). Lint and formatting are enforced in CI (`.github/workflows/ci.yml`).

## Adding a check: here vs. upstream

- **Belongs here (`scripts/checks/`)** when the rule only makes sense for a
  Claude Code skill specifically: `SKILL.md` frontmatter, the
  `scripts/`-vs-root layout convention, or anything that reads
  `skill-audit.toml`.
- **Belongs upstream, in `claude-skill-repo-audit`'s `scripts/auditlib/`**
  when the rule is generic to any public repository regardless of whether
  it happens to be a skill: artifact presence, `.gitattributes`/`.gitignore`
  coverage, `pyproject.toml` tooling, CI matrix shape, CHANGELOG format,
  Python style, hardcoded paths. If you find yourself editing
  `scripts/auditlib/` directly to fix a bug or add a rule in this
  category, stop -- make the change in a `claude-skill-repo-audit` clone
  instead, then re-vendor:

  ```sh
  uv run python scripts/sync_auditlib.py --from <path-to-claude-skill-repo-audit-clone>
  uv run python scripts/sync_auditlib.py --check
  ```

  **Never hand-edit anything under `scripts/auditlib/`.** The drift gate
  (`sync_auditlib.py --check`, also run in CI) will fail the moment the
  vendored copy and the manifest's sha256 disagree, which is the intended
  signal that a hand-edit happened.

For a skill-specific check:

1. Create `scripts/checks/<name>.py` exposing a `@register("<name>")`
   function `run(ctx: CheckContext) -> list[CheckResult]`.
2. Add `<name>` to `enabled_checks` in `profiles/skill-public.toml` and
   `profiles/skill-local.toml`.
3. Cover it with at least two cases in `tests/test_skill_checks.py`: one
   passing, one failing.
4. Document it in `docs/rules.md` (what it checks, severity per profile,
   why it matters, how to fix).
5. Update `CHANGELOG.md` under `[Unreleased]`.

Layer 2 prompts specific to this skill live in `prompts/`; the four
generic ones live under `scripts/auditlib/prompts/` (upstream, do not
edit here). To add a skill-specific prompt: create `prompts/<id>.md`
following the shape in `docs/layer2_prompts.md`, then add `<id>` to
`layer2_prompts` in both profile files.

## Dogfooding

Before opening a PR, run the skill against itself:

```sh
uv run python scripts/check.py . --profile skill-public
uv run python scripts/report.py --json <the JSON_PATH= line printed above>
```

The result must have zero `FAIL`. Any new `WARN` should be intentional and
documented in `CHANGELOG.md`.

## Commit policy

- **Subject lines in English**, Conventional Commits (`feat:`, `fix:`,
  `docs:`, `chore:`, `test:`, `refactor:`). `SKILL.md`'s frontmatter
  `description:` is the only intentional pt-BR in this repo.
- One logical change per commit.
- Update `CHANGELOG.md` under `[Unreleased]` for any user-visible change.
