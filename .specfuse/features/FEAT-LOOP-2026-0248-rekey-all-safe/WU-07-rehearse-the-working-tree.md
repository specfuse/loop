---
id: FEAT-LOOP-2026-0248/T07
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 1.50
provenance: "T05's re-armed attempt (events.jsonl human_escalation agent_reported_blocked, 2026-10-29 ~13:06) was refused in 22s: --rehearse refuses a dirty tree (ids.py:682), and during any driver dispatch the driver's own WU frontmatter and events.jsonl are modified, so it can never run inside a unit. It also rehearses HEAD (ids.py:705), so a unit's own uncommitted edits are never in the rehearsal; T05's first attempt worked around both with a private copy script. Operator approved adding this unit ('go ahead, add T07 and re-arm T05')."
produces:
  - specfuse/loop/ids.py
  - tests/test_migrate_all_repo_stays_valid.py
---

# T07 — `--rehearse` rehearses the working tree as it is, not `HEAD`

**Objective.** A rehearsal includes the operator's, or a unit's, uncommitted changes, and
it runs whether or not the real tree is dirty, because it never writes there.

**Context.** `FEAT-LOOP-2026-0248/T07`. This unit **edits** `ids.py` (T04's `rehearse`)
and the oracle module. Today `rehearse` refuses a dirty tree (`ids.py:682`) and adds a
worktree at `HEAD` (`ids.py:705`). Change it to snapshot the working tree:

1. Drop the dirty-tree refusal from `rehearse` only. `--apply`'s refusal stays.
2. `git worktree add --detach <tmp> HEAD`, then bring the working tree's state across:
   apply `git diff HEAD --binary` from the real tree, and copy every untracked,
   non-ignored file (`git ls-files --others --exclude-standard`).
3. Inside the throwaway worktree only, `git add -A && git commit -q --no-verify -m
   "rehearsal snapshot"` on its detached HEAD, so the migration's own clean-tree refusal
   (`ids.py:629`) passes. No real branch or ref is created or moved.
4. Report which state was rehearsed: `HEAD` alone, or `HEAD` plus N modified and M
   untracked files.

Everything else in T04 and T06 stays: validation runs the renamed copy's own code, the
tests command runs there, and the worktree is always removed.

**Acceptance criteria.**

1. New oracle tests: with an uncommitted edit to a tracked file and a new untracked file
   in the real tree, a rehearsal runs (no refusal), its command sees both, and afterwards
   the real tree's `git status --porcelain`, tracked-file hashes, branch list and
   `git worktree list` are unchanged. Fails before, passes after.
2. `python3 -m unittest tests.test_migrate_all_repo_stays_valid tests.test_ids_migrate_all -b`
   passes, including T04's clean-tree rehearsal case.

**Do not touch.** `--apply`'s dirty-tree refusal, rewrite rules (T02, T03), validation
(T06).

**Verification.** The narrow tier for `implementation`, plus AC2's command.

**Escalation triggers.** If `git apply` of the diff fails on binary or mode changes in the
worktree, fall back to copying the modified files' contents and say so in the report; if
that also cannot represent a change (a deleted tracked file), stop and name the case.
