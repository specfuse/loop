---
id: FEAT-2026-0023/T03
type: implementation
model: opus
effort: high
status: done
attempts: 1
planned_cost_usd: 1.50
produces: tests/test_ensure_feature_branch.py
produces_driver_helper: ensure_feature_branch
duration_seconds: 347.615
cost_usd: 1.54766
input_tokens: 9071
output_tokens: 18901
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Harden the feature-branch seam (ensure_feature_branch)

**Objective.** Make `ensure_feature_branch` robust to the two real-world states
that crash it with a raw traceback today (#48): a dirty working tree (the
`/pick-feature` status flips, uncommitted) and a stale pre-existing branch that
diverges from the current base. Instead of an unhandled `CalledProcessError`,
the driver surfaces git's actual stderr and either proceeds deliberately or
stops with an actionable message.

**Context.** This is `FEAT-2026-0023/T03`. `ensure_feature_branch`
(loop.py:613–641) calls `git("checkout", branch)` (loop.py:637) or
`git("checkout", "-B", branch)` (loop.py:640) unguarded; `git()` (loop.py:572)
runs with `check=True` and `capture_output=True`, so any non-zero exit raises a
bare `CalledProcessError` that propagates out of `main()` and swallows the
stderr that explains the cause.

Two observed failure states (issue #48):
1. **Dirty tree** — `/pick-feature` writes `status: active` to `roadmap.md` and
   the feature's `PLAN.md` but does not commit. `git checkout <branch>` then
   fails: "Your local changes ... would be overwritten by checkout." The
   expected pick flips SHOULD travel onto the feature branch (the `-B`-from-HEAD
   create path already carries them); only unexpected dirty paths should stop.
2. **Stale existing branch** — a branch left over from an earlier draft session
   exists locally (`rev-parse --verify` succeeds), so the code takes the
   `checkout <existing>` path (loop.py:636–638) and fails on the dirty tree, OR
   silently reuses a branch that diverges from the current base.

Reference the binding rules under `.specfuse/rules/`. The driver owns git; edit
files only.

**Acceptance criteria.**
1. **Red test (fails on HEAD).** New test file
   `tests/test_ensure_feature_branch.py::test_dirty_tree_checkout_raises_clean_error`
   sets up a tmp git repo with an existing target branch and an uncommitted
   change that blocks the switch, calls `ensure_feature_branch`, and asserts it
   raises a clear driver error whose message CONTAINS git's stderr (not a bare
   `CalledProcessError`). **Fails on HEAD** — today it raises the unguarded
   `CalledProcessError`.
2. The checkout calls are wrapped so a failure raises a dedicated, readable
   error (or returns a structured failure) that includes git's captured stderr.
   No raw `CalledProcessError` escapes `ensure_feature_branch`.
3. **Dirty-tree carry.** When the working tree is dirty only with the expected
   `/pick-feature` flip paths (`.specfuse/roadmap.md` and the feature's
   `PLAN.md`), `ensure_feature_branch` carries them onto the feature branch
   (create-from-HEAD semantics) rather than failing. Tested by
   `test_pick_flips_carried_onto_new_branch`.
4. **Unexpected dirty paths stop.** When the tree is dirty with paths OTHER than
   the expected flips, the driver stops with a message naming them and
   suggesting commit/stash — it does NOT silently carry arbitrary changes.
   Tested by `test_unexpected_dirty_paths_block`.
5. **Stale divergent branch surfaced.** When the declared branch exists but
   diverges from the current base (not an ancestor of HEAD), surface it (e.g.
   "branch `feat/...` exists and diverges from HEAD") rather than silently
   checking out the stale branch. Tested by
   `test_stale_divergent_branch_surfaced`. (Resolution policy — reuse / recreate
   / abort — is the driver's call; this WU at minimum makes it visible and
   non-crashing.)
6. **Clean path preserved** — `test_clean_tree_creates_or_switches`: on a clean
   tree with no existing branch, `-B` creates from HEAD as today; on a clean
   tree already on the branch, it is a no-op.
7. **Existence check.** `python3 -c "from loop import ensure_feature_branch"`
   succeeds and the new test file exists and is non-empty.

**Do not touch.** These files change: `.specfuse/scripts/loop.py` and one new
test file `tests/test_ensure_feature_branch.py`. Do NOT modify
`fire_terminal_flips` (T01 owns it), `auto_archive_feature`,
`.specfuse/verification.yml`, existing WU files, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the
red→green proofs in AC 1/3/4/5/6 and the smoke import in AC 7.

**Escalation triggers.**
1. **Completeness.** If a raw `CalledProcessError` can still escape
   `ensure_feature_branch` on the dirty-tree or stale-branch paths after your
   edits, emit `status: blocked` — do not claim complete.
2. **Over-broad carry.** If your "carry the pick flips" logic carries arbitrary
   uncommitted changes (not just the expected flip paths), stop and emit
   `status: blocked` — silently moving unrelated edits onto a feature branch is
   worse than failing loudly.
3. **Spec ambiguity on stale-branch policy.** If reuse-vs-recreate-vs-abort for
   a divergent existing branch is unclear for the loop's own conventions, make
   it non-crashing + visible and emit `status: blocked` naming the open policy
   question rather than guessing a destructive default (e.g. auto-deleting a
   branch).
