<!-- inputs: SKILL.md, README.md, SETUP.md -->

# Layer 2 prompt: aspiration_to_base_skill

## What to read

`SKILL.md`, `README.md`, and `SETUP.md` of the skill under review, alongside
this repository's own `examples/base_skill/` as the reference layout.

## What to look for

- Does `SKILL.md` have a non-empty `description:` in its frontmatter (Layer 1
  already hard-fails on this -- do not repeat that finding here; look at
  whether the description reads as a usable trigger, not just a label).
- Does `README.md` open with a one-paragraph summary of what the skill does
  and for whom, the way `examples/base_skill/README.md` does.
- Does `SETUP.md` document at least one environment variable or explicitly
  state there are none, the way `examples/base_skill/SETUP.md` does.
- If the skill ships `scripts/*.py`, do the scripts live under `scripts/`
  (not scattered across the root)? `skill_layout.root_python` already flags
  this deterministically -- do not repeat it, but a WARN here is appropriate
  if the *organization* inside `scripts/` is confusing even though no file
  sits at the root.

## What to ignore

- Exact wording or section titles -- `examples/base_skill/` is aspirational,
  not normative. A skill that achieves the same clarity with a different
  structure is not a gap.
- Anything already covered by a Layer 1 check (`skill_md.frontmatter`,
  `skill_md.description_length`, `skill_layout.*`) or another Layer 2 prompt
  (`readme_quality`, `setup_completeness`).

## Output

Emit zero or more findings as a JSON list, each shaped as:

```json
{
  "source": "layer2",
  "check": "aspiration_to_base_skill.<short_slug>",
  "severity": "INFO|WARN",
  "message": "one sentence describing the gap",
  "file": "SKILL.md",
  "line": null,
  "remediation": "one concrete sentence on how to fix it"
}
```

Never emit `FAIL` -- the engine caps layer 2 severity at `WARN` regardless.
Do not invent findings to pad the report; an empty list is a valid, good
outcome, especially for a skill that is deliberately minimal.
