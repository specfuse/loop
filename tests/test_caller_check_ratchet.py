#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Ratchet on symbols whose only callers are tests (#3324).

Four September defects shared one shape — a symbol that existed, was tested,
and was wired to nothing. Three were detectable from the tree; none was
detected, and each surfaced in a later feature instead of its own gate.

This is the guard, as a **baseline-and-ratchet** rather than zero tolerance.
The tree carries 20 pre-existing instances, most of them reached from the
umbrella repo (`doctor`, `lint_roadmap`, `stamp_release`,
`validate_escalation_body` …) which a single-repo check cannot see. Failing on
today's state would be the unsatisfiable-predicate defect
`planning-discipline.md` §2 names — the same reason #3320's binding-block check
ships as an advisory.

**Adding a symbol here is a decision, not a chore.** If a new name needs to go
in the baseline, the honest question is why it has no caller — that is exactly
the condition this guard exists to surface.
"""
from __future__ import annotations

import unittest

from specfuse.loop import caller_check


#: Symbols with no in-tree non-test caller when this guard landed (2026-09-15).
#: `assert_produces_in_diff` left on 2026-09-17 — it was dead rather than
#: umbrella-reached, and was removed (#3328), which is what this baseline is
#: for: an entry leaving it is the guard doing its job.
#: Most are reached from the umbrella repo or by a runner this check cannot see.
BASELINE = {
    "all_requirements",
    "annotate_if_quiet",
    "append_entry",
    "build_azure_transport",
    "census",
    "code_gate_names",
    "collect_reports",
    "diff_edits_driver",
    "doctor",
    "lint_roadmap",
    "list_promoted",
    "migrate_legacy",
    "ratified_after_override",
    "released_section_drift",
    "stamp_release",
    "sweep_arm_predicate",
    "triaged_bug_intake",
    "validate_escalation_body",
    "wrapped",
}


class NoNewUnwiredSymbols(unittest.TestCase):

    def test_no_symbol_outside_the_baseline_is_called_only_by_tests(self):
        new = caller_check.new_since_baseline(BASELINE)
        self.assertEqual(
            [], new,
            "these public symbols have no caller outside tests/ and are not in "
            "BASELINE — wire them, or add them with a reason:\n  "
            + "\n  ".join(f"{f['name']} ({f['module']})" for f in new))

    def test_the_baseline_has_not_silently_shrunk(self):
        # A name that leaves the findings has been wired, which is good — but
        # the baseline should follow, or it slowly stops meaning anything.
        current = {f["name"] for f in caller_check.unreached_symbols()}
        stale = BASELINE - current
        self.assertEqual(
            set(), stale,
            "these are in BASELINE but now have a caller — remove them from "
            f"BASELINE: {sorted(stale)}")


class ReachabilityRules(unittest.TestCase):

    def test_a_string_reference_counts_as_reached(self):
        # closing_requirements.py dispatches every closing guard by name.
        names = {f["name"] for f in caller_check.unreached_symbols()}
        self.assertNotIn("assert_cost_analysis_section_when_met", names)
        self.assertNotIn("assert_verdict_well_formed", names)

    def test_an_entry_point_is_not_a_finding(self):
        names = {f["name"] for f in caller_check.unreached_symbols()}
        self.assertNotIn("main", names)

    def test_a_wired_symbol_drops_out(self):
        # propose_distilled_learnings was the #3315 finding until #3325 gave it
        # a caller; it must no longer be reported.
        names = {f["name"] for f in caller_check.unreached_symbols()}
        self.assertNotIn("propose_distilled_learnings", names)
        self.assertNotIn("check_binding_block_budget", names)


if __name__ == "__main__":
    unittest.main()
