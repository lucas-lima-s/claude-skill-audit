# JSON contract -- schema v2

`scripts/check.py` prints `JSON_PATH=<absolute-path>` as the **last line of
stdout**. Everything else -- the human-readable preamble -- goes to stderr.
Exit codes: `0` = PASS, `1` = BLOCK, `2` = usage/IO error. Setting
`SKILL_AUDIT_NEVER_EXIT_NONZERO=1` forces exit `0` regardless of gate
(manual debugging only -- CI must never set this).

This is the same envelope shape `claude-skill-repo-audit` uses (schema v2,
same field names), so a tool that already knows how to read one report
knows how to read the other -- only `tool` and `kind` differ.

```json
{
  "schema_version": 2,
  "tool": "skill-audit",
  "tool_version": "0.2.0",
  "kind": "skill",
  "generated_at": "2026-08-25T12:00:00Z",
  "target_path": "/abs/path",
  "target_name": "my-skill",
  "profile": "skill-public",
  "gate": "PASS",
  "scorecard": {"present": 12, "total": 14, "ok": 20, "info": 3, "warn": 1, "fail": 0},
  "findings_layer1": [
    {
      "check": "hardcoded_paths.literal",
      "severity": "FAIL",
      "message": "literal machine-specific path found",
      "file": "scripts/leak.py",
      "line": 2,
      "remediation": "replace with an env var, a relative path, or a CI-provided temp dir",
      "source": "layer1",
      "evidence": {}
    }
  ],
  "targets_for_layer2": [
    {
      "prompt_id": "readme_quality",
      "prompt_file": "/abs/.../scripts/auditlib/prompts/readme_quality.md",
      "files": ["/abs/README.md"]
    }
  ],
  "findings_layer2": []
}
```

- `scorecard.present`/`total` count the `artifacts.*` checks only.
  `ok`/`info`/`warn`/`fail` count every `findings_layer1` entry by severity
  (this includes any `layer2.budget.*` INFO entries `check.py` appends).
- `gate` is computed **only** from `findings_layer1` -- a `FAIL` in
  `findings_layer2` is impossible; the engine demotes it to `WARN` before it
  ever reaches the report.
- `findings_layer2` starts empty. The invoking agent appends to it after
  running the prompts named in `targets_for_layer2` (or calls
  `auditlib.layer2.merge_layer2`, which does the same thing programmatically).

## Layer 2 finding shape

Every entry appended to `findings_layer2` (or passed to `merge_layer2`)
must have at least `check`, `severity`, and `message`; `file`, `line`,
`remediation`, `evidence` are optional. `severity: "FAIL"` is accepted but
silently rewritten to `"WARN"` with a note appended to the message -- layer
2 can never gate a skill on its own.

## Validating a report

`auditlib.report.load_and_validate(path)` reads a JSON report and raises
`SystemExit(2)` if `schema_version != 2`. `scripts/report.py` uses this
internally; use it directly if you are writing a new tool against this
contract, so a future schema bump fails loudly instead of silently
misreading old fields.
