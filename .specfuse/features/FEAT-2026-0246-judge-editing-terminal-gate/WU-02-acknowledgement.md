---
id: FEAT-2026-0246/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/loop/arm_eval.py
  - specfuse/loop/loop.py
  - specfuse/loop/lint_plan.py
  - specfuse/loop/data/schemas/driver-event.schema.json
  - tests/test_arm_eval_terminal.py
  - tests/test_terminal_judge_editing_end_to_end.py
  - tests/test_lint_judge_edit_acknowledged.py
model: sonnet
effort: medium
gate_set: code
produces_driver_helper:
  - stop_for_terminal_judge_edit
---

# T02 — an operator's acknowledgement clears the stop, and only for the paths it names

**Objective.** An operator clears a `judge_editing_terminal` halt by writing an
acknowledgement into the close unit. A re-run proceeds when the acknowledgement covers
every current hit, records the operator's reason, and re-fires on any hit it does not
cover (PLAN decision 4).

**Context.** `FEAT-2026-0246/T02`. The field, on the terminal close unit's frontmatter:

```yaml
judge_edit_acknowledged:
  paths: [specfuse/loop/arm_eval.py]
  reason: "<the operator's own words>"
```

The shape follows the operator-authored `re_arm_override` field
(`rearm_reproduction_gate`, `loop.py`). The driver never writes this field, and no
skill authors its `reason` (`operator-escalation.md`: never author the operator's own
justification).

`arm_eval.evaluate_terminal_judge_editing` gains the acknowledgement read: a hit is
covered when its path is in `paths` (a `produces_driver_helper` hit is covered by the
literal entry `produces_driver_helper`). All hits covered → `clean`, with the reason
naming the acknowledged paths. Any uncovered hit → `fired`, naming only the uncovered
ones. `loop.py`'s `stop_for_terminal_judge_edit` emits `terminal_judge_editing_acknowledged` (paths, reason, close unit
id) when a check is clean because of an acknowledgement; register it in
`driver-event.schema.json`.

`lint_plan.py`: an ERROR when `judge_edit_acknowledged` is present on any unit and is
not a mapping with a non-empty list of string `paths` and a non-empty string `reason`,
or when it sits on a unit whose type is not `close`.

Un-skip `AcknowledgedStopProceeds` and `NewPathRefires` in the oracle module.

**Acceptance criteria.**

1. `tests/test_terminal_judge_editing_end_to_end.py::AcknowledgedStopProceeds` and
   `::NewPathRefires` fail on HEAD (skipped, then failing once un-skipped before the
   change) and pass after: the fixture halts, the test writes the field and flips the
   close unit to `pending` (what `/unblock-wu` does), the re-run dispatches the close,
   and `events.jsonl` carries `terminal_judge_editing_acknowledged` with the reason;
   adding a second judge path to a done unit after acknowledgement halts again naming
   only the new path.
2. `tests/test_arm_eval_terminal.py` adds: full coverage → clean; partial coverage →
   fired naming only uncovered paths; a `produces_driver_helper` hit covered by the
   literal entry; an acknowledgement on a feature with no hits → clean with no
   acknowledgement event.
3. `tests/test_lint_judge_edit_acknowledged.py` covers: valid field passes; missing
   `reason`, empty `reason`, empty `paths`, non-list `paths`, and the field on an
   `implementation` unit are each an ERROR — every case paired with the valid fixture.
4. `specfuse lint .specfuse/features/FEAT-2026-0246-judge-editing-terminal-gate`
   exits 0.

**Do not touch.** The brief text (T03). Docs (T04). `/unblock-wu` itself — it already
flips `blocked_human` → `pending`.

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If `_miniyaml` cannot parse the nested mapping with a flow
list, stop and escalate: the documented field shape would need to change, which is a
user-facing decision.
