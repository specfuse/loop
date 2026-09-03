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

from specfuse.loop.lint_plan import check_closing_guard_literals

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


if __name__ == "__main__":
    unittest.main()
