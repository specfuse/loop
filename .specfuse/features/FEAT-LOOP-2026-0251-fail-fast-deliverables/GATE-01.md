---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_fail_fast_deliverables -v -b"
cost_budget_usd: 14.00
---

# Gate 1 — a missing deliverable is refused before any verification gate runs

## Definition of done

**Stated as an outcome.** In temporary feature folders, with a stubbed agent session that
leaves a known diff and a `verify_fn` that counts its calls:

1. **`produces_not_in_diff` early.** An attempt whose diff leaves a declared `produces:` path
   untouched, with no `produces_unchanged:` / `produces_amended:` in its RESULT, ends
   `produces_not_in_diff` with `verify_fn` called zero times, `verify_seconds: 0` and no
   `gate_result` events. The same unit with the path changed calls `verify_fn` once and passes.
2. **Presence early.** `deliverable_missing` (a declared path absent or empty) and
   `no_deliverable_files` (the diff names only the unit file and events) are likewise refused
   with `verify_fn` never called.
3. **Opt-out.** With `defaults.fail_fast_deliverables: false`, each of the three cases calls
   `verify_fn` before refusing, with the same outcome and failure class as today.
4. **Tree and note.** An early refusal keeps or resets the tree per
   `defaults.retain_on_guard_refusal`, as the late refusal does; its retry note states that
   verification did not run and lists the paths this attempt changed (or says it changed
   none).
5. **Arm-time warning.** `specfuse lint` prints a WARN for a dispatchable unit whose `produces:`
   path appears nowhere in its body, by full path or file name, and stays silent when it does.
6. **Nothing else changes.** Every existing test of the three guards passes unchanged, apart
   from assertions on the order of `verify` and the guard, which are updated and named in the
   close.

The `feature_oracle` proves 1–5. It is red on the current tree; `FEAT-LOOP-2026-0251/T01` is the
walking skeleton that creates `tests/test_fail_fast_deliverables.py` and turns clause 1 green,
with every other class `unittest.skip` naming its owner (T02–T04). A skip surviving to the close
is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One decision, two call sites.** The early and late checks call the same helper; a
  duplicated condition is a defect.
- **Positive controls.** Clause 1 pairs a refused attempt with a passing one; clause 3 pairs
  the opt-out with the default; clause 5 pairs a mentioned path with an unmentioned one.
- **Counted, not inferred.** "Verification did not run" is asserted by a call counter on
  `verify_fn`, never by timing.
- **Expected self-halt.** `loop.py` and `lint_plan.py` are judge surfaces; acknowledge the stop
  with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
