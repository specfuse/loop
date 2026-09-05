# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Guards LABEL_REGISTRY against drift from escalation.py's label vocabulary."""

from __future__ import annotations

import re
import unittest

from specfuse.loop import bug_lane, closing_requirements, escalation, gh_features, notify_sla, triage
from specfuse.monitor import autofix_state, issues
from specfuse.loop.labels import LABEL_REGISTRY

_COLOUR_RE = re.compile(r"^[0-9a-f]{6}$")


class TestLabelRegistry(unittest.TestCase):
    def test_registry_has_exactly_fourteen_entries(self):
        # Seven at FEAT-2026-0071; the eighth is the harvester's finding label,
        # added by #300 after `gh issue create` rejected it on a fresh repository.
        # The ninth is FEAT-2026-0042/T02's autofix-failed label, registered
        # ahead of gate 2, its consumer, for the same reason. The tenth through
        # thirteenth are FEAT-2026-0045/T01's category->label projection. The
        # fourteenth is FEAT-2026-0047/T03's parked-escalation label. The
        # fifteenth through twenty-first are the bug lane's declining-reason
        # labels, registered by the #1420 fix — the lane emitted them as raw
        # REASON_* constants that this registry never declared, so
        # provision_labels created none of them and every declining path
        # failed against a real repository.
        # The twenty-second and twenty-third are FEAT-2026-0085/T03's
        # follow-up and post-merge-checklist labels — a not_met close's
        # tracked follow-ups and a met close's Post-merge checklist file as
        # their own issues, distinct from needs-human.
        # The twenty-fourth is FEAT-2026-0108/T04's ci-pending label (#3177):
        # a pending-at-deadline CI run declines as its own reason rather than
        # being folded into ci-not-green.
        # A bare count is a weak invariant — it fails on every legitimate addition
        # and catches nothing a coverage assertion does not. The real guard is
        # tests/test_label_registry_covers_consumers.py, which discovers every
        # label constant in the package and asserts each is declared here.
        self.assertEqual(len(LABEL_REGISTRY), 24)

    def test_entries_expose_nonempty_string_fields(self):
        for entry in LABEL_REGISTRY:
            self.assertIsInstance(entry.name, str)
            self.assertTrue(entry.name)
            self.assertIsInstance(entry.colour, str)
            self.assertTrue(entry.colour)
            self.assertIsInstance(entry.description, str)
            self.assertTrue(entry.description)

    def test_colours_are_six_lowercase_hex_digits(self):
        for entry in LABEL_REGISTRY:
            self.assertRegex(entry.colour, _COLOUR_RE)

    def test_registry_covers_every_escalation_label(self):
        expected = (
            {escalation.NEEDS_HUMAN_LABEL}
            | set(escalation.CATEGORY_LABELS)
            | {gh_features.FEATURE_LABEL}
            | {issues.FINDING_LABEL}
            | {autofix_state.AUTOFIX_FAILED_LABEL}
            | {
                triage.BUG_LABEL,
                triage.FEATURE_LABEL,
                triage.DUPLICATE_LABEL,
                triage.WONTFIX_LABEL,
            }
            | {notify_sla.PARKED_LABEL}
            | set(bug_lane.DECLINE_LABELS.values())
            | {closing_requirements.FOLLOW_UP_LABEL, closing_requirements.POST_MERGE_LABEL}
        )
        actual = {entry.name for entry in LABEL_REGISTRY}
        self.assertEqual(actual, expected)

    def test_specfuse_monitor_is_not_a_registry_entry(self):
        names = {entry.name for entry in LABEL_REGISTRY}
        self.assertNotIn("specfuse-monitor", names)

    def test_registry_names_are_unique(self):
        names = [entry.name for entry in LABEL_REGISTRY]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
