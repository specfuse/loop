# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.agent.repo_detect and the `--repo` contract (#2271).

`specfuse agent` with no `--repo` used to run to completion, report
`drained`, and exit 0 — having done nothing, because `default_providers`
returns `()` on a `None` repo. These cover the two halves of the fix: the
repo is detected from the checkout, and a run that genuinely cannot
determine one fails loudly instead of draining successfully.
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace

from specfuse.agent import run as run_module
from specfuse.agent.repo_detect import detect_repo, resolve_repo
from specfuse.agent.state import gather_snapshot


class _ScriptedRunner:
    """Replays one result per command prefix; records every call."""

    def __init__(self, results):
        self._results = dict(results)
        self.calls = []

    def __call__(self, argv, check=False):
        self.calls.append(list(argv))
        for prefix, result in self._results.items():
            if list(argv)[: len(prefix)] == list(prefix):
                if isinstance(result, Exception):
                    raise result
                return result
        return SimpleNamespace(returncode=1, stdout="", stderr="no such command")


def _ok(stdout):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


_FAIL = SimpleNamespace(returncode=1, stdout="", stderr="boom")


class DetectRepoTests(unittest.TestCase):
    def test_reads_gh_repo_view_first(self):
        runner = _ScriptedRunner(
            {("gh", "repo", "view"): _ok("acme-widget/example\n")}
        )
        self.assertEqual(detect_repo(runner=runner), "acme-widget/example")
        # `gh` answered, so the git remote is never consulted.
        self.assertEqual(len(runner.calls), 1)

    def test_falls_back_to_the_ssh_remote(self):
        runner = _ScriptedRunner(
            {
                ("gh", "repo", "view"): _FAIL,
                ("git", "remote"): _ok("git@github.com:acme-widget/example.git\n"),
            }
        )
        self.assertEqual(detect_repo(runner=runner), "acme-widget/example")

    def test_falls_back_to_the_https_remote(self):
        runner = _ScriptedRunner(
            {
                ("gh", "repo", "view"): _FAIL,
                ("git", "remote"): _ok("https://github.com/acme-widget/example.git\n"),
            }
        )
        self.assertEqual(detect_repo(runner=runner), "acme-widget/example")

    def test_remote_without_the_git_suffix(self):
        runner = _ScriptedRunner(
            {
                ("gh", "repo", "view"): _FAIL,
                ("git", "remote"): _ok("https://github.com/acme-widget/example\n"),
            }
        )
        self.assertEqual(detect_repo(runner=runner), "acme-widget/example")

    def test_a_non_github_remote_is_not_guessed_at(self):
        runner = _ScriptedRunner(
            {
                ("gh", "repo", "view"): _FAIL,
                ("git", "remote"): _ok("https://gitlab.com/acme-widget/example.git\n"),
            }
        )
        self.assertIsNone(detect_repo(runner=runner))

    def test_neither_source_answers(self):
        runner = _ScriptedRunner(
            {("gh", "repo", "view"): _FAIL, ("git", "remote"): _FAIL}
        )
        self.assertIsNone(detect_repo(runner=runner))

    def test_a_raising_runner_is_not_an_error(self):
        runner = _ScriptedRunner(
            {
                ("gh", "repo", "view"): FileNotFoundError("gh"),
                ("git", "remote"): FileNotFoundError("git"),
            }
        )
        self.assertIsNone(detect_repo(runner=runner))

    def test_blank_output_is_not_a_repo(self):
        runner = _ScriptedRunner(
            {("gh", "repo", "view"): _ok("\n"), ("git", "remote"): _ok("  \n")}
        )
        self.assertIsNone(detect_repo(runner=runner))

    def test_an_explicit_repo_wins_and_probes_nothing(self):
        runner = _ScriptedRunner(
            {("gh", "repo", "view"): _ok("detected/one\n")}
        )
        self.assertEqual(resolve_repo("chosen/one", runner=runner), "chosen/one")
        self.assertEqual(runner.calls, [])


class SnapshotWithoutARepoTests(unittest.TestCase):
    """A `None` repo used to reach `gh issue list --repo None` and surface as
    a `subprocess` TypeError about `os.PathLike` — a message naming neither
    `--repo` nor `gh`."""

    def test_the_sections_name_the_missing_repo_and_issue_no_command(self):
        runner = _ScriptedRunner({})
        snapshot = gather_snapshot(runner, None)

        self.assertEqual(runner.calls, [])
        for error in (snapshot.issues_error, snapshot.prs_error):
            self.assertIsNotNone(error)
            self.assertIn("repo", error)
            self.assertNotIn("PathLike", error)


class MainRepoContractTests(unittest.TestCase):
    """`main()` owes the operator a repo or a plain failure — never a
    successful-looking `drained` summary it did no work behind."""

    def setUp(self):
        self._real_run_agent = run_module.run_agent
        self._real_detect = run_module.detect_repo
        self._real_warn = run_module.warn_if_out_of_tree
        self._real_current = run_module.worktree.current_branch
        self._real_restore = run_module.worktree.restore_branch
        run_module.warn_if_out_of_tree = lambda *a, **k: None
        run_module.worktree.current_branch = lambda *a, **k: "main"
        run_module.worktree.restore_branch = lambda *a, **k: True

    def tearDown(self):
        run_module.run_agent = self._real_run_agent
        run_module.detect_repo = self._real_detect
        run_module.warn_if_out_of_tree = self._real_warn
        run_module.worktree.current_branch = self._real_current
        run_module.worktree.restore_branch = self._real_restore

    def test_an_undetectable_repo_fails_loudly_and_runs_nothing(self):
        run_module.detect_repo = lambda **kwargs: None
        called = []
        run_module.run_agent = lambda **kwargs: called.append(kwargs)

        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = run_module.main([])

        self.assertNotEqual(code, 0)
        self.assertEqual(called, [])
        message = err.getvalue()
        self.assertIn("--repo", message)
        self.assertNotIn("drained", message)

    def test_a_detected_repo_reaches_the_run_and_its_providers(self):
        run_module.detect_repo = lambda **kwargs: "acme-widget/example"
        seen = {}

        def _fake_run_agent(**kwargs):
            seen.update(kwargs)
            return run_module.RunSummary(
                items_attempted=0,
                items_completed=0,
                items_escalated=0,
                escalations=(),
                stop_reason="drained",
                elapsed_minutes=0.0,
                tokens_spent=0,
            )

        run_module.run_agent = _fake_run_agent
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = run_module.main([])

        self.assertEqual(code, 0)
        self.assertEqual(seen["repo"], "acme-widget/example")
        # The providers are built from the same detected value, not from the
        # `None` that made them an empty tuple.
        self.assertTrue(seen["providers"])


if __name__ == "__main__":
    unittest.main()
