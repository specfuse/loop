---
gate: 1
status: open
cost_budget_usd: 28.00
# Sum of drafted WU estimates ($23.50) plus one re-attempt of the largest
# ($4.50, T03) — the defensive-padding shape planning-discipline recommends.
baseline:
  sha: 2ad6f95022905fd086b2c0c00b02efaf2c082b0d
  probed_at: 2026-07-30T19:11:07.984055+00:00
  failing: []
---

# Gate 1 — Arm predicate + machine-readable contract (shadow trail live)

## Definition of done

- Every gate close on any feature in this repo emits one
  `arm_predicate_evaluated` event carrying the full per-class evaluation; no
  arming behavior changes anywhere.
- The plan baseline snapshot exists and is immutable after first dispatch.
- The plan-next contract fields (`open_questions`, `human_only`, `provenance`)
  are documented in both template copies and covered by warn-only lint.
- A retrospective exists; generalizable lessons promoted to
  `.specfuse/LEARNINGS.md`; docs and roadmap reflect what was built.
- Gate 2's work units are drafted and `GATE-02-REVIEW.md` is written.

The closing sequence is `G1-CLOSE-INTERMEDIATE` then `G1-PLAN`. The driver runs
the gate unattended, then stops at `awaiting_review` for human review-and-arm —
which, on this feature of all features, is worth doing attentively: the drafted
gate 2 is the one that makes arming live.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for a default/severity flip (§4).** Gate 2 flips the
  contract-field lint warns to blocking under `auto`. Apply the change locally,
  run the exact lint command over every feature folder in this repo, and paste
  the finding list into `GATE-02-REVIEW.md`. That list is the enumerated
  migration surface.
- **Escalation-predicate satisfiability (§2).** PLAN.md answers it for gate 1
  (warn-only, zero on correct input by construction). G1-PLAN must answer it
  again for gate 2's blocking flip.
- **Budget brake.** Set gate 2's `cost_budget_usd` at arming — the successor
  gate is where a newly built enforcement mechanism gets exercised for the
  first time (`[FEAT-2026-0007/G2-LESSONS]`).
- **First-firing check.** This gate's own `awaiting_review` flip is the shadow
  predicate's first live firing (T04 lands mid-gate; the event fires after both
  closing WUs). Before arming gate 2, confirm `events.jsonl` carries exactly one
  `arm_predicate_evaluated` event for gate 1 and read its per-class verdicts. No
  event = T04's central claim is false — do not arm; escalate.

## Reflection notes

<Written by the human at review time.>
