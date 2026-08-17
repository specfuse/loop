---
gate: 2
status: passed
cost_budget_usd: 25.00
baseline:
  sha: 0d5a40edbd606c994de8edd64fda53fb9de6eab9
  probed_at: 2026-08-16T20:25:59.374084+00:00
  failing: []
---

# Gate 2 — drafting from answers

An answered question issue produces a linted feature folder, with every
defaulted decision recorded as an explicit assumption, and `FeatureProvider`
dispatches this path instead of escalating.

## Definition of done

- Every implementation work unit in this gate is `done`.
- The question issue instructs a reply shape its own parser accepts — a reply
  copied out of the issue binds to every question (T04).
- `/draft-feature` documents an answers-supplied mode in which answers, not a
  live human, authorize a write; the drafted folder lands `planned` and unarmed
  (T05).
- A `draft_ready` answer set produces the argv and prompt for one headless
  drafting session, and a `fallback` result produces none (T06).
- `FeatureProvider` dispatches that path on `needs_drafting` instead of
  escalating, and its `fallback` payload is still equal field-for-field to
  today's (T07, D3).
- A retrospective exists, lessons are staged to `LEARNINGS-pending.md`
  (`autonomy_default: auto`), and the terminal verdict is written.

The terminal `close` work unit was pre-declared in `PLAN.md` so the linter
reads this gate, not gate 1, as the feature's terminal gate; `G1-PLAN` inserted
this gate's substantive units *before* it.

## Out of scope for this gate

- Answering the questions. The operator answers; no code path supplies a value
  for an elicitation question.
- Gate-1 review of whatever this path drafts — that checkpoint stays human
  under every dial.
- Any change to `specfuse/loop/escalation.py`, including
  `render_escalation_body`'s reply instruction and `CATEGORY_LABELS`.

## Arming discipline

`GATE-02-REVIEW.md` carries the runtime probe, the
`driver_edit.is_driver_module_path` predicate check, the cross-repo contracts
table, and two open questions. Both must be answered before arming:

- **T05 carries `human_only: true`** and must not be armed on a silent read —
  it restates a rule humans rely on.
- **T04 is armed first.** The gate's later units consume its output; without it
  the interview cannot be answered at all.

The probe found **no observed operator reply** — gate 1 posted no issue and
auto-closed — so this gate's parsing criteria are drafted against a measured
round-trip, not against a human. That limit is recorded rather than assumed
away, and gate 2's close is where a first real reply would be reported.
