#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""resolve_base / ensure_base_ref / BaseBranchError (FEAT-2026-0031/T01).

resolve_base turns PLAN.md frontmatter's optional `base` key into a usable git
ref name; ensure_base_ref makes that ref locally resolvable, fetching from
origin only when needed. These tests use real git in a tmpdir with a local
bare repo as `origin` — no network, no mocking of git itself.
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


@contextmanager
def _repo_with_origin():
    """A temp repo on `main`, with a local bare repo cloned in as `origin`."""
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        bare = tmp_path / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)

        root = tmp_path / "work"
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        _git(root, "config", "user.email", "test@example.com")
        _git(root, "config", "user.name", "Test")
        _git(root, "config", "commit.gpgSign", "false")
        (root / "README.md").write_text("# fixture\n")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        _git(root, "remote", "add", "origin", str(bare))
        _git(root, "push", "-q", "origin", "main")
        yield root


def _commit_file(root: Path, rel: str, content: str, msg: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    _git(root, "add", rel)
    _git(root, "commit", "-q", "-m", msg)


class TestResolveBase(unittest.TestCase):
    def test_frontmatter_base_wins_over_default(self):
        with _repo_no_remote() as root:
            with _chdir(root):
                result = loop.resolve_base({"base": "release/9.9"})
            self.assertEqual(result, "release/9.9")

    def test_absent_base_falls_back_to_default_branch(self):
        with _repo_no_remote() as root:
            with _chdir(root):
                result = loop.resolve_base({})
            self.assertEqual(result, "main")

    def test_empty_or_whitespace_base_falls_back_to_default_branch(self):
        with _repo_no_remote() as root:
            with _chdir(root):
                self.assertEqual(loop.resolve_base({"base": ""}), "main")
                self.assertEqual(loop.resolve_base({"base": "   "}), "main")
                self.assertEqual(loop.resolve_base({"base": None}), "main")

    def test_absent_base_and_no_default_falls_back_to_current_branch(self):
        with _repo_no_remote() as root:
            _git(root, "checkout", "-q", "-b", "feat/orphan")
            with _chdir(root):
                orig = loop._default_branch
                loop._default_branch = lambda: None
                try:
                    result = loop.resolve_base({})
                finally:
                    loop._default_branch = orig
            self.assertEqual(result, "feat/orphan")


class TestEnsureBaseRef(unittest.TestCase):
    def test_symbol_importable(self):
        self.assertTrue(callable(loop.ensure_base_ref))
        self.assertTrue(issubclass(loop.BaseBranchError, Exception))

    # AC 6 — local ref already resolvable: no-op, no network call needed.
    def test_local_ref_present_noop(self):
        with _repo_no_remote() as root:
            _git(root, "branch", "already-here")
            with _chdir(root):
                loop.ensure_base_ref("already-here")  # must not raise

    # AC 7/8 — local ref absent, but present on origin: fetched.
    def test_remote_ref_fetched_when_absent_locally(self):
        with _repo_with_origin() as root:
            # push a second branch to origin that the local clone never tracked
            _git(root, "checkout", "-q", "-b", "release/1.0")
            _commit_file(root, "rel.txt", "1\n", "release commit")
            _git(root, "push", "-q", "origin", "release/1.0")
            _git(root, "checkout", "-q", "main")
            _git(root, "branch", "-D", "release/1.0")

            with _chdir(root):
                local_before = subprocess.run(
                    ["git", "rev-parse", "--verify", "release/1.0"],
                    capture_output=True, text=True,
                ).returncode
                self.assertNotEqual(local_before, 0)
                loop.ensure_base_ref("release/1.0")
                fetched = subprocess.run(
                    ["git", "rev-parse", "--verify", "FETCH_HEAD"],
                    capture_output=True, text=True,
                )
            self.assertEqual(fetched.returncode, 0)

    # AC 9 — remote confirms the ref does not exist: typo error, names candidates.
    def test_remote_confirms_missing_raises_typo_error(self):
        with _repo_with_origin() as root:
            _git(root, "branch", "feat/existing-local")
            with _chdir(root):
                with self.assertRaises(loop.BaseBranchError) as ctx:
                    loop.ensure_base_ref("totally-bogus-ref")
            msg = str(ctx.exception)
            self.assertIn("totally-bogus-ref", msg)
            self.assertIn("feat/existing-local", msg)
            self.assertNotIn("unreachable", msg.lower())

    # AC 10 — remote unreachable (no `origin` configured at all): distinct wording.
    def test_remote_unreachable_raises_distinct_error(self):
        with _repo_no_remote() as root:
            with _chdir(root):
                with self.assertRaises(loop.BaseBranchError) as ctx:
                    loop.ensure_base_ref("some-ref")
            msg = str(ctx.exception).lower()
            self.assertIn("unreachable", msg)
            self.assertNotIn("typo", msg)


if __name__ == "__main__":
    unittest.main()
