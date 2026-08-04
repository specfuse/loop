---
id: FEAT-2026-0073/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
produces:
  - .specfuse/scripts/event_type_gate.py
  - .specfuse/verification.yml
  - tests/test_event_gate_full_envelope.py
oracle_env: macos_local
duration_seconds: 2510.488
cost_usd: 5.46923
input_tokens: 278
output_tokens: 54985
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-08-04T05:52:43+00:00
    prior_status: blocked_human
    prior_attempts: 3
    prior_cost_usd: 5.46923
    prior_duration_seconds: 2510.488
    reason: "Agent-authored on the operator's standing overnight instruction; the operator was away. The WU body was amended, not retried as-is: its own rename invitation contradicted its produces list, so a rename made the declared deliverable absent (attempt 1 DELIVERABLE MISSING) and keeping the name left a declared path with no diff (attempts 2-3 FILES_CHANGED MISMATCH). The invitation is withdrawn and criterion 6 now names the exact verification.yml comment to rewrite."
---

# Widen the gate from one field to the whole envelope

**Objective.** `event_type_gate.py` checks `event_type` errors only, deliberately, and
says so in its own docstring: the scoping exists because 279 `correlation_id` errors
made a whole-envelope gate impossible. T01 removes that reason. This work unit widens
the gate to the full envelope and leaves it exiting 0.

**Context.** Correlation ID `FEAT-2026-0073/T02`. Read `PLAN.md` and T01's result
first. The gate's docstring records the scoping and names this feature as the condition
for widening it — that comment is now stale and must go with the change.

**Why this is safe to assert.** T02's criterion is "zero errors corpus-wide," which is
satisfiable **only** because every failure measured before drafting was
`correlation_id` and every failing shape was a documented closing form. That
measurement is in `PLAN.md`:

```
285 errors across 38 folders — {'correlation_id': 285, 'other': 0}
```

If T01 did its job the count goes to zero. **If it does not, that is a finding, not a
criterion to soften** — see the escalation triggers.

**Do NOT rename the file, and do not rename the gate.** `event_type_gate.py` keeps its
path and `event-type-gate` keeps its `verification.yml` name. The name is admittedly a
poor fit once the gate validates the whole envelope, and an earlier draft of this work
unit invited a rename — that invitation was a defect and is withdrawn.

It contradicted this work unit's own `produces` list, which declares
`.specfuse/scripts/event_type_gate.py`. A rename makes that declared deliverable absent,
the presence gate fires `DELIVERABLE MISSING`, and no amount of correct work can satisfy
both. That is precisely what happened on the first attempt of this WU, and the two
attempts after it escalated as `spinning_detected` at a cost of $5.47. The rename is
cosmetic; the scope change is the deliverable. If the name still grates once this lands,
it is a one-line follow-up bug, not this work unit's business.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_event_gate_full_envelope.py::TestEventGateFullEnvelope::test_non_event_type_error_now_fails_the_gate`
   exists and **fails on HEAD before this WU runs** (today's gate ignores every
   non-`event_type` error, so a fixture carrying one exits 0; that counts as red).
2. That test plants an event with a malformed `correlation_id` — one that is malformed
   under T01's *widened* pattern, not merely under the old one — and asserts the gate
   exits 1 and names the offending file, line, and field. It passes after this WU.
3. A test asserts a corpus with no errors of any kind exits 0 and prints a summary
   naming what was checked and the counts.
4. **The gate exits 0 on this tree.** Run it against the real `.specfuse/features/`
   corpus and quote the exit code and summary in the result.
5. The docstring's scoping paragraph — the one explaining that the gate is narrowed to
   `event_type` because `correlation_id` errors remain — is **removed or rewritten**. A
   stale comment claiming a narrower scope than the code has is worse than none.
6. `.specfuse/verification.yml`'s comment on the `event-type-gate` entry is rewritten.
   It currently reads *"scoped to event_type errors only … 279 correlation_id errors
   remain … Widen once 0073 lands"* — every clause of which this feature falsifies. The
   `command:` line and the gate's `name:` are unchanged; the comment is the diff. This
   file **must** show a real diff, because it is in `produces` and the driver's
   files-changed cross-check compares against HEAD.
7. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/loop/validate_event.py` and
`specfuse/loop/data/schemas/driver-event.schema.json` — T01 owns the override; if the
gate needs a validator behaviour that does not exist, that is an escalation, not a quiet
edit to T01's work. `specfuse/loop/data/schemas/event.schema.json` — never, in either
work unit. Historical `events.jsonl` files: if the corpus still has errors, they are
reported, never edited away.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Plus criterion 4: the widened gate must run
green against the real corpus with the exit code quoted. A gate wired into
`verification.yml` that has never been run against real input is a failure shape this
project has shipped against twice.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
corpus still carries errors after T01 and they are **not** `correlation_id` — report the
class, the count, and a sample offender, because `PLAN.md`'s satisfiability answer rests
on `other: 0` and a non-zero other class means that answer was wrong; or the remaining
errors are `correlation_id` shapes T01's widening does not cover, which means the
documented contract is incomplete rather than the schema being wrong. Do **not** narrow
the gate back to a subset of fields to make it green — the narrowing is precisely what
this work unit exists to remove, and re-adding it under a new name would hide the
finding that motivated the block.
