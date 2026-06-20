# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0027/T05 — scaffold.doctor read-only self-provisioning diagnosis.

Tests cover:
  project_behind   → scaffold_status + upgrade recommendation
  project_ahead    → scaffold_status + driver-upgrade recommendation
  current          → scaffold_status current, no action
  no_scaffold      → absent .specfuse/VERSION
  plugin drift     → dry-run refresh detects changes
  no drift         → empty plugin_config_drift
  manifest absent  → installed_plugin_version None, partial-diagnosis note
  manifest present → installed_plugin_version read from synthetic fixture
  manifest invalid → graceful degradation to None
  no writes        → doctor makes zero filesystem mutations
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specfuse.loop.scaffold import (
    _MARKETPLACE_KEY,
    _MARKETPLACE_VALUE,
    _PLUGIN_KEY,
    doctor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_target(version: str | None = None) -> tuple[Path, str]:
    d = tempfile.mkdtemp()
    target = Path(d)
    if version is not None:
        specfuse = target / ".specfuse"
        specfuse.mkdir()
        (specfuse / "VERSION").write_text(version + "\n", encoding="utf-8")
    return target, d


def _write_settings(target: Path, data: dict) -> Path:
    claude_dir = target / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return settings_path


def _synthetic_manifest(version: str = "deadbeef0000") -> str:
    """Return JSON for a synthetic installed_plugins.json with fake values."""
    return json.dumps({"plugins": {_PLUGIN_KEY: [{"version": version}]}})


_NONEXISTENT = "/nonexistent/installed_plugins.json"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDoctor(unittest.TestCase):
    """Unit tests for scaffold.doctor."""

    # --- scaffold_status branches ---

    def test_reports_scaffold_version_drift(self):
        """project_behind when project VERSION < installed scaffold version."""
        target, tmpdir = _make_target("0.1.0")
        try:
            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                result = doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=_NONEXISTENT,
                )
            self.assertEqual(result["scaffold_status"], "project_behind")
            self.assertEqual(result["scaffold_version"], "0.1.0")
            self.assertEqual(result["installed_scaffold_version"], "0.2.0")
            self.assertIn("upgrade", result["recommended_action"].lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_scaffold_status_project_ahead(self):
        """project_ahead when project VERSION > installed scaffold version."""
        target, tmpdir = _make_target("0.3.0")
        try:
            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                result = doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=_NONEXISTENT,
                )
            self.assertEqual(result["scaffold_status"], "project_ahead")
            self.assertIn("driver", result["recommended_action"].lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_scaffold_status_current(self):
        """current when project VERSION == installed scaffold version."""
        target, tmpdir = _make_target("0.2.0")
        try:
            _write_settings(target, {
                "extraKnownMarketplaces": {_MARKETPLACE_KEY: _MARKETPLACE_VALUE},
                "enabledPlugins": {_PLUGIN_KEY: True},
            })
            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                result = doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=_NONEXISTENT,
                )
            self.assertEqual(result["scaffold_status"], "current")
            self.assertEqual(result["installed_scaffold_version"], "0.2.0")
        finally:
            shutil.rmtree(tmpdir)

    def test_scaffold_status_no_scaffold(self):
        """no_scaffold when .specfuse/VERSION is absent."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            result = doctor(
                target,
                installed_driver_version="0.2.0",
                plugins_manifest_path=_NONEXISTENT,
            )
        self.assertEqual(result["scaffold_status"], "no_scaffold")
        self.assertIsNone(result["scaffold_version"])
        self.assertIn("init", result["recommended_action"].lower())

    # --- plugin_config_drift ---

    def test_plugin_config_drift_present(self):
        """Non-empty drift list when settings.json is missing plugin config."""
        target, tmpdir = _make_target("0.2.0")
        try:
            _write_settings(target, {"permissions": {"allow": []}})
            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                result = doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=_NONEXISTENT,
                )
            self.assertGreater(len(result["plugin_config_drift"]), 0)
            self.assertIn("drift", result["recommended_action"].lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_plugin_config_drift_absent(self):
        """Empty drift list when settings.json already has correct plugin config."""
        target, tmpdir = _make_target("0.2.0")
        try:
            _write_settings(target, {
                "extraKnownMarketplaces": {_MARKETPLACE_KEY: _MARKETPLACE_VALUE},
                "enabledPlugins": {_PLUGIN_KEY: True},
            })
            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                result = doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=_NONEXISTENT,
                )
            self.assertEqual(result["plugin_config_drift"], [])
        finally:
            shutil.rmtree(tmpdir)

    # --- cross-process manifest ---

    def test_manifest_absent_degrades_gracefully(self):
        """installed_plugin_version is None when manifest path does not exist."""
        with tempfile.TemporaryDirectory() as d:
            result = doctor(
                Path(d),
                installed_driver_version="0.2.0",
                plugins_manifest_path=_NONEXISTENT,
            )
        self.assertIsNone(result["installed_plugin_version"])
        self.assertIn("skipped", result["recommended_action"].lower())

    def test_manifest_present_reads_plugin_version(self):
        """installed_plugin_version is read from a synthetic fixture manifest."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            manifest_path = target / "installed_plugins.json"
            manifest_path.write_text(_synthetic_manifest("deadbeef0000"), encoding="utf-8")
            result = doctor(
                target,
                installed_driver_version="0.2.0",
                plugins_manifest_path=manifest_path,
            )
        self.assertEqual(result["installed_plugin_version"], "deadbeef0000")

    def test_manifest_unparseable_degrades_gracefully(self):
        """installed_plugin_version is None when manifest is invalid JSON."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            manifest_path = target / "installed_plugins.json"
            manifest_path.write_text("not-valid-json{{", encoding="utf-8")
            result = doctor(
                target,
                installed_driver_version="0.2.0",
                plugins_manifest_path=manifest_path,
            )
        self.assertIsNone(result["installed_plugin_version"])

    # --- no writes ---

    def test_doctor_writes_nothing(self):
        """doctor must perform zero filesystem mutations."""
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            specfuse = target / ".specfuse"
            specfuse.mkdir()
            (specfuse / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            claude_dir = target / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            settings_path.write_text(
                json.dumps({"permissions": {"allow": []}}) + "\n",
                encoding="utf-8",
            )
            mtime_before = settings_path.stat().st_mtime
            files_before = {str(p) for p in target.rglob("*")}

            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=_NONEXISTENT,
                )

            files_after = {str(p) for p in target.rglob("*")}
            mtime_after = settings_path.stat().st_mtime
            self.assertEqual(files_before, files_after, "doctor must not create new files")
            self.assertEqual(mtime_before, mtime_after, "doctor must not write settings.json")

    # --- fully current → no action ---

    def test_fully_current_recommends_no_action(self):
        """Fully current repo (scaffold current, no drift, manifest readable) → no action."""
        target, tmpdir = _make_target("0.2.0")
        try:
            _write_settings(target, {
                "extraKnownMarketplaces": {_MARKETPLACE_KEY: _MARKETPLACE_VALUE},
                "enabledPlugins": {_PLUGIN_KEY: True},
            })
            manifest_path = Path(tmpdir) / "installed_plugins.json"
            manifest_path.write_text(_synthetic_manifest("deadbeef0000"), encoding="utf-8")
            with patch("specfuse.loop.scaffold.scaffold_version", return_value="0.2.0"):
                result = doctor(
                    target,
                    installed_driver_version="0.2.0",
                    plugins_manifest_path=manifest_path,
                )
            self.assertIn("no action", result["recommended_action"].lower())
            self.assertEqual(result["scaffold_status"], "current")
            self.assertEqual(result["plugin_config_drift"], [])
            self.assertEqual(result["installed_plugin_version"], "deadbeef0000")
        finally:
            shutil.rmtree(tmpdir)
