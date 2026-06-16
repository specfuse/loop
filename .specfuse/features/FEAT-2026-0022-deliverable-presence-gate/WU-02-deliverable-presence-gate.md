---
id: FEAT-2026-0022/T02
type: implementation
model: opus
effort: high
status: done
attempts: 1
planned_cost_usd: 2.00
produces_driver_helper: assert_declared_deliverables
duration_seconds: 491.397
cost_usd: 2.890176
input_tokens: 9604
output_tokens: 25290
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Deliverable-presence gate — enforce `produces:` on disk

**Objective.** Before the driver accepts a WU's `complete`, verify that every
path the WU declared in `produces:` exists on disk and is non-empty. If any is
absent or empty, treat the attempt as a failed attempt (reset + re-dispatch);
exhausting MAX_ATTEMPTS escalates to `blocked_human` via the existing machinery.
This catches the partial-bundle hollow pass (FEAT-2026-0020/T12:
`SECURITY.md` present, bundled `CODE_OF_CONDUCT.md` absent).

**Context.** This is `FEAT-2026-0022/T02`; depends on T01 (the `produces:`
field and `WorkUnit.produces`). The hook point is the `outcome == "passed"`
branch in the attempt loop, where the existing guards already chain:
`extract_smoke_imports`/`run_smoke_imports` (loop.py:2731), then
`assert_closing_deliverables` (loop.py:2750). This new guard slots in the same
region, **after** smoke and closing-deliverable guards, reusing their exact
failure shape: `reset_preserving_events(head_before, events_path)` →
`emit_attempt_outcome(..., "deliverable_missing", ...)` → append note →
`continue`. See the `closing_deliverable_missing` block (loop.py:2753–2769) and
the `files_changed_mismatch` block (loop.py:2835–2858) as the two patterns to
mirror. The squash has already happened by this point (loop.py:2721), so the
reset rolls the deliverable-less tree out of history exactly as the closing
guard does.

The presence check is file-level: exists AND non-empty (`test -s` semantics —
`Path(p).exists()` and `Path(p).stat().st_size > 0`). Symbol-level checks are
explicitly out of scope (see PLAN Scope OUT).

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit files only.

**Acceptance criteria.**
1. **Red test (fails on HEAD).** New test file
   `tests/test_deliverable_presence_gate.py::test_declared_deliverable_absent_blocks`
   drives a stubbed dispatch in a temp git repo: an `implementation` WU declares
   `produces: ["DELIVERABLE.md"]` and the agent reports `complete` **without
   creating the file**. The test asserts the WU does NOT reach `done` (no
   PASS/squash survives) and the attempt records `outcome: deliverable_missing`.
   This **fails on HEAD** because no such gate exists — the WU reaches `done`
   today. This is issue #41 point 3 made executable.
2. New helper
   `assert_declared_deliverables(wu: WorkUnit) -> tuple[bool, str]` returns
   `(True, "")` when `wu.produces` is empty (opt-out: undeclared → no gate) or
   when every declared path exists and is non-empty; otherwise `(False, summary)`
   where `summary` names the first offending path and whether it was absent or
   empty. A path that exists but is zero-length is treated as missing (an empty
   deliverable is a hollow deliverable).
3. The guard is wired into the `outcome == "passed"` branch (loop.py, after the
   `assert_closing_deliverables` block at ~loop.py:2769), fired for **all** WU
   types (a declared `produces:` is honored regardless of type; closing WUs
   simply rarely declare one). On `(False, summary)`:
   (a) `reset_preserving_events(head_before, events_path)`,
   (b) append `emit_attempt_outcome(wu, attempt, "deliverable_missing",
       attempts_usage[-1], extras={"summary": summary, "missing": <path>})`,
   (c) append the note to `attempt_notes`, set `failure_note`,
   (d) print a `DELIVERABLE MISSING attempt N/MAX` line,
   (e) `continue` (retry within budget; MAX_ATTEMPTS exhaustion escalates to
       `blocked_human` through the existing loop machinery — no new escalation
       code).
4. **Opt-out preserved.** When `wu.produces` is empty/absent the guard does NOT
   fire — existing behavior for every current WU is unchanged. Tested by
   `test_no_produces_passes_unchanged`.
5. **Partial-bundle caught.** Test
   `test_partial_bundle_blocks`: a WU declaring
   `produces: ["SECURITY.md", "CODE_OF_CONDUCT.md"]` where the agent creates
   only `SECURITY.md` records `deliverable_missing` naming `CODE_OF_CONDUCT.md`
   and does not reach `done`. (The FEAT-2026-0020/T12 shape.)
6. **Empty-file caught.** Test `test_empty_deliverable_blocks`: a declared path
   created but zero-length records `deliverable_missing`.
7. **Green path.** Test `test_all_deliverables_present_passes`: a WU declaring
   `produces: ["X.md"]` that creates a non-empty `X.md` reaches `done` and
   records `outcome: passed`.
8. **Existence check.**
   `python3 -c "from loop import assert_declared_deliverables"` must succeed
   before declaring complete.

**Do not touch.** Exactly these files change: `.specfuse/scripts/loop.py` and
one new test file `tests/test_deliverable_presence_gate.py`. Do NOT modify the
`produces:` parse or `WorkUnit` (T01 owns those — depend on them, do not
re-edit). Do NOT touch `verify_files_changed`, `assert_closing_deliverables`,
`.specfuse/verification.yml`, existing WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the
red→green proof in AC 1/3/7 and the smoke import in AC 8.

**Escalation triggers.**
1. **Completeness.** If `assert_declared_deliverables` is absent from `loop.py`
   after your edits, emit `status: blocked` — do not claim complete.
2. **Sequencing.** The guard MUST run after the squash and after the smoke +
   closing-deliverable guards, mirroring their reset-on-fail shape. If the
   deliverable check runs before squash, freshly-created files behave
   inconsistently with the closing guard's contract — stop and emit
   `status: blocked`.
3. **Opt-out regression.** If your implementation fires the guard on WUs whose
   `produces:` is empty (treating absence as "zero required deliverables that
   must all exist"), stop and emit `status: blocked` — absence opts out, exactly
   as `verify_files_changed`'s absence opt-out (loop.py:974–976).
4. **Dependency.** If `WorkUnit.produces` does not exist (T01 not yet landed),
   emit `status: blocked` — do not re-implement the field here.
