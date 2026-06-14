---
gate: 2
status: awaiting_review
cost_budget_usd: 16.00  # raised from 9.00 — gate 1 ran 2.14× plan; gate 2 driver-wiring (xhigh × 2 + medium) likely similar
---

# Gate 2 — Driver wiring + stub retro + force-full-close (drafted by G1-PLAN)

## Definition of done

Drafted by G1-PLAN from gate 1's retrospective + lessons. Expected
shape (subject to refinement at arm time):

- Driver (`loop.py`) imports `gate_eval` and calls
  `evaluate_auto_close` at gate-boundary set-`awaiting_review` site.
- On auto + terminal gate: skip `close` WU dispatch, write stub
  `RETROSPECTIVE.md`, fire `fire_terminal_flips`. Post-pass
  invariant guard (FEAT-2026-0017/T01's `assert_terminal_flips_fired`)
  STILL fires — verifies flips actually materialized.
- On auto + intermediate gate (option A): skip `close-intermediate`
  WU dispatch but DO dispatch `plan-next` WU (so next gate gets
  drafted). Write stub gate-section in `RETROSPECTIVE.md`. Arm
  next gate's drafts via existing path.
- Skipped close WUs: marked `status: done` with frontmatter
  `auto_close: true` + `auto_close_reasons: [...]`. No new
  lifecycle status added.
- `auto_close_decision` event written to `events.jsonl` carrying
  decision + reasons.
- `--force-full-close <feature-id>` CLI flag bypasses predicate.
- PLAN.md frontmatter `auto_close_disabled: true` per-feature
  override.
- Existing close path (when predicate refuses): unchanged.

## Reflection notes

<Written by the human at gate-2 review time.>
