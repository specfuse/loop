## Gate 1 — auto-closed (predicate=v1)

On-plan close; full retrospective ceremony skipped per
`evaluate_auto_close`.

- feature_id: FEAT-2026-0063
- predicate_version: v1
- gate_total_cost: $3.63
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

<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03 criteria=27 predicate=v1 -->

- **FEAT-2026-0063/T01** (`WU-01-arm-sweep-module.md`)
  - deferred: `tests/test_arm_sweep.py::TestArmSweep::test_excluded_features_reported_not_dropped`
  - deferred: That test builds a fixture root holding two features — one with
  - deferred: A test asserts a feature whose `PLAN.md` raises during evaluation appears in the
  - deferred: A test asserts per-class observation records the *absence* of a status: a fixture
  - deferred: A test asserts gates are read from each feature's own `PLAN.md` graph — a
  - deferred: A test asserts first-observation is recorded as (feature_id, gate) and is the
  - deferred: `specfuse/loop/arm_sweep.py` does not import `loop.py`, and neither `arm_eval.py`
  - deferred: **Run against the real tree and record the numbers.** Sweep
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
- **FEAT-2026-0063/T02** (`WU-02-coverage-gate.md`)
  - deferred: `tests/test_arm_sweep_gate.py::TestArmSweepGate::test_unevaluable_feature_fails_the_gate`
  - deferred: That test builds a fixture root containing a baselined feature whose `PLAN.md`
  - deferred: A test asserts a fixture where every evaluable feature sweeps cleanly and no
  - deferred: A test asserts a `not_evaluable` verdict among evaluable features exits 1 and
  - deferred: A test asserts the branch-observation table is printed on stdout on both the
  - deferred: A test asserts an empty evaluable set (no baselined feature anywhere) exits 0 with
  - deferred: The entry point's docstring states, in plain sentences, that the gate does not
  - deferred: `.specfuse/verification.yml` carries the new gate with a comment recording the
  - deferred: **The gate exits 0 on this tree.** Run it against the real
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
- **FEAT-2026-0063/T03** (`WU-03-observed-branch-record.md`)
  - deferred: The section states, per class, which verdict branches have been observed on real
  - deferred: The section carries an explicit measurement date and the exact command to
  - deferred: The section names the never-fired classes explicitly as **unverified**, and states
  - deferred: The section states that the sample is small and grows by one per baselined
  - deferred: It does **not** claim the five never-fired classes are broken. Never having fired
  - deferred: `docs/concepts/autonomy-stop-classes.md` and
  - deferred: `tests/test_scaffold_data_in_sync.py` passes — the specific guard this WU is most
  - deferred: The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
