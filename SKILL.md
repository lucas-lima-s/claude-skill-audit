---
name: skill-audit
description: Audits a Claude Code skill against public-release standards: artifact presence, SKILL.md frontmatter, .gitignore/.gitattributes/pyproject/CI/CHANGELOG format, AST checks for Python style and undeclared runtime imports, and hardcoded user paths. Layer 1 is deterministic Python; Layer 2 delegates README quality, SETUP completeness, CHANGELOG significance and language coherence to the agent. Output: a maturity scorecard plus findings ranked OK | INFO | WARN | FAIL; exit 1 only on a deterministic FAIL. Use when the user says "audit this skill", "is this skill ready to publish", "skill-audit <path>", "/skill-audit", or in pt-BR "audita essa skill", "checa a skill X", "ver se essa skill ta pronta para publicar".
argument-hint: [skill-path] [--profile skill-public|skill-local]
allowed-tools:
  - Read
  - Bash(*scripts/check.py*)
  - Bash(*scripts/report.py*)
  - Bash(*scripts/init_skill.py*)
  - Bash(*scripts/fix.py*)
---

# skill-audit -- single entry point

Audits a Claude Code skill against the public-release standards documented
in `docs/rules.md`. The audit has two layers:

- **Layer 1 (deterministic)** runs in Python via `scripts/check.py`. It
  combines the vendored `scripts/auditlib/` engine (artifact presence,
  `.gitattributes`/`.gitignore`/`pyproject.toml`/CI/CHANGELOG format, Python
  style, hardcoded paths) with this repo's skill-specific checks
  (`SKILL.md` frontmatter, layout, undeclared runtime imports).
- **Layer 2 (judgemental)** delegates to Claude (the agent invoking this
  skill). Five curated prompts in `docs/layer2_prompts.md` evaluate README
  quality, SETUP completeness, CHANGELOG significance, language coherence,
  and alignment with `examples/base_skill/`.

## End-to-end flow

When the user asks for an audit:

1. **Resolve the skill path.** The user may provide it explicitly
   (`skill-audit ~/.claude/skills/foo`); if absent, ask. If the user says
   "this skill" inside a skill's own repo, use the cwd.
2. **Run Layer 1** via Bash:

       "$SKILLS_PYTHON" "$SKILL_AUDIT_HOME/scripts/check.py" \
         <skill-path> [--profile skill-public|skill-local]

   The script prints `JSON_PATH=<abs-path>` as the **last line of
   stdout** and writes the report to that path. The stderr preamble is
   fine to ignore. `$SKILL_AUDIT_HOME` is the directory this skill was
   cloned into (see `SETUP.md`).
3. **Read the report.** The JSON has `scorecard`, `findings_layer1`,
   `targets_for_layer2[]`, and an empty `findings_layer2[]`. See
   `docs/json_contract.md` for the full shape.
4. **Run Layer 2 evaluations.** For each entry in `targets_for_layer2`,
   apply the matching prompt named by its `prompt_file`. Read the listed
   input files (or enumerate the directory if an entry points at one),
   produce a finding object per `docs/layer2_prompts.md`'s shape, and
   **append** it to `findings_layer2[]` in the same JSON file. Severity
   caps at `WARN`.
5. **Render the merged report** via Bash:

       "$SKILLS_PYTHON" "$SKILL_AUDIT_HOME/scripts/report.py" --json <abs-path>

   Print the markdown returned by `report.py` to the user. Exit code
   reflects the merged result (`1` only if Layer 1 has any `FAIL`).

## When to skip Layer 2

- The user explicitly asked "only deterministic" / "skip the LLM passes".
- The Layer 1 report has nothing to evaluate against (e.g. the skill has
  no README and no SETUP).

In both cases run only the rendering step on the JSON as-is.

## Profiles

| Profile | When to pick it | Behaviour |
|---|---|---|
| `skill-public` | Skill is (or aims to be) on a public repo | Full severity. Missing README/SETUP/`.gitignore` = WARN. |
| `skill-local` | Personal skill, no public-release ambition | WARN-on-absence downgraded to INFO. Less noise. |

`--profile public` / `--profile local` are accepted as aliases for
`skill-public` / `skill-local`. Default, when neither `--profile` nor the
target's `skill-audit.toml` declares one, is `skill-local`.

A `skill-audit.toml` at the root of the target skill can pin the profile
and add a `runtime_stdlib` allowlist:

```toml
profile = "skill-public"

[runtime_stdlib.allowlist]
yaml = "pyyaml"
cv2 = "opencv-python"
```

## Bootstrapping a new skill

`scripts/init_skill.py --out DIR --name NAME [--description TEXT]`
materializes `examples/base_skill/` into `DIR`, already passing
`--profile skill-public` cleanly.

## Mechanical fixes

`scripts/fix.py <skill-path> [--apply]` applies mechanical, single-answer
corrections (the `.gitattributes` eol line, a missing `## [Unreleased]`,
Python-cache `.gitignore` coverage). Default is dry-run: it prints a
unified diff and writes nothing.

## Output rules

- Render the markdown returned by `report.py` directly. Do not wrap it in
  a code fence.
- The scorecard line at the top is meant to be glanceable
  ("`Polish scorecard: 12 / 14 artifacts present`"). Keep it.
- After printing, summarise in 1-2 sentences only when the user explicitly
  asked for guidance ("what should I fix first?"). Otherwise let the
  report speak for itself.

## Inviolable rules

- **Never auto-fix outside `scripts/fix.py --apply`.** `check.py` and
  `report.py` only report; the user (or an explicit `--apply`) fixes.
- **Never run Layer 2 without Layer 1.** The JSON contract is the source
  of truth for which files to read.
- **Layer 2 severity caps at `WARN`.** Never append a `FAIL` from a Layer 2
  evaluation.
- **Do not write inside the target skill.** The JSON report lives under
  `$TEMP` / `$env:TEMP` (or `--json-out`) only.
