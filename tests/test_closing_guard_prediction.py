#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests the arm-time guard-literal prediction (issue #265, driver-side half).

Closing-WU guards inspect artifacts that do not exist until the WU has run, so
the guards themselves cannot move earlier. What can move earlier is the
**prediction**: if a closing WU's body never instructs the agent to produce the
literal its guard will demand, the refusal is foreseeable at arm time, for free.

Measured motivation — 158 closing WUs across 9 repositories, 28% of all
closing-WU spend went to refused attempts. The two refusals in FEAT-2026-0069
are the worked examples, and both are regression-tested below:

    G1-CLOSE-INTERMEDIATE  no `## Gate 1` instruction        $4.45
    G1-PLAN                said GATE-01, guard wanted GATE-02 $8.61

**The backtick scoping is the load-bearing detail.** A bare substring search
matches the WU's own H1 title — `# Gate 1 close-intermediate — …` — and so
would have *passed* the exact WU that went on to be refused. A check with a
false-pass mode is worse than no check, because it converts an unknown into a
false assurance. `test_wu_title_alone_does_not_satisfy_the_check` pins that.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.lint_plan import (
    check_autoclose_debt_prediction,
    check_closing_guard_literals,
)

_FM = """---
id: FEAT-2026-9401/{wid}
type: {wtype}
status: {status}
---

# Gate 1 {wtype} — retrospective and friends

{body}
"""


class _Harness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _wu(self, wid: str, wtype: str, body: str = "", status: str = "pending") -> list:
        (self.dir / "WU.md").write_text(
            _FM.format(wid=wid, wtype=wtype, status=status, body=body)
        )
        return [{"work_units": [{"file": "WU.md"}]}]

    def _run(self, gates) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_closing_guard_literals(self.dir, gates)
        return buf.getvalue()


class TestFiresOnMissingLiterals(_Harness):
    def test_close_intermediate_without_gate_heading_warns(self):
        out = self._run(self._wu("G1-CLOSE-INTERMEDIATE", "close-intermediate",
                                 "RETROSPECTIVE.md exists with per-WU outcomes."))
        self.assertIn("WARN", out)
        self.assertIn("Gate 1", out)
        self.assertIn("assert_retrospective_gate_section", out)

    def test_close_without_cost_analysis_warns(self):
        out = self._run(self._wu("G1-CLOSE", "close", "Write a retrospective."))
        self.assertIn("assert_cost_analysis_section_when_met", out)

    def test_plan_next_naming_the_wrong_gate_review_warns(self):
        """The $8.61 case: the body names the gate being closed, not drafted."""
        out = self._run(self._wu("G1-PLAN", "plan-next",
                                 "Write `GATE-01-REVIEW.md` with the findings."))
        self.assertIn("WARN", out)
        self.assertIn("GATE-02-REVIEW.md", out)


class TestSilentWhenInstructed(_Harness):
    def test_close_intermediate_naming_the_heading_is_silent(self):
        out = self._run(self._wu("G1-CLOSE-INTERMEDIATE", "close-intermediate",
                                 "RETROSPECTIVE.md carries a `## Gate 1` section."))
        self.assertEqual(out, "")

    def test_plan_next_naming_the_right_review_file_is_silent(self):
        out = self._run(self._wu("G1-PLAN", "plan-next",
                                 "Write `GATE-02-REVIEW.md` — named for the gate armed."))
        self.assertEqual(out, "")

    def test_close_naming_cost_analysis_is_silent(self):
        out = self._run(self._wu("G1-CLOSE", "close",
                                 "A `## Cost analysis` section reconciling spend."))
        self.assertEqual(out, "")

    def test_deeper_heading_still_satisfies_the_gate_section(self):
        """The guard accepts `#{1,3} Gate N`; the check must not be stricter."""
        out = self._run(self._wu("G1-CLOSE-INTERMEDIATE", "close-intermediate",
                                 "Add a `### Gate 1` block."))
        self.assertEqual(out, "")


class TestNoFalsePasses(_Harness):
    def test_wu_title_alone_does_not_satisfy_the_check(self):
        """The regression that nearly shipped.

        Every closing WU's H1 is `# Gate N <type> — ...`, which satisfies a bare
        `#{1,3} Gate N` substring search. Scoping to backticks is what makes the
        check mean "the body instructs this" rather than "these characters
        appear somewhere".
        """
        out = self._run(self._wu("G1-CLOSE-INTERMEDIATE", "close-intermediate",
                                 "No instruction about headings here."))
        self.assertIn("WARN", out, "the WU's own H1 title produced a false pass")

    def test_unrelated_backticked_prose_does_not_satisfy_it(self):
        out = self._run(self._wu("G1-PLAN", "plan-next",
                                 "Read `GATE-01.md` and `PLAN.md` first."))
        self.assertIn("WARN", out)


