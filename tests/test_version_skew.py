#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0019 gate 2 / FEAT-2026-0027 T02 — version-skew contract.

auto_sync() replaces the old fail-loud check_scaffold_version().
Old behavior: sys.exit on missing or older scaffold.
New behavior: self-heal (create or upgrade); refuse only on newer-than-installed.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._loop_loader import load_loop

loop = load_loop()


class TestParseVersion(unittest.TestCase):

    def test_dotted_ints(self):
        self.assertEqual(loop._parse_version("0.2.0"), (0, 2, 0))

    def test_ordering(self):
        self.assertLess(loop._parse_version("0.1.9"), loop._parse_version("0.2.0"))
        self.assertGreater(loop._parse_version("1.0.0"), loop._parse_version("0.9.9"))

    def test_rc_suffix_component_drops_junk(self):
        # `0.3.0rc1` -> (0, 3, 0); the rc suffix in the last component is ignored.
        self.assertEqual(loop._parse_version("0.3.0rc1"), (0, 3, 0))

    def test_missing_components_count_zero(self):
        self.assertEqual(loop._parse_version("1"), (1,))
        self.assertLess(loop._parse_version("1"), loop._parse_version("1.0.1"))


class TestAutoSyncVersionContract(unittest.TestCase):
    """Version-skew contract: auto_sync heals rather than fails loud."""

    def _make_target(self, version: str | None) -> tuple[Path, str]:
        d = tempfile.mkdtemp()
        target = Path(d)
        specfuse = target / ".specfuse"
        specfuse.mkdir()
        if version is not None:
            (specfuse / "VERSION").write_text(version + "\n", encoding="utf-8")
        return target, d

    def test_equal_is_noop(self):
        target, tmpdir = self._make_target("0.2.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    with patch("specfuse.loop.loop._scaffold.init") as mock_init:
                        loop.auto_sync(target)
            mock_upgrade.assert_not_called()
            mock_init.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_older_triggers_upgrade_not_exit(self):
        # Old check_scaffold_version() would sys.exit here; auto_sync upgrades instead.
        target, tmpdir = self._make_target("0.1.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.detect_modified", return_value=[]):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        loop.auto_sync(target)  # must NOT raise SystemExit
            mock_upgrade.assert_called_once_with(target)
        finally:
            shutil.rmtree(tmpdir)

    def test_missing_version_triggers_upgrade_not_exit(self):
        # Old check_scaffold_version() would sys.exit; auto_sync treats as older and upgrades.
        target, tmpdir = self._make_target(None)
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.detect_modified", return_value=[]):
                    with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                        loop.auto_sync(target)  # must NOT raise SystemExit
            mock_upgrade.assert_called_once_with(target)
        finally:
            shutil.rmtree(tmpdir)

    def test_newer_than_installed_refuses_without_exit(self):
        # Target VERSION newer than installed seed: warn + refuse (no sys.exit, no downgrade).
        target, tmpdir = self._make_target("99.0.0")
        try:
            with patch("specfuse.loop.loop._scaffold.scaffold_version", return_value="0.2.0"):
                with patch("specfuse.loop.loop._scaffold.upgrade_specfuse") as mock_upgrade:
                    loop.auto_sync(target)  # must NOT raise SystemExit
            mock_upgrade.assert_not_called()
        finally:
            shutil.rmtree(tmpdir)

    def test_min_matches_driver_default(self):
        # The shipped MIN_SCAFFOLD_VERSION is the floor; this repo's own
        # .specfuse/VERSION must satisfy it (guards against forgetting to bump
        # the stamp when MIN is raised).
        repo_version = (loop.REPO_ROOT / ".specfuse" / "VERSION")
        if repo_version.exists():
            self.assertGreaterEqual(
                loop._parse_version(repo_version.read_text().strip()),
                loop._parse_version(loop.MIN_SCAFFOLD_VERSION),
            )


if __name__ == "__main__":
    unittest.main()
