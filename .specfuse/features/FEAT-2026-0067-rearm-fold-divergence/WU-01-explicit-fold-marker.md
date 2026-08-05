---
id: FEAT-2026-0067/T01
type: implementation
status: pending
planned_cost_usd: 4.00
produces:
  - specfuse/loop/loop.py
  - tests/test_rearm_fold_marker.py
produces_driver_helper: "detect_rearm_dispatch, fold_cumulative_on_rearm"
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
---

# The fold is triggered by an explicit marker, not by a value

**Objective.** Replace `detect_rearm_dispatch`'s `cost_usd > 0` guard with an
explicit fold marker, so the fold runs on every re-arm regardless of what the
prior cycle cost.

**Context.** Correlation ID `FEAT-2026-0067/T01`. Read `PLAN.md` first — it
records why *converge* was chosen over *admit two paths*, and the census that
sizes the migration T02 will do.

**The defect, precisely.** `detect_rearm_dispatch` returns True only when
`cost_usd > 0`. A zero means either "the prior cycle cost nothing" or "a prior
fold already moved it", and the function cannot tell those apart. When it
guesses wrong the fold never runs and the spend survives only in
`re_arm_history[].prior_cost_usd`.

**The marker.** Add `folded_through_re_arm` (int) to the WU frontmatter. A fold
is owed when `re_arm_count > folded_through_re_arm`; `fold_cumulative_on_rearm`
stamps `folded_through_re_arm = re_arm_count` as part of the same write set it
already uses for the accumulators. Absent marker reads as `0`.

**Idempotence is the thing the old guard got right by accident.** The
`cost_usd > 0` test did prevent a double-fold, because a fold zeroes `cost_usd`.
Removing it removes that protection, so the marker must provide it
deliberately: two `fold_cumulative_on_rearm` calls for one re-arm must produce
the same accumulators as one. Prove it with a test that calls it twice.

**Do not resolve the migration here.** Existing WUs have no marker, and six of
them were already folded under the old logic. Treating an absent marker as `0`
would re-fold those on their next dispatch. T02 owns that; this WU must not
add a value-inferring fallback to paper over it — that would reintroduce
exactly the defect being removed. State the exposure in the docstring and let
T02 close it.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_rearm_fold_marker.py::TestFoldMarker::test_zero_cost_rearm_still_folds`
   exists and **fails on HEAD before this WU runs** (today the fold is skipped
   when `cost_usd` is 0), and passes after.
2. A test asserts `detect_rearm_dispatch` returns True for a re-armed WU whose
   `cost_usd` is exactly `0` and whose `folded_through_re_arm` is behind
   `re_arm_count`.
3. A test asserts it returns False when `folded_through_re_arm == re_arm_count`
   — the fold is not owed twice for one re-arm.
4. A test asserts it returns False when `re_arm_count` is absent or `0`, so a
   first-time dispatch is unaffected.
5. **Idempotence:** a test calls `fold_cumulative_on_rearm` twice for a single
   re-arm and asserts `cumulative_cost_usd`, `cumulative_duration_seconds`,
   `cumulative_input_tokens`, and `cumulative_output_tokens` each match the
   single-call result. Assert all four, not cost alone — they carry the
   identical split and this is the moment it gets fixed for all of them.
6. A test asserts `fold_cumulative_on_rearm` stamps
   `folded_through_re_arm = re_arm_count`.
7. `grep -n "cost_usd" specfuse/loop/loop.py` shows no remaining use of
   `cost_usd`'s *value* to decide whether a fold is owed. Quote the grep output
   in the RESULT block.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`. **Run any named suite in-process via
   `unittest.defaultTestLoader`, never by shelling out to `pytest`** —
   `tests/test_no_pytest_subprocess.py` fails the build if you reach for it.

**Do not touch.** `specfuse/loop/cost.py` — T03 owns the contract and accessor
documentation. Existing WU files under `.specfuse/features/` — T02 owns the
migration; a WU that edits real feature records here will collide with it.
`re_arm_history`'s shape, written by `/unblock-wu`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`. Criteria
1 and 5 are load-bearing: without 1 the defect is untouched, and without 5 the
fix trades a silent under-count for a silent double-count.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the marker cannot be written in the same atomic write set as the accumulators
(a partial write would leave a WU folded but unmarked, which is worse than
today's shape); or `detect_rearm_dispatch` turns out to have a caller that
depends on its current value-based semantics, which would make this a
multi-caller contract change rather than a one-function fix.
