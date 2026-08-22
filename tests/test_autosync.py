# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0027/T02 — auto_sync decision-tree core.

Tests cover each branch of the auto_sync decision tree:
  missing   → scaffold.init called
  older, clean → scaffold.upgrade_specfuse called
  older, modified → partial overlay (user edits preserved, warn emitted)
  equal     → no-op (no writes)
  newer     → warn + refuse (no writes)
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from specfuse.loop import loop
from specfuse.loop.loop import auto_sync


@contextmanager
def _chdir(target: Path):
    """Run with cwd == the target auto_sync is pointed at.

    Without this, these tests point auto_sync at a temp dir while cwd stays in
    the real repository — and auto_sync's persistence step operates on cwd, so
    it committed *this* repo. That produced three real commits before #290
    guarded against it. The guard makes the mismatch harmless; chdir'ing makes
    the tests stop creating it in the first place, which is what a test pointed
    at a temp tree should have done from the start.
    """
    previous = os.getcwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(previous)


class TestAutoSyncCreatesMissing(unittest.TestCase):
    """Missing .specfuse/ → scaffold.init called."""

    def test_autosync_creates_when_missing(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with _chdir(target):
                    auto_sync(target)
            mock_init.assert_called_once_with(target)

    def test_autosync_creates_dry_run_no_write(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with _chdir(target):
                    auto_sync(target, dry_run=True)
            mock_init.assert_not_called()
            self.assertFalse((target / ".specfuse").exists())


class TestAutoSyncRefusesNewer(unittest.TestCase):
    """Newer .specfuse/VERSION → warn + refuse, no upgrade."""

    def _make_target(self, version: str) -> tuple[Path, object]:
        d = tempfile.mkdtemp()
        target = Path(d)
        specfuse = target / ".specfuse"
        specfuse.mkdir()
        (specfuse / "VERSION").write_text(version + "\n", encoding="utf-8")
        return target, d

    def test_autosync_refuses_newer(self):
        target, tmpdir = self._make_target("99.0.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                        with _chdir(target):
                            # Raises since #2643; the guarantees this test
                            # owns — no downgrade, no re-init — are unchanged.
                            with self.assertRaises(loop.ScaffoldVersionSkew):
                                auto_sync(target)
            mock_upgrade.assert_not_called()
            mock_init.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_autosync_refuses_newer_emits_warning(self):
        target, tmpdir = self._make_target("99.0.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with _chdir(target):
                    with self.assertRaises(loop.ScaffoldVersionSkew) as ctx:
                        auto_sync(target)
            # The guarantee is that the operator is TOLD which version is
            # ahead. Since #2643 that travels on the exception rather than
            # stderr, because the run now stops on it.
            self.assertIn("99.0.0", str(ctx.exception))
        finally:
            shutil.rmtree(tmpdir)


class TestAutoSyncOlderClean(unittest.TestCase):
    """Older VERSION, no modified files → upgrade_specfuse called."""

    def _make_target(self, version: str) -> tuple[Path, str]:
        d = tempfile.mkdtemp()
        target = Path(d)
        specfuse = target / ".specfuse"
        specfuse.mkdir()
        (specfuse / "VERSION").write_text(version + "\n", encoding="utf-8")
        return target, d

    def test_autosync_upgrades_older_clean(self):
        target, tmpdir = self._make_target("0.1.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.detect_modified", return_value=[]):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        with _chdir(target):
                            auto_sync(target)
            mock_upgrade.assert_called_once_with(target)
        finally:
            shutil.rmtree(tmpdir)

    def test_autosync_dry_run_no_write_on_older_clean(self):
        target, tmpdir = self._make_target("0.1.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.detect_modified", return_value=[]):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        with _chdir(target):
                            auto_sync(target, dry_run=True)
            mock_upgrade.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)


class TestAutoSyncOlderModified(unittest.TestCase):
    """Older VERSION, modified files → partial overlay; user edits preserved."""

    def test_autosync_preserves_modified_files(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            # Simulate a modified versioned file.
            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            modified_file = rules_dir / "result-contract.md"
            user_content = b"# user's custom content - must survive"
            modified_file.write_bytes(user_content)

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/result-contract.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse"):
                        # Force the non-interactive (skip+warn) branch — this test
                        # asserts modified files are preserved, NOT the TTY prompt
                        # (covered in test_autosync_consent.py). Without pinning
                        # isatty, a TTY-attached gate runner hits real input() and hangs.
                        with patch("sys.stdin.isatty", return_value=False):
                            with _chdir(target):
                                auto_sync(target)

            self.assertEqual(modified_file.read_bytes(), user_content)

    def test_autosync_partial_dry_run_no_upgrade(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/result-contract.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        with patch("sys.stdin.isatty", return_value=False):
                            with _chdir(target):
                                auto_sync(target, dry_run=True)

            mock_upgrade.assert_not_called()


class TestAutoSyncEqual(unittest.TestCase):
    """Equal VERSION → no-op (no scaffold calls)."""

    def test_autosync_noop_on_equal(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.2.0\n", encoding="utf-8")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                        with patch("specfuse.loop.loop._scaffold.detect_modified") as mock_detect:
                            with _chdir(target):
                                auto_sync(target)

            mock_upgrade.assert_not_called()
            mock_init.assert_not_called()
            mock_detect.assert_not_called()

    def test_autosync_noop_dry_run_on_equal(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.2.0\n", encoding="utf-8")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                        with _chdir(target):
                            auto_sync(target, dry_run=True)

            mock_upgrade.assert_not_called()
            mock_init.assert_not_called()


if __name__ == "__main__":
    unittest.main()
