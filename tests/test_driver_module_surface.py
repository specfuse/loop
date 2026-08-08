#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests narrowing driver-staleness detection to the importable surface
(FEAT-2026-0075/T04).

`is_driver_module_path` must exclude paths under `specfuse/loop/data/` — those
are not cached in `sys.modules`, so editing them costs a running loop nothing.
"""

from __future__ import annotations

import unittest

from specfuse.loop.driver_edit import (
    DRIVER_DATA_PREFIXES,
    diff_edits_driver,
    driver_paths_in,
    is_driver_module_path,
)


class TestDataPathIsNotADriverModule(unittest.TestCase):
    def test_data_path_is_not_a_driver_module(self):
        self.assertFalse(
            diff_edits_driver(
                ["specfuse/loop/data/schemas/driver-event.schema.json"]
            )
        )


class TestIsDriverModulePathPositive(unittest.TestCase):
    def test_loop_py(self):
        self.assertTrue(is_driver_module_path("specfuse/loop/loop.py"))

    def test_driver_edit_py(self):
        self.assertTrue(is_driver_module_path("specfuse/loop/driver_edit.py"))

    def test_arm_eval_py(self):
        self.assertTrue(is_driver_module_path("specfuse/loop/arm_eval.py"))


class TestIsDriverModulePathNegative(unittest.TestCase):
    def test_schema_json(self):
        self.assertFalse(
            is_driver_module_path(
                "specfuse/loop/data/schemas/driver-event.schema.json"
            )
        )

    def test_methodology_md(self):
        self.assertFalse(
            is_driver_module_path("specfuse/loop/data/docs/methodology.md")
        )

    def test_wu_template_md(self):
        self.assertFalse(
            is_driver_module_path("specfuse/loop/data/templates/WU.template.md")
        )

    def test_monitoring_yml_example(self):
        self.assertFalse(
            is_driver_module_path("specfuse/loop/data/monitoring.yml.example")
        )

    def test_hypothetical_scaffold_payload_py_under_data(self):
        self.assertFalse(
            is_driver_module_path("specfuse/loop/data/scaffold_payload.py")
        )


class TestDriverDataPrefixes(unittest.TestCase):
    def test_contains_data_prefix(self):
        self.assertIn("specfuse/loop/data/", DRIVER_DATA_PREFIXES)


class TestDelegation(unittest.TestCase):
    def test_diff_edits_driver_excludes_data(self):
        self.assertFalse(
            diff_edits_driver(["specfuse/loop/data/docs/methodology.md"])
        )

    def test_driver_paths_in_excludes_data(self):
        self.assertEqual(
            driver_paths_in(
                [
                    "specfuse/loop/loop.py",
                    "specfuse/loop/data/docs/methodology.md",
                ]
            ),
            ["specfuse/loop/loop.py"],
        )


if __name__ == "__main__":
    unittest.main()
