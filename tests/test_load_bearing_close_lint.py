#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A load-bearing close WU must declare `auto_close_disabled` (#293).

`close-discipline.md` says a close carrying any §1–§3 obligation is
**load-bearing**, and the plan author must set `auto_close_disabled: true` so
`evaluate_auto_close` cannot optimize it away (#189). Nothing enforced that but
a human remembering: `specfuse-lint` reported `OK — structurally valid` on a
folder whose close was silently skipped — twice, including on a conformance
pass whose entire purpose was close-discipline debt.

Three recorded instances, all on well-behaved features:

* `clabonte/generator` FEAT-2026-0066 gate 1 — textbook §1 re-verification
  language, no flag, auto-closed at `attempts: 0`; the gate's Verdict section
  was left at its literal placeholder.
* FEAT-2026-0061 — lost all 26 acceptance criteria the same way.
* FEAT-2026-0063 — lost one criterion, and it was load-bearing for the
  accuracy of the roadmap row.

**Two signals, because one is not enough.** The issue proposed matching §1–§3
verification phrasing. Its own follow-up comment then reported a case that slips
past exactly that heuristic: FEAT-2026-0063's dropped criterion was a
*durable-surface write* — reconciling the roadmap row with what was built —
containing no re-verification language at all. So this lint also treats a close
whose acceptance names a path **outside its own feature folder** as load-bearing
by construction, which is mechanical rather than heuristic.

The selection effect is what makes this expensive: a gate only auto-closes when
it is on-plan and under budget, so these criteria are dropped precisely on the
features that behaved well and therefore attract the least scrutiny.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

load_loop()

from specfuse.loop.lint_plan import (  # noqa: E402  (after sys.path setup above)
    detect_load_bearing_close,
)


class TestVerificationPhrasingSignal(unittest.TestCase):
    """§1–§3 obligations, the class the issue originally proposed."""

    def test_fresh_oracle_rerun_is_load_bearing(self):
        ac = ("1. Every oracle is re-run fresh, full commands, exit codes read "
              "directly — never a producing work unit's self-report.")
        self.assertTrue(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_reverify_language_is_load_bearing(self):
        ac = ("Gate 1's Definition of Done is re-verified item by item against "
              "actual output from a fresh out/ directory.")
        self.assertTrue(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_hedged_verdict_record_is_load_bearing(self):
        ac = ("On met_locally, write a named record per unmet criterion with a "
              "kind: field.")
        self.assertTrue(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_consumer_visible_contract_enumeration_is_load_bearing(self):
        ac = ("Enumerate every consumer-visible contract change across the "
              "feature's producing work units.")
        self.assertTrue(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))


class TestSurfaceScopeSignal(unittest.TestCase):
    """Durable-surface writes — the class the phrase match misses (#293 comment 2)."""

    def test_a_path_outside_the_feature_folder_is_load_bearing(self):
        # FEAT-2026-0063's criterion 6, near-verbatim. No verification verb
        # anywhere in it; the phrase match alone would let this through.
        ac = ("6. The roadmap row and its detail section in `.specfuse/roadmap.md` "
              "reflect what was actually built, including the retitle recorded "
              "in PLAN.md.")
        self.assertTrue(
            detect_load_bearing_close(ac, "FEAT-2026-0063-arm-sweep"),
            "a close that is the sole writer of a surface outside its own "
            "feature folder is load-bearing by construction")

    def test_changelog_write_is_load_bearing(self):
        ac = "Append one entry to `CHANGELOG.md`'s Unreleased section."
        self.assertTrue(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_learnings_promotion_alone_is_deliberately_not_a_signal(self):
        """LEARNINGS.md is a durable surface a skipped close genuinely corrupts
        (FEAT-2026-0031 lost every entry that way) — and it is still excluded,
        on measurement rather than principle.

        68 of 71 close WUs in this repo mention it; 3 declare it in `produces:`.
        A signal present in ~96% of the population separates nothing. Including
        it fired this warning on 29 of 55 features instead of 22, and a check
        that fires on half of everything is the shape that trains an operator to
        ignore it — the #771 lesson, applied to a check written the same day.

        The lesson-loss risk stays owned by close-discipline's own guards.
        """
        ac = "Candidate lessons are promoted to `.specfuse/LEARNINGS.md`."
        self.assertFalse(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_roadmap_reconciliation_still_fires_alongside_learnings(self):
        # Excluding LEARNINGS must not suppress a criterion that ALSO names a
        # selective surface — the two appear together constantly.
        ac = ("Lessons are promoted to `.specfuse/LEARNINGS.md`, and the "
              "roadmap row in `.specfuse/roadmap.md` reflects what shipped.")
        self.assertTrue(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_a_path_inside_the_feature_folder_alone_is_not(self):
        # RETROSPECTIVE.md lives in the feature's own folder, so writing it is
        # not a durable-surface write. Without this carve-out every close in
        # existence trips the rule and the warning becomes noise.
        ac = ("Write RETROSPECTIVE.md in this feature folder with a "
              "## Cost analysis heading.")
        self.assertFalse(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))


class TestNonLoadBearingCloses(unittest.TestCase):
    """The rule must stay quiet on closes that genuinely carry no obligation."""

    def test_a_plain_close_is_not_load_bearing(self):
        ac = ("1. The gate's work units are all done.\n"
              "2. A short summary of what shipped is written.")
        self.assertFalse(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))

    def test_empty_acceptance_is_not_load_bearing(self):
        self.assertFalse(detect_load_bearing_close("", "FEAT-2026-9001-x"))

    def test_the_feature_folders_own_name_does_not_trip_it(self):
        # A close naming its own folder is not reaching outside it.
        ac = "Read .specfuse/features/FEAT-2026-9001-x/PLAN.md for the framing."
        self.assertFalse(detect_load_bearing_close(ac, "FEAT-2026-9001-x"))


if __name__ == "__main__":
    unittest.main()
