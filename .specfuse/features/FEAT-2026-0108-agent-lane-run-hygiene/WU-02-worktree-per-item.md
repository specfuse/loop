---
id: FEAT-2026-0108/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 7.00
model: opus
effort: high
oracle_env: macos_local
produces_driver_helper: item_worktree
produces:
  - specfuse/agent/worktree.py
  - specfuse/agent/run.py
  - tests/test_agent_item_worktree.py
---

# One working tree per item, and nothing anonymous left behind

**Objective.** Each agent item runs in its own `git worktree` on its own
branch, created before the provider executes and removed after. An item that
ends without committing has its edits committed under an item-tagged ref
(`wip/<item_id>`) and named in the run summary, so no finished work is left as
uncommitted edits on a branch named for a different issue.

**Context.** FEAT-2026-0108/T02; read `PLAN.md`. Today `agent/worktree.py`
only records the starting branch and restores it at run end
(`current_branch`, `is_dirty`, `restore_branch`), and the run's final report
already prints "working tree left on '<branch>' — NOT restored: it has
uncommitted changes" (#3179's evidence). Add `item_worktree(item_id, base)`
as a context manager: `git worktree add <tmpdir> -b agent/<item_id> <base>`,
yield the path, and on exit either remove it (clean) or commit its changes to
`wip/<item_id>`, remove the worktree, and record the ref on the outcome.
Providers receive the path as `working_dir` (the bug lane already takes one:
`run_bug_lane(..., working_dir=)`). A dirty starting tree is refused before
the first item with a message naming the dirty paths. Red test first; use a
real temporary git repository as `tests/test_loop_files_changed_guard.py`
does.

**Acceptance criteria.**

- `tests/test_agent_item_worktree.py::test_each_item_runs_in_its_own_worktree` fails on HEAD and passes after: two fixture items record different `working_dir` values, neither equal to the repository root, and both are gone after the run.
- `tests/test_agent_item_worktree.py::test_uncommitted_item_work_is_committed_under_wip_ref`: a fixture provider that writes a file and returns without committing leaves `refs/heads/wip/<item_id>` containing that file, the run summary names the ref, and the main tree is clean.
- `tests/test_agent_item_worktree.py::test_dirty_starting_tree_refuses_to_dispatch`: `run()` on a dirty tree starts zero items and reports the dirty paths.
- `tests/test_agent_item_worktree.py::test_pushed_branch_is_left_alone`: an item that committed and pushed keeps its branch; no `wip/` ref is created.
- `python3 -m unittest discover -s tests -q` reports `OK`.

**Do not touch.** the WU driver module (everything under `specfuse/loop/` not named in `produces:`); the invoke modules (T01, T03);
escalation payload text (T06); `.git/`, secrets.

**Verification.** The `code` gates in `.specfuse/verification.yml` plus
`python3 -c "from specfuse.agent.worktree import item_worktree"` exits 0.

**Escalation triggers.** Emit `status: blocked` if a provider cannot be given
a `working_dir` without changing its public signature in a way its tests do
not cover; name the provider.
