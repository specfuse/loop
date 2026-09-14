<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Project-authored rules (`rules-local/`)

This directory belongs to **your project**, not to Specfuse. Put binding rules
here that are specific to this repository — its tools, its paths, its failure
modes — and that should survive every scaffold upgrade.

**The contract:** `specfuse upgrade` never writes, overwrites, or prunes
anything in `rules-local/`. That is the opposite of the sibling
`.specfuse/rules/` directory, which is versioned: upgrades overwrite its files
with the shipped versions and delete files the shipped scaffold no longer
carries. A project rule placed in `rules/` will be lost on upgrade; the same
rule placed here is permanent.

## When to write a rule here vs. upstream

- **Here:** the rule names your project's directories, commands, tools, or
  conventions ("grep `src/main/java/.../validation/rules/` before designing a
  rule", "the generator jar's `templates` command lists artifacts"). Upstream
  would have to genericize away exactly the specifics that make it useful to
  you.
- **Upstream (a PR to the scaffold's `rules/`):** the failure mode is
  project-agnostic and other Specfuse projects would hit it too. Keep the
  provenance; genericize the examples.

## Wiring a rule into the loop

Rules load via the `@`-references in your `.claude/CLAUDE.md` Specfuse rules
block. Add one line per rule you author:

```markdown
@.specfuse/rules-local/<your-rule>.md
```

Follow the shipped rules' format: one failure mode per rule, the check stated
imperatively, provenance recorded so the reasoning survives the rule (see
`.specfuse/rules/planning-discipline.md` for the model).

## The shared word budget

The `.claude/CLAUDE.md` binding rules block a work-unit session is dispatched
against is capped at 2,500 words total, and every rule you add here counts
against that one shared budget alongside the loop's own rules — this is not a
free directory. `.specfuse/rules-local/learnings-distilled.md`, the
LEARNINGS-derived distillate, carries its own 500-word sub-budget inside that
total; its content is decided by a human accept step
(`apply_distilled_decisions` in `specfuse/loop/loop.py`) that cuts a ranked
proposal to the sub-budget, not to an entry count. Before adding an entry to
that distillate or to a rule here, check whether a guard or lint already
enforces it — if so, it does not belong in the block: the block is for what a
session must be *told*, not for what tooling already *checks*.

The ranking's `reach` field (count of other feature files citing an entry) is
a tiebreaker with an age bias, not a ranking: it inflates on its own
visibility and favors older entries. Neither `reach` nor the entry's recorded
cost measures whether the rule actually improves a session's work — that
judgment call is still the accept step's, made by reading the entry.

This README is seeded once and never overwritten — edit it freely.
