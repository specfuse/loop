---
id: FEAT-LOOP-2026-0248/T04
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 3.00
produces:
  - specfuse/loop/ids.py
  - tests/test_migrate_all_repo_stays_valid.py
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
model: sonnet
effort: medium
gate_set: code
driver_version: 0.30.0
started_at: 2026-10-29T15:17:59.652409+00:00
duration_seconds: 120.643
cost_usd: 0.30746
input_tokens: 22
output_tokens: 6748
---

# T04 — `--rehearse`: prove a rename on a throwaway copy before applying it

**Objective.** An operator can see exactly what a full rename would break, including the
repository's own test suite, without touching the real tree.

**Context.** `FEAT-LOOP-2026-0248/T04`. This unit **edits** `ids.py`, the oracle module and
the methodology doc (adding to the "Renaming existing features" paragraph FEAT-2026-0247
wrote). Add `--rehearse` to `ids migrate` (both modes):

- `git worktree add --detach <tmp> HEAD`, run the migration there with every other option
  given (as `--apply`, including T01's post-apply validation), then run the `tests` gate's
  `command` from `.specfuse/verification.yml` in the worktree (or `--rehearse-command
  "<cmd>"`), with `PYTHONPATH` set to the worktree so the renamed code is what runs.
- Print the validation result, the test command's exit status and its failing test ids
  (unittest `FAIL:`/`ERROR:` lines, pytest `FAILED` lines, or the last 20 lines otherwise).
- Always remove the worktree (`git worktree remove --force`), also on error or
  interrupt. Exit zero only when validation and the command both pass.
- Refuse when the real tree is dirty (tracked files) so `HEAD` is what the operator has.
  Never write to the real tree.

Un-skip the oracle's clause-5 class with a fast `--rehearse-command` (for example a
`python3 -c` that checks a renamed folder exists) so the oracle does not run a full suite.

**Acceptance criteria.**

1. The clause-5 class: rehearse exits zero with a passing command and non-zero with a
   failing one, reports the command's failing lines, leaves the real tree byte-identical
   (compare `git status --porcelain` and a hash of tracked files before and after) and
   leaves no worktree registered (`git worktree list`). Fails before, passes after.
2. `python3 -m unittest tests.test_ids_migrate_all tests.test_caller_check_ratchet tests.test_judge_path_registry -b`
   passes (new public helpers have non-test callers; `ids.py` stays classified).

**Do not touch.** Rewrite rules (T02, T03), validation (T01).

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If the tests gate command cannot run inside a worktree (for
example it depends on an absolute path to the real checkout), stop and name the
dependency.
