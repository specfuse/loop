---
gate: 2
status: open
---

# Gate 2 — wire the planning consumers (drafted by gate 1's plan-next)

## Definition of done

- `/draft-feature`, `/pick-feature`, `plan-next`, and `/authoring-work-units` load
  the relevant LEARNINGS slice via `learnings_query` instead of the whole file,
  honoring the load-whole threshold fallback.
- Query assembly (feature goal + slug + touched paths → query terms) is specified
  and, if it belongs consumer-side, implemented as `build_query`.

The substantive work units for this gate are **drafted by gate 1's `plan-next`
WU** at the gate boundary, then human-reviewed and armed (flipped from `draft`
to `pending`). Until then this gate is a skeleton with an empty `work_units`
list in `PLAN.md`.

## Reflection notes

<Written by the human at review time.>
