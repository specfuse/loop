# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0027/T03 — auto_sync consent layer.

Tests cover:
  TTY + modified → user prompted (overwrite/keep, per-file or all/keep-all)
  No-TTY + modified → skip+warn (T02 default, never blocks)
  --no-autosync flag / no_autosync=True → entire auto-sync skipped
  .specfuse/config autosync: false → entire auto-sync skipped
  Absent config → auto-sync on (default)
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specfuse.loop.loop import auto_sync


# ---------------------------------------------------------------------------
# Red tests (AC1): these two must fail on HEAD, pass after T03 lands.
# ---------------------------------------------------------------------------


class TestAutoSyncRedTests(unittest.TestCase):
    """The two gate-1 red tests that mark the T03 boundary."""

    def test_modified_prompts_on_tty(self):
        """input() is called for a modified file when stdin is a TTY (AC2)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            modified_file = rules_dir / "result-contract.md"
            modified_file.write_bytes(b"# user content")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/result-contract.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse"):
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="N") as mock_input:
                                auto_sync(target)

            mock_input.assert_called()

    def test_no_autosync_flag_skips(self):
        """auto_sync(no_autosync=True) performs no scaffold writes (AC4)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            # No .specfuse/ — would normally trigger scaffold.init.

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    auto_sync(target, no_autosync=True)

            mock_init.assert_not_called()
            mock_upgrade.assert_not_called()


# ---------------------------------------------------------------------------
# TTY consent branch (AC2)
# ---------------------------------------------------------------------------


class TestAutoSyncTTYConsent(unittest.TestCase):
    """TTY present + modified files → user is prompted per-file."""

    def test_tty_yes_overlays_file(self):
        """User answers 'y' → upgrade_specfuse called; file not in saved set."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            (rules_dir / "result-contract.md").write_bytes(b"# user content")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/result-contract.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="y"):
                                auto_sync(target)

            mock_upgrade.assert_called_once()

    def test_tty_no_preserves_file(self):
        """User answers 'N' (default keep) → file content is restored after upgrade."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            modified_file = rules_dir / "result-contract.md"
            user_content = b"# user's custom content"
            modified_file.write_bytes(user_content)

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/result-contract.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse"):
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="N"):
                                auto_sync(target)

            self.assertEqual(modified_file.read_bytes(), user_content)

    def test_tty_all_overlays_without_further_prompts(self):
        """'all' on first file → second file not prompted; both overlaid."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            (rules_dir / "a.md").write_bytes(b"a")
            (rules_dir / "b.md").write_bytes(b"b")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/a.md", "rules/b.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="all") as mock_input:
                                auto_sync(target)

            self.assertEqual(mock_input.call_count, 1)
            mock_upgrade.assert_called_once()

    def test_tty_keep_all_preserves_without_further_prompts(self):
        """'keep-all' on first file → remaining not prompted; all preserved."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            a_content = b"user content a"
            b_content = b"user content b"
            (rules_dir / "a.md").write_bytes(a_content)
            (rules_dir / "b.md").write_bytes(b_content)

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/a.md", "rules/b.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse"):
                        with patch("sys.stdin.isatty", return_value=True):
                            with patch("builtins.input", return_value="keep-all") as mock_input:
                                auto_sync(target)

            self.assertEqual(mock_input.call_count, 1)
            self.assertEqual((rules_dir / "a.md").read_bytes(), a_content)
            self.assertEqual((rules_dir / "b.md").read_bytes(), b_content)


# ---------------------------------------------------------------------------
# No-TTY default preserved (AC3)
# ---------------------------------------------------------------------------


class TestAutoSyncNoTTYDefault(unittest.TestCase):
    """No TTY → T02 behavior: skip+warn, no blocking on input()."""

    def test_no_tty_never_prompts(self):
        """input() is never called when stdin is not a TTY."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            rules_dir = specfuse / "rules"
            rules_dir.mkdir()
            (rules_dir / "result-contract.md").write_bytes(b"# user content")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch(
                    "specfuse.loop.loop._scaffold.detect_modified",
                    return_value=["rules/result-contract.md"],
                ):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse"):
                        with patch("sys.stdin.isatty", return_value=False):
                            with patch("builtins.input") as mock_input:
                                auto_sync(target)

            mock_input.assert_not_called()


# ---------------------------------------------------------------------------
# --no-autosync flag (AC4)
# ---------------------------------------------------------------------------


class TestAutoSyncNoAutosyncFlag(unittest.TestCase):
    """no_autosync=True → all scaffold writes skipped."""

    def test_no_autosync_flag_skips_when_older(self):
        """no_autosync=True skips upgrade even when scaffold is older."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    auto_sync(target, no_autosync=True)

            mock_upgrade.assert_not_called()


# ---------------------------------------------------------------------------
# .specfuse/config toggle (AC5)
# ---------------------------------------------------------------------------


class TestAutoSyncConfigToggle(unittest.TestCase):
    """.specfuse/config autosync: false → auto-sync disabled."""

    def test_config_autosync_false_skips(self):
        """autosync: false in .specfuse/config disables all scaffold writes."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "config").write_text("autosync: false\n", encoding="utf-8")

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    auto_sync(target)

            mock_init.assert_not_called()
            mock_upgrade.assert_not_called()

    def test_config_absent_enables_autosync(self):
        """Absent .specfuse/config → auto-sync on (default)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            # No .specfuse/ → scaffold.init should be called.

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                auto_sync(target)

            mock_init.assert_called_once_with(target)

    def test_config_autosync_true_enables_autosync(self):
        """autosync: true in config → auto-sync proceeds (upgrade runs)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.1.0\n", encoding="utf-8")
            (specfuse / "config").write_text("autosync: true\n", encoding="utf-8")

            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.detect_modified", return_value=[]):
                    with patch(
                        "specfuse.loop.loop._scaffold.upgrade_specfuse"
                    ) as mock_upgrade:
                        auto_sync(target)

            mock_upgrade.assert_called_once_with(target)


if __name__ == "__main__":
    unittest.main()
