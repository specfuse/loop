#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""auto_sync's scaffold upgrade must not poison the same run's --prepare.

Before this fix, `specfuse-loop --prepare` crashed with a traceback: auto_sync
overlays the new scaffold (dirtying .specfuse/VERSION, .scaffold-manifest,
docs/, templates/) and leaves it uncommitted, then ensure_feature_branch
refuses to carry those "unexpected" paths onto the new feature branch.

The graceful behavior pinned here:

  1. auto_sync COMMITS its own scaffold overlay on a non-default branch
     (`chore(loop): sync scaffold to X.Y.Z`) so the tree is clean; on the
     DEFAULT branch it leaves them + prints guidance (--prepare carries them).
  2. ensure_feature_branch CARRIES scaffold-managed dirty paths onto a new
     branch instead of refusing — but still blocks genuinely-unrelated edits.
  3. prepare_feature FOLDS the scaffold-managed paths into its scaffold commit
     (so the default-branch case lands them committed on the feature branch).
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
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


@contextmanager
def _repo():
    """Temp git repo on `main`, one commit, a tracked scaffold template."""
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        _git(root, "config", "commit.gpgSign", "false")
        tmpl = root / ".specfuse/templates/WU.template.md"
        tmpl.parent.mkdir(parents=True)
        tmpl.write_text("old template\n")
        (root / ".specfuse/VERSION").write_text("0.3.0\n")
        (root / "README.md").write_text("# fixture\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        yield root


def _dirty_scaffold(root: Path) -> None:
    """Simulate auto_sync's overlay: modify tracked scaffold files."""
    (root / ".specfuse/templates/WU.template.md").write_text("new template\n")
    (root / ".specfuse/VERSION").write_text("0.3.11\n")


class TestDefaultBranch(unittest.TestCase):
    def test_local_main_detected(self):
        with _repo() as root, _chdir(root):
            self.assertEqual(loop._default_branch(), "main")


class TestScaffoldManagedDirty(unittest.TestCase):
    def test_classifies_scaffold_vs_user_paths(self):
        with _repo() as root:
            _dirty_scaffold(root)
            (root / "README.md").write_text("# edited\n")  # user edit
            with _chdir(root):
                managed = loop._scaffold_managed_dirty()
        self.assertIn(".specfuse/templates/WU.template.md", managed)
        self.assertIn(".specfuse/VERSION", managed)
        self.assertNotIn("README.md", managed)


class TestPersistScaffoldSync(unittest.TestCase):
    def test_commits_on_feature_branch(self):
        with _repo() as root:
            _git(root, "checkout", "-q", "-b", "feat/x")
            _dirty_scaffold(root)
            with _chdir(root):
                loop._persist_scaffold_sync("0.3.11")
                dirty = loop._tracked_dirty_paths()
            self.assertEqual(dirty, set(), "scaffold sync must be committed")
            self.assertIn("sync scaffold to 0.3.11",
                          _git(root, "log", "-1", "--pretty=%s"))

    def test_guides_and_leaves_on_default_branch(self):
        with _repo() as root:  # on main == default
            _dirty_scaffold(root)
            with _chdir(root):
                loop._persist_scaffold_sync("0.3.11")
                dirty = loop._tracked_dirty_paths()
            # left uncommitted (no surprise commit on the default branch)
            self.assertIn(".specfuse/VERSION", dirty)
            self.assertEqual("init", _git(root, "log", "-1", "--pretty=%s"))


class TestEnsureFeatureBranchCarriesScaffold(unittest.TestCase):
    def test_scaffold_paths_carry_onto_new_branch(self):
        with _repo() as root:
            _dirty_scaffold(root)
            with _chdir(root):
                loop.ensure_feature_branch({"branch": "feat/y"})
                current = _git(root, "branch", "--show-current")
            self.assertEqual(current, "feat/y")
            self.assertEqual(
                (root / ".specfuse/templates/WU.template.md").read_text(),
                "new template\n",
            )

    def test_unexpected_edit_still_blocks_even_with_scaffold_dirty(self):
        with _repo() as root:
            _commit = root / "src/app.py"
            _commit.parent.mkdir()
            _commit.write_text("x = 1\n")
            _git(root, "add", ".")
            _git(root, "commit", "-q", "-m", "app")
            _dirty_scaffold(root)
            (root / "src/app.py").write_text("x = 2\n")  # unrelated edit
            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch({"branch": "feat/z"})
            self.assertIn("src/app.py", str(ctx.exception))


class TestPrepareFoldsScaffold(unittest.TestCase):
    def test_default_branch_scaffold_folds_into_prepare_commit(self):
        with _repo() as root:  # on main == default
            feat_dir = root / ".specfuse/features/FEAT-2026-0099-x"
            feat_dir.mkdir(parents=True)
            (feat_dir / "PLAN.md").write_text("branch: feat/FEAT-2026-0099-x\n")
            _dirty_scaffold(root)  # auto_sync left these on default branch
            with _chdir(root):
                loop.prepare_feature(
                    {"branch": "feat/FEAT-2026-0099-x"}, feat_dir,
                    "FEAT-2026-0099",
                )
                dirty = loop._tracked_dirty_paths()
                current = _git(root, "branch", "--show-current")
            self.assertEqual(current, "feat/FEAT-2026-0099-x")
            self.assertEqual(dirty, set(), "scaffold + folder must be committed")
            # scaffold file is committed on the feature branch
            self.assertEqual(
                _git(root, "show", "HEAD:.specfuse/templates/WU.template.md"),
                "new template",
            )


if __name__ == "__main__":
    unittest.main()
