## Gate 1 — auto-closed (predicate=v1)

On-plan close; full retrospective ceremony skipped per
`evaluate_auto_close`.

- feature_id: FEAT-2026-0062
- predicate_version: v1
- gate_total_cost: $8.41
- gate_budget: $21.00
- reasons: [] (auto=True)

## What the loop did NOT verify (gate 1)

This terminal gate auto-closed on-plan; the full close ceremony did not
run, so the per-criterion deferred-verification list was **not**
enumerated, and there is no downstream gate to reconcile it. Before
treating the feature as fully verified, the operator MUST confirm every
acceptance criterion was actually verified in-loop (not only by artifact
shape). Any AC deferred to a post-merge or real-system step must be
recorded and completed now.

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=31 predicate=v1 -->

- **FEAT-2026-0062/T01** (`WU-01-lifetime-cost-helper.md`)
  - deferred: `tests/test_cost_lifetime.py::TestLifetimeCost::test_fold_never_ran_wu_reads_full_lifetime`
  - deferred: That test asserts a `FEAT-2026-0053/WU-07`-shaped fixture — `cost_usd: 4.281823`,
  - deferred: A test asserts the fold-ran shape does **not** double-count: a fixture with
  - deferred: A test asserts a work unit with **no** `attempt_outcome` events falls back to
  - deferred: A test asserts a missing `events.jsonl` takes the fallback path rather than
  - deferred: A test asserts a never-re-armed work unit (no cumulative, no history) returns
  - deferred: Malformed input contributes 0.0 without raising: an unparseable JSONL line, an
  - deferred: `specfuse/loop/cost.py` imports neither `loop.py` nor `arm_eval.py`. Assert with
  - deferred: **Fallback blast radius measured, not assumed.** Run the helper across all 44
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
- **FEAT-2026-0062/T02** (`WU-02-wire-both-consumers.md`)
  - deferred: `tests/test_arm_eval.py::TestArmPredicate::test_budget_projection_counts_rearmed_lifetime_spend`
  - deferred: That test passes after this WU's edits, and `python3 -m unittest tests.test_arm_eval -v`
  - deferred: A test asserts `gate_spent_usd` returns the **full $9.29** on a
  - deferred: A test asserts neither consumer double-counts on the fold-ran shape — a fixture
  - deferred: A test asserts a never-re-armed work unit produces the identical number before and
  - deferred: A test asserts the two consumers agree: over the same gate fixture,
  - deferred: `grep -n "cost_usd" specfuse/loop/arm_eval.py` shows no remaining bare per-cycle
  - deferred: `gate_spent_usd`'s docstring names `events.jsonl` as the primary source and the
  - deferred: The pre-existing budget tests still pass unmodified, or each modification is
  - deferred: A tree-wide sweep is run and recorded: `evaluate_arm_predicate` over all 44
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
- **FEAT-2026-0062/T03** (`WU-03-post-dispatch-brake-check.md`)
  - deferred: `tests/test_gate_budget_post_dispatch.py::TestPostDispatchBreach::test_final_wu_overrun_is_reported`
  - deferred: That test passes after this WU's edits, and the file's whole suite exits zero.
  - deferred: A test asserts the breach is observable after the **final** work unit of a gate
  - deferred: A test asserts a gate that halts on the existing **pre-dispatch** check still
  - deferred: A test asserts no **double report**: a gate stopped by the pre-dispatch check does
  - deferred: A test asserts a gate that stays within budget emits nothing new — the
  - deferred: A test asserts a gate with **no** `cost_budget_usd` declared emits nothing, exactly
  - deferred: The breach signal names the gate, the declared budget, and the actual spend, so an
  - deferred: The pre-existing budget tests still pass unmodified, or each modification is
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
