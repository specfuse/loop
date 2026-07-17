# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Issue #156: commit_bookkeeping (the driver's per-outcome status-flip /
# events commit) must also bypass the human-oriented structural pre-commit
# hook — it fires on every WU and carries the same false-positive-block hazard
# as squash_commit. Internal driver commits belong to the `--all` scan trust
# context (denylist + gitleaks), not the structural pre-commit.

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class TestBookkeepingNoVerify(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        _git(root, "config", "commit.gpgSign", "false")
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        (root / "seed").write_text("seed\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        os.chdir(root)
        self.root = root

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _install_rejecting_hook(self) -> None:
        hook = self.root / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'HOOK-REJECT' 1>&2\nexit 1\n")
        hook.chmod(0o755)

    def test_rejecting_precommit_hook_is_bypassed(self):
        """A rejecting pre-commit hook does not block commit_bookkeeping."""
        self._install_rejecting_hook()
        (self.root / "note.txt").write_text("bookkeeping state\n")
        sha = loop.commit_bookkeeping(["note.txt"], "chore(loop): bookkeeping")
        self.assertIsInstance(sha, str)
        # the file is now committed
        tracked = subprocess.run(
            ["git", "ls-files", "note.txt"], capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(tracked, "note.txt")

    def test_nothing_to_commit_returns_none(self):
        """Existing behavior preserved: no matching path -> None, no error."""
        self.assertIsNone(loop.commit_bookkeeping(["absent.txt"], "msg"))


if __name__ == "__main__":
    unittest.main()
