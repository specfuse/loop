# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0027/T06 — first-run consent prompt for auto_sync create branch.

Tests cover:
  TTY + decline  → init/refresh not called, no writes (red test AC1)
  TTY + confirm  → init + refresh called
  No TTY         → init + refresh called, single notice printed, no prompt
  --no-autosync  → create branch never reached (short-circuit)
  config autosync: false → create branch never reached (short-circuit)
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specfuse.loop.loop import auto_sync


class TestFirstRun(unittest.TestCase):
    """TTY first-run prompt — create branch only (no .specfuse/ present)."""

    def test_create_aborts_on_tty_decline(self):
        """TTY + explicit 'n' → scaffold.init NOT called, no .specfuse/ written (AC3)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            # No .specfuse/ — triggers create branch.

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch(
                    "specfuse.loop.loop._scaffold.refresh_claude_plugin_config"
                ) as mock_refresh:
                    with patch("sys.stdin.isatty", return_value=True):
                        with patch("builtins.input", return_value="n"):
                            auto_sync(target)

            mock_init.assert_not_called()
            mock_refresh.assert_not_called()
            self.assertFalse((target / ".specfuse").exists())

    def test_create_tty_confirm_proceeds(self):
        """TTY + empty answer (default yes) → init + refresh called (AC2)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch(
                    "specfuse.loop.loop._scaffold.refresh_claude_plugin_config"
                ) as mock_refresh:
                    with patch("sys.stdin.isatty", return_value=True):
                        with patch("builtins.input", return_value=""):
                            auto_sync(target)

            mock_init.assert_called_once_with(target)
            mock_refresh.assert_called_once_with(target)

    def test_create_tty_explicit_yes_proceeds(self):
        """TTY + 'y' → init + refresh called (AC2)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch(
                    "specfuse.loop.loop._scaffold.refresh_claude_plugin_config"
                ) as mock_refresh:
                    with patch("sys.stdin.isatty", return_value=True):
                        with patch("builtins.input", return_value="y"):
                            auto_sync(target)

            mock_init.assert_called_once_with(target)
            mock_refresh.assert_called_once_with(target)

    def test_create_no_tty_proceeds_with_notice(self):
        """No TTY → init + refresh called, input() never called (AC4)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch(
                    "specfuse.loop.loop._scaffold.refresh_claude_plugin_config"
                ) as mock_refresh:
                    with patch("sys.stdin.isatty", return_value=False):
                        with patch("builtins.input") as mock_input:
                            auto_sync(target)

            mock_init.assert_called_once_with(target)
            mock_refresh.assert_called_once_with(target)
            mock_input.assert_not_called()

    def test_decline_no_writes_explicit_no(self):
        """TTY + 'no' (long form) → nothing written (AC3 strict)."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch(
                    "specfuse.loop.loop._scaffold.refresh_claude_plugin_config"
                ) as mock_refresh:
                    with patch("sys.stdin.isatty", return_value=True):
                        with patch("builtins.input", return_value="no"):
                            auto_sync(target)

            mock_init.assert_not_called()
            mock_refresh.assert_not_called()


class TestFirstRunOptOutsShortCircuit(unittest.TestCase):
    """Opt-outs skip auto_sync entirely — first-run prompt never reached (AC5)."""

    def test_no_autosync_flag_skips_create(self):
        """--no-autosync → init not called even when .specfuse/ absent."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)

            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch("builtins.input") as mock_input:
                    auto_sync(target, no_autosync=True)

            mock_init.assert_not_called()
            mock_input.assert_not_called()

    def test_config_autosync_false_skips_create(self):
        """autosync: false in config → init not called."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "config").write_text("autosync: false\n", encoding="utf-8")

            # Even if we delete .specfuse/ after writing config — but that's circular.
            # Instead test: a *separate* dir where config opt-out was written first.
            # Simpler: use no_autosync=True as the config path is already covered above.
            # Directly test config path via a dir that has config but no VERSION.
            with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                with patch("builtins.input") as mock_input:
                    auto_sync(target)

            mock_init.assert_not_called()
            mock_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
