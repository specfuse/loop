---
gate: 1
status: open
cost_budget_usd: 17.50
baseline:
  sha: 609325bfc99e05b02f52991ff3e7c7a150af2857
  probed_at: 2026-08-04T05:55:20.240228+00:00
  failing: []
---

# Gate 1 — the event log validates end to end

## Definition of done

The driver's event log validates against the envelope in every dimension, not just
`event_type`: the correlation-ID shapes `.specfuse/rules/correlation-ids.md` documents
are accepted, the rules file and the schema state the same contract, and the repo's
event gate checks the whole envelope rather than one field.

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation and roadmap status reflect what was actually built.

This gate is **terminal**: the closing sequence is a single `close` WU.

## Cost budget

`cost_budget_usd: 17.50` — the $12.50 sum of WU estimates ($4.00 / $3.50 / $5.00) plus
one re-attempt of the largest ($5.00, the close), per the GATE template's defensive
padding while the closing-WU retry defect (#260) is open.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md` and load-bearing
  here: T02's "zero errors corpus-wide" is satisfiable **only** because a measurement
  taken before drafting showed all 285 failures are `correlation_id` and every failing
  shape is a documented closing-sequence form. This is the exact check FEAT-2026-0060
  skipped — it measured `event_type` only, then authored a criterion demanding zero
  *total* errors while forbidding the only file that could deliver them. One blocked
  attempt, $4.48.
- **Runtime probe for a default/severity flip (§4).** Not applicable: no default,
  threshold, or severity changes. A pattern is widened to accept inputs the methodology
  already calls valid; the widening is strictly additive and T01 asserts that directly.
- **Flag-scope table (§3).** Not applicable: no behaviour flag introduced.

## The count will not match, and that is expected

`PLAN.md` records 285 failures across 38 folders. Every feature that closes adds more
(279 when the row was filed, 282, 285). T01 and T02 will measure a different total.
**A different number is not a discrepancy** — the shape distribution is what the
satisfiability answer rests on. A *new error class* would be a real finding; a larger
count of the same class is just time passing.

## Known limits, recorded so the close does not misread them

**This is a local override of a field another repository owns.** The vendored schema's
`$id` points at the orchestrator and its `$comment` is that repository's changelog,
which already records one upstream widening of this same pattern. The driver-local
override is the right call *here* — an unowned edit would be reverted by the next
vendor sync, silently — but it leaves the two definitions able to diverge. The close
files the upstream need so this is a recorded bridge rather than a quiet fork.

**Nothing rewrites history.** The 285 failing events are correct as emitted. The schema
is what disagreed with the documented contract, and the schema is what changes.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed and why,
anything the retrospective got wrong. This is your record, not the agent's — keep it
honest.>
