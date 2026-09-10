---
id: FEAT-2026-0103/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.00
produces_driver_helper:
  - auto_repair_files_changed
produces:
  - specfuse/loop/loop.py
  - tests/test_files_changed_auto_repair.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.18.0
started_at: 2026-09-10T02:20:28.961005+00:00
duration_seconds: 355.835
cost_usd: 1.736334
input_tokens: 122
output_tokens: 30381
---

# A RESULT naming an untouched non-deliverable is repaired without a dispatch

**Objective.** When `verify_files_changed` finds paths that show no diff and
none of them is in the unit's `produces:`, the driver drops those paths from
the RESULT's `files_changed`, records what it dropped, and the attempt proceeds
as passed. A session should not be paid to delete a line from a list.

**Context.** FEAT-2026-0103/T03. `execute_unit_attempt` in `specfuse/loop/loop.py` returns
`("files_changed_mismatch", unchanged, usage)` when `verify_files_changed`
reports unchanged paths. Add `auto_repair_files_changed(wu, parsed, unchanged)`:
if every path in `unchanged` is outside `wu.produces` (compare normalised
relative paths), remove them from `parsed["files_changed"]`, return the
repaired list; otherwise return None and the guard fires as today (a deliverable
that shows no diff is `produces_not_in_diff`'s business, and T01 retains for it).
On repair, `execute_unit_attempt` returns `"passed"` and the `attempt_outcome`
the passed path emits carries `extras={"auto_repaired_files_changed": [...]}`;
the driver prints one line naming the dropped paths. The squash and the
downstream guards run exactly as on any pass — this changes only the RESULT's
advisory claim, never the diff.

**Acceptance criteria.**

1. `tests/test_files_changed_auto_repair.py::test_untouched_non_deliverable_is_dropped_and_the_attempt_passes`
   fails on HEAD and passes after: a RESULT declaring one real change and one
   untouched path outside `produces:` yields outcome `passed`, the returned
   `wu.result_block["files_changed"]` no longer lists the untouched path, and
   the passed `attempt_outcome` names it under `auto_repaired_files_changed`.
2. `::test_untouched_deliverable_still_refuses`: the same RESULT with the
   untouched path listed in `produces:` yields `files_changed_mismatch`,
   unchanged.
3. `::test_nothing_to_repair_is_a_plain_pass`: a RESULT with no mismatch emits
   no `auto_repaired_files_changed` key.
4. `python3 -m unittest tests.test_files_changed_guard tests.test_attempt_outcome_contract tests.test_guard_repair_e2e -v` exits 0.

**Do not touch.** `verify_files_changed` itself; `resolve_produces_refusal`
and the `produces_unchanged` justification path; T01's retain helper; the
`events.jsonl` schema (`extras` is the existing free-form field).

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`.

**Escalation triggers.** Stop with `status: blocked` if `wu.produces` and the
RESULT's paths cannot be compared without a path-normalisation rule this
repository does not already have (name the two forms that disagree).
