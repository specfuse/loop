#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature oracle for FEAT-LOOP-2026-0249 gate 1 — one class per Definition-of-done clause.

Temp git repositories driven through the real writer. Clause 1 and clause 5's
writer half are implemented by T01; the rest are skipped naming their owner.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

from specfuse.loop.changelog import parse_changelog

_SEED = "# Changelog\n\n## [Unreleased]\n\n## [0.1.0+umbrella.0.1.0] - 2026-01-01\n\n### Added\n\n- first (#1)\n"
_GIT = ("git", "-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@example.com")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*_GIT, *args], cwd=repo, capture_output=True, text=True, check=False
    )


def _add(repo: Path, *, trace: str, summary: str, entry_class: str = "added"):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [
            sys.executable, "-m", "specfuse.loop.changelog_fragments",
            "--repo", str(repo), "add",
            "--class", entry_class, "--trace", trace, "--summary", summary,
        ],
        capture_output=True, text=True, env=env, check=False,
    )


def _init_repo(root: Path, mode: str | None) -> None:
    assert _git(root, "init", "-q", "-b", "main").returncode == 0
    (root / "CHANGELOG.md").write_text(_SEED, encoding="utf-8")
    if mode is not None:
        (root / ".specfuse").mkdir()
        (root / ".specfuse" / "layout.yml").write_text(
            f"changelog:\n  mode: {mode}\n", encoding="utf-8"
        )
    _git(root, "add", "-A")
    assert _git(root, "commit", "-q", "-m", "init").returncode == 0


def _two_branch_merge(root: Path, mode: str | None) -> subprocess.CompletedProcess:
    _init_repo(root, mode)
    for name, trace, summary in (("a", "#101", "alpha change"), ("b", "#102", "beta change")):
        assert _git(root, "checkout", "-q", "-b", name, "main").returncode == 0
        done = _add(root, trace=trace, summary=summary)
        assert done.returncode == 0, done.stderr
        _git(root, "add", "-A")
        assert _git(root, "commit", "-q", "-m", name).returncode == 0
    assert _git(root, "checkout", "-q", "main").returncode == 0
    assert _git(root, "merge", "-q", "--no-edit", "a").returncode == 0
    return _git(root, "merge", "--no-edit", "b")


class TestClause1ConcurrentPrsDoNotConflict(unittest.TestCase):
    def test_fragments_mode_second_merge_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            merged = _two_branch_merge(root, "fragments")
            self.assertEqual(merged.returncode, 0, merged.stdout + merged.stderr)
            self.assertEqual(
                sorted(p.name for p in (root / "changelog.d").iterdir()),
                ["101-alpha-change.md", "102-beta-change.md"],
            )

    def test_single_mode_control_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            merged = _two_branch_merge(Path(tmp), "single")
            self.assertNotEqual(merged.returncode, 0, "control: single mode must conflict")

    def test_add_refuses_bad_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root, "fragments")
            self.assertNotEqual(_add(root, trace="#1", summary="x", entry_class="nope").returncode, 0)
            self.assertNotEqual(_add(root, trace="not-a-trace", summary="x").returncode, 0)
            self.assertNotEqual(_add(root, trace="#1", summary="two\nlines").returncode, 0)
            self.assertEqual(_add(root, trace="#1", summary="same").returncode, 0)
            self.assertNotEqual(_add(root, trace="#1", summary="same").returncode, 0)


@unittest.skip("T02 owns clause 2: one reader for close-k, lint --closing and the auto-close guard")
class TestClause2GuardsReadFragments(unittest.TestCase):
    def test_pending(self):
        pass


@unittest.skip("T03 owns clause 3: collation at release")
class TestClause3CollateAtRelease(unittest.TestCase):
    def test_pending(self):
        pass


@unittest.skip("T04 owns clause 4: the check gate")
class TestClause4CheckGate(unittest.TestCase):
    def test_pending(self):
        pass


class TestClause5NoModeKeyBehavesAsBefore(unittest.TestCase):
    def test_add_without_mode_edits_changelog_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_repo(root, None)
            done = _add(root, trace="#7", summary="plain entry")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertFalse((root / "changelog.d").exists())
            result = parse_changelog((root / "CHANGELOG.md").read_text(encoding="utf-8"))
            self.assertTrue(result.ok, result.findings)
            self.assertEqual([e.trace for e in result.unreleased().entries], ["#7"])

    @unittest.skip("T03 owns the release-output half of clause 5")
    def test_release_without_fragments_unchanged(self):
        pass


if __name__ == "__main__":
    unittest.main()
