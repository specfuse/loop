---
id: FEAT-2026-0053/T04
type: implementation
status: done
attempts: 1
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-07-30T20:03:52+00:00
    prior_status: blocked_human
    prior_attempts: 1
    prior_cost_usd: 1.220458
    prior_duration_seconds: 209.885
    reason: "AC#2 narrowed to drop the schema requirement; registry gap tracked separately"
planned_cost_usd: 3.00
produces:
  - tests/test_arm_eval_wiring.py
produces_driver_helper:
  - evaluate_arm_predicate call site at the awaiting_review flip
  - write_baseline_if_absent call site at first dispatch
duration_seconds: 580.185
cost_usd: 2.536497
input_tokens: 114
output_tokens: 22900
cumulative_cost_usd: 1.220458
cumulative_duration_seconds: 209.885
cumulative_input_tokens: 58
cumulative_output_tokens: 14684
cumulative_attempts: 1
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.1
started_at: 2026-07-30T20:40:48.530269+00:00
folded_through_re_arm: 1
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

**Cross-surface value (authoring §8) — resolved, do NOT re-litigate.** An
earlier attempt of this WU blocked on escalation trigger 2 below, correctly:
`validate_event.py`'s per-type registry (`PER_TYPE_SCHEMA_DIR`,
`specfuse/loop/data/schemas/events/`) holds four schemas, all core-orchestrator
event types vendored from another repo, and the envelope's `event_type` enum in
`event.schema.json` is a closed 28-entry list this repo does not own. There is
no sanctioned in-repo mechanism to extend either.

**This WU adds no per-type schema and does not touch the enum.** That matches
what the driver already does: `gate_reached` and `attempt_outcome` are emitted
on every run and appear in neither the enum nor the per-type registry, and the
driver's emit path (`build_event` / `flush_events` in `loop.py`) never invokes
the validator — `validate_event.py` is a standalone CLI. `arm_predicate_evaluated`
follows that existing precedent rather than establishing a new one. The
registry gap is real, spans three driver-local event types and two repos, and is
tracked as its own roadmap feature; it is explicitly out of scope here.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_arm_eval_wiring.py::TestShadowWiring::test_gate_close_emits_arm_predicate_event`
   exists and **fails on HEAD before this WU runs** (file does not yet exist —
   red).
2. Every `awaiting_review` flip appends exactly one `arm_predicate_evaluated`
   event carrying the full per-class evaluation and the overall `would_arm`.
   No per-type schema is added and the envelope enum is not touched (see
   Cross-surface value above) — the test asserts the payload shape directly
   against the keys it expects.
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
iteration run: `python3 -m unittest tests.test_arm_eval_wiring -v`. Do **not**
run `validate_event.py` over the generated event — `arm_predicate_evaluated` is
absent from the envelope `event_type` enum by design (above), so that check
fails for a reason unrelated to this WU's work, exactly as it does today for
`gate_reached`. Assert the payload's keys and types in the test instead.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
the `awaiting_review` flip enumeration finds sites whose context makes a single
shared wiring point impossible without refactoring the close path — refactors
are a different unit.

The former trigger 2 (per-type schema registry contradicts this WU's
assumption) fired on attempt 1 and has been **resolved by the operator**: no
schema is added, no enum is touched. Do not re-block on it. If some *other*
cross-surface contract turns out to contradict this WU, that is still a block —
name the specific mismatch.
