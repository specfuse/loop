#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0057/T02 — bound T01's captured oracle output for injection.

`specfuse.loop.prerun_capture.format_oracle_capture` turns T01's
`oracle_results` into a session-prompt section whose total size never
exceeds `ORACLE_CAPTURE_BUDGET_BYTES`, reusing
`select_gate_report_lines` (FEAT-2026-0068) so a verdict line survives
truncation instead of a positional tail dropping it.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

load_loop()  # ensures specfuse.loop.loop is importable the same way other tests load it

from specfuse.loop.prerun_capture import (  # noqa: E402  (after sys.path setup above)
    ORACLE_CAPTURE_BUDGET_BYTES,
    format_oracle_capture,
)


class TestCapture(unittest.TestCase):
    def test_verdict_survives_truncation(self):
        noise = "\n".join(f"noise line {i}" for i in range(500))
        report = f"OK\n{noise}"
        results = [{"name": "big_oracle", "ok": True, "report": report}]

        section = format_oracle_capture(results)

        self.assertLessEqual(len(section.encode("utf-8")), ORACLE_CAPTURE_BUDGET_BYTES)
        self.assertIn("OK", section.splitlines())

    def test_budget_enforced_for_many_multiples_of_budget(self):
        huge = "\n".join(f"line {i} " + "x" * 40 for i in range(20000))
        results = [
            {"name": "oracle_a", "ok": False, "report": huge},
            {"name": "oracle_b", "ok": False, "report": huge},
            {"name": "oracle_c", "ok": False, "report": huge},
        ]

        section = format_oracle_capture(results)

        self.assertLessEqual(len(section.encode("utf-8")), ORACLE_CAPTURE_BUDGET_BYTES)

    def test_truncation_marker_names_dropped_bytes(self):
        huge = "\n".join(f"line {i} " + "x" * 40 for i in range(20000))
        results = [{"name": "oracle_a", "ok": False, "report": huge}]

        section = format_oracle_capture(results)

        self.assertIn("byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES", section)

    def test_no_oracles_yields_no_section_and_no_marker(self):
        self.assertEqual(format_oracle_capture([]), "")
        self.assertEqual(format_oracle_capture(None), "")

    def test_small_report_is_not_truncated_and_carries_no_marker(self):
        results = [{"name": "small_oracle", "ok": True, "report": "OK\nRan 1 test\n"}]

        section = format_oracle_capture(results)

        self.assertIn("OK", section)
        self.assertNotIn("dropped", section)


if __name__ == "__main__":
    unittest.main()
