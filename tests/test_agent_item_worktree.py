# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""One working tree per item, and nothing anonymous left behind
(FEAT-2026-0108/T02).

The 2026-09-02 unattended run left one item's complete, passing fix as
uncommitted edits on a branch named for a *different* issue (#3179). The
run's own report said so -- "working tree left on '<branch>' -- NOT restored:
it has uncommitted changes" -- and that was the only trace: no ref named the
work, and the next item started from the same tree.

These tests pin the four properties that removes:

  1. Each item executes in its own `git worktree`, never in the repository
     root, and the trees are gone when the run ends.
  2. An item that ends without committing has its edits committed under
     `refs/heads/wip/<item_id>`, named in the run summary, leaving the main
     tree clean.
  3. A dirty starting tree refuses to dispatch at all -- branching every item
     off a base that already carries someone's edits is how one item's work
     ends up attributed to another.
  4. An item that committed and pushed keeps its branch; nothing is
     re-committed under a `wip/` ref behind it.

A real temporary git repository throughout, as
`tests/test_loop_files_changed_guard.py` does: `git worktree` is the
mechanism under test, and a scripted double would only prove the double.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent import worktree
from specfuse.agent.run import (
    ActionItem,
    ActionOutcome,
    STATUS_COMPLETED,
    _format_summary,
    run_agent,
)


def _empty_json_runner(calls):
    """The conductor's `gh` transport: every list call comes back empty."""

    def runner(argv, check=False):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    return runner


class _FakeClock:
    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now


def _git(root, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


class _IsolatedProvider:
    """Records the `working_dir` it is handed for each item, and optionally
    acts inside it -- writing, committing, whatever the test needs the item's
    session to have done."""

    def __init__(self, items, *, action=None):
        self._pending = list(items)
        self._action = action
        self.working_dirs = {}

    def advertise(self, snapshot):
        return tuple(self._pending)

    def execute(self, item, working_dir=None):
        self._pending = [i for i in self._pending if i.item_id != item.item_id]
        self.working_dirs[item.item_id] = working_dir
        if self._action is not None:
            self._action(item, working_dir)
        return ActionOutcome(status=STATUS_COMPLETED, detail="ok")

    def reconcile(self, item, outcome):
        pass


class _ItemWorktreeCase(unittest.TestCase):
    """A one-commit git repository, with the agent lane's `.specfuse/` in it."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name).resolve()
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        _git(root, "config", "commit.gpgSign", "false")
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        (root / "README.md").write_text("hello\n")
        # The lane's own lock file lives under `.specfuse/`; ignoring it keeps
        # "the main tree is clean" an assertion about the *item's* edits.
        (root / ".gitignore").write_text(".specfuse/.agent.lock\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        self.root = root
        self.specfuse_dir = root / ".specfuse"
        self.specfuse_dir.mkdir()
        self.features_root = self.specfuse_dir / "features"
        self.features_root.mkdir()
        os.chdir(root)

    def tearDown(self):
        os.chdir(self._cwd)
        # Leave nothing registered even if an assertion aborted mid-run.
        _git(self.root, "worktree", "prune", check=False)
        self._tmp.cleanup()

    def run_agent_isolated(self, provider):
        self.report_lines = []
        return run_agent(
            specfuse_dir=self.specfuse_dir,
            repo="acme/widget",
            runner=_empty_json_runner([]),
            providers=(provider,),
            policy_path=str(self.specfuse_dir / "agent-policy.yml"),
            features_root=self.features_root,
            clock=_FakeClock(),
            reporter=self.report_lines.append,
            isolate_items=True,
        )

    def ref_exists(self, ref):
        return _git(self.root, "rev-parse", "--verify", "-q", ref, check=False).returncode == 0

    def porcelain(self):
        return _git(self.root, "status", "--porcelain").stdout


class TestItemWorktree(_ItemWorktreeCase):

    def test_each_item_runs_in_its_own_worktree(self):
        provider = _IsolatedProvider(
            [
                ActionItem(item_id="bug-1", kind="bug"),
                ActionItem(item_id="bug-2", kind="bug"),
            ]
        )

        summary = self.run_agent_isolated(provider)

        self.assertEqual(summary.items_attempted, 2)
        self.assertEqual(summary.items_completed, 2)
        dirs = provider.working_dirs
        self.assertEqual(sorted(dirs), ["bug-1", "bug-2"])
        for item_id, path in dirs.items():
            self.assertIsNotNone(path, f"{item_id} was handed no working_dir")
            resolved = Path(path).resolve()
            self.assertNotEqual(
                resolved, self.root, f"{item_id} ran in the repository root"
            )
        self.assertNotEqual(
            Path(dirs["bug-1"]).resolve(),
            Path(dirs["bug-2"]).resolve(),
            "both items shared one working tree",
        )
        for path in dirs.values():
            self.assertFalse(
                Path(path).exists(), f"{path} outlived the run"
            )
        registered = _git(self.root, "worktree", "list", "--porcelain").stdout
        for path in dirs.values():
            self.assertNotIn(str(Path(path).resolve()), registered)

    def test_uncommitted_item_work_is_committed_under_wip_ref(self):
        def write_and_return(item, working_dir):
            (Path(working_dir) / "fixed.txt").write_text("the fix\n")

        provider = _IsolatedProvider(
            [ActionItem(item_id="bug-77", kind="bug")], action=write_and_return
        )

        summary = self.run_agent_isolated(provider)

        self.assertTrue(
            self.ref_exists("refs/heads/wip/bug-77"),
            "the item's uncommitted work was left with no ref naming it",
        )
        shown = _git(self.root, "show", "wip/bug-77:fixed.txt").stdout
        self.assertEqual(shown, "the fix\n")
        self.assertIn("wip/bug-77", _format_summary(summary))
        self.assertEqual(self.porcelain(), "", "the main tree was left dirty")

    def test_dirty_starting_tree_refuses_to_dispatch(self):
        (self.root / "README.md").write_text("hello\nedited by a human\n")
        provider = _IsolatedProvider([ActionItem(item_id="bug-3", kind="bug")])

        summary = self.run_agent_isolated(provider)

        self.assertEqual(summary.items_attempted, 0)
        self.assertEqual(provider.working_dirs, {})
        rendered = _format_summary(summary) + "\n".join(self.report_lines)
        self.assertIn("README.md", rendered)

    def test_pushed_branch_is_left_alone(self):
        def commit_and_push(item, working_dir):
            (Path(working_dir) / "fixed.txt").write_text("the fix\n")
            _git(working_dir, "add", "-A")
            _git(working_dir, "commit", "-q", "-m", "fix: the fix")

        provider = _IsolatedProvider(
            [ActionItem(item_id="bug-9", kind="bug")], action=commit_and_push
        )

        self.run_agent_isolated(provider)

        self.assertTrue(
            self.ref_exists("refs/heads/agent/bug-9"),
            "an item that committed lost the branch holding its commit",
        )
        self.assertEqual(
            _git(self.root, "show", "agent/bug-9:fixed.txt").stdout, "the fix\n"
        )
        self.assertFalse(
            self.ref_exists("refs/heads/wip/bug-9"),
            "a committed item was re-committed under a wip/ ref",
        )


class TestHandingProvidersTheirTree(_ItemWorktreeCase):
    """The six shipped providers predate per-item isolation, so the tree is
    offered three ways. Each one is a way an item's edits do or do not end up
    in the right place, so each one is pinned."""

    def test_a_provider_holding_working_dir_is_pointed_at_its_tree(self):
        """The four dispatching providers keep `self._working_dir` and pass it
        into `build_invocation`. They are re-pointed for the call and put back
        after it, so nothing is left aimed at a directory that no longer
        exists."""
        seen = []

        class _AttributeProvider:
            def __init__(self):
                self._working_dir = "."

            def advertise(self, snapshot):
                return (ActionItem(item_id="bug-4", kind="bug"),)

            def execute(self, item):
                seen.append(self._working_dir)
                return ActionOutcome(status=STATUS_COMPLETED)

            def reconcile(self, item, outcome):
                pass

        provider = _AttributeProvider()
        self.run_agent_isolated(provider)

        self.assertEqual(len(seen), 1)
        self.assertNotEqual(Path(seen[0]).resolve(), self.root)
        self.assertEqual(
            provider._working_dir, ".", "the provider was left pointing at a dead tree"
        )

    def test_a_provider_that_cannot_take_one_is_named_once(self):
        class _PlainProvider:
            def __init__(self):
                self._pending = [
                    ActionItem(item_id="bug-5", kind="bug"),
                    ActionItem(item_id="bug-6", kind="bug"),
                ]
                self.ran = []

            def advertise(self, snapshot):
                return tuple(self._pending)

            def execute(self, item):
                self._pending = [i for i in self._pending if i.item_id != item.item_id]
                self.ran.append(item.item_id)
                return ActionOutcome(status=STATUS_COMPLETED)

            def reconcile(self, item, outcome):
                pass

        provider = _PlainProvider()
        summary = self.run_agent_isolated(provider)

        self.assertEqual(provider.ran, ["bug-5", "bug-6"])
        self.assertEqual(summary.items_completed, 2)
        named = [
            line
            for line in self.report_lines
            if "takes no working directory" in line
        ]
        self.assertEqual(len(named), 1, f"expected one notice, got {named}")
        self.assertIn("repository root", named[0])

    def test_a_session_that_raises_still_has_its_edits_parked(self):
        """The item whose session died half-way is exactly the one whose edits
        would otherwise be inherited by the next item."""

        def write_then_die(item, working_dir):
            (Path(working_dir) / "half.txt").write_text("half a fix\n")
            raise RuntimeError("the session ended mid-gate")

        provider = _IsolatedProvider(
            [ActionItem(item_id="bug-8", kind="bug")], action=write_then_die
        )

        summary = self.run_agent_isolated(provider)

        self.assertEqual(summary.items_completed, 0)
        self.assertEqual(summary.items_escalated, 1)
        self.assertIn("the session ended mid-gate", summary.escalations[0].reason)
        self.assertTrue(self.ref_exists("refs/heads/wip/bug-8"))
        self.assertEqual(
            _git(self.root, "show", "wip/bug-8:half.txt").stdout, "half a fix\n"
        )
        self.assertIn("wip/bug-8", summary.wip_refs)


class TestItemWorktreeDirectly(_ItemWorktreeCase):
    """`item_worktree`'s own edges, driven without the conductor."""

    def test_an_existing_item_branch_is_not_reset_under_a_rerun(self):
        _git(self.root, "branch", "agent/bug-5")

        with worktree.item_worktree("bug-5", "HEAD") as tree:
            self.assertNotEqual(tree.branch, "agent/bug-5")
            self.assertTrue(tree.branch.startswith("agent/bug-5-"))
            (Path(tree.working_dir) / "new.txt").write_text("x\n")

        self.assertTrue(
            self.ref_exists("refs/heads/agent/bug-5"),
            "a rerun reset a branch that may have held real work",
        )

    def test_leftovers_that_cannot_be_committed_leave_the_tree_on_disk(self):
        """Tidying up must never be what destroys the work."""
        notes = []

        def refuses_to_commit(argv, check=False):
            if "commit" in argv:
                return SimpleNamespace(
                    returncode=1, stdout="", stderr="commit refused by a hook"
                )
            return subprocess.run(argv, capture_output=True, text=True, check=False)

        with worktree.item_worktree(
            "bug-11", "HEAD", runner=refuses_to_commit, report=notes.append
        ) as tree:
            (Path(tree.working_dir) / "precious.txt").write_text("do not lose me\n")
            path = Path(tree.working_dir)

        self.assertTrue(path.exists(), "the unsaved work was deleted")
        self.assertEqual(
            (path / "precious.txt").read_text(), "do not lose me\n"
        )
        self.assertIsNone(tree.wip_ref)
        self.assertTrue(any("could NOT be committed" in note for note in notes), notes)
        # Registered worktrees are the caller's to clean up by hand; do it here
        # so the temporary repository can be torn down.
        _git(self.root, "worktree", "remove", "--force", str(path), check=False)

    def test_dirty_paths_names_tracked_changes_only(self):
        (self.root / "README.md").write_text("hello\nedited\n")
        (self.root / "scratch.txt").write_text("not mine to judge\n")

        self.assertEqual(worktree.dirty_paths(), ["README.md"])

    def test_ref_slug_flattens_ids_git_could_not_hold(self):
        # `/` would make `agent/a` and `agent/a/b` a file and a directory at
        # the same path; the rest are simply not ref characters.
        self.assertEqual(worktree.ref_slug("finding/44"), "finding-44")
        self.assertEqual(worktree.ref_slug("issue #240: fix"), "issue-240-fix")
        self.assertEqual(worktree.ref_slug("a..b"), "a.b")
        self.assertEqual(worktree.ref_slug("---"), "item")
        self.assertEqual(worktree.ref_slug(""), "item")


if __name__ == "__main__":
    unittest.main()
