---
id: FEAT-2026-0103/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 5.00
produces_driver_helper:
  - retain_tree_after_refusal
  - resolve_retain_on_guard_refusal
produces:
  - specfuse/loop/loop.py
  - tests/test_guard_repair_e2e.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.18.0
started_at: 2026-09-10T02:07:25.299311+00:00
duration_seconds: 491.894
cost_usd: 2.593358
input_tokens: 150
output_tokens: 40201
---

# A guard refusal keeps the working tree

**Objective.** When one of the four bookkeeping guards refuses an attempt, uncommit
the squash and leave the working tree as the attempt left it, so the next attempt
repairs in place. Today every site calls `reset_preserving_events(head_before, …)`
and the work is gone.

**Context.** FEAT-2026-0103/T01, this gate's **walking skeleton**: wire the thinnest
end-to-end path and turn `GATE-01.md`'s `feature_oracle` green; T02 and T03 refine
it. The four sites are in `run()`'s attempt loop in `specfuse/loop/loop.py`, each
a `reset_preserving_events(...)` call directly under the guard that fired:
`deliverable_missing` (after `assert_declared_deliverables`),
`no_deliverable_files` (after `assert_implementation_touched_files`),
`produces_not_in_diff` (after `resolve_produces_refusal`) and
`files_changed_mismatch` (the `if outcome == "files_changed_mismatch":` branch).
Add `retain_tree_after_refusal(head_before, events_path)`: `git reset --mixed
<head_before>` (the squash is uncommitted, the tree and `events.jsonl` untouched —
no content needs re-writing, unlike the hard reset), returning the retained diff
via the existing `capture_working_tree_diff(head_before)`. Each site calls it
instead of the reset when `resolve_retain_on_guard_refusal(cfg)` is true (reads
`verification.yml` `defaults.retain_on_guard_refusal`, default `True`, the same
`defaults` block `resolve_max_attempts` reads), appends the retained diff to the
note it already builds under a `Retained diff (your tree is still here):` line,
and passes `extras={"tree_retained": True, …}` on the `attempt_outcome` it
already emits. The existing `_retained` flag that reaches
`synthesize_retry_directive(retained=True)` must be true on the next attempt for
these sites too. Red test first: `tests/test_guard_repair_e2e.py` is the gate's
oracle, shaped like `tests/test_tiered_verification_e2e.py`'s
`integration_workspace` + stubbed `dispatch` harness; its stub returns a RESULT
with one untouched extra path on attempt 1 and a clean RESULT on attempt 2.

**Acceptance criteria.**

1. `tests/test_guard_repair_e2e.py` fails on HEAD before this unit's edits (the
   module is absent); after, `python3 -m unittest tests.test_guard_repair_e2e -v`
   exits 0.
2. That module asserts, end to end through `loop.run()`: attempt 1's
   `attempt_outcome` is `files_changed_mismatch` with `tree_retained: true`;
   the deliverable attempt 1 wrote exists on disk when the stub is invoked for
   attempt 2; attempt 2's failure note contains the guard's complaint and the
   line `Retained diff` followed by a hunk from attempt 1's file; the unit ends
   `done` with exactly one squash commit whose diff against the base contains
   attempt 1's file.
3. A second case in the same module sets `defaults: retain_on_guard_refusal:
   false` in the fixture's `verification.yml` and asserts the deliverable is
   absent when attempt 2 starts (today's reset, unchanged).
4. `python3 -m unittest tests.test_loop_files_changed_guard tests.test_deliverable_presence_gate tests.test_empty_files_escalation tests.test_produces_justification -v` exits 0 with no edit to those modules; if one of them asserts the tree was reset after a refusal, stop with `status: blocked` naming the test (that is an arming finding, not a test to rewrite).
5. `python3 -m unittest tests.test_attempt_outcome_contract -v` exits 0: no new
   outcome string is introduced — `tree_retained` is an `extras` field.

**Do not touch.** The guards' refusal logic and their summaries; the convergent
iteration branch (`if wu.iterate_on_failure:`) and `decide_convergence_action`;
the `learnings_not_staged` site; `.specfuse/verification.yml`; plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if `git reset --mixed`
cannot leave `events.jsonl` intact at any site (name the site and what the
events file looked like); or if criterion 4 names a test that encodes today's
reset.