class TestScope(_Harness):
    def test_done_closing_wus_are_skipped(self):
        """Sealed history: backfilling instructions onto a finished WU is noise."""
        out = self._run(self._wu("G1-CLOSE", "close", "no literal", status="done"))
        self.assertEqual(out, "")

    def test_implementation_wus_are_untouched(self):
        out = self._run(self._wu("T01", "implementation", "no literal"))
        self.assertEqual(out, "")

    def test_missing_wu_file_is_not_an_error(self):
        self.assertEqual(self._run([{"work_units": [{"file": "absent.md"}]}]), "")

    def test_gateless_id_is_skipped_rather_than_crashing(self):
        out = self._run(self._wu("T01H", "close", "no literal"))
        self.assertEqual(out, "")


class TestAdvisoryOnly(_Harness):
    def test_check_returns_none_and_raises_nothing(self):
        """WARN-only by contract: 22% of this repo's existing closing WUs would
        fail it, and they are history. An ERROR predicate unsatisfiable on a
        populated tree is `[FEAT-2026-0015/G2-CLOSE]`."""
        self.assertIsNone(check_closing_guard_literals(
            self.dir, self._wu("G1-CLOSE", "close", "nothing")))


class TestAutoCloseDebtPrediction(unittest.TestCase):
    """FEAT-2026-0070/T08: predicts `assert_autoclose_debt_reconciled`
    (FEAT-2026-0070/T07) at arm time. Conditional on feature state — fires
    only when RETROSPECTIVE.md already carries T06's debt marker."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _retro(self, marker_gate: int = 1) -> None:
        (self.dir / "RETROSPECTIVE.md").write_text(
            f"## Gate {marker_gate} auto-closed\n\n"
            f"<!-- specfuse:autoclose-debt gate={marker_gate} wus=T01 "
            "criteria=3 predicate=v1 -->\n"
            "deferred: some criterion\n"
        )

    def _gates(self, close_body: str, status: str = "pending") -> list:
        (self.dir / "CLOSE.md").write_text(
            "---\n"
            "id: FEAT-2026-9402/G2-CLOSE\n"
            "type: close\n"
            f"status: {status}\n"
            "---\n\n"
            "# Gate 2 close — retrospective and friends\n\n"
            f"{close_body}\n"
        )
        return [
            {"gate": 1, "work_units": [{"id": "T01", "file": "T01.md"}]},
            {"gate": 2, "work_units": [{"id": "G2-CLOSE", "file": "CLOSE.md"}]},
        ]

    def _run(self, gates: list) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_autoclose_debt_prediction(self.dir, gates)
        return buf.getvalue()

    def test_warns_when_terminal_close_body_ignores_marked_debt(self):
        self._retro(marker_gate=1)
        gates = self._gates("Write a retrospective with per-WU outcomes.")
        out = self._run(gates)
        self.assertIn("WARN", out)
        self.assertIn("assert_autoclose_debt_reconciled", out)

    def test_silent_when_body_instructs_reconciling_the_marked_gate(self):
        """Positive control: a predictor that warns unconditionally is worse
        than none — it trains the reader to skip the line."""
        self._retro(marker_gate=1)
        gates = self._gates(
            "Name gate 1 in the '## What the loop did NOT verify' section."
        )
        self.assertEqual(self._run(gates), "")

    def test_no_marker_no_warn(self):
        """Mirrors FEAT-2026-0070/T07 AC4: keeps the check off every feature
        that closed before T06 shipped."""
        (self.dir / "RETROSPECTIVE.md").write_text("No debt marker in here.")
        gates = self._gates("Write a retrospective.")
        self.assertEqual(self._run(gates), "")

    def test_done_terminal_close_wu_is_skipped(self):
        """Sealed history: matches check_closing_guard_literals's :427
        behavior."""
        self._retro(marker_gate=1)
        gates = self._gates("Write a retrospective.", status="done")
        self.assertEqual(self._run(gates), "")


if __name__ == "__main__":
    unittest.main()
