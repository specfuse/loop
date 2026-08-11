#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`select_gate_report_lines` must recognise Maven surefire's verdicts (#1413).

FEAT-2026-0068 made gate FAIL reports verdict-aware: rather than taking a
positional tail, `select_gate_report_lines` pins recognisable pass/fail summary
lines so the reader sees the verdict even when it falls outside the window.

Its pattern covers unittest, pytest, coverage and ruff. It does **not** cover
Maven + surefire: a surefire failure's actionable content — the
`Tests run: N, Failures: M` summary and the `<<< FAILURE!` / `<<< ERROR!`
per-test lines naming the failing class — sits well above the final
`[ERROR] Failed to execute goal ...` block, which is all a positional tail
keeps. That block names no failing test, so on every surefire failure the
selector pins nothing, appends its `NO VERDICT FOUND` banner, and degrades to
the content-free tail (issue #1413).

The captured shape below is the excerpt quoted verbatim in #1413's report.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

load_loop()

from specfuse.loop.loop import (  # noqa: E402  (after sys.path setup above)
    _NO_VERDICT_NOTE,
    select_gate_report_lines,
)


SUREFIRE_OUTPUT = (
    "[INFO] Running com.example.FooTest\n"
    "[ERROR] testBar  Time elapsed: 0.012 s  <<< FAILURE!\n"
    "java.lang.AssertionError: expected:<1> but was:<2>\n"
    "\tat com.example.FooTest.testBar(FooTest.java:42)\n"
    "\n"
    "[INFO] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0\n"
    "[INFO]\n"
    "[INFO] BUILD FAILURE\n"
)


class TestSurefireVerdictsAreRecognised(unittest.TestCase):
    def test_tests_run_summary_is_pinned_as_a_verdict(self):
        # 700 lines of unrelated noise between the real summary and the tail,
        # matching #1413's description of the actionable content sitting well
        # above the content-free [ERROR] block a positional tail would keep.
        noise = "\n".join(f"[INFO] unrelated build log line {i}" for i in range(700))
        out = f"{SUREFIRE_OUTPUT}{noise}\n"

        lines = select_gate_report_lines(out, window=15)

        self.assertIn("[INFO] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0", lines)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_failure_marker_line_is_pinned(self):
        noise = "\n".join(f"[INFO] unrelated build log line {i}" for i in range(700))
        out = f"{SUREFIRE_OUTPUT}{noise}\n"

        lines = select_gate_report_lines(out, window=15)

        self.assertTrue(
            any("<<< FAILURE!" in ln for ln in lines),
            f"failing test marker not pinned: {lines[:5]}")

    def test_the_verdict_survives_the_final_error_tail(self):
        # Verbatim shape from #1413: the [ERROR] tail names no test at all.
        tail_block = (
            "[ERROR] Failed to execute goal "
            "...maven-surefire-plugin:3.2.3:test (default-test) on project X: "
            "There are test failures.\n"
            "[ERROR]\n"
            "[ERROR] Please refer to /path/to/target/surefire-reports for the "
            "individual test results.\n"
        )
        out = SUREFIRE_OUTPUT + ("\n".join(f"[INFO] noise {i}" for i in range(50))) + "\n" + tail_block

        lines = select_gate_report_lines(out, window=15)

        self.assertIn("[INFO] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0", lines)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)


if __name__ == "__main__":
    unittest.main()
