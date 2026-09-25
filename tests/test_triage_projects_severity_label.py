#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Triage writes the repository's own severity word, not just the canonical one.

`severity_aliases` was one-directional (#3386). The bug lane translated a
repository's own words INBOUND through `read_severity_label`, and triage wrote
canonical words OUTBOUND through `severity_label_for` — words that repository
may never have defined.

On a repo labelling `severity:critical` / `severity:major` / `severity:minor`, a
run produced seven escalations of this shape:

    triage-1965 escalated after 5s — issue #1965: label repair failed --
    ... '--add-label', 'triage:bug,severity:high'] returned non-zero exit status 1

Worse than a failed write. The marker is written first and succeeds, so severity
IS judged and recorded — but the bug lane reads severity from the LABEL, not the
marker. So issues came out of triage with no severity label, or with a stale one
contradicting the marker their own run had just written. An unreadable severity
fails closed against `min_severity`, correctly. The net effect is that **triage
silently removes from the lane the very issues it just classified for it**, and
the only trace is a `gh` exit status in an escalation.

The projection this needs already existed. `labels.severity_label_projection`
shipped with #3353 and was wired into the backfill's write path — and only
there. Triage is the other writer, and it was left unprojected: one fix applied
to one of two call sites.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from specfuse.loop.triage import apply_triage, render_marker


class _Runner:
    def __init__(self, fail_on=()):
        self.calls = []
        self._fail_on = set(fail_on)

    def __call__(self, argv, check=False):
        self.calls.append(list(argv))
        for token in self._fail_on:
            if token in argv:
                raise RuntimeError(f"label does not exist: {token}")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def added_labels(self):
        out = []
        for argv in self.calls:
            if "--add-label" in argv:
                out.extend(argv[argv.index("--add-label") + 1].split(","))
        return out


def _decision(number=1965, severity="high"):
    return {
        "number": number,
        "body": "A bug report with no marker yet.",
        "category": "bug",
        "confidence": "high",
        "severity": severity,
        "labels": [],
    }


class TriageWritesTheProjectedLabel(unittest.TestCase):

    def test_the_repositorys_own_word_is_written(self):
        runner = _Runner()

        apply_triage(runner, "acme/widget", [_decision()],
                     label_projection={"high": "severity:major"})

        self.assertIn("severity:major", runner.added_labels())
        self.assertNotIn("severity:high", runner.added_labels())

    def test_the_marker_still_records_the_canonical_value(self):
        # Same split as the backfill: the marker stays comparable across
        # repositories, only the label takes the operator's word.
        runner = _Runner()

        apply_triage(runner, "acme/widget", [_decision()],
                     label_projection={"high": "severity:major"})

        bodies = [a[a.index("--body") + 1] for a in runner.calls if "--body" in a]
        self.assertEqual(1, len(bodies))
        self.assertIn("severity=high", bodies[0])
        self.assertNotIn("severity=major", bodies[0])

    def test_absent_projection_keeps_todays_behaviour(self):
        runner = _Runner()

        apply_triage(runner, "acme/widget", [_decision()])

        self.assertIn("severity:high", runner.added_labels())

    def test_a_value_with_no_projection_entry_stays_canonical(self):
        runner = _Runner()

        apply_triage(runner, "acme/widget", [_decision(severity="critical")],
                     label_projection={"high": "severity:major"})

        self.assertIn("severity:critical", runner.added_labels())

    def test_the_category_labels_are_unaffected(self):
        runner = _Runner()

        apply_triage(runner, "acme/widget", [_decision()],
                     label_projection={"high": "severity:major"})

        self.assertIn("triage:bug", runner.added_labels())


class TheRepairPathProjectsToo(unittest.TestCase):
    """The second writer: an issue already carrying a marker whose label is
    missing. It retries only the label write, and wrote canonically too."""

    def _marked(self, severity="high"):
        return {
            "number": 1965,
            "body": render_marker("bug", "high", severity) + "\n\nBody.",
            "category": "bug",
            "labels": [{"name": "triage:bug"}],
        }

    def test_the_repair_writes_the_projected_label(self):
        runner = _Runner()

        results = apply_triage(runner, "acme/widget", [self._marked()],
                               label_projection={"high": "severity:major"})

        self.assertTrue(results[0]["skipped"], "marker already present")
        self.assertIn("severity:major", runner.added_labels())
        self.assertNotIn("severity:high", runner.added_labels())

    def test_the_repair_without_a_projection_is_unchanged(self):
        runner = _Runner()

        apply_triage(runner, "acme/widget", [self._marked()])

        self.assertIn("severity:high", runner.added_labels())


class TheLabelListingStaysOncePerRun(unittest.TestCase):
    """The rubric accessor carried a once-per-run `gh label list` invariant.

    Deriving the projection from a second listing would double it. The same
    mistake, made in the backfill's version of this fix, was caught only by an
    existing test — so it gets its own assertion here.
    """

    def _provider(self, runner):
        from specfuse.agent.providers.triage import TriageProvider
        return TriageProvider(repo="acme/widget", runner=runner, working_dir=".")

    def test_rubric_and_projection_share_one_listing(self):
        import json

        calls = []

        def runner(argv, check=False, cwd=None):
            calls.append(list(argv))
            if argv[:3] == ["gh", "label", "list"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps([
                    {"name": "severity:critical", "description": "Drop all."},
                    {"name": "severity:major", "description": "Wrong."},
                    {"name": "severity:minor", "description": "Cosmetic."},
                ]), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        provider = self._provider(runner)
        rubric = provider._rubric_for_run()
        projection = provider._projection_for_run()

        listings = [c for c in calls if c[:3] == ["gh", "label", "list"]]
        self.assertEqual(
            1, len(listings),
            f"one `gh label list` per run; got {len(listings)}",
        )
        self.assertEqual({"critical", "high", "low"}, set(rubric))
        self.assertEqual("severity:major", projection.get("high"))
        self.assertEqual("severity:minor", projection.get("low"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
