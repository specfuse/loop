---
gate: 2
status: open
---

# Gate 2 — Semantics, audit, and new-contract dogfood

## Definition of done

Detailed by Gate 1's `plan-next` (`G1-PLAN`). Expected scope per PLAN.md
intent:

- Hollow-pass guard with type-keyed assertion table for the new
  closing-WU taxonomy (extends FEAT-2026-0008's three guards).
- Verdict-state ↔ PLAN-flip coupling driver-side (`verdict:` frontmatter
  field gates the terminal flips).
- Oracle env-parity declaration + lint check.
- State-flip ownership consolidation: terminal flips
  (gate→passed, roadmap row→done, auto-archive) move from
  /wrap-feature into the new `close` WU's deliverables.
- Planned-cost capture: WU-level + PLAN-level frontmatter field +
  close-WU `## Cost analysis` deliverable + lint warnings.
- Gate 2's own terminal close uses the NEW `close` WU contract —
  first production exercise + recursive close audit.

## Reflection notes

<Written by the human at review time after G2 completion.>
