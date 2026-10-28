#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Narrow selection ignores non-module `produces:` paths (#3539).

With the default `format: python_module`, every `produces:` entry under
`tests/` used to go through `_test_module_name`, which strips `.py` only when
present. A fixture glob (`tests/fixtures/x/**`) or a data file
(`tests/fixtures/x/roadmap.md`) therefore became a module name unittest cannot
import, and the per-attempt tests gate failed identically on every attempt
(FEAT-2026-0224/T04).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

GATE = {
    "name": "tests",
    "command": "FULLCMD",
    "narrow_command": "python3 -m unittest {selected_test_modules} -v -b",
}


def _wu(produces):
    return loop.WorkUnit(
        wu_id="X/T1", file=Path("WU-1.md"), depends_on=[],
        type="implementation", model="m", status="pending", attempts=0,
        title="t", body="", produces=produces,
    )


class NarrowSelectionIgnoresNonModulePaths(unittest.TestCase):
    def test_glob_under_tests_is_not_a_module(self):
        wu = _wu([
            "tests/test_goldens.py",
            "tests/fixtures/layout_goldens/**",
        ])
        self.assertEqual(
            loop.resolve_narrow_command(GATE, wu),
            "python3 -m unittest tests.test_goldens -v -b",
        )

    def test_data_file_under_tests_is_not_a_module(self):
        wu = _wu([
            "tests/fixtures/repo/.specfuse/roadmap.md",
            "tests/test_goldens.py",
        ])
        self.assertEqual(
            loop.resolve_narrow_command(GATE, wu),
            "python3 -m unittest tests.test_goldens -v -b",
        )

    def test_only_non_module_paths_fall_back_to_full_command(self):
        wu = _wu(["tests/fixtures/x/**", "tests/fixtures/x/data.json"])
        self.assertEqual(loop.resolve_narrow_command(GATE, wu), "FULLCMD")

    def test_path_format_still_passes_entries_verbatim(self):
        gate = dict(GATE, narrow_selection={"format": "path"})
        wu = _wu(["tests/fixtures/x/data.json"])
        self.assertIn(
            "tests/fixtures/x/data.json", loop.resolve_narrow_command(gate, wu),
        )


if __name__ == "__main__":
    unittest.main()
