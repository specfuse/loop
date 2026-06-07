#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for GitHubBackend lifecycle hooks and make_backend factory selection.

Loads loop as "loop" (not "loop_under_test") so that gh_backend.py's
`import loop` resolves to the same module object — keeping isinstance
checks coherent across both modules in a single test process.
No live gh call fires: all subprocess interaction goes through a stub runner.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(relpath: str, module_name: str):
    path = REPO_ROOT / relpath
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Load loop as "loop" first so gh_backend's `import loop` resolves here.
_loop = _load_module(".specfuse/scripts/loop.py", "loop")
# gh_backend imports loop at module level; load after "loop" is registered.
_gh = _load_module(".specfuse/scripts/gh_backend.py", "gh_backend")

Backend = _loop.Backend
GitHubBackend = _gh.GitHubBackend
make_backend = _loop.make_backend


# --------------------------------------------------------------------------- #
# GitHubBackend — lifecycle hook behaviour                                    #
# --------------------------------------------------------------------------- #


class TestGitHubBackendHooks(unittest.TestCase):

    def setUp(self):
        self.calls: list[list[str]] = []

        def stub_runner(args: list) -> None:
            self.calls.append(list(args))

        self.backend = GitHubBackend("owner/repo", 287, runner=stub_runner)

    def test_on_feature_start_exact_args(self):
        self.backend.on_feature_start("FEAT-2026-0003", {})
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0], [
            "gh", "issue", "edit", "287",
            "--repo", "owner/repo",
            "--add-label", "state:in-progress",
            "--remove-label", "state:ready",
        ])

    def test_on_gate_passed_fires_runner_zero_times(self):
        self.backend.on_gate_passed("FEAT-2026-0003", 1)
        self.assertEqual(self.calls, [])

    def test_on_feature_complete_exact_args(self):
        self.backend.on_feature_complete("FEAT-2026-0003")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0], [
            "gh", "issue", "edit", "287",
            "--repo", "owner/repo",
            "--add-label", "state:done",
            "--remove-label", "state:in-progress",
        ])

    def test_github_backend_is_backend_subclass(self):
        self.assertIsInstance(self.backend, Backend)


# --------------------------------------------------------------------------- #
# make_backend factory — selection logic                                       #
# --------------------------------------------------------------------------- #


class TestMakeBackendFactory(unittest.TestCase):

    def test_empty_fm_returns_plain_backend(self):
        """Regression guard for T05's contract: no source_issue_url → plain Backend."""
        b = make_backend({})
        self.assertIsInstance(b, Backend)
        self.assertNotIsInstance(b, GitHubBackend)

    def test_valid_source_issue_url_returns_github_backend(self):
        b = make_backend({"source_issue_url": "https://github.com/owner/repo/issues/287"})
        self.assertIsInstance(b, GitHubBackend)
        self.assertEqual(b.repo, "owner/repo")
        self.assertEqual(b.issue_number, 287)

    def test_malformed_url_returns_plain_backend(self):
        """Graceful fallback: a bad URL must not raise — degraded is safer than crashed."""
        b = make_backend({"source_issue_url": "not-a-url"})
        self.assertIsInstance(b, Backend)
        self.assertNotIsInstance(b, GitHubBackend)

    def test_partial_github_url_returns_plain_backend(self):
        """A GitHub URL that lacks /issues/<n> does not match."""
        b = make_backend({"source_issue_url": "https://github.com/owner/repo"})
        self.assertIsInstance(b, Backend)
        self.assertNotIsInstance(b, GitHubBackend)

    def test_empty_source_issue_url_returns_plain_backend(self):
        b = make_backend({"source_issue_url": ""})
        self.assertIsInstance(b, Backend)
        self.assertNotIsInstance(b, GitHubBackend)

    def test_fm_without_source_issue_url_key_returns_plain_backend(self):
        b = make_backend({"feature_id": "FEAT-X", "branch": "feat/x"})
        self.assertIsInstance(b, Backend)
        self.assertNotIsInstance(b, GitHubBackend)


if __name__ == "__main__":
    unittest.main()
