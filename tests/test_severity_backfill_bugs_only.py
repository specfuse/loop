# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Severity backfill selects bugs only (#3360).

Severity exists to gate the bug lane: `rules.bugs.min_severity` decides which
triaged bugs it may dispatch, and a bug with no severity is stranded under the
floor -- the 31 issues FEAT-2026-0113 opened on. The candidate predicate took
any triaged category, so the first `--limit 200` dry run on the measured
repository selected 31 candidates of which 25 were features: an `--apply` would
have labelled `[GAP]`/`[RFE]` issues `severity:high` for a gate they never
reach. The predicate now takes bugs only -- by the effective category, so an
issue promoted to a feature by relabelling (#3415) is not one.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.triage import FEATURE_LABEL, list_severity_backfill_candidates


def _issue(number, category, labels=()):
    return {
        "number": number,
        "title": f"issue {number}",
        "body": f"<!-- specfuse:triage category={category} confidence=high -->\n\nBody.",
        "labels": [{"name": n} for n in labels],
    }


def _candidates(issues):
    def runner(argv, check=False, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps(issues), stderr="")

    return [i["number"] for i in list_severity_backfill_candidates(runner, "o/r", limit=50)]


class TestBackfillSelectsBugsOnly(unittest.TestCase):
    def test_a_marked_bug_is_a_candidate(self):
        self.assertEqual(_candidates([_issue(1, "bug")]), [1])

    def test_other_categories_are_not(self):
        issues = [
            _issue(2, "feature"), _issue(3, "question"),
            _issue(4, "duplicate"), _issue(5, "wontfix"),
        ]

        self.assertEqual(_candidates(issues), [])

    def test_a_bug_promoted_to_a_feature_is_not(self):
        self.assertEqual(_candidates([_issue(6, "bug", labels=(FEATURE_LABEL,))]), [])


if __name__ == "__main__":
    unittest.main()
