#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression + hardening for ensure_feature_branch (FEAT-2026-0023/T03, #48).

ensure_feature_branch used to call `git checkout <branch>` / `git checkout -B
<branch>` unguarded through git() (check=True, capture_output=True). Two
real-world states crashed it with a bare CalledProcessError that swallowed the
stderr explaining the cause:

  1. a dirty working tree (the /pick-feature status flips, uncommitted), and
  2. a stale pre-existing branch that diverges from the current base.

These tests pin the hardened behavior: a clear FeatureBranchError carrying
git's stderr, expected pick-flips carried onto a new branch, unexpected dirty
paths refused, and a divergent stale branch surfaced rather than silently used.
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


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


@contextmanager
def _chdir(path: Path):
    """ensure_feature_branch shells out to cwd-relative git; run it inside the
    temp repo and always restore the previous cwd."""
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


@contextmanager
def _repo():
    """A temp git repo on `main` with one commit; README.md tracked."""
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


def _commit_file(root: Path, rel: str, content: str, msg: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    _git(root, "add", rel)
    _git(root, "commit", "-q", "-m", msg)


class TestEnsureFeatureBranch(unittest.TestCase):
    # AC 1 — RED on HEAD: a dirty tree blocking the switch into an existing
    # (non-divergent) branch must raise a clear error containing git's stderr,
    # never a bare CalledProcessError.
    def test_dirty_tree_checkout_raises_clean_error(self):
        with _repo() as root:
            # commit1 on main: foo.txt="a"
            _commit_file(root, "foo.txt", "a\n", "add foo")
            # branch points at commit1 (ancestor of HEAD — not divergent)
            _git(root, "branch", "feat/x")
            # advance main so foo.txt differs from the branch's version
            _commit_file(root, "foo.txt", "b\n", "change foo")
            # uncommitted local change blocks `checkout feat/x`
            (root / "foo.txt").write_text("c\n")

            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch({"branch": "feat/x"})
            msg = str(ctx.exception)
            # message carries git's own stderr (which names the blocking file)
            self.assertIn("foo.txt", msg)
            self.assertNotIsInstance(ctx.exception, subprocess.CalledProcessError)

    # AC 3 — expected /pick-feature flips ride onto a freshly created branch.
    def test_pick_flips_carried_onto_new_branch(self):
        with _repo() as root:
            feat_dir = root / ".specfuse/features/FEAT-2026-0023-x"
            _commit_file(root, ".specfuse/roadmap.md", "rm base\n", "roadmap")
            _commit_file(root, ".specfuse/features/FEAT-2026-0023-x/PLAN.md",
                         "status: planned\n", "plan")
            # /pick-feature flips, uncommitted
            (root / ".specfuse/roadmap.md").write_text("rm ACTIVE\n")
            (feat_dir / "PLAN.md").write_text("status: active\n")

            with _chdir(root):
                loop.ensure_feature_branch(
                    {"branch": "feat/FEAT-2026-0023-x"}, feat_dir
                )
                current = _git(root, "branch", "--show-current")
            self.assertEqual(current, "feat/FEAT-2026-0023-x")
            # flips carried (still present and still dirty on the new branch)
            self.assertEqual((root / ".specfuse/roadmap.md").read_text(), "rm ACTIVE\n")
            self.assertEqual((feat_dir / "PLAN.md").read_text(), "status: active\n")
            dirty = loop._tracked_dirty_paths
            with _chdir(root):
                self.assertTrue(dirty())

    # AC 4 — tracked changes to paths OTHER than the expected flips stop the
    # driver; the branch is not created and unrelated edits are not carried.
    def test_unexpected_dirty_paths_block(self):
        with _repo() as root:
            feat_dir = root / ".specfuse/features/FEAT-2026-0023-x"
            _commit_file(root, "src/app.py", "x = 1\n", "app")
            # an unrelated tracked file is dirty
            (root / "src/app.py").write_text("x = 2\n")

            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch(
                        {"branch": "feat/FEAT-2026-0023-x"}, feat_dir
                    )
                # branch was NOT created
                exists = subprocess.run(
                    ["git", "rev-parse", "--verify", "feat/FEAT-2026-0023-x"],
                    capture_output=True, text=True,
                ).returncode == 0
            self.assertFalse(exists)
            self.assertIn("src/app.py", str(ctx.exception))

    # AC 5 — a pre-existing branch that diverges from HEAD is surfaced, not
    # silently checked out.
    def test_stale_divergent_branch_surfaced(self):
        with _repo() as root:
            # create feat/x and put a commit on it that main never sees
            _git(root, "checkout", "-q", "-b", "feat/x")
            _commit_file(root, "only_on_branch.txt", "1\n", "branch-only commit")
            _git(root, "checkout", "-q", "main")
            # advance main independently → feat/x diverges (not an ancestor)
            _commit_file(root, "only_on_main.txt", "1\n", "main-only commit")

            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch({"branch": "feat/x"})
                # not silently switched
                current = _git(root, "branch", "--show-current")
            self.assertEqual(current, "main")
            self.assertIn("diverge", str(ctx.exception).lower())

    # AC 6 — clean path preserved: -B creates from HEAD when absent; no-op when
    # already on the branch.
    def test_clean_tree_creates_or_switches(self):
        with _repo() as root:
            with _chdir(root):
                # clean, no existing branch → create from HEAD
                loop.ensure_feature_branch({"branch": "feat/clean"})
                self.assertEqual(_git(root, "branch", "--show-current"), "feat/clean")
                # already on the branch, clean → no-op, still there
                loop.ensure_feature_branch({"branch": "feat/clean"})
                self.assertEqual(_git(root, "branch", "--show-current"), "feat/clean")

    # AC 7 — existence/import smoke.
    def test_symbol_importable(self):
        self.assertTrue(callable(loop.ensure_feature_branch))
        self.assertTrue(issubclass(loop.FeatureBranchError, Exception))

    def test_smoke_import_from_scripts_dir(self):
        scripts = Path(__file__).resolve().parent.parent / ".specfuse" / "scripts"
        proc = subprocess.run(
            ["python3", "-c", "from loop import ensure_feature_branch"],
            cwd=str(scripts), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
