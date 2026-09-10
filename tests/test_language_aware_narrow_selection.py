#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Language-aware narrow selection — FEAT-2026-0110/T01, this gate's
`feature_oracle`.

A `code` gate may declare an optional `narrow_selection` block naming
`test_roots`, `format`, `item_template`, and `separator` — so a unit whose
tests live outside `tests/` (a non-Python project's `src/test/java/`, say)
still resolves to a narrow command instead of falling back to the gate's
full command, which is all a Python-only `tests/`-rooted selector could ever
do. This module asserts the Maven shape end to end, and that a gate
declaring no `narrow_selection` at all is untouched.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


class LanguageAwareNarrowSelectionTests(unittest.TestCase):
    def test_maven_shape_resolves_through_narrow_command(self):
        wu = loop.WorkUnit(
            wu_id="X/T1", file=Path("WU-1.md"), depends_on=[],
            type="implementation", model="m", status="pending", attempts=0,
            title="t", body="",
            produces=[
                "src/test/java/com/acme/FooTest.java",
                "src/test/java/com/acme/BarTest.java",
            ],
        )
        gate = {
            "name": "tests",
            "command": "FULLCMD",
            "narrow_command": "./mvnw test -Dtest={selected_test_modules}",
            "narrow_selection": {
                "test_roots": ["src/test/java/"],
                "format": "class_name",
                "separator": ",",
            },
        }
        command = loop.resolve_narrow_command(gate, wu)
        self.assertEqual(command, "./mvnw test -Dtest=FooTest,BarTest")

    def test_no_narrow_selection_key_is_byte_identical_to_today(self):
        wu = loop.WorkUnit(
            wu_id="X/T2", file=Path("WU-2.md"), depends_on=[],
            type="implementation", model="m", status="pending", attempts=0,
            title="t", body="",
            produces=["tests/test_declared.py"],
        )
        gate = {
            "name": "tests",
            "command": "FULLCMD",
            "narrow_command": "python3 -m unittest {selected_test_modules}",
        }
        command = loop.resolve_narrow_command(gate, wu)
        self.assertEqual(command, "python3 -m unittest tests.test_declared")


if __name__ == "__main__":
    unittest.main()
