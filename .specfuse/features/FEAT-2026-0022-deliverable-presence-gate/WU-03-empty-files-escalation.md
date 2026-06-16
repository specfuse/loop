---
id: FEAT-2026-0022/T03
type: implementation
model: opus
effort: high
status: done
attempts: 1
planned_cost_usd: 1.50
produces_driver_helper: assert_implementation_touched_files
duration_seconds: 517.045
cost_usd: 3.342376
input_tokens: 9516
output_tokens: 29378
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Empty-files escalation for implementation WUs

**Objective.** When an `implementation`-type WU reports `complete` but its
attempt touched **zero deliverable files** (the squash diff names only the WU
file and/or `events.jsonl`, or nothing), the driver refuses the pass and treats
it as a failed attempt; MAX_ATTEMPTS exhaustion escalates to `blocked_human`.
This is a **hard rule independent of `produces:`** — it fires on the
`files_touched` signal every WU already produces, so it closes the
zero-deliverable hollow pass even for WUs that declare no `produces:`
(FEAT-2026-0020/T16: passed `done` having touched zero files, ~$1.48 cost).

**Context.** This is `FEAT-2026-0022/T03`. Independent of T01/T02 — it does not
read `produces:`. The hook point is the same `outcome == "passed"` branch. The
squash SHA is computed at `loop.py:2721` (`sha = squash_commit(wu, head_before)`)
and the touched-paths list is already derived for the passed event at
`loop.py:2822` via `git_diff_names(head_before, sha)`. Compute that list once
and gate on it: for `wu.type == "implementation"`, strip the WU's own file
(`wu.file`) and `events.jsonl` from the diff; if nothing remains, the attempt
produced no deliverable.

This overlaps but does not duplicate `verify_files_changed` (loop.py:957):
that guard checks paths the agent **claimed** in `files_changed`, and opts out
when the agent claims nothing. T16's failure is exactly that opt-out — an agent
that declares no `files_changed` and writes nothing slides through. T03 closes
it from the other side: regardless of what the agent claimed, an
`implementation` WU that produced no file diff cannot be `done`.

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit files only.

**Acceptance criteria.**
1. **Red test (fails on HEAD).** New test file
   `tests/test_empty_files_escalation.py::test_implementation_zero_files_blocks`
   drives a stubbed dispatch in a temp git repo: an `implementation` WU whose
   agent reports `complete` but writes no file (the only diff is the WU
   frontmatter status flip + events.jsonl) does NOT reach `done` and records
   `outcome: no_deliverable_files`. **Fails on HEAD** — the WU reaches `done`
   today (the T16 shape).
2. New helper
   `assert_implementation_touched_files(wu: WorkUnit, touched: list[str]) ->
   tuple[bool, str]` returns `(True, "")` when `wu.type != "implementation"`,
   or when `touched` (after removing the WU's own file path and any
   `events.jsonl` entry) is non-empty; otherwise `(False, summary)` with a
   summary naming that the implementation WU produced no deliverable files.
3. Wired into the `outcome == "passed"` branch, after the squash and the smoke
   guard. Compute `touched = git_diff_names(head_before, sha)` once (reuse for
   the existing passed event at loop.py:2822 rather than calling twice). On
   `(False, summary)`:
   (a) `reset_preserving_events(head_before, events_path)`,
   (b) `emit_attempt_outcome(wu, attempt, "no_deliverable_files",
       attempts_usage[-1], extras={"summary": summary})`,
   (c) append note, set `failure_note`,
   (d) print `NO DELIVERABLE FILES attempt N/MAX`,
   (e) `continue` (MAX_ATTEMPTS exhaustion escalates via existing machinery).
4. **Type-scoped.** Non-`implementation` WUs (`close`, `plan-next`,
   `retrospective`, `lessons`, `docs`, `close-intermediate`) are exempt — they
   legitimately produce reflective or planning artifacts already gated by
   `assert_closing_deliverables`. Tested by
   `test_close_wu_not_subject_to_empty_files_rule`.
5. **WU-file-only diff blocks.** Test `test_only_wu_file_touched_blocks`: an
   implementation attempt whose diff is solely the WU file + events.jsonl
   records `no_deliverable_files`. (The exact T16 shape.)
6. **Green path.** Test `test_implementation_with_real_file_passes`: an
   implementation WU that writes a real source/test file reaches `done`.
7. **Existence check.**
   `python3 -c "from loop import assert_implementation_touched_files"` must
   succeed before declaring complete.

**Do not touch.** Exactly these files change: `.specfuse/scripts/loop.py` and
one new test file `tests/test_empty_files_escalation.py`. Do NOT modify
`verify_files_changed` or `git_diff_names`. Do NOT touch
`.specfuse/verification.yml`, existing WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the
red→green proof in AC 1/3/6 and the smoke import in AC 7.

**Escalation triggers.**
1. **Completeness.** If `assert_implementation_touched_files` is absent from
   `loop.py` after your edits, emit `status: blocked` — do not claim complete.
2. **WU-file false-positive.** The squash always includes the WU's own status
   flip and may include `events.jsonl`. If your filter does not strip those, the
   guard never fires (every attempt looks like it touched a file) — a silent
   no-op. The AC 5 test (`test_only_wu_file_touched_blocks`) must catch this;
   if it cannot, stop and emit `status: blocked`.
3. **Sequencing.** Compute `touched` from the post-squash `sha`. If you gate on
   the pre-squash working tree, the diff is empty for a different reason and the
   guard's meaning changes — stop and emit `status: blocked`.
