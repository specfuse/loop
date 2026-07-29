---
id: FEAT-2026-0053/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/plan_baseline.py
  - tests/test_plan_baseline.py
produces_driver_helper:
  - write_baseline_if_absent
  - load_baseline
---

# Snapshot the as-activated plan graph as an immutable baseline

**Objective.** Ship `plan_baseline.py`: the driver writes a one-time JSON
snapshot of a feature's PLAN graph on first dispatch, and every later drift
measurement reads it.

**Context.** Correlation ID `FEAT-2026-0053/T01`. Drift detection (T03's added-WU
/ added-gate / retroactive-edit classes) needs a stable reference to the
as-activated graph. Git archaeology was rejected at drafting — the driver stays
dumb and reads files, not history. The baseline is therefore an explicit
artifact: `PLAN.baseline.json` in the feature directory, written once, never
rewritten. Immutability is the entire point — a baseline that can be refreshed
is a drift detector that can be gamed by drifting.

The snapshot captures, per gate: gate number, and per WU the `id`, `type`, the
goal line (the WU's `# ` title line from its file when present, else the id),
and `planned_cost_usd`. Parse PLAN.md with the existing `_miniyaml.py` /
frontmatter helpers the driver already uses — do not hand-roll a YAML subset.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_plan_baseline.py::TestBaseline::test_first_dispatch_writes_baseline_once`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. `specfuse/loop/plan_baseline.py` defines
   `write_baseline_if_absent(feature_dir, plan)` writing
   `<feature_dir>/PLAN.baseline.json` with per-gate WU ids, types, goal lines,
   and planned costs.
3. A second call against an existing baseline is a no-op: the file's bytes are
   identical before and after, asserted by a test that mutates the plan between
   calls and shows the baseline did not follow.
4. `load_baseline(feature_dir)` returns the parsed snapshot, and returns `None`
   when the file is absent — features predating this mechanism degrade
   gracefully rather than crash.
5. `tests/test_plan_baseline.py::TestBaseline::test_first_dispatch_writes_baseline_once`
   **passes after this WU's edits**.

**Do not touch.** `specfuse/loop/loop.py` — the dispatch-time call site is T04's
wiring territory; this unit ships the module and its tests only.
`specfuse/loop/_miniyaml.py` (consume, never modify). Sibling WU files in this
gate. Generated directories, secrets, `.git/`. The driver owns all git — edit
files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml` (tests, lint,
security, coverage ≥ 90%, leak-scan, monitoring-example-lint, bats gates), plus
symbol existence:
`python3 -c "from specfuse.loop.plan_baseline import write_baseline_if_absent, load_baseline"`.
Scoped iteration run: `python3 -m unittest tests.test_plan_baseline -v`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
PLAN parsing cannot be done with the existing frontmatter/`_miniyaml` helpers
and would require modifying the parser — parser changes are a different unit of
work; or `write_baseline_if_absent` / `load_baseline` are absent from the files
you edited — do not claim complete.
