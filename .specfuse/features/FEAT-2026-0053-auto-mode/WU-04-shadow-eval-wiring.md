---
id: FEAT-2026-0053/T04
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - tests/test_arm_eval_wiring.py
  - specfuse/loop/data/schemas/events/arm_predicate_evaluated.schema.json
produces_driver_helper:
  - evaluate_arm_predicate call site at the awaiting_review flip
  - write_baseline_if_absent call site at first dispatch
---

# Shadow wiring — evaluate and emit at every `awaiting_review` flip

**Objective.** Wire the baseline write into first dispatch and the arm predicate
into every gate close, emitting one `arm_predicate_evaluated` event per close —
with zero behavior change to arming.

**Context.** Correlation ID `FEAT-2026-0053/T04`. Two call sites in
`specfuse/loop/loop.py`:

- **First dispatch of a feature:** call `write_baseline_if_absent` (T01) so
  every feature the driver touches from now on has a baseline.
- **Every gate → `awaiting_review` flip:** call `evaluate_arm_predicate` (T03)
  and append one `arm_predicate_evaluated` event to `events.jsonl` carrying the
  full per-class evaluation and the overall `would_arm`.

**No behavior change is the load-bearing property.** The driver halts at
`awaiting_review` exactly as today regardless of the verdict. Acting on the
verdict is gate 2, behind the dial. A reviewer must be able to read this WU's
diff and see that the control flow after the event append is byte-identical to
before.

**Enumeration first (authoring §10):** grep for every site that flips a gate to
`awaiting_review` before wiring — `grep -n "awaiting_review" specfuse/loop/loop.py`.
Every flip site is in scope, or the WU blocks naming the extras.

**Cross-surface value (authoring §8):** the event type name
`arm_predicate_evaluated` and its schema home must match `validate_event.py`'s
per-type registry — schema files live in the directory `PER_TYPE_SCHEMA_DIR`
points at, one `<event_type>.schema.json` per type. Verify the exact directory
and existing schema shapes against the source before locking the payload;
mirror an existing per-type schema (e.g. `attempt_outcome`) rather than
inventing a new envelope.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_arm_eval_wiring.py::TestShadowWiring::test_gate_close_emits_arm_predicate_event`
   exists and **fails on HEAD before this WU runs** (file does not yet exist —
   red).
2. Every `awaiting_review` flip appends exactly one `arm_predicate_evaluated`
   event whose payload validates against the schema this WU adds to the
   per-type registry.
3. Driver control flow is verdict-independent — a test closes a gate whose
   evaluation yields `would_arm: True` and asserts the driver still halts at
   `awaiting_review`.
4. A predicate exception degrades to an event with an `evaluation_error` field
   and the close path completes — the shadow trail must never crash a gate
   close.
5. `tests/test_arm_eval_wiring.py::TestShadowWiring::test_gate_close_emits_arm_predicate_event`
   **passes after this WU's edits**.

**Do not touch.** `specfuse/loop/arm_eval.py` and
`specfuse/loop/plan_baseline.py` beyond importing them — evaluation logic
belongs to T03, snapshot logic to T01; if wiring reveals a defect in either,
block rather than patch it here. The arming/halt control flow itself.
Generated directories, secrets, `.git/`. The driver owns all git — edit files
only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_arm_eval_wiring -v`. Event
validation: run `validate_event.py` over a generated event in the test.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the `awaiting_review` flip enumeration finds sites whose context makes a single
shared wiring point impossible without refactoring the close path — refactors
are a different unit; or the per-type schema registry's shape contradicts what
this WU assumes (name the mismatch; do not invent an envelope).
