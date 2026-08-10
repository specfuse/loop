#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Regression guard for #1420: the bug lane labelled pull requests with the raw
# `REASON_*` constant, and none of those values were in LABEL_REGISTRY — so
# `provision_labels` created them in no repository, including this one, and every
# declining path issued `gh pr edit --add-label <nonexistent>` with check=True.
#
# Not caught by the feature's own suite because every test there injects a fake
# runner, so no test exercised a real label write. The falsifiable check is
# structural, and it is the shape of tests/test_bats_suites_gated.py (#257):
# diff a declared set against an actual set and assert both directions.

import unittest

from specfuse.loop import bug_lane
from specfuse.loop.labels import LABEL_REGISTRY


def _reason_values() -> set:
    """Every REASON_* value bug_lane can put on a MergeDecision."""
    return {
        getattr(bug_lane, name)
        for name in dir(bug_lane)
        if name.startswith("REASON_")
    }


class TestDeclineLabelsAreRegistered(unittest.TestCase):
    def test_decline_labels_mapping_exists(self):
        self.assertTrue(
            hasattr(bug_lane, "DECLINE_LABELS"),
            "bug_lane must expose DECLINE_LABELS mapping reason -> public label name; "
            "the reason constant is an internal identifier and must not double as "
            "the label",
        )

    def test_every_declining_reason_has_a_label(self):
        # Every reason except the pass case can reach the labelling call, so every
        # one of them needs a name. A reason with no mapping would raise at the
        # call site instead of labelling.
        declining = _reason_values() - {bug_lane.REASON_ELIGIBLE}
        missing = sorted(declining - set(bug_lane.DECLINE_LABELS))
        self.assertEqual(missing, [], f"declining reasons with no label: {missing}")

    def test_no_label_for_the_eligible_reason(self):
        # `eligible` is not a decline and is never labelled; mapping it would
        # invite labelling a PR that merged.
        self.assertNotIn(bug_lane.REASON_ELIGIBLE, bug_lane.DECLINE_LABELS)

    def test_every_emittable_label_is_in_the_registry(self):
        # The forward direction, and the one #1420 is about: provision_labels only
        # creates what LABEL_REGISTRY declares.
        registered = {spec.name for spec in LABEL_REGISTRY}
        emittable = set(bug_lane.DECLINE_LABELS.values())
        missing = sorted(emittable - registered)
        self.assertEqual(
            missing, [],
            f"labels the bug lane can emit but provision_labels never creates: {missing}",
        )

    def test_labels_follow_the_registry_naming_convention(self):
        # The registry uses `needs-human`, `triage:bug`. A snake_case constant
        # leaking into the public label surface is what made this defect visible.
        for reason, label in sorted(bug_lane.DECLINE_LABELS.items()):
            with self.subTest(reason=reason):
                self.assertNotIn("_", label, f"{label!r} is not registry-conventional")
                self.assertEqual(label, label.lower(), f"{label!r} must be lowercase")

    def test_registry_entries_carry_a_description_and_consumer(self):
        emittable = set(bug_lane.DECLINE_LABELS.values())
        for spec in LABEL_REGISTRY:
            if spec.name in emittable:
                with self.subTest(label=spec.name):
                    self.assertTrue(spec.description.strip(), "description required")
                    self.assertTrue(spec.consumer.strip(), "consumer required")


if __name__ == "__main__":
    unittest.main()
