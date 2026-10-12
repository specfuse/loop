# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The red-on-base probe fetches a base it lacks, and says why it gave up (#3416).

`_merge_base_sha` asks GitHub for `baseRefOid` -- the base branch's tip *now*.
Any PR merged to it during a run moves that tip past the local clone's
`origin/main`, so `git worktree add <sha>` failed and every later bug-lane PR
in the run declined `red_on_base_unverified` (5 of 5 on clabonte/generator,
2026-10-03). The probe now fetches the commit when it is absent.

And every give-up path returned a bare `None`, so nobody could tell after the
fact whether the lookup, the worktree or the command had failed. Each now
carries a reason, which reaches the escalation's evidence.
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

from specfuse.loop.bug_lane import REASON_RED_ON_BASE_UNVERIFIED
from specfuse.loop.bug_lane_run import _evidence_for
from specfuse.loop.red_on_base import probe_red_on_base


def _git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _real_runner(argv, check=False, cwd=None, **_kwargs):
    return subprocess.run(argv, check=check, capture_output=True, text=True, cwd=cwd)


class TestBaseCommitMissingLocally(unittest.TestCase):
    """A real origin that advanced after the clone was taken."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        origin = tmp / "origin"
        origin.mkdir()
        _git(origin, "init", "-q", "-b", "main")
        (origin / "a.txt").write_text("a\n")
        _git(origin, "add", ".")
        _git(origin, "commit", "-q", "-m", "first")
        self.clone = tmp / "clone"
        _git(tmp, "clone", "-q", str(origin), str(self.clone))
        # main advances on the remote mid-run: the clone never sees it.
        (origin / "only_at_new_base.txt").write_text("x\n")
        _git(origin, "add", ".")
        _git(origin, "commit", "-q", "-m", "merged during the run")
        self.new_base = _git(origin, "rev-parse", "HEAD")
        self._cwd = os.getcwd()
        os.chdir(self.clone)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_absent_base_is_fetched_and_the_probe_answers(self):
        probe = probe_red_on_base(
            _real_runner,
            base_sha=self.new_base,
            test_files=["tests/test_x.py"],
            # Red only where the tree is the new base: the marker exists there.
            command_template="test ! -f only_at_new_base.txt || exit 1; : {tests}",
            worktree_root=self._tmp.name,
        )

        self.assertIs(probe.verdict, True, probe.reason)


def _runner(failing=None, raising=None):
    """Fake runner: argv prefixes in *failing* exit 1, in *raising* raise."""
    failing = failing or {}

    def run(argv, check=False, **_kwargs):
        if raising and argv[: len(raising)] == raising:
            raise OSError("no such file")
        for prefix, stderr in failing.items():
            if tuple(argv[: len(prefix)]) == prefix:
                return SimpleNamespace(returncode=1, stdout="", stderr=stderr)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return run


def _probe(runner, **overrides):
    kwargs = dict(
        base_sha="abc123", test_files=["tests/test_a.py"],
        command_template="pytest {tests}", worktree_root=tempfile.gettempdir(),
    )
    kwargs.update(overrides)
    return probe_red_on_base(runner, **kwargs)


class TestEveryGiveUpCarriesAReason(unittest.TestCase):
    def test_no_command(self):
        self.assertEqual(_probe(_runner(), command_template="").reason, "no_command")

    def test_no_test_files(self):
        self.assertEqual(_probe(_runner(), test_files=[]).reason, "no_test_files")

    def test_base_sha_lookup_failed(self):
        self.assertEqual(_probe(_runner(), base_sha="").reason, "base_sha_lookup_failed")

    def test_fetch_failed_names_gits_error(self):
        probe = _probe(_runner(failing={
            ("git", "cat-file"): "",
            ("git", "fetch"): "fatal: couldn't find remote ref abc123",
        }))

        self.assertIsNone(probe.verdict)
        self.assertTrue(probe.reason.startswith("fetch_failed"), probe.reason)
        self.assertIn("couldn't find remote ref", probe.reason)

    def test_worktree_add_failed_names_gits_error(self):
        probe = _probe(_runner(failing={
            ("git", "worktree", "add"): "fatal: invalid reference: abc123",
        }))

        self.assertTrue(probe.reason.startswith("worktree_add_failed"), probe.reason)
        self.assertIn("invalid reference", probe.reason)

    def test_runner_raised(self):
        probe = _probe(_runner(raising=["sh", "-c"]))

        self.assertTrue(probe.reason.startswith("runner_raised"), probe.reason)

    def test_could_not_execute(self):
        probe = _probe(_runner(failing={("sh", "-c"): "sh: pytest: not found"}))
        # exit 1 is a verdict; 127 is not
        self.assertIs(probe.verdict, True)

        def not_found(argv, check=False, **_kwargs):
            code = 127 if argv[:2] == ["sh", "-c"] else 0
            return SimpleNamespace(returncode=code, stdout="", stderr="")

        probe = _probe(not_found)

        self.assertIsNone(probe.verdict)
        self.assertEqual(probe.reason, "could_not_execute: exit 127")

    def test_a_verdict_carries_no_reason(self):
        self.assertEqual(_probe(_runner()).reason, "")


class TestReasonReachesTheEscalation(unittest.TestCase):
    def test_unverified_evidence_names_the_reason(self):
        evidence = _evidence_for(
            REASON_RED_ON_BASE_UNVERIFIED, ["tests/test_a.py"], 5, {},
            red_on_base_reason="worktree_add_failed: fatal: invalid reference",
        )

        self.assertTrue(evidence)
        self.assertIn("worktree_add_failed", evidence[0])


if __name__ == "__main__":
    unittest.main()
