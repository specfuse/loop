# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""An issue an operator promoted to a feature leaves the bug lane (#3415).

The lane read an issue's triage category from the body marker only. An
operator promotes a refused bug by relabelling it (`triage:bug` ->
`triage:feature`) and clearing `needs-human`; the marker still said
`category=bug`, so the next run dispatched `/fix-bug` on it again -- ten
promoted issues on clabonte/generator in one run (2026-09-25), one of which
got a competing bug-lane PR. Triage's marker/label repair made it worse: a
`bug` marker without `triage:bug` read as a desync and re-applied the label.

A triage category label that disagrees with the marker is a human override,
and it wins -- for selection, and for repair.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.agent.providers.bugs import BugsProvider
from specfuse.agent.state import AgentSnapshot, _to_issue_summary
from specfuse.loop.triage import (
    BUG_LABEL,
    FEATURE_LABEL,
    effective_category,
    list_untriaged,
)

_BUG_MARKER = "<!-- specfuse:triage category=bug confidence=high severity=high -->"


def _raw(number, labels, body=_BUG_MARKER):
    return {
        "number": number,
        "title": f"issue {number}",
        "body": body,
        "labels": [{"name": n} for n in labels],
    }


class TestEffectiveCategory(unittest.TestCase):
    def test_no_category_label_keeps_the_marker(self):
        self.assertEqual(effective_category("bug", ()), "bug")

    def test_matching_label_keeps_the_marker(self):
        self.assertEqual(effective_category("bug", (BUG_LABEL, "severity:high")), "bug")

    def test_a_different_category_label_wins(self):
        self.assertEqual(effective_category("bug", (FEATURE_LABEL,)), "feature")

    def test_conflicting_category_labels_are_no_category(self):
        self.assertIsNone(effective_category("bug", (BUG_LABEL, FEATURE_LABEL)))

    def test_no_marker_stays_no_category(self):
        self.assertIsNone(effective_category(None, (FEATURE_LABEL,)))


class TestPromotedIssueIsNotSelected(unittest.TestCase):
    def test_promoted_issue_reads_as_feature(self):
        summary = _to_issue_summary(_raw(2085, (FEATURE_LABEL,)))

        self.assertEqual(summary.triage_category, "feature")

    def test_bug_lane_does_not_advertise_a_promoted_issue(self):
        snapshot = AgentSnapshot(
            queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
            issues=(
                _to_issue_summary(_raw(2085, (FEATURE_LABEL,))),
                _to_issue_summary(_raw(2100, (BUG_LABEL,))),
            ),
            issues_error=None, prs=(), prs_error=None, features=(),
        )

        items = BugsProvider(repo="o/r").advertise(snapshot)

        self.assertEqual([i.item_id for i in items], ["bug-2100"])


class TestRepairDoesNotUndoAPromotion(unittest.TestCase):
    def _untriaged(self, issues):
        def runner(argv, check=False, **_kwargs):
            return SimpleNamespace(returncode=0, stdout=json.dumps(issues), stderr="")

        return list_untriaged(runner, "o/r")

    def test_promoted_issue_is_not_flagged_for_repair(self):
        rows = self._untriaged([_raw(2085, (FEATURE_LABEL,))])

        self.assertEqual(rows, [])

    def test_a_genuinely_missing_label_is_still_repaired(self):
        rows = self._untriaged([_raw(2100, ())])

        self.assertEqual([r["number"] for r in rows], [2100])
        self.assertTrue(rows[0]["needs_repair"])


if __name__ == "__main__":
    unittest.main()
