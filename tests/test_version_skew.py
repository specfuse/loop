#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0019 gate 2 — driver/scaffold version-skew guard.

The scaffold stamps its own version into `.specfuse/VERSION` (init.sh). The driver
declares MIN_SCAFFOLD_VERSION — the oldest scaffold it can drive — and fails loud at
startup if the consumer's scaffold is missing, empty, or older. Direction: tool
requires a minimum data-format version.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


class TestParseVersion(unittest.TestCase):

    def test_dotted_ints(self):
        self.assertEqual(loop._parse_version("0.2.0"), (0, 2, 0))

    def test_ordering(self):
        self.assertLess(loop._parse_version("0.1.9"), loop._parse_version("0.2.0"))
        self.assertGreater(loop._parse_version("1.0.0"), loop._parse_version("0.9.9"))

    def test_rc_suffix_component_drops_junk(self):
        # `0.3.0rc1` → (0, 3, 0); the rc suffix in the last component is ignored.
        self.assertEqual(loop._parse_version("0.3.0rc1"), (0, 3, 0))

    def test_missing_components_count_zero(self):
        self.assertEqual(loop._parse_version("1"), (1,))
        self.assertLess(loop._parse_version("1"), loop._parse_version("1.0.1"))


class TestCheckScaffoldVersion(unittest.TestCase):

    def _version_file(self, tmp: Path, content: str) -> Path:
        p = tmp / "VERSION"
        p.write_text(content)
        return p

    def test_equal_passes_and_returns_version(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._version_file(Path(d), "0.2.0\n")
            self.assertEqual(loop.check_scaffold_version(p, driver_min="0.2.0"), "0.2.0")

    def test_newer_scaffold_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._version_file(Path(d), "0.3.1\n")
            self.assertEqual(loop.check_scaffold_version(p, driver_min="0.2.0"), "0.3.1")

    def test_older_scaffold_fails_loud(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._version_file(Path(d), "0.1.0\n")
            with self.assertRaises(SystemExit) as cm:
                loop.check_scaffold_version(p, driver_min="0.2.0")
            self.assertIn("older", str(cm.exception))
            self.assertIn("specfuse upgrade", str(cm.exception))

    def test_missing_file_fails_loud(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "VERSION"  # not created
            with self.assertRaises(SystemExit) as cm:
                loop.check_scaffold_version(p, driver_min="0.2.0")
            self.assertIn("missing", str(cm.exception))
            self.assertIn("specfuse upgrade", str(cm.exception))

    def test_empty_file_fails_loud(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._version_file(Path(d), "   \n")
            with self.assertRaises(SystemExit) as cm:
                loop.check_scaffold_version(p, driver_min="0.2.0")
            self.assertIn("empty", str(cm.exception))

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
