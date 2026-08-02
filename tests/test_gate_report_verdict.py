#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""select_gate_report_lines — a gate's FAIL report must contain the failure.

FEAT-2026-0068. `_run_gate_set` showed the agent the last 15 lines of a gate
command's output. For this repo's `tests`/`coverage` gates that window reliably
contains no verdict: `unittest` writes its summary to unbuffered stderr while
the integration suites' driver output goes to block-buffered stdout, which
flushes afterwards and displaces it.

Cost of the defect, FEAT-2026-0060/T01: two attempts, 1350s, $5.31, escalated
`spinning_signature_repeat`, no artifact and no diagnosis — both attempts saw
the same uninformative tail, which is *why* their signatures matched.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()


# A faithful reduction of the real failure: a unittest verdict, then a large
# block of a fixture feature's driver output flushed after it.
_NOISE = "\n".join(
    f"[18:29:19] -- FEAT-2026-9301/G1-DOCS [docs] model=haiku effort=low\n"
    f"   PASS — committed {i:040d}"
    for i in range(12)
)


class TestVerdictOutsideWindow(unittest.TestCase):
    """The verdict must survive even when later output displaces it."""

    def test_failed_verdict_outside_window_is_pinned_into_report(self):
        out = "Ran 2007 tests in 81.016s\nFAILED (errors=3)\n" + _NOISE
        lines = loop.select_gate_report_lines(out, window=15)
        joined = "\n".join(lines)
        self.assertIn("FAILED (errors=3)", joined,
                      "the verdict must appear in the report even when the "
                      "positional tail does not contain it")
        self.assertIn("Ran 2007 tests", joined)

    def test_ok_verdict_outside_window_is_pinned_into_report(self):
        out = "Ran 2007 tests in 81.016s\nOK (skipped=3)\n" + _NOISE
        lines = loop.select_gate_report_lines(out, window=15)
        self.assertIn("OK (skipped=3)", "\n".join(lines))

    def test_tail_is_still_present_alongside_the_pinned_verdict(self):
        """Pinning the verdict must not discard the trailing context."""
        out = "FAILED (errors=1)\n" + _NOISE
        lines = loop.select_gate_report_lines(out, window=15)
        joined = "\n".join(lines)
        self.assertIn("FAILED (errors=1)", joined)
        self.assertIn(out.strip().splitlines()[-1], joined,
                      "the last line of output must still be shown")

    def test_elision_is_marked_not_silent(self):
        out = "FAILED (errors=1)\n" + _NOISE
        lines = loop.select_gate_report_lines(out, window=15)
        self.assertTrue(
            any("elided" in ln for ln in lines),
            "dropping lines between the pinned verdict and the tail must be "
            "visible, not silent",
        )


class TestVerdictInsideWindow(unittest.TestCase):
    """Short output must be returned unchanged — no pinning, no elision."""

    def test_short_output_returned_as_is(self):
        out = "Ran 3 tests in 0.1s\nOK"
        self.assertEqual(loop.select_gate_report_lines(out, window=15),
                         ["Ran 3 tests in 0.1s", "OK"])

    def test_no_elision_marker_when_nothing_elided(self):
        out = "Ran 3 tests in 0.1s\nOK"
        lines = loop.select_gate_report_lines(out, window=15)
        self.assertFalse(any("elided" in ln for ln in lines))


class TestNoVerdictFound(unittest.TestCase):
    """A report with no recognisable verdict must say so, not disguise it."""

    def test_absent_verdict_is_named(self):
        lines = loop.select_gate_report_lines(_NOISE, window=15)
        self.assertTrue(
            any("NO VERDICT" in ln for ln in lines),
            "when no verdict can be found anywhere, the report must say so — "
            "silently showing unrelated trailing output is the defect",
        )

    def test_absent_verdict_still_shows_the_tail(self):
        lines = loop.select_gate_report_lines(_NOISE, window=15)
        self.assertIn(_NOISE.strip().splitlines()[-1], "\n".join(lines))


class TestEdgeCases(unittest.TestCase):

    def test_empty_output(self):
        self.assertEqual(loop.select_gate_report_lines("", window=15), [])
        self.assertEqual(loop.select_gate_report_lines(None, window=15), [])

    def test_whitespace_only_output(self):
        self.assertEqual(loop.select_gate_report_lines("   \n\n  ", window=15), [])

    def test_window_is_respected_for_the_tail_portion(self):
        out = "\n".join(f"line{i}" for i in range(100))
        lines = loop.select_gate_report_lines(out, window=5)
        # No verdict anywhere, so: 5 tail lines + the NO VERDICT note.
        self.assertIn("line99", lines)
        self.assertNotIn("line50", lines)

    def test_recognises_pytest_and_coverage_verdicts(self):
        for verdict in ("3 failed, 2 passed in 1.2s",
                        "TOTAL                     6155    395    94%",
                        "ERROR: something broke",
                        "AssertionError: nope"):
            with self.subTest(verdict=verdict):
                out = verdict + "\n" + _NOISE
                self.assertIn(
                    verdict,
                    "\n".join(loop.select_gate_report_lines(out, window=15)),
                )


if __name__ == "__main__":
    unittest.main()
