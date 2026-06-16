---
gate: 1
status: awaiting_review
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate 1 — The driver machine-enforces per-WU deliverable presence

## Definition of done

- `produces:` is a parsed WU frontmatter field carried on `WorkUnit`, with an
  advisory lint WARN when an `implementation` WU declares none (T01).
- The driver rejects a `complete` attempt whose declared `produces:` deliverable
  is absent or empty on disk, escalating to `blocked` after MAX_ATTEMPTS (T02).
- The driver rejects a `complete` attempt from an `implementation`-type WU whose
  `files_touched` is empty, independent of `produces:` (T03).
- Every implementation WU in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation reflects what was built: `WU.template.md` documents `produces:`,
  and `.specfuse/skills/authoring-work-units/SKILL.md` carries the new rule.
- The terminal feature-arc verdict is written.

This is a single-gate feature: the gate's `close` WU collapses
retrospective + lessons + docs + terminal verdict into one session. With
`autonomy_default: auto` the driver runs the gate unattended to a terminal
outcome; there is no mid-gate review-and-arm checkpoint.

## Reflection notes

<Written by the human at review time. What surprised you, what the
retrospective got wrong, anything the auto run produced that needs a second
look. This is your record, not the agent's — keep it honest.>
