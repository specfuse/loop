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

This README is seeded once and never overwritten — edit it freely.
