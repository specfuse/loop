#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression tests for FEAT-2026-0024 — commit_bookkeeping must not crash with
a raw CalledProcessError when a pre-commit hook rejects the bookkeeping commit.

Repro: the driver's awaiting_review bookkeeping commit (`commit_bookkeeping`)
ran `subprocess.run([... "commit" ...], check=True, capture_output=True)`. A
pre-commit hook exiting non-zero (here: the leak-scan hook re-tripping on a
`git@github.com` line captured into events.jsonl from a prior squash-rejection
error) raised a bare CalledProcessError with git's stderr swallowed, which
propagated out of run()/main() as an unhandled traceback. commit_bookkeeping
must instead raise a dedicated, readable error carrying git's stderr — the
sibling of squash_commit's #51 fix.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True)


class TestBookkeepingCommitHookCrash(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)],
                       check=True)
        _git(root, "config", "commit.gpgSign", "false")
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        (root / "init.txt").write_text("init\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        os.chdir(root)
        self.root = root

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _install_rejecting_hook(self, message: str) -> None:
        hook = self.root / ".git" / "hooks" / "pre-commit"
        hook.write_text(f"#!/bin/sh\necho '{message}' 1>&2\nexit 1\n")
        hook.chmod(0o755)

    def test_rejecting_precommit_hook_is_bypassed(self):
        """issue #156: commit_bookkeeping commits with --no-verify, so a
        rejecting pre-commit hook is BYPASSED — the bookkeeping commit lands.
        Internal driver commits belong to the `--all` scan trust context, not
        the human-oriented structural pre-commit. (Supersedes the FEAT-2026-0024
        behavior of surfacing the hook's rejection — the hook no longer runs.)"""
        self._install_rejecting_hook("HOOK-REJECTED-SENTINEL")
        (self.root / "gate.md").write_text("status: awaiting_review\n")
        sha = loop.commit_bookkeeping(["gate.md"], "chore(loop): gate 1 awaiting_review")
        self.assertIsInstance(sha, str)

    def test_genuine_commit_failure_still_raises_clean_error(self):
        """FEAT-2026-0024 crash-safety retained for NON-hook failures: a
        non-zero `git commit` from any other cause still raises
        BookkeepingCommitError carrying git's stderr (not a bare
        CalledProcessError). Simulated by patching subprocess.run."""
        import types
        (self.root / "gate.md").write_text("status: awaiting_review\n")
        real_run = subprocess.run

        def fake_run(cmd, *a, **kw):
            if cmd[:2] == ["git", "commit"]:
                return types.SimpleNamespace(
                    returncode=1, stdout="", stderr="fatal: simulated commit failure")
            return real_run(cmd, *a, **kw)

        orig = loop.subprocess.run
        loop.subprocess.run = fake_run
        try:
            with self.assertRaises(loop.BookkeepingCommitError) as ctx:
                loop.commit_bookkeeping(["gate.md"], "chore(loop): gate 1 awaiting_review")
        finally:
            loop.subprocess.run = orig
        self.assertIn("simulated commit failure", str(ctx.exception))

    def test_bookkeeping_succeeds_when_hook_passes(self):
        """Green path: no rejecting hook -> commit lands, returns the new sha."""
        (self.root / "gate.md").write_text("status: awaiting_review\n")
        sha = loop.commit_bookkeeping(["gate.md"], "chore(loop): bookkeeping")
        self.assertIsInstance(sha, str)

    def test_no_paths_returns_none(self):
        """Existing behavior preserved: no existing paths -> None, no error."""
        self.assertIsNone(
            loop.commit_bookkeeping(["does-not-exist.md"], "chore(loop): noop")
        )

    def test_no_diff_returns_none(self):
        """Existing behavior preserved: path exists but already committed ->
        None (nothing to commit), no error."""
        # init.txt is already committed and unchanged.
        self.assertIsNone(
            loop.commit_bookkeeping(["init.txt"], "chore(loop): noop")
        )


if __name__ == "__main__":
    unittest.main()
