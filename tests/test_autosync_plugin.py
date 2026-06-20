# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0027/T04 — auto_sync plugin-config refresh + drift correction.

Tests cover:
  equal version     → refresh_claude_plugin_config called; removed plugin restored
  drifted value     → extraKnownMarketplaces["specfuse"] corrected
  already current   → no write (idempotent / byte-stable)
  dry-run           → computes changes, writes nothing
  opt-outs          → --no-autosync and autosync:false skip refresh entirely
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specfuse.loop.loop import auto_sync
from specfuse.loop.scaffold import (
    _MARKETPLACE_KEY,
    _MARKETPLACE_VALUE,
    _PLUGIN_KEY,
    refresh_claude_plugin_config,
)


def _make_versioned_target(version: str) -> tuple[Path, str]:
    d = tempfile.mkdtemp()
    target = Path(d)
    specfuse = target / ".specfuse"
    specfuse.mkdir()
    (specfuse / "VERSION").write_text(version + "\n", encoding="utf-8")
    return target, d


def _write_settings(target: Path, data: dict) -> Path:
    claude_dir = target / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings = claude_dir / "settings.json"
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return settings


def _read_settings(target: Path) -> dict:
    return json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))


class TestRefreshClaudePluginConfig(unittest.TestCase):
    """Unit tests for scaffold.refresh_claude_plugin_config."""

    def test_restores_removed_plugin(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            _write_settings(target, {"permissions": {"allow": []}})
            changes = refresh_claude_plugin_config(target)
            self.assertIn(f"enabledPlugins.{_PLUGIN_KEY}", changes)
            data = _read_settings(target)
            self.assertTrue(data["enabledPlugins"][_PLUGIN_KEY])

    def test_corrects_drifted_marketplace_value(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            stale = {"source": {"source": "github", "repo": "old/repo"}}
            _write_settings(target, {"extraKnownMarketplaces": {_MARKETPLACE_KEY: stale}})
            changes = refresh_claude_plugin_config(target)
            self.assertIn(f"extraKnownMarketplaces.{_MARKETPLACE_KEY}", changes)
            data = _read_settings(target)
            self.assertEqual(data["extraKnownMarketplaces"][_MARKETPLACE_KEY], _MARKETPLACE_VALUE)

    def test_noop_when_current(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            settings_path = _write_settings(target, {
                "extraKnownMarketplaces": {_MARKETPLACE_KEY: _MARKETPLACE_VALUE},
                "enabledPlugins": {_PLUGIN_KEY: True},
            })
            mtime_before = settings_path.stat().st_mtime
            changes = refresh_claude_plugin_config(target)
            self.assertEqual(changes, [])
            mtime_after = settings_path.stat().st_mtime
            self.assertEqual(mtime_before, mtime_after, "settings.json must not be rewritten when current")

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            settings_path = _write_settings(target, {"permissions": {"allow": []}})
            original = settings_path.read_text(encoding="utf-8")
            changes = refresh_claude_plugin_config(target, dry_run=True)
            self.assertTrue(len(changes) > 0, "should report would-be changes")
            self.assertEqual(
                settings_path.read_text(encoding="utf-8"),
                original,
                "dry_run must not write settings.json",
            )

    def test_preserves_other_settings_keys(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            _write_settings(target, {
                "permissions": {"allow": ["Bash(my-tool:*)"]},
                "theme": "dark",
            })
            refresh_claude_plugin_config(target)
            data = _read_settings(target)
            self.assertEqual(data["permissions"]["allow"], ["Bash(my-tool:*)"])
            self.assertEqual(data["theme"], "dark")

    def test_creates_settings_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / ".claude").mkdir()
            changes = refresh_claude_plugin_config(target)
            self.assertTrue(len(changes) > 0)
            data = _read_settings(target)
            self.assertEqual(data["extraKnownMarketplaces"][_MARKETPLACE_KEY], _MARKETPLACE_VALUE)
            self.assertTrue(data["enabledPlugins"][_PLUGIN_KEY])


class TestAutosyncPlugin(unittest.TestCase):
    """Integration tests: auto_sync wires plugin-config refresh on the right branches."""

    def test_equal_version_refreshes_plugin_config(self):
        """Equal-version branch must call refresh_claude_plugin_config (was a no-op before T04)."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            _write_settings(target, {"permissions": {"allow": []}})
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                auto_sync(target)
            data = _read_settings(target)
            self.assertTrue(
                data.get("enabledPlugins", {}).get(_PLUGIN_KEY),
                "equal-version run must restore missing plugin entry",
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_drifted_marketplace_value_corrected(self):
        """Drifted extraKnownMarketplaces["specfuse"] value must be overwritten (not kept)."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            stale = {"source": {"source": "github", "repo": "old/repo"}}
            _write_settings(target, {"extraKnownMarketplaces": {_MARKETPLACE_KEY: stale}})
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                auto_sync(target)
            data = _read_settings(target)
            self.assertEqual(
                data["extraKnownMarketplaces"][_MARKETPLACE_KEY],
                _MARKETPLACE_VALUE,
                "drifted marketplace value must be corrected to installed _MARKETPLACE_VALUE",
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_equal_version_noop_when_current_no_write(self):
        """Equal-version, already-current config must not rewrite settings.json."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            settings_path = _write_settings(target, {
                "extraKnownMarketplaces": {_MARKETPLACE_KEY: _MARKETPLACE_VALUE},
                "enabledPlugins": {_PLUGIN_KEY: True},
            })
            mtime_before = settings_path.stat().st_mtime
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                auto_sync(target)
            mtime_after = settings_path.stat().st_mtime
            self.assertEqual(mtime_before, mtime_after, "no write when config already current")
        finally:
            shutil.rmtree(tmpdir)

    def test_equal_version_drift_emits_warning(self):
        """Drift correction on equal-version run must print WARNING to stderr."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            _write_settings(target, {"permissions": {"allow": []}})
            import io
            stderr_buf = io.StringIO()
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("sys.stderr", stderr_buf):
                    auto_sync(target)
            output = stderr_buf.getvalue()
            self.assertIn("WARNING", output, "drift correction must produce a WARNING line")
            self.assertIn("drift", output.lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_dry_run_equal_writes_nothing(self):
        """--dry-run on equal-version branch: report would-be changes, write nothing."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            settings_path = _write_settings(target, {"permissions": {"allow": []}})
            original_text = settings_path.read_text(encoding="utf-8")
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                auto_sync(target, dry_run=True)
            self.assertEqual(
                settings_path.read_text(encoding="utf-8"),
                original_text,
                "dry-run must not write settings.json",
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_no_autosync_skips_plugin_refresh(self):
        """--no-autosync must skip refresh_claude_plugin_config entirely."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            _write_settings(target, {"permissions": {"allow": []}})
            with patch("specfuse.loop.loop._scaffold.refresh_claude_plugin_config") as mock_refresh:
                auto_sync(target, no_autosync=True)
            mock_refresh.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_autosync_false_config_skips_plugin_refresh(self):
        """autosync: false in .specfuse/config must skip refresh_claude_plugin_config."""
        target, tmpdir = _make_versioned_target("0.2.0")
        try:
            _write_settings(target, {"permissions": {"allow": []}})
            config_path = target / ".specfuse" / "config"
            config_path.write_text("autosync: false\n", encoding="utf-8")
            with patch("specfuse.loop.loop._scaffold.refresh_claude_plugin_config") as mock_refresh:
                auto_sync(target)
            mock_refresh.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_older_clean_upgrade_refreshes_plugin_config(self):
        """Older + no modified files: plugin config refreshed after upgrade."""
        target, tmpdir = _make_versioned_target("0.1.0")
        try:
            _write_settings(target, {"permissions": {"allow": []}})
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.detect_modified", return_value=[]):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse"):
                        with patch(
                            "specfuse.loop.loop._scaffold.refresh_claude_plugin_config",
                            return_value=[f"enabledPlugins.{_PLUGIN_KEY}"],
                        ) as mock_refresh:
                            auto_sync(target)
            mock_refresh.assert_called_once_with(target)
        finally:
            shutil.rmtree(tmpdir)
