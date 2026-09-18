---
id: FEAT-2026-0113/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/loop/triage.py
  - tests/test_triage_severity_write.py
---

# T04 — the write path records severity: marker first, label second

**Objective.** `render_marker` and `apply_triage` record a severity in the marker
and project it as a `severity:<value>` label, in that order.

**Context.** `PLAN.md`'s **Record precedence** section is binding and is not a
variation point: the marker's `severity=` field is the authoritative record, the
label is a projection re-derived from it, and the marker is written first. A
failed label write then leaves an issue correctly classified and merely lacking a
swatch; the reverse order would leave an issue labelled that still scans as
carrying no severity.

`apply_triage` already implements exactly this shape for the category — marker
write, then `--add-label`, with a label failure recorded on the returned row and
never raised — and already carries the "marker present, label missing" repair
branch (`specfuse/loop/triage.py:164`). This unit extends both to severity and
changes no classification: the severity arrives on the decision mapping, and T05
is what puts it there.

Gate 1 made the reader tolerant of this field before anything wrote it, and
proved the two-field form reads byte-identically (`RETROSPECTIVE.md`, gate 1).
That proof is what this unit is allowed to build on, and criterion 2 is what
keeps it true.

**Acceptance criteria.**

1. `tests/test_triage_severity_write.py::SeverityWrite::test_marker_is_written_before_label`
   fails on HEAD before this unit runs and passes after, asserting on the **order**
   of the injected runner's recorded calls, not merely on their presence.
2. `render_marker` emits today's two-field string byte-identically when no severity
   is given — asserted by string equality against a literal — and appends
   `severity=<value>` as a third field, after `confidence`, when one is.
3. A decision carrying no `severity` key produces the identical `gh` argv sequence
   `apply_triage` produces today, asserted sequence-to-sequence against the
   pre-existing expectation in `tests/test_triage_apply.py`.
4. A failed `severity:<value>` label write is recorded on the returned row and
   never raised, and the marker it projects from is left in place — the failure
   mode the precedence exists to make safe.
5. The repair branch is idempotent for severity: an issue whose marker carries
   `severity=high` but whose labels lack `severity:high` gets the label added on a
   re-run; one already carrying it is left untouched, and neither re-writes the
   marker.

**Do not touch.** `parse_marker`'s `(category, confidence)` return type — severity
is reached through `parse_marker_fields`, which gate 1 added for exactly this. Its
call sites in the four other modules that read the marker:
`specfuse/agent/state.py:167`,
`specfuse/agent/triage_invoke.py:70`, `specfuse/loop/bug_lane_run.py:488`,
`specfuse/loop/bug_lane_state.py:209` (the count and the paths are gate 1's
retrospective finding, not `PLAN.md`'s older three-caller list).
`specfuse/loop/promotion.py`, which defines its own unrelated `parse_marker` /
`render_marker` over the `specfuse:promoted` marker and greps like a caller
without being one. `specfuse/loop/labels.py` (T03). The classification prompt in
`specfuse/agent/triage_invoke.py` (T05). `CATEGORIES` / `CONFIDENCES`.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_triage tests.test_triage_apply tests.test_marker_dual_shape tests.test_caller_check_ratchet -b`.

**Escalation triggers.** If recording severity appears to require changing
`parse_marker`'s return type or editing a call site outside
`specfuse/loop/triage.py`, stop — that is a wider contract change than this unit
permits. If the two-field `render_marker` output cannot be kept byte-identical,
stop and escalate rather than adjusting the literal: every marker already written
in the wild is read against that string, and gate 1's entire proof rests on it.
