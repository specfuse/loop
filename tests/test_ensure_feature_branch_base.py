#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""ensure_feature_branch cut from the resolved base (FEAT-2026-0031/T02).

Before this WU, ensure_feature_branch always created and staleness-checked
branches against HEAD/the current branch. With a declared `base` in PLAN.md
frontmatter, that is wrong: the feature branch must be cut from the declared
base (via resolve_base/ensure_base_ref, T01), and the staleness guard must
measure divergence against that base — not against wherever the operator
happens to be standing. These tests use real git in a tmpdir; no mocking.
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
def _repo_no_remote():
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


def _commit_file(root: Path, rel: str, content: str, msg: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    _git(root, "add", rel)
    _git(root, "commit", "-q", "-m", msg)


class TestEnsureFeatureBranchBase(unittest.TestCase):
    # AC 1/4/12 — RED on HEAD (resolve_base/ensure_base_ref not wired in yet):
    # with `base: release/2.0` declared and HEAD standing on `main`, the
    # created feature branch must be cut from release/2.0, not from HEAD/main.
    def test_branch_is_cut_from_declared_base(self):
        with _repo_no_remote() as root:
            _git(root, "checkout", "-q", "-b", "release/2.0")
            _commit_file(root, "release_only.txt", "1\n", "release-only commit")
            release_tip = _git(root, "rev-parse", "release/2.0")

            _git(root, "checkout", "-q", "main")
            _commit_file(root, "main_only.txt", "1\n", "main-only commit")

            with _chdir(root):
                loop.ensure_feature_branch({"branch": "feat/x", "base": "release/2.0"})
                current = _git(root, "branch", "--show-current")
                merge_base = _git(root, "merge-base", "feat/x", "release/2.0")

            self.assertEqual(current, "feat/x")
            self.assertEqual(merge_base, release_tip)

    # AC 6 — no-regression path: a feature with no `base` key still resolves
    # via _default_branch() and is cut from the default branch (main).
    def test_no_base_key_still_cuts_from_default_branch(self):
        with _repo_no_remote() as root:
            main_tip = _git(root, "rev-parse", "main")

            with _chdir(root):
                loop.ensure_feature_branch({"branch": "feat/no-base"})
                current = _git(root, "branch", "--show-current")
                merge_base = _git(root, "merge-base", "feat/no-base", "main")

            self.assertEqual(current, "feat/no-base")
            self.assertEqual(merge_base, main_tip)

    # AC 5/7/8/9/10 — staleness guard re-anchored to the resolved base: a
    # branch that diverges from the declared base (even while being an
    # ancestor of HEAD) is surfaced with an operator-readable message that
    # names the branch and base, offers the rebase-onto-base hint, and never
    # offers `git branch -D`.
    def test_stale_branch_surfaced_against_base_not_head(self):
        with _repo_no_remote() as root:
            _git(root, "checkout", "-q", "-b", "release/2.0")
            _commit_file(root, "release_only.txt", "1\n", "release-only commit")

            _git(root, "checkout", "-q", "main")
            _git(root, "checkout", "-q", "-b", "feat/x")
            _commit_file(root, "feat_only.txt", "1\n", "feat-only commit")
            _git(root, "checkout", "-q", "main")

            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch({"branch": "feat/x", "base": "release/2.0"})
                current = _git(root, "branch", "--show-current")

            self.assertEqual(current, "main")  # not silently switched
            msg = str(ctx.exception)
            self.assertIn("feat/x", msg)
            self.assertIn("release/2.0", msg)
            self.assertIn("git rebase release/2.0", msg)
            self.assertNotIn("-D", msg)

    # AC 11 — regression: the dirty-tree allowlist (_expected_flip_paths |
    # _scaffold_managed_dirty) is unchanged; unexpected tracked edits still
    # block branch creation even with a declared base.
    def test_unexpected_dirty_paths_still_block_with_base(self):
        with _repo_no_remote() as root:
            _git(root, "checkout", "-q", "-b", "release/2.0")
            _git(root, "checkout", "-q", "main")
            _commit_file(root, "src/app.py", "x = 1\n", "app")
            (root / "src/app.py").write_text("x = 2\n")

            with _chdir(root):
                with self.assertRaises(loop.FeatureBranchError) as ctx:
                    loop.ensure_feature_branch({"branch": "feat/x", "base": "release/2.0"})
                exists = subprocess.run(
                    ["git", "rev-parse", "--verify", "feat/x"],
                    capture_output=True, text=True,
                ).returncode == 0

            self.assertFalse(exists)
            self.assertIn("src/app.py", str(ctx.exception))

    # AC 13 — a BaseBranchError raised by ensure_base_ref (declared base does
    # not exist, no origin to check it against) propagates unchanged, not
    # reshaped into a FeatureBranchError.
    def test_base_branch_error_propagates_unwrapped(self):
        with _repo_no_remote() as root:
            with _chdir(root):
                with self.assertRaises(loop.BaseBranchError):
                    loop.ensure_feature_branch({"branch": "feat/x", "base": "nonexistent/base"})
