---
id: FEAT-2026-0109/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.00
oracle_env: macos_local
produces:
  - specfuse/loop/loop.py
  - tests/test_baseline_tree_hash_key.py
---

# Key the baseline record on the tree hash, not the HEAD sha

**Objective.** Make a baseline record valid for a *tree* rather than a commit,
so a bookkeeping commit that leaves the code identical does not invalidate it.

**Context.** FEAT-2026-0109/T02; read `PLAN.md` and T01. `gate_baseline_check`
(`loop.py:4618`) reuses a record only when `baseline["sha"] == head_sha`.
Every bookkeeping commit — squash, `baseline probed clean`, `halted for driver
restart` — moves the sha while leaving `specfuse/` and `tests/` untouched, so
the record is discarded and the set re-runs. That is why every restart re-probed
on the FEAT-2026-0101 run.

T01 already removes most of this cost by not probing on the green path. This
unit covers the residual: when attribution *does* run, its record should stay
valid across the bookkeeping commits that follow.

**Incremental edit to `specfuse/loop/loop.py`.** T01 delivered this file (the
attribution helper and the skipped entry call). This unit changes only the
record's key and the comparison that reads it: write `tree` alongside the
existing `sha`, and prefer `tree` when deciding reuse. T01's attribution logic
is otherwise untouched.

**The primitive.** `git rev-parse HEAD^{tree}` — the tree object of the current
commit. Prefer it over `git write-tree`, which requires a clean index and would
couple the record to staging state.

**Compatibility.** A record written before this unit has no `tree` key. Fall
back to the `sha` comparison for those rather than discarding them, so an
in-flight feature does not re-probe once on upgrade for no reason. Keep `sha`
in the record: it is what a human reads to locate the commit.

**Acceptance criteria.**

- `tests/test_baseline_tree_hash_key.py::test_bookkeeping_commit_preserves_the_record` fails on HEAD and passes after: writing a record, then making a commit that changes no tracked file content under `specfuse/` or `tests/`, leaves the record valid and re-runs nothing.
- `::test_a_real_code_change_invalidates_the_record`: editing a tracked source file changes the tree hash and does invalidate it — the boundary that stops this from being a stale-record bug.
- `::test_legacy_record_without_tree_falls_back_to_sha`: a record carrying only `sha` is honoured on its old terms, not discarded.
- `::test_record_still_carries_sha_for_human_reading`: the written record contains both keys.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** T01's attribution trigger and its once-per-gate bound; T03's
provenance field; `verify()` and the `feature_oracle` path; `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml`, plus this
gate's `feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if `HEAD^{tree}` is not
resolvable in the driver's working context (e.g. mid-rebase or detached states
the driver can legitimately be in) and no equally cheap primitive covers those
cases — say what was observed rather than falling back to hashing files by
hand.
</content>
