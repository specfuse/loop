---
id: FEAT-2026-0002/T01
type: implementation
effort: high
status: pending
attempts: 0
---

# Cover the remaining orchestration paths in loop.py

**Objective.** Raise `.specfuse/scripts/loop.py` per-file coverage from 87%
to ≥ 95% by adding unit tests for the named-uncovered orchestration arms.
No production code changes; tests only.

**Context.** This is `FEAT-2026-0002/T01`. The current uncovered line set
in `loop.py` (measured by `coverage run --source=.specfuse/scripts -m
unittest discover -s tests && coverage report -m
--include=.specfuse/scripts/loop.py`) is concentrated in seven clusters:

1. `squash_commit` soft-reset path (around `loop.py:590-606`).
2. `find_feature` 0/1/many actives error arms (around `loop.py:280-289`).
3. `require_git_ready` non-repo and missing-commits arms (around
   `loop.py:336, 357, 361, 378, 390-391`).
4. `dispatch` subprocess error arms (around `loop.py:466, 469, 475,
   508, 511, 518, 520`).
5. `BlockingIOError` print arm in `run()` (`loop.py:967-973`).
6. `gate-budget` halt arm in `run()` (`loop.py:1036-1054`).
7. `main()` argparse arms (`loop.py:1293-1305`).

Existing test files demonstrate the stubbed-dispatch pattern needed:
`tests/test_loop_zero_token_guard.py`, `tests/test_loop_files_changed_guard.py`,
`tests/test_driver_lock.py`. Reuse this seam — do not refactor `loop.py`'s
`dispatch()` signature.

Reference the binding rules under `.specfuse/rules/`. The driver owns git;
edit test files only.

**Acceptance criteria.**

1. New file `tests/test_loop_orchestration.py` exists and contains at least
   one test class per uncovered cluster (`TestSquashCommitSoftReset`,
   `TestFindFeatureSelection`, `TestRequireGitReady`,
   `TestDispatchErrorArms`, `TestRunLockContention`,
   `TestRunGateBudgetHalt`, `TestMainArgparse`).
2. `squash_commit` soft-reset tested against a real temp git repo: a
   stub agent commits two files; `squash_commit` produces exactly one
   commit folding both with the WU trailer, and `HEAD` matches the
   expected SHA shape.
3. `find_feature(None)` raises (or exits) when zero features are active
   with a message naming the directory it searched.
4. `find_feature(None)` succeeds and returns the lone feature dir when
   exactly one is active.
5. `find_feature(None)` raises (or exits) when more than one feature is
   active with a message naming the conflicting feature IDs.
6. `require_git_ready` against a non-repo working directory raises
   `RuntimeError` (or exits non-zero) with a message containing
   "not a git" or equivalent.
7. `require_git_ready` against a repo with no commits raises with a
   message containing "no commits".
8. `dispatch` error arms exercised via subprocess stubbing: each branch
   in lines 466/469/475/508/511/518/520 of `loop.py` is hit by at least
   one test, asserted by the per-file coverage AC below.
9. `run()` `BlockingIOError` arm: a test acquires the tree lock first,
   then calls `loop.run(None, dry_run=False)`; the second invocation
   exits with code 1 and prints the lock-held message to stderr.
10. `run()` gate-budget halt: a test sets `cost_budget_usd` low on a
    GATE-NN.md fixture, runs a stubbed-dispatch sequence whose first WU
    drives `gate_spent_usd` over the ceiling, and asserts the gate flips
    to `awaiting_review` before the next WU's dispatch, an event with
    `reason: "gate_budget_exceeded"` is in `events.jsonl`, and `run()`
    returns 1.
11. `main()`: tests cover `--feature`, `--dry-run`, no-args (multi-active
    error), and `--help`-style arms by invoking `loop.main()` with a
    patched `sys.argv` against a temp workspace.
12. **Per-file coverage AC.** `coverage run --source=.specfuse/scripts
    -m unittest discover -s tests && coverage report
    --include=.specfuse/scripts/loop.py --fail-under=95` exits 0.
13. **Existence check** (per LEARNINGS `[FEAT-2026-0007/G1-LESSONS]`):
    `python3 -c "from tests.test_loop_orchestration import
    TestSquashCommitSoftReset, TestFindFeatureSelection,
    TestRequireGitReady, TestDispatchErrorArms, TestRunLockContention,
    TestRunGateBudgetHalt, TestMainArgparse"` succeeds.

**Do not touch.** Exactly 1 new file: `tests/test_loop_orchestration.py`.
No edits to: `.specfuse/scripts/loop.py` (production code stays untouched —
this WU is tests only), `.specfuse/rules/`, `.specfuse/verification.yml`
(T05 owns the floor flip), `WU.template.md`, other test files (T03/T04
own theirs), secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

If a test reveals a real bug in `loop.py` that cannot be unit-tested
without a fix, **emit `status: blocked`** with the bug evidence rather
than touching production code in this WU.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage at the current `--fail-under=70` floor
— T05 raises it later), PLUS the per-file coverage AC 12, PLUS the
existence check AC 13. Declare `files_changed: [tests/test_loop_orchestration.py]`
in the RESULT block (driver T02 guard requires it).

**Escalation triggers.**

1. **Completeness.** If `tests/test_loop_orchestration.py` is absent from
   the files you edited, emit `status: blocked` — do not claim complete.
2. **Per-file floor not met.** If `coverage report --include=.specfuse/scripts/loop.py
   --fail-under=95` exits non-zero after your tests, emit `status: blocked`
   naming the lines still uncovered. Do not pad with trivial tests to
   reach the threshold.
3. **Untestable arm requires production change.** If any uncovered arm
   listed in Context cannot be reached without modifying `loop.py`'s
   public seams (e.g. extracting a helper), emit `status: blocked`
   naming the arm and the proposed seam — a production change is a
   separate WU.
