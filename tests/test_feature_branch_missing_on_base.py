#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""ensure_feature_branch must not cut a branch that lacks the feature (#3601).

A feature folder committed on a working branch, whose PLAN.md names a branch
that does not exist yet and a `base` that does not contain the folder, used to
be cut from that base: the new branch had no PLAN.md, the next read raised a
bare FileNotFoundError, and the operator was left on the new branch. The driver
now refuses before switching, and leaves the operator where they were.

Real git in a tmpdir; no mocking.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from tests._loop_loader import load_loop

loop = load_loop()

FEATURE = ".specfuse/features/FEAT-X-0001-demo"
FM = {"branch": "feat/FEAT-X-0001-demo", "base": "main"}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


@contextmanager
def _chdir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


@contextmanager
def _repo():
    """A temp git repo on `main` with one commit, no origin configured."""
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        _git(root, "config", "commit.gpgSign", "false")
        (root / "README.md").write_text("# fixture\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        yield root


def _write_feature(root: Path) -> Path:
    fd = root / FEATURE
    fd.mkdir(parents=True)
    (fd / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-X-0001\nbranch: feat/FEAT-X-0001-demo\nbase: main\n---\n"
    )
    return fd


def _branch_exists(root: Path, name: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "-q", name],
        capture_output=True, check=False,
    ).returncode == 0


class TestFeatureMissingOnBase(unittest.TestCase):
    def test_refuses_before_switching_when_base_lacks_the_committed_feature(self):
        with _repo() as root:
            _git(root, "checkout", "-q", "-b", "work")
            fd = _write_feature(root)
            _git(root, "add", ".")
            _git(root, "commit", "-q", "-m", "draft feature on work")

            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch(dict(FM), fd)

            msg = str(ctx.exception)
            self.assertIn(f"{FEATURE}/PLAN.md", msg)
            self.assertIn("'main'", msg)
            self.assertIn("'work'", msg)
            self.assertEqual(_git(root, "branch", "--show-current"), "work")
            self.assertFalse(_branch_exists(root, FM["branch"]))
            self.assertTrue((fd / "PLAN.md").is_file())

    def test_base_that_holds_the_feature_still_creates_the_branch(self):
        with _repo() as root:
            fd = _write_feature(root)
            _git(root, "add", ".")
            _git(root, "commit", "-q", "-m", "feature on main")

            with _chdir(root):
                loop.ensure_feature_branch(dict(FM), fd)

            self.assertEqual(_git(root, "branch", "--show-current"), FM["branch"])
            self.assertTrue((fd / "PLAN.md").is_file())

    def test_untracked_feature_folder_still_rides_onto_the_new_branch(self):
        # The draft-feature / --prepare path: the folder is not committed
        # anywhere yet, so `checkout -B` carries it along untouched.
        with _repo() as root:
            fd = _write_feature(root)

            with _chdir(root):
                loop.ensure_feature_branch(dict(FM), fd)

            self.assertEqual(_git(root, "branch", "--show-current"), FM["branch"])
            self.assertTrue((fd / "PLAN.md").is_file())


if __name__ == "__main__":
    unittest.main()
