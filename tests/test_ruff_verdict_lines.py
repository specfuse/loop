#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`select_gate_report_lines` must recognise ruff's verdicts (#723).

FEAT-2026-0068 made gate FAIL reports verdict-aware: rather than taking a
positional tail, `select_gate_report_lines` pins recognisable pass/fail summary
lines so the reader sees the verdict even when it falls outside the window.

Its pattern covers unittest, pytest and coverage. It does **not** cover `ruff`,
which is the second entry in this repo's own `code` gate set — so for the `lint`
gate the selector pins nothing, appends its `NO VERDICT FOUND` banner, and
degrades to exactly the positional tail FEAT-2026-0068 exists to prevent.

Carried through three consecutive retrospectives of FEAT-2026-0057 unchanged,
each time re-measured against the real captured output of that feature's own
`B905` lint failure.

The two verdict strings asserted here were captured from the installed ruff, not
recalled: a failing run ends `Found N error(s).` and a clean run prints
`All checks passed!`.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

load_loop()

from specfuse.loop.loop import (  # noqa: E402  (after sys.path setup above)
    _NO_VERDICT_NOTE,
    select_gate_report_lines,
)


class TestRuffVerdictsAreRecognised(unittest.TestCase):
    def test_failing_ruff_summary_is_pinned_as_a_verdict(self):
        # Verbatim shape of a real failure: this repo's own T02 attempt-1 B905.
        out = (
            "specfuse/loop/prerun_capture.py:58:9: B905 `zip()` without an "
            "explicit `strict=` parameter\n"
            "Found 1 error.\n"
            "[*] 1 fixable with the `--fix` option.\n"
        )

        lines = select_gate_report_lines(out, window=15)

        self.assertIn("Found 1 error.", lines)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_plural_error_count_is_recognised(self):
        lines = select_gate_report_lines("a.py:1:1: F401 unused\nFound 2 errors.\n", 15)

        self.assertIn("Found 2 errors.", lines)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_all_checks_passed_is_recognised(self):
        lines = select_gate_report_lines("All checks passed!\n", window=15)

        self.assertIn("All checks passed!", lines)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_the_verdict_survives_a_flood_that_pushes_it_out_of_the_window(self):
        # The whole point of FEAT-2026-0068: a verdict at the TOP must survive a
        # window that would otherwise show only unrelated tail noise. Without a
        # ruff pattern the selector pins nothing here and the summary is lost.
        noise = "\n".join(f"src/mod_{i}.py:{i}:1: F401 unused import" for i in range(400))
        out = f"Found 400 errors.\n{noise}\n"

        lines = select_gate_report_lines(out, window=15)

        # The verdict is pinned FIRST, ahead of the tail it would otherwise have
        # been pushed out of.
        self.assertEqual(lines[0], "Found 400 errors.")
        # The drop is stated rather than silent.
        self.assertTrue(
            any("elided" in ln for ln in lines),
            f"no elision marker in {lines[:3]}")
        # And the flood itself is still bounded: verdict + marker + the window,
        # not 400 lines.
        self.assertLess(len(lines), 20)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_a_genuinely_verdictless_output_still_gets_the_banner(self):
        # Guard the other direction: this fix must not make the banner
        # unreachable, or a gate whose oracle really did produce no summary
        # would silently look fine.
        lines = select_gate_report_lines("some unrelated chatter\nand more\n", 15)

        self.assertIn(_NO_VERDICT_NOTE, lines)


if __name__ == "__main__":
    unittest.main()
