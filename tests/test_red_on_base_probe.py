#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Running the PR's own test at the merge base, safely (#3377).

The verdict `evaluate_merge_guardrails` consumes has to come from somewhere,
and the somewhere is two test runs. The one at the merge base is the new
information: CI already proved the head is green.

Two things this must not do. It must not check out the base in the working
tree -- the lane runs there, and a checkout would move the driver's own
ground under a run in progress -- so the probe uses an isolated
`git worktree`. And it must never guess the test command: the operator
declares it, because a guessed command that silently matches nothing would
report every test as red on base and wave every PR through, which is worse
than the gap being closed.

Fails closed everywhere. No declared command, no test files in the diff, a
worktree that will not create, a command that cannot run -- each returns
`None`, which the guardrail reads as unverified and declines.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from specfuse.loop.red_on_base import (
    select_test_files,
    test_was_red_on_base,
)


class SelectingTheTestsToRun(unittest.TestCase):

    def test_only_declared_test_paths_are_selected(self):
        selected = select_test_files(
            ["src/widget.py", "tests/test_widget.py", "docs/x.md"],
            ("tests/",),
        )

        self.assertEqual(["tests/test_widget.py"], selected)

    def test_several_test_roots_are_honoured(self):
        selected = select_test_files(
            ["src/main/java/A.java", "src/test/java/ATest.java", "spec/b_spec.rb"],
            ("src/test/", "spec/"),
        )

        self.assertEqual(
            ["spec/b_spec.rb", "src/test/java/ATest.java"], sorted(selected))

    def test_a_diff_with_no_test_file_selects_nothing(self):
        self.assertEqual([], select_test_files(["src/widget.py"], ("tests/",)))

    def test_unreadable_input_selects_nothing_rather_than_everything(self):
        self.assertEqual([], select_test_files(None, ("tests/",)))
        self.assertEqual([], select_test_files(["tests/a.py"], None))
        self.assertEqual([], select_test_files("tests/a.py", ("tests/",)))


class TheProbe(unittest.TestCase):

    def _tmp(self) -> Path:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_no_declared_command_is_unverified_not_a_pass(self):
        calls = []

        def runner(argv, **kw):
            calls.append(argv)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        verdict = test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="", worktree_root=self._tmp(),
        )

        self.assertIsNone(verdict)
        self.assertEqual([], calls, "nothing runs without a declared command")

    def test_no_test_files_is_unverified(self):
        verdict = test_was_red_on_base(
            lambda argv, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""),
            base_sha="abc123", test_files=[],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        )

        self.assertIsNone(verdict)

    def test_a_failing_run_at_the_base_is_red(self):
        seen = {}

        def runner(argv, **kw):
            if argv[:2] == ["git", "worktree"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            seen["cmd"] = argv
            return SimpleNamespace(returncode=1, stdout="1 failed", stderr="")

        verdict = test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        )

        self.assertIs(True, verdict)
        self.assertIn("tests/test_a.py", " ".join(seen["cmd"]))

    def test_a_passing_run_at_the_base_is_not_red(self):
        def runner(argv, **kw):
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        verdict = test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        )

        self.assertIs(False, verdict)

    def test_a_worktree_that_will_not_create_is_unverified(self):
        def runner(argv, **kw):
            if argv[:2] == ["git", "worktree"]:
                return SimpleNamespace(returncode=1, stdout="", stderr="fatal")
            raise AssertionError("must not run tests without a worktree")

        verdict = test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        )

        self.assertIsNone(verdict)

    def test_a_raising_runner_is_unverified_rather_than_fatal(self):
        def runner(argv, **kw):
            raise OSError("boom")

        self.assertIsNone(test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        ))

    def test_the_worktree_is_removed_afterwards(self):
        removals = []

        def runner(argv, **kw):
            if argv[:2] == ["git", "worktree"]:
                if "remove" in argv:
                    removals.append(argv)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="")

        test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        )

        self.assertEqual(1, len(removals), "the probe cleans up after itself")

    def test_the_live_working_tree_is_never_checked_out(self):
        # The lane is running in the working tree. A `git checkout` there would
        # move the ground under it mid-run.
        argvs = []

        def runner(argv, **kw):
            argvs.append(list(argv))
            return SimpleNamespace(returncode=1, stdout="", stderr="")

        test_was_red_on_base(
            runner, base_sha="abc123", test_files=["tests/test_a.py"],
            command_template="pytest {tests}", worktree_root=self._tmp(),
        )

        for argv in argvs:
            self.assertNotIn("checkout", argv)
            self.assertNotIn("reset", argv)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
