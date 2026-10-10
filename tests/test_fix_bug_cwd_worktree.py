# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3420: the headless `/fix-bug` session runs *in* the item's worktree.

With per-item worktrees on, `_call_execute` pointed `BugsProvider` at the
item's tree, but that path only ever reached the session as a line of prompt
text (`Working directory: ...`). The `claude` subprocess itself was launched
with the run's own cwd -- the operator's primary checkout. Sessions that
`cd`'d into the tree stayed isolated; sessions that followed `/fix-bug`'s own
branch workflow from where they started branched, committed and rebased in
the primary checkout (4 of 9 items on 2026-10-08).

The fix is the process boundary: the `claude` dispatch is started with
`cwd=<item worktree>`, so isolation no longer depends on the model reading
one line of its prompt.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent import run as agent_run
from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import KIND_BUG, ActionItem, _call_execute
from specfuse.loop.bug_lane_run import BugLaneResult, OUTCOME_MERGED


def _kwarg_recording_runner(calls: list):
    def runner(argv, check: bool = False, **kwargs):
        calls.append((list(argv), kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


def _fake_lane(passed_runner, repo, issue_number, **kwargs):
    passed_runner(["gh", "issue", "view", str(issue_number)], check=False)
    passed_runner(["claude", "-p", "--model", "sonnet", "/specfuse:fix-bug"], check=False)
    return BugLaneResult(outcome=OUTCOME_MERGED, reason="eligible", pr_number=5)


class TestFixBugSessionRunsInItemWorktree(unittest.TestCase):
    def _dispatch(self, working_dir):
        calls = []
        provider = BugsProvider(repo="o/r", runner=_kwarg_recording_runner(calls))
        item = ActionItem(item_id="bug-2350", kind=KIND_BUG)
        with patch("specfuse.agent.providers.bugs.run_bug_lane", side_effect=_fake_lane):
            _call_execute(provider, item, working_dir, lambda _m: None, set())
        return calls

    def test_claude_dispatch_is_started_in_the_item_worktree(self):
        calls = self._dispatch("/tmp/specfuse-item-bug-2350")

        claude = [kw for argv, kw in calls if argv[:1] == ["claude"]]
        self.assertEqual(len(claude), 1)
        self.assertEqual(claude[0].get("cwd"), "/tmp/specfuse-item-bug-2350")

    def test_gh_calls_are_not_relocated(self):
        calls = self._dispatch("/tmp/specfuse-item-bug-2350")

        gh = [kw for argv, kw in calls if argv[:1] == ["gh"]]
        self.assertEqual(len(gh), 1)
        self.assertNotIn("cwd", gh[0])

    def test_default_runner_forwards_cwd_to_subprocess(self):
        with patch.object(agent_run.subprocess, "run") as run:
            agent_run._default_runner(["claude", "-p"], cwd="/tmp/tree")

        self.assertEqual(run.call_args.kwargs.get("cwd"), "/tmp/tree")


if __name__ == "__main__":
    unittest.main()
