---
id: FEAT-2026-0104/T10
type: implementation
status: done
attempts: 2
planned_cost_usd: 4.00
produces_driver_helper:
  - escalate_unit
produces:
  - tests/test_brief_covers_every_unit_escalation.py
duration_seconds: 1068.903
cost_usd: 4.604066
input_tokens: 250
output_tokens: 75717
---

# Render the brief at every unit-level escalation, not just attempt exhaustion

**Objective.** Make every `blocked_human` escalation of a work unit carry the
six-part brief, instead of only the one raised when a unit exhausts its
attempt budget.

**Context.** FEAT-2026-0104/T10. Gate 2's definition of done says "after a
work unit escalates with `blocked_human`, the operator-facing brief presents
re-planning the remaining gate as its default option" — unqualified.
`GATE-02-REVIEW.md` flagged at arming that T07's flag-scope table narrowed
that to the spin-out reasons and that the narrowing "is the draft's reading,
not the plan's words." A probe against a real model boundary then measured the
cost of that reading: `format_spinout_escalation_brief` is called from exactly
one site — the `for-else` that fires on attempt exhaustion, covering
`spinning_detected` and `all_attempts_zero_token` — and a real
`agent_reported_blocked` escalation emitted `reason`, `attempts`,
`attempts_usage`, `blocked_reason` and **no `message` at all**.

Across 636 `human_escalation` events in the corpus the brief reaches about
19%. `agent_reported_blocked` alone is 22.2% and gets nothing;
`spinning_signature_repeat` 15.6%, `deterministic_refusal_repeat` 4.7%, same.
`REPLAN_OPTION_SCOPE` already has an entry for all eleven reasons — the
predicate was built for this; only the render site was not.

Roughly ten per-unit sites emit `human_escalation` keyed on `wu.wu_id`. The
four keyed on `feature_id` are gate-level halts (budget, pre-existing gate
failure) and are **out of scope**: the definition of done is about a work unit
escalating, and a gate-level halt is a different object with no single unit to
brief about.

**Acceptance criteria.**

- `python3 -m unittest tests.test_brief_covers_every_unit_escalation -v -b`
  fails on HEAD before this unit's edits and passes after, asserting that every
  per-unit `blocked_human` escalation carries the brief on its event payload
  under `message` — enumerating the per-unit reason vocabulary from the source
  rather than a hand-copied list, so a reason added later fails this test
  instead of silently losing its brief.
- A real `loop.run()` driven to an `agent_reported_blocked` escalation — the
  reason the probe actually hit, and the corpus's most common — prints a brief
  that `escalation.validate_escalation_body()` accepts, and the assertion is on
  the run's own output, not a composed brief.
- Gate-level halts are unchanged: a test asserts the four `feature_id`-keyed
  escalations still emit exactly what they emit today.

**Do not touch.** `REPLAN_OPTION_SCOPE` and `replan_option_applies` — the
predicate is already correct for all eleven reasons and this unit is the
render side. `escalation.py`. The gate-level escalation sites. The sibling WU
files in this gate.

**Verification.** The narrow tier is NOT sufficient: this edits the driver's
escalation paths, which many modules drive through `loop.run()`. Run the
**full** suite — `python3 -m unittest discover -s tests -b` — before reporting
complete. Plus
`python3 -m unittest tests.test_brief_covers_every_unit_escalation tests.test_spinout_brief_replan_option tests.test_spinout_brief_end_to_end -v -b`
plus `SpinoutBriefEveryPartHasContent`, so the widened sites inherit the
every-part-says-something contract rather than re-opening the #3305 hole,
and the symbol check (§9):
`python3 -c "from specfuse.loop.loop import escalate_unit"`.

**Escalation triggers.** Stop with `status: blocked` if a per-unit site lacks
the state the brief needs (gate number, done and remaining unit ids) and
threading it there would change a function signature outside this unit's
touch-set — that is a second unit, not a widening of this one.
