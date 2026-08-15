---
id: FEAT-2026-0080/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
oracle_env: macos_local
produces:
  - plugins/specfuse/skills/fix-bug/SKILL.md
  - .specfuse/skills/fix-bug/SKILL.md
  - tests/test_fix_bug_reads_comments.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.11.0
started_at: 2026-08-13T01:00:33.282471+00:00
duration_seconds: 563.988
cost_usd: 0.575359
input_tokens: 28
output_tokens: 5121
---

# Make `/fix-bug` read the issue comments it already claims to read

**Objective.** Change `/fix-bug`'s Step 1 to name a command that actually returns
comment bodies, so an operator's guidance reaches the session that retries the bug.

**Context.** Correlation ID `FEAT-2026-0080/T02`. Independent of T01 — disjoint
files, no shared output.

`/fix-bug` Step 1 already instructs the session to read comments
(`.specfuse/skills/fix-bug/SKILL.md:66` — "Read: title, labels, body, comments").
The command named one line above, at `:65`, is `gh issue view <issue-number>`,
which does **not** return comment bodies. Verified live against issue #1872 on
2026-08-12: the default output ends at the issue body; `gh issue view <n> --comments`
is what surfaces them.

This is the read side of FEAT-2026-0080. T01 writes an operator's guidance as an
issue comment; without this WU that guidance is written into a void, and the whole
feature is a well-formatted no-op. PLAN.md's existing-mechanism search records this
as "found a partial mechanism, extending it" — the instruction exists and is
correct, only the command under it is wrong.

Note the dispatch path this serves: `autofix_invoke.build_invocation`
(`specfuse/monitor/autofix_invoke.py:40`) passes only the issue number, repository
and working directory into the headless session. Everything the session learns
about the issue, it learns by reading the issue itself — which is why the command
in Step 1 is load-bearing rather than cosmetic.

**Acceptance criteria.**

1. `tests/test_fix_bug_reads_comments.py::TestFixBugReadsComments::test_step_1_command_returns_comments`
   fails on HEAD before this WU runs (Step 1 names a command without `--comments`),
   and the failure is recorded in the attempt note.
2. `.specfuse/skills/fix-bug/SKILL.md` Step 1 names a command that returns comment
   bodies — `gh issue view <issue-number> --comments`.
3. The canonical copy at `plugins/specfuse/skills/fix-bug/SKILL.md` carries the
   identical change, and a test asserts the two copies are byte-identical (the
   existing invariant in `tests/test_fix_bug_headless.py`).
4. Step 1's prose states why comments matter to a retry: a prior run may have been
   answered by an operator, and that guidance is the difference between repeating a
   refusal and resolving it.
5. No other step of `/fix-bug` is reworded. A test asserts the headless halt-to-
   outcome mapping table and the `refused` / `could_not_proceed` / `completed`
   outcome definitions are unchanged, so this WU cannot silently alter the lane's
   contract.
6. `tests/test_fix_bug_headless.py` and `tests/test_fix_bug_diff_self_check.py`
   both still pass unchanged.
7. All tests in `tests/test_fix_bug_reads_comments.py` pass after this WU's edits.

**Do not touch.** `plugins/specfuse/skills/answer-escalation/` and its vendored
copy — those belong to T01. Any Python under `specfuse/`: this WU changes skill
prose only, and in particular `autofix_invoke.build_invocation` is deliberately
left alone (the session reads the issue itself; widening the prompt payload is a
different design and is not in this feature's scope). Generated directories,
secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` — `tests`,
`lint`, `security`, `coverage`, `leak-scan`. Plus, specific to this unit:

- `python3 -m unittest tests.test_fix_bug_reads_comments -v` passes.
- `python3 -m unittest tests.test_fix_bug_headless tests.test_fix_bug_diff_self_check -v`
  passes, confirming criterion 5 and 6.
- `diff plugins/specfuse/skills/fix-bug/SKILL.md .specfuse/skills/fix-bug/SKILL.md`
  exits 0.

**Escalation triggers.** Stop and emit `status: blocked` rather than pushing
through if: the two `fix-bug/SKILL.md` copies already differ before your edit (that
is a pre-existing sync defect and fixing it is not this WU's call); or making Step 1
return comments turns out to require changing `autofix_invoke.build_invocation`,
which this WU's Do-not-touch list forbids — that would mean the design assumption
above is wrong and the operator should re-scope. If `--comments` is absent from the
Step 1 command in the files you edited, emit `status: blocked` — do not claim
complete.
