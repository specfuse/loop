---
gate: 1
status: passed
cost_budget_usd: 6.0
---

# Gate 1 — Ceremony proportionality + slim WU template (terminal)

This is the feature's only gate, drafted per its own proportionality rule
(≤4 substantive WUs ⇒ single gate + single terminal `close`). There is no
next gate to draft; the closing sequence is the single terminal `close` WU.

## Definition of done

- T01 (`slim WU template`) is `done`: driver-owned/audit fields collapsed in
  `WU.template.md` into one `<!-- driver-owned -->` block, and the
  acceptance-criteria guidance nudges toward assertion-shaped criteria.
  Pure-markdown; no lint or driver change.
- T02 (`ceremony proportionality`) is `done`: `draft-feature` carries the ≤4
  size rule, `methodology.md` documents it including the off-plan escape.
- `RETROSPECTIVE.md` exists with `## Cost analysis` and `## What the loop did
  NOT verify` sections, and records the measurement baseline ($174 total /
  43% ceremony cost / $1.43 avg impl WU) for follow-up comparison.
- Generalizable lessons promoted to `.specfuse/LEARNINGS.md`.
- Docs and roadmap row reflect what was built; terminal feature-arc verdict
  written.

## Reflection notes

<Written by the human at review of the terminal close commit. Did the slim
template lose any field a reviewer actually needed? Is the ≤4 threshold the
right line, or did the dogfood expose drift? What ceremony-execution levers
should the follow-up feature carry?>
