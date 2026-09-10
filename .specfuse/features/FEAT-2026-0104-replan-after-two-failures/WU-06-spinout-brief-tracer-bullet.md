---
id: FEAT-2026-0104/T06
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.50
produces_driver_helper:
  - format_spinout_escalation_brief
produces:
  - tests/test_spinout_brief_end_to_end.py
---

# Wire the spin-out brief end to end

**Objective.** Make gate 2's `feature_oracle` runnable and green by rendering
a six-part operator brief at the attempt-exhaustion halt and carrying it on
the escalation record — the whole path, none of it well.

**Context.** FEAT-2026-0104/T06. This is the gate's **tracer bullet**
(`/authoring-work-units` §14): stubs are permitted in this unit and nowhere
else in the gate. Today that halt prints one line — measured, not recalled:
`   BLOCKED after 3 attempts — escalated (spinning_detected)` — and the
`human_escalation` payload carries `reason`, `attempts`, `attempts_usage`
and nothing a person can read. The sibling that already does this right is
`format_human_unit_brief` (`loop.py:2911`), which renders under
`ESCALATION_PART_HEADINGS` imported from `specfuse/loop/escalation.py` so the
printed brief and an escalation issue can never disagree about part names;
follow it. It omits the `<!-- specfuse:escalation id=… -->` marker and so
does not satisfy `validate_escalation_body`; this brief must carry the marker
with the WU id as its correlation id. The option text and the recommendation
are T07's — stub them to the thinnest thing the oracle can observe.

**Acceptance criteria.**

- `python3 -m unittest tests.test_spinout_brief_end_to_end -v -b` fails on
  HEAD before this unit's edits (the module does not exist) and passes after.
- The end-to-end test drives a real `loop.run()` to attempt exhaustion —
  harness as in `tests/test_lazy_baseline_e2e.py`, `integration_workspace()`
  plus stubbed `dispatch`/`verify`/`probe_baseline` — and asserts
  `escalation.validate_escalation_body()` returns `[]` for the brief the run
  itself printed. Composing a brief in the test and validating that instead
  is the failure `[FEAT-2026-0108/G1-CLOSE]` names; assert on the run's own
  output.
- The same brief text is on the `human_escalation` event's payload under
  `message`, as `halt_for_human_unit` already does, so `/attention` and
  `/gate-status` read the brief rather than re-derive it.
- Part 1 states the unit's attempt history from that run, including whether
  the automatic re-plan fired — the probe in `GATE-02.md` shows it always has
  by this point on an eligible unit.

**Do not touch.** `format_human_unit_brief` and the `human_step_required`
path — a `human` unit is not a spin-out and T07 owns which reasons get this
brief. `specfuse/loop/escalation.py` — import its headings and validator, do
not widen them. The sibling WU files in this gate.

**Verification.** The narrow tier is NOT sufficient for this unit: it edits
the central dispatch loop's escalation branch, which many modules drive
through `loop.run()`, so run the **full** suite —
`python3 -m unittest discover -s tests -b` — before reporting complete.
Narrow tier for `implementation`: the `code` gates minus `tier: broad`, plus
`python3 -m unittest tests.test_spinout_brief_end_to_end -v -b`. Symbol check
(§9): `python3 -c "from specfuse.loop.loop import format_spinout_escalation_brief"`.

**Escalation triggers.** Stop with `status: blocked` if a six-part brief
cannot be rendered without inventing a part — a part with nothing to say is
stated as such per `.specfuse/rules/operator-escalation.md`, never dropped or
padded. Stop also if the brief cannot reach the event payload without
changing the driver event schema; that is a separate unit, not a widening of
this one.
