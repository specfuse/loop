---
id: FEAT-2026-0104/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces_driver_helper:
  - emit_replan_event
produces:
  - tests/test_replan_event_emission.py
---

# Emit the replan event into the consumer that already waits for it

**Objective.** Emit `event_type: "replan"` when a re-plan fires, register the
type so the repo's own event gate accepts it, and prove the event reaches
`gate_eval`'s auto-close check.

**Context.** FEAT-2026-0104/T04. This is the seam where the emitter meets a
consumer built two years of features ago and never fed: `gate_eval.py:197`
treats a `replan` event as check 2 of `evaluate_auto_close`, disabling
auto-close for the gate, documented at `docs/methodology.md:187` and fixtured
by FEAT-2026-0018/T02's `TestReplanEvent`. `replan` is **not** in
`specfuse/loop/data/schemas/driver-event.schema.json` (15 types today), so
emitting it without registering it fails the repo's `event-type-gate`.

`[FEAT-2026-0108/G1-CLOSE]` is the reason the third criterion below is written
the way it is: a gate whose producer and renderer each passed on constructed
inputs shipped a behaviour that did not exist, because no criterion crossed
the seam. Do not assert this one against a hand-built event dict.

**Acceptance criteria.**

- `python3 -m unittest tests.test_replan_event_emission -v -b` fails on HEAD
  before this unit's edits and passes after.
- `python3 .specfuse/scripts/event_type_gate.py` exits 0 with a real emitted
  `replan` event in the corpus — which requires `replan` added to
  `driver-event.schema.json`'s `event_types`.
- The validation assertion is scoped to the `replan` event this unit emits,
  not to every line of a synthetic fixture's `events.jsonl`. A previous
  attempt asserted zero offenders across the whole file and failed on 19
  unrelated envelope complaints from other event types, which says nothing
  about whether `replan` validates.


**Do not touch.** `gate_eval.py`'s consumer logic — it is already correct and
this unit's job is to satisfy it, not to edit it. The vendored
`event.schema.json` (only the driver-local registry is ours to extend). The
sibling WU files in this gate.

**Verification.** The narrow tier is NOT sufficient for this unit: it edits
the central dispatch loop, which 44 test modules drive through `loop.run()`,
so run the **full** suite — `python3 -m unittest discover -s tests -b`, OK on
3901 tests in ~151s on a clean tree — before reporting complete. Narrow tier for `implementation`, plus
`python3 -m unittest tests.test_replan_event_emission tests.test_replan_end_to_end -v -b`
and `python3 .specfuse/scripts/event_type_gate.py`.

**Escalation triggers.** Stop with `status: blocked` if `replan` cannot be
added to the driver registry without also touching the vendored envelope —
that crosses a boundary `validate_event.py` documents as deliberate.
