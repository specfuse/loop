#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Convergent work units iterate instead of restarting (#2650).

For a unit whose oracle is a strict whole-tree validator, "gate failed"
usually means *the attempt is incomplete*, not *the attempt was wrong*.
Those need opposite responses — continue versus discard — and the driver
only implemented discard, so three attempts were three independent restarts
and the knowledge each produced was thrown away (#2641).

Opt-in per unit via `iterate_on_failure`, because the author knows whether
partial progress is meaningful for their oracle. Convergence is **declared
and measured**, never inferred: the validator emits `FINDINGS: <n>` and the
driver compares. Inferring progress from a raw failure count would be the
proxy-guessing this repository records as
`[meta/six-bug-sweep/detecting-a-condition-is-not-handling-it]`.

Three behaviours pinned here:

- **improving keeps the tree** — the next attempt continues in place, and
  its `oracles` pre-dispatch set re-runs the validator so the prompt opens
  with current findings rather than a stale diff;
- **not improving restores the best tree**, so a worse iteration cannot
  destroy a better one — the reset's original purpose (bugs #71/#74) is
  preserved rather than abandoned;
- **a plateau escalates**, because a unit that stops converging is exactly
  the case the attempt ceiling exists for.
"""

from __future__ import annotations

import unittest

from specfuse.loop.loop import (
    CONVERGENCE_PLATEAU_LIMIT,
    ConvergenceState,
    decide_convergence_action,
    parse_convergence_findings,
    synthesize_retry_directive,
)


class TestParsingTheDeclaredMetric(unittest.TestCase):
    def test_a_findings_line_is_read(self):
        self.assertEqual(parse_convergence_findings("FINDINGS: 12\n"), 12)

    def test_it_is_found_among_other_output(self):
        out = "validating specs...\nerror: x\nFINDINGS: 3\ndone\n"
        self.assertEqual(parse_convergence_findings(out), 3)

    def test_the_last_occurrence_wins(self):
        # A run that validates in phases reports more than once; the final
        # tally is the one that describes the tree as it now stands.
        self.assertEqual(
            parse_convergence_findings("FINDINGS: 9\nFINDINGS: 4\n"), 4)

    def test_zero_is_a_real_value_not_absence(self):
        self.assertEqual(parse_convergence_findings("FINDINGS: 0\n"), 0)

    def test_absent_metric_is_none_rather_than_zero(self):
        # "I could not tell" must not read as "nothing is wrong".
        self.assertIsNone(parse_convergence_findings("no metric here\n"))

    def test_a_malformed_count_is_none(self):
        self.assertIsNone(parse_convergence_findings("FINDINGS: many\n"))


class TestTheDecision(unittest.TestCase):
    def test_the_first_failure_retains_and_records_a_baseline(self):
        state = ConvergenceState()
        action, state = decide_convergence_action(10, state)

        self.assertEqual(action, "retain")
        self.assertEqual(state.best_findings, 10)
        self.assertEqual(state.plateau, 0)

    def test_improving_retains_and_lowers_the_baseline(self):
        state = ConvergenceState(best_findings=10)
        action, state = decide_convergence_action(4, state)

        self.assertEqual(action, "retain")
        self.assertEqual(state.best_findings, 4)
        self.assertEqual(state.plateau, 0)

    def test_not_improving_restores_the_best_tree(self):
        state = ConvergenceState(best_findings=4)
        action, state = decide_convergence_action(4, state)

        self.assertEqual(action, "restore")
        self.assertEqual(state.best_findings, 4, "baseline must not regress")
        self.assertEqual(state.plateau, 1)

    def test_getting_worse_also_restores(self):
        state = ConvergenceState(best_findings=4)
        action, state = decide_convergence_action(9, state)

        self.assertEqual(action, "restore")
        self.assertEqual(state.best_findings, 4)

    def test_a_sustained_plateau_escalates(self):
        state = ConvergenceState(best_findings=4)
        for _ in range(CONVERGENCE_PLATEAU_LIMIT - 1):
            action, state = decide_convergence_action(4, state)
            self.assertEqual(action, "restore")
        action, state = decide_convergence_action(4, state)

        self.assertEqual(action, "escalate")

    def test_progress_clears_an_accumulated_plateau(self):
        # Two stalls then a breakthrough must not escalate on the next stall.
        state = ConvergenceState(best_findings=10, plateau=1)
        action, state = decide_convergence_action(6, state)

        self.assertEqual(action, "retain")
        self.assertEqual(state.plateau, 0)

    def test_reaching_zero_findings_retains(self):
        # Zero is progress, not a plateau — and the gate itself decides pass.
        state = ConvergenceState(best_findings=3)
        action, state = decide_convergence_action(0, state)

        self.assertEqual(action, "retain")
        self.assertEqual(state.best_findings, 0)


class TestAnUnmeasurableOracleDoesNotSilentlyIterate(unittest.TestCase):
    def test_no_metric_falls_back_to_the_discard_behaviour(self):
        # A unit declaring itself convergent whose validator emits no metric
        # cannot be iterated safely: there is nothing to say whether the tree
        # got better. Fall back to today's semantics rather than retaining a
        # tree that might be worse on every axis.
        state = ConvergenceState(best_findings=4)
        action, state = decide_convergence_action(None, state)

        self.assertEqual(action, "reset")

    def test_an_unmeasurable_attempt_counts_toward_the_plateau(self):
        # Otherwise a validator that never emits the metric would iterate
        # forever against the attempt ceiling with no progress signal.
        state = ConvergenceState(best_findings=4)
        _, state = decide_convergence_action(None, state)

        self.assertEqual(state.plateau, 1)


class TestTheRetryDirectiveTellsTheTruth(unittest.TestCase):
    def test_the_default_still_says_the_work_was_discarded(self):
        self.assertIn("DISCARDED", synthesize_retry_directive("tests"))

    def test_a_retained_attempt_is_not_told_its_work_was_discarded(self):
        # The standing directive is a lie for a retained unit, and acting on
        # it means re-authoring from scratch — the opposite of iterating.
        directive = synthesize_retry_directive("tests", retained=True)

        self.assertNotIn("DISCARDED", directive)
        self.assertNotIn("no longer exist", directive)

    def test_a_retained_attempt_is_told_the_work_is_still_there(self):
        directive = synthesize_retry_directive("tests", retained=True)

        self.assertIn("still present", directive.lower())

    def test_the_class_hint_survives_both_variants(self):
        plain = synthesize_retry_directive("lint")
        retained = synthesize_retry_directive("lint", retained=True)
        hint = plain.split(". ")[-1]

        self.assertIn(hint, retained)


class TestTheFieldIsOptInAndOff(unittest.TestCase):
    def test_a_work_unit_defaults_to_the_discard_behaviour(self):
        import tempfile
        from pathlib import Path

        from specfuse.loop.loop import load_wu

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "WU-01.md").write_text(
                "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
                "status: pending\n---\n\n# Unit\n\nBody.\n")
            wu = load_wu(Path(tmp),
                         {"id": "FEAT-2026-9999/T01", "file": "WU-01.md"})

        self.assertFalse(wu.iterate_on_failure)

    def test_the_field_is_read_off_disk(self):
        import tempfile
        from pathlib import Path

        from specfuse.loop.loop import load_wu

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "WU-01.md").write_text(
                "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
                "status: pending\niterate_on_failure: true\n---\n\n# U\n\nB.\n")
            wu = load_wu(Path(tmp),
                         {"id": "FEAT-2026-9999/T01", "file": "WU-01.md"})

        self.assertTrue(wu.iterate_on_failure)


if __name__ == "__main__":
    unittest.main()
