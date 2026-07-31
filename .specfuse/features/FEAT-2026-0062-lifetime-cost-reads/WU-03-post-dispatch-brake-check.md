---
id: FEAT-2026-0062/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - specfuse/loop/loop.py
  - tests/test_gate_budget_post_dispatch.py
produces_driver_helper:
  - _should_report_budget_breach
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-07-31T18:41:34.655597+00:00
duration_seconds: 775.766
cost_usd: 2.516068
input_tokens: 110
output_tokens: 28498
---

# Make a final-work-unit overrun visible to the per-gate brake

**Objective.** The per-gate budget brake is evaluated only *before* each dispatch, so
an overrun that happens inside a gate's last work unit cannot be seen. Add a
post-outcome breach check so the gate reports it instead of closing silently.

**Context.** Correlation ID `FEAT-2026-0062/T03`. Independent of T01 and T02: this
is about *when* the check runs, not *what it reads*. It can land before, after, or
alongside them.

`_should_halt_for_budget` (`loop.py:1821`) is called at `loop.py:5142` in the run
loop, before dispatching each work unit. The consequence, measured: FEAT-2026-0053's
gate 2 closed **$4.94 over** its $31.50 brake and the brake never fired, because the
spend that breached it was incurred by the unit the loop had already dispatched and
there was no subsequent dispatch to check against.

**Report, do not refuse — this is the decision `PLAN.md` settled.** The alternative
considered was a projected-cost pre-check refusing to dispatch a unit whose
`planned_cost_usd` would breach the budget. That was rejected: it brakes on an
estimate, and refusing real work on a guess is a larger behaviour change than
reporting a breach that has already happened. Do not implement the pre-check.

**Name the new predicate `_should_report_budget_breach`,** a sibling of
`_should_halt_for_budget` and matching its shape: read the gate's declared budget,
compare against actual spend, return a bool, and leave the emitting to the caller.
Declared in this WU's `produces_driver_helper` so the driver-wiring guard
(`authoring-work-units` §9 / FEAT-2026-0017) can see it.

**The existing pre-dispatch halt stays exactly as it is.** This WU adds a second,
later observation point. A gate that already halts before dispatch must keep
halting at the same moment, with the same event, for the same reason — the new check
must not fire redundantly on a gate the old one already stopped.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_gate_budget_post_dispatch.py::TestPostDispatchBreach::test_final_wu_overrun_is_reported`
   exists and **fails on HEAD before this WU runs** — a gate whose budget is breached
   only by its last work unit currently produces no breach signal at all.
2. That test passes after this WU's edits, and the file's whole suite exits zero.
3. A test asserts the breach is observable after the **final** work unit of a gate
   completes — the case the pre-dispatch check structurally cannot reach.
4. A test asserts a gate that halts on the existing **pre-dispatch** check still
   halts at that point, with its existing `human_escalation` /
   `gate_budget_exceeded` event unchanged. The old path is not replaced.
5. A test asserts no **double report**: a gate stopped by the pre-dispatch check does
   not also emit a post-dispatch breach for the same overrun.
6. A test asserts a gate that stays within budget emits nothing new — the
   satisfiability guarantee from `PLAN.md`, held as a test.
7. A test asserts a gate with **no** `cost_budget_usd` declared emits nothing, exactly
   as `_should_halt_for_budget` returns `False` today when no budget is set.
8. The breach signal names the gate, the declared budget, and the actual spend, so an
   operator reading it can act without opening the feature folder. If it is emitted
   as an event, its `event_type` is stated in the result — see the note below.
9. The pre-existing budget tests still pass unmodified, or each modification is
   justified inline.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.

**A constraint worth checking before you emit a new event type.**
[FEAT-2026-0060](../../roadmap.md#feat-2026-0060) records that the driver already
emits three event types absent from the envelope `event_type` enum in
`specfuse/loop/data/schemas/event.schema.json`, and that the emit path never
invokes the validator. **Do not add a fourth unsanctioned type as a side effect of
this WU.** Prefer reusing the existing `human_escalation` shape with a distinct
`reason` value. If a new type is genuinely warranted, say so in the result and
escalate rather than deciding it here — that decision belongs to FEAT-2026-0060.

**Do not touch.** `specfuse/loop/cost.py`, `specfuse/loop/arm_eval.py` — T01 and T02
own the reading side. `gate_budget_usd` and any `cost_budget_usd` value — this WU
changes when the check runs, never the threshold. The pre-dispatch call site's
existing behaviour. `specfuse/loop/data/schemas/event.schema.json`. Generated
directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run in
criteria 1–2.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
run loop has no point after a work unit's outcome where the gate is still the
current context, which would make "post-dispatch" structurally impossible and turn
this into a run-loop restructure rather than an added check; satisfying criterion 5
requires state that has to be threaded through the run loop, which is a design
change beyond this WU; or a new `event_type` appears unavoidable per the note above.
If `specfuse/loop/loop.py` is absent from the files you edited, emit `status:
blocked` — do not claim complete.
