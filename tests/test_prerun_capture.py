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

from specfuse.loop.loop import select_gate_report_lines  # noqa: E402
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

    def test_complete_capture_carries_no_verdict_banner(self):
        # An informational oracle (e.g. `git log --oneline -20`) has no
        # pass/fail summary and never will. Even when its capture must be
        # truncated to fit the budget, it must not be told it has "NO
        # VERDICT FOUND" — that claim is false for a complete, non-failure
        # capture — and must never be instructed to re-run the command
        # itself, which this feature exists to eliminate.
        log_lines = "\n".join(f"abc{i:04d} commit message {i} " + "x" * 40 for i in range(300))
        results = [{"name": "git_log", "ok": True, "report": log_lines}]

        section = format_oracle_capture(results)

        self.assertNotIn("NO VERDICT FOUND", section)
        self.assertNotIn("Run the command directly.", section)
        self.assertIn("[", section)  # dropped-bytes marker still present
        self.assertIn("byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES", section)


def _gate_set_shaped_report(name: str, command: str, output: str) -> str:
    """Build a report exactly as `_run_gate_set` composes one (`loop.py:2883`).

    This is the ONLY report shape the production path ever hands
    `format_oracle_capture`: a `### <name>: <verdict>` line, then a fenced block
    whose body is `select_gate_report_lines` output. Crucially, that selector has
    already appended its no-verdict banner by the time the report exists — which
    is why a fixture built from a raw command output (as
    `test_complete_capture_carries_no_verdict_banner` does) cannot exercise
    issue #756, and did not.
    """
    tail = select_gate_report_lines(output, window=15)
    return f"### {name}: PASS\n```\n$ {command}\n" + "\n".join(tail) + "\n```"


class TestGateSetShapedCapture(unittest.TestCase):
    """Issue #756 — the banner is embedded upstream, so it must be stripped
    regardless of whether the report is over or under its budget share."""

    def test_fixture_actually_carries_the_banner(self):
        # Guard: if select_gate_report_lines ever stops appending the banner for
        # verdict-less output, the two tests below would pass vacuously and stop
        # protecting anything. This asserts they are still exercising the defect.
        report = _gate_set_shaped_report(
            "recent-commits", "git log --oneline -20",
            "\n".join(f"abc{i:04d} commit subject {i}" for i in range(20)),
        )
        self.assertIn("NO VERDICT FOUND", report)
        self.assertIn("Run the command directly.", report)

    def test_under_budget_report_is_stripped(self):
        # The production case: both of this repo's declared oracles fit their
        # share comfortably, so they take _fit_to_budget's early return. Before
        # #756 that path returned the report untouched, banner included.
        report = _gate_set_shaped_report(
            "recent-commits", "git log --oneline -20",
            "\n".join(f"abc{i:04d} commit subject {i}" for i in range(20)),
        )
        self.assertLessEqual(len(report.encode("utf-8")), ORACLE_CAPTURE_BUDGET_BYTES)

        section = format_oracle_capture([{"name": "recent-commits", "ok": True,
                                          "report": report}])

        self.assertNotIn("NO VERDICT FOUND", section)
        self.assertNotIn("Run the command directly.", section)
        self.assertIn("abc0019 commit subject 19", section)  # content preserved
        self.assertNotIn("byte(s) dropped", section)  # nothing was truncated

    def test_over_budget_report_is_stripped_and_still_marks_dropped_bytes(self):
        # Long lines, not many lines: select_gate_report_lines caps the tail at a
        # 15-line window, so line COUNT cannot push a gate-set-shaped report over
        # budget — line LENGTH is the only way there. A scenario matrix emitting
        # long absolute paths is the realistic case.
        report = _gate_set_shaped_report(
            "big-oracle", "some-command",
            "\n".join(f"line {i} " + "y" * 1000 for i in range(400)),
        )
        self.assertGreater(len(report.encode("utf-8")), ORACLE_CAPTURE_BUDGET_BYTES)

        section = format_oracle_capture([{"name": "big-oracle", "ok": True,
                                          "report": report}])

        self.assertNotIn("NO VERDICT FOUND", section)
        self.assertNotIn("Run the command directly.", section)
        self.assertIn("byte(s) dropped by ORACLE_CAPTURE_BUDGET_BYTES", section)
        self.assertLessEqual(len(section.encode("utf-8")), ORACLE_CAPTURE_BUDGET_BYTES)


if __name__ == "__main__":
    unittest.main()
