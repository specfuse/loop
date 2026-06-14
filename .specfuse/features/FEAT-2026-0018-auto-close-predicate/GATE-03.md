---
gate: 3
status: open  # reopened for T11H hygiene + G3-CLOSE re-run per gate-3 recursive-dogfood evidence (terminal wiring relocation)
cost_budget_usd: 8.00  # raised from 4.50 per G2-PLAN GATE-03-REVIEW open-verification #1 — gate-2 ratio 1.64×, gate 3 substantives + close projected ~$6 with buffer
---

# Gate 3 — Plan-next lint + /wrap-feature trim + migrate skill + docs (drafted by G2-PLAN)

## Definition of done

Drafted by G2-PLAN from gate 2's retrospective + lessons. Expected
shape (subject to refinement at arm time):

- `lint_plan.py` extended with plan-next-draft lint pass. Driver
  hook runs it between plan-next WU squash and dispatch-loop
  resume. Warn-only v1 (block-on-error deferred).
- `/wrap-feature` skill stripped of retrospective evaluation prose;
  push + PR + CI watch + next-pick only.
- `/migrate-to-auto-close` skill: scans target project's features,
  surfaces the new capability per feature, opt-in only (no
  auto-rewrites).
- `/draft-feature` template defaults updated: new features author
  cost tables anticipating predicate evaluation (already mostly
  in place per FEAT-2026-0015's planned-cost-capture work).
- `docs/methodology.md` (if exists) updated with the deterministic
  close path. LEARNINGS appended.
- Recursive dogfood result documented in G3-CLOSE's RETROSPECTIVE:
  whether this gate auto-closed or not, and why.

## Reflection notes

<Written by the human at gate-3 review time. Especially: did the
predicate fire on this gate's close? If not, which criterion?>
