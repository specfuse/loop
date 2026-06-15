#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression: the test process must be isolated from any inherited git
environment so subprocess `git` calls target temp repos, never the host repo.

Root cause (incident 2026-06-15): when the suite runs from a git hook
(e.g. the pre-push hook calling scripts/smoke-test.sh), git exports
GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE into the environment. Child `git`
processes honor those over cwd, so every test that `git init`-s a temp dir
instead read/wrote the HOST repo — observed: core.bare=true written into the
real .git/config and ~20 fixture branches created in the real ref store.

The fix scrubs those vars once, at tests-package import (tests/__init__.py),
before any test runs.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests import scrub_git_env
from tests._workspace import integration_workspace


class TestGitEnvIsolation(unittest.TestCase):
    def test_scrub_removes_leaky_vars_only(self):
        env = {
            "GIT_DIR": "/host/.git",
            "GIT_WORK_TREE": "/host",
            "GIT_INDEX_FILE": "/host/.git/index",
            "PATH": "/usr/bin",
        }
        removed = scrub_git_env(env)
        self.assertIn("GIT_DIR", removed)
        self.assertNotIn("GIT_DIR", env)
        self.assertNotIn("GIT_WORK_TREE", env)
        self.assertNotIn("GIT_INDEX_FILE", env)
        self.assertEqual(env.get("GIT_CONFIG_NOSYSTEM"), "1")
        # non-git vars untouched
        self.assertEqual(env["PATH"], "/usr/bin")

    def test_scrub_is_idempotent(self):
        env = {"PATH": "/usr/bin"}
        self.assertEqual(scrub_git_env(env), [])
        self.assertEqual(env.get("GIT_CONFIG_NOSYSTEM"), "1")

    def test_process_env_already_scrubbed_at_import(self):
        # tests/__init__ ran scrub_git_env() at import; the leaky vars must be
        # absent from the live process environment.
        for v in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            self.assertNotIn(v, os.environ)

    def test_workspace_targets_temp_repo_when_git_dir_leaked(self):
        # Simulate the pre-push-hook condition: GIT_DIR leaked into the env at
        # a bogus host path. After scrub (what import does), the workspace's
        # git ops must resolve INSIDE the temp root, never the leaked path.
        bogus = "/nonexistent/host/.git"
        prev = os.environ.get("GIT_DIR")
        os.environ["GIT_DIR"] = bogus
        try:
            scrub_git_env()
            self.assertNotIn("GIT_DIR", os.environ)
            with integration_workspace() as root:
                got = subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
                    capture_output=True, text=True, check=True,
                ).stdout.strip()
                self.assertTrue(
                    Path(got).resolve().is_relative_to(Path(root).resolve()),
                    f"workspace git dir {got!r} escaped temp root {root!r}",
                )
        finally:
            if prev is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = prev


if __name__ == "__main__":
    unittest.main()
