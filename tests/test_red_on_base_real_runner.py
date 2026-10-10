# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3452: the red-on-base probe runs through the bug lane's *real* runner.

`test_was_red_on_base` runs the operator's command with `runner(..., cwd=)`.
The runner the bug lane hands it is `BugsProvider`'s `_bounded_runner`
wrapper around the agent's `_default_runner`, and neither accepted `cwd`.
The `TypeError` was swallowed by the probe's fail-closed `except`, so every
bug-lane PR declined `red_on_base_unverified` whatever its tests did (4 of 4
correct PRs on 2026-10-09). The existing tests injected a runner that
accepted `cwd`, which is how this shipped green.

This drives the probe through the same runner chain `BugsProvider.execute`
builds, over a real git repository, with no fake runner anywhere.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.run import KIND_BUG, ActionItem
from specfuse.loop.bug_lane_run import BugLaneResult, OUTCOME_MERGED
from specfuse.loop.red_on_base import test_was_red_on_base


def _git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    )


class TestRedOnBaseThroughTheLaneRunner(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")
        (self.repo / "only_at_base.txt").write_text("x\n")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self._cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self):
        os.chdir(self._cwd)
        subprocess.run(
            ["git", "worktree", "prune"], cwd=self.repo, capture_output=True, check=False
        )
        self._tmp.cleanup()

    def _probe_via_provider(self, command_template):
        verdicts = []

        def fake_lane(passed_runner, repo, issue_number, **kwargs):
            verdicts.append(
                test_was_red_on_base(
                    passed_runner,
                    base_sha=self.base,
                    test_files=["tests/test_x.py"],
                    command_template=command_template,
                    worktree_root=self._tmp.name,
                )
            )
            return BugLaneResult(outcome=OUTCOME_MERGED, reason="eligible", pr_number=1)

        provider = BugsProvider(repo="o/r")  # the real `_default_runner`
        with patch("specfuse.agent.providers.bugs.run_bug_lane", side_effect=fake_lane):
            provider.execute(ActionItem(item_id="bug-2436", kind=KIND_BUG))
        return verdicts[0]

    def test_a_test_failing_at_base_reads_red(self):
        # Fails only where the base tree is the cwd: the marker exists there.
        verdict = self._probe_via_provider("test ! -f only_at_base.txt {tests}")

        self.assertIs(verdict, True)

    def test_a_test_passing_at_base_reads_not_red(self):
        verdict = self._probe_via_provider("test -f only_at_base.txt || exit 1; : {tests}")

        self.assertIs(verdict, False)


if __name__ == "__main__":
    unittest.main()
