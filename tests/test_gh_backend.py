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
from unittest.mock import patch

import specfuse.loop.loop as _pkg_loop

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
        # Idempotency-probe returncode a stub_runner call to `gh pr view` reports.
        # Defaults to "not found" (1) so PR-creation tests exercise the create path
        # without each having to configure it explicitly.
        self.probe_returncode = 1

        def stub_runner(args: list, check: bool = True):
            self.calls.append(list(args))
            if args[:3] == ["gh", "pr", "view"]:
                return type("R", (), {"returncode": self.probe_returncode})()
            return None

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

    def test_on_feature_complete_creates_pr_and_flips_label(self):
        self.backend.on_feature_start("FEAT-2026-0003", {
            "branch": "feat/FEAT-2026-0003",
            "title": "Add thing",
            "initiative": "INIT-1",
        })
        self.calls.clear()
        # probe_returncode stays at setUp's default (1) -> PR does not yet exist.
        self.backend.on_feature_complete("FEAT-2026-0003")
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.calls[0][:3], ["gh", "pr", "view"])
        self.assertEqual(self.calls[1][:3], ["gh", "pr", "create"])
        self.assertIn("--head", self.calls[1])
        self.assertEqual(self.calls[1][self.calls[1].index("--head") + 1], "feat/FEAT-2026-0003")
        self.assertEqual(self.calls[2], [
            "gh", "issue", "edit", "287",
            "--repo", "owner/repo",
            "--add-label", "state:done",
            "--remove-label", "state:in-progress",
        ])

    def test_on_feature_complete_skips_pr_when_already_exists(self):
        self.backend.on_feature_start("FEAT-2026-0003", {"branch": "feat/x", "title": "t"})
        self.calls.clear()
        self.probe_returncode = 0
        self.backend.on_feature_complete("FEAT-2026-0003")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.calls[0][:3], ["gh", "pr", "view"])
        self.assertEqual(self.calls[1][:4], ["gh", "issue", "edit", "287"])

    def test_gh_pr_view_probe_goes_through_runner(self):
        """The idempotency probe must be observable by the injected runner,
        not escape via a direct subprocess.run call (see gh_backend.py's
        on_feature_complete)."""
        self.backend.on_feature_start("FEAT-2026-0003", {"branch": "feat/x", "title": "t"})
        self.calls.clear()
        self.backend.on_feature_complete("FEAT-2026-0003")
        probe_calls = [c for c in self.calls if c[:3] == ["gh", "pr", "view"]]
        self.assertEqual(len(probe_calls), 1)
        self.assertEqual(probe_calls[0], ["gh", "pr", "view", "feat/x", "--repo", "owner/repo", "--json", "number"])

    def test_pr_create_targets_resolved_base(self):
        self.backend.on_feature_start("FEAT-2026-0003", {
            "branch": "feat/FEAT-2026-0003",
            "title": "Add thing",
            "base": "release/2026.1",
        })
        self.calls.clear()
        self.backend.on_feature_complete("FEAT-2026-0003")
        create_call = next(c for c in self.calls if c[:3] == ["gh", "pr", "create"])
        self.assertIn("--base", create_call)
        self.assertEqual(create_call[create_call.index("--base") + 1], "release/2026.1")

    def test_pr_create_targets_default_branch_when_base_absent(self):
        self.backend.on_feature_start("FEAT-2026-0003", {
            "branch": "feat/FEAT-2026-0003",
            "title": "Add thing",
        })
        self.calls.clear()
        with patch.object(_pkg_loop, "_default_branch", return_value="develop"):
            self.backend.on_feature_complete("FEAT-2026-0003")
        create_call = next(c for c in self.calls if c[:3] == ["gh", "pr", "create"])
        self.assertIn("--base", create_call)
        self.assertEqual(create_call[create_call.index("--base") + 1], "develop")

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
