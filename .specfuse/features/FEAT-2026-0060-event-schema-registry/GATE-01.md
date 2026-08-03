---
gate: 1
status: open
cost_budget_usd: 18.00
baseline:
  sha: aaa1796352bdf3b0742b9e4d908b42073a2fb686
  probed_at: 2026-08-03T00:14:19.728009+00:00
  failing: []
---

# Gate 1 — the driver's own event log validates, and the next unsanctioned type is caught in CI

## Definition of done

`validate_event.py` exits 0 over a real driver-produced `events.jsonl` without
the vendored orchestrator schema being modified; and a type the driver can emit
but has not registered fails a check in CI rather than accumulating unnoticed.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU, not
`close-intermediate` + `plan-next`. There is no next gate to draft.

## Cost budget

`cost_budget_usd: 18.00` — the $13.00 sum of WU estimates ($4.50 / $3.50 /
$5.00) plus one re-attempt of the largest WU ($5.00, the close), per the
defensive padding the GATE template prescribes while the closing-WU retry defect
(#260) is open.

## Ordering constraint — read before arming or re-ordering

**T02 must not land before T01.** The real-log gate T02 wires into
`verification.yml` reports **7 errors on the tree as it stands** and only reports
zero once T01's registry sanctions the driver's types. Wiring it first makes the
`code` gate set red for every subsequent work unit in this gate, including its
own close. This is the `planning-discipline.md` §2 satisfiability answer applied
as a scheduling constraint, and it is why `depends_on` is load-bearing here
rather than cosmetic.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

This gate's WUs are armed at draft time (`status: pending`), so the discipline
below applies to this drafting:

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md` — zero
  after T01, seven before it. The ordering constraint above is the mitigation.
  Confirmed before drafting.
- **Runtime probe for a default/severity flip (§4).** Applicable and **already
  performed**: the exact command T02's gate will run was executed at draft time
  against a real log and returned `7 validation error(s) across 13 event(s)`,
  and the corpus sweep returned the seven-type list recorded in `PLAN.md`. Those
  numbers are the enumerated failure surface; T01 is required to re-derive them
  rather than trust them.
- **Flag-scope table (§3).** Not applicable: no behavior flag is introduced.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and
why, anything the retrospective got wrong. This is your record, not the agent's
— keep it honest.>
