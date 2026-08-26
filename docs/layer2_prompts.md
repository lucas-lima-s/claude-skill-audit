# Layer 2 prompts

Layer 2 is delegated to the LLM agent that invoked the skill (typically
Claude). `scripts/check.py` populates `targets_for_layer2[]` in the JSON
report with each prompt's file and the input paths it should read. The
agent applies each prompt, appends the resulting finding(s) to
`findings_layer2[]` in the same JSON file, then runs
`scripts/report.py --json <path>` to render the merged markdown.

## Severity rules (apply to every prompt)

- **Never emit `FAIL`.** Layer 1 reserves `FAIL` for objective failures.
  `auditlib.layer2.merge_layer2` demotes any `FAIL` a prompt emits to
  `WARN`, with a note appended to the message.
- Use `OK` (or simply no finding) when the artifact looks complete for the
  skill being audited. Do not invent issues to pad the report.
- Use `INFO` for observations worth surfacing that are not problems.
- Use `WARN` when there is a concrete gap a reasonable reviewer would flag.

## Finding shape

```json
{
  "source": "layer2",
  "check": "<prompt_id>.<short_slug>",
  "severity": "INFO|WARN",
  "message": "one sentence describing the gap",
  "file": "<path or null>",
  "line": null,
  "remediation": "one concrete sentence on how to fix it"
}
```

## Prompt index

| `prompt_id` | file |
|---|---|
| `readme_quality` | `scripts/auditlib/prompts/readme_quality.md` |
| `setup_completeness` | `scripts/auditlib/prompts/setup_completeness.md` |
| `changelog_significance` | `scripts/auditlib/prompts/changelog_significance.md` |
| `language_coherence` | `scripts/auditlib/prompts/language_coherence.md` |
| `aspiration_to_base_skill` | `prompts/aspiration_to_base_skill.md` |

The first four are vendored from `claude-skill-repo-audit` verbatim (they
are generic enough to apply to any repository, skill or not); the fifth is
specific to this skill and lives at the repo root under `prompts/`.
