#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression tests for issue #51 — squash_commit must not crash with a raw
CalledProcessError when a pre-commit hook rejects the commit.

Repro: the driver's internal squash commit (`squash_commit`) ran
`subprocess.run([... "commit" ...], check=True, capture_output=True)`. A
pre-commit hook exiting non-zero (e.g. the leak-scan hook flagging a fixture
email) raised a bare CalledProcessError with git's stderr swallowed, which
propagated out of run()/main() as an unhandled traceback. squash_commit must
instead raise a dedicated, readable error carrying git's stderr.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import types
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True)


class TestSquashCommitHookCrash(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)],
                       check=True)
        _git(root, "config", "commit.gpgSign", "false")
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        (root / "a.py").write_text("a\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        self.head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        os.chdir(root)
        self.root = root
        self.wu = types.SimpleNamespace(title="Test WU", wu_id="FEAT-TEST/T01")

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _install_rejecting_hook(self, message: str) -> None:
        hook = self.root / ".git" / "hooks" / "pre-commit"
        hook.write_text(f"#!/bin/sh\necho '{message}' 1>&2\nexit 1\n")
        hook.chmod(0o755)

    def test_hook_rejection_raises_clean_error_not_calledprocesserror(self):
        """A pre-commit hook exiting non-zero raises SquashCommitError, not a
        bare CalledProcessError. This is the #51 crash."""
        self._install_rejecting_hook("HOOK-REJECTED-SENTINEL")
        (self.root / "a.py").write_text("a\nchanged\n")
        with self.assertRaises(loop.SquashCommitError):
            loop.squash_commit(self.wu, self.head)

    def test_hook_rejection_error_carries_git_stderr(self):
        """The raised error surfaces git's stderr (the hook's message), which
        the old code swallowed via capture_output."""
        self._install_rejecting_hook("HOOK-REJECTED-SENTINEL")
        (self.root / "a.py").write_text("a\nchanged\n")
        try:
            loop.squash_commit(self.wu, self.head)
        except loop.SquashCommitError as exc:
            self.assertIn("HOOK-REJECTED-SENTINEL", str(exc))
        else:
            self.fail("squash_commit did not raise SquashCommitError")

    def test_squash_commit_succeeds_when_hook_passes(self):
        """Green path: no rejecting hook -> commit lands, returns the new sha."""
        (self.root / "a.py").write_text("a\nchanged\n")
        sha = loop.squash_commit(self.wu, self.head)
        self.assertIsInstance(sha, str)
        self.assertNotEqual(sha, self.head)

    def test_squash_commit_no_changes_returns_none(self):
        """Existing behavior preserved: nothing to commit -> None, no error."""
        self.assertIsNone(loop.squash_commit(self.wu, self.head))


if __name__ == "__main__":
    unittest.main()
