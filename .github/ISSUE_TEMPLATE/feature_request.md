---
name: Feature request
about: Suggest a new check, profile, or capability
title: ""
labels: enhancement
---

## Problem

What concrete situation is the current skill failing to flag (or
flagging incorrectly)?

## Proposed solution

How would you like the skill to behave? Be specific:

- Is it a new Layer 1 check (deterministic, belongs in `scripts/checks/`
  if it is skill-specific, or upstream in `claude-skill-repo-audit` if it
  is generic) or a Layer 2 prompt (judgement)?
- What severity should it emit, and under which profile?
- Does it need configuration in `skill-audit.toml`?

## Alternatives considered

Other approaches and why they fall short.

## Layer affected

- [ ] Layer 1 (deterministic -- `scripts/checks/*.py`)
- [ ] Layer 2 (LLM -- `docs/layer2_prompts.md`)
- [ ] Both
- [ ] Neither (e.g. profile, config, output rendering)
