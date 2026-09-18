#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`rules.bugs.min_severity` must filter what the bug lane advertises (#3339).

The key is validated by `validate_agent_policy` against
`SEVERITY_VALUES = {low, medium, high, critical}` and was read by nothing:
`BugsProvider.advertise` admitted every issue whose triage marker said `bug`,
whatever its severity, so a policy declaring `min_severity: medium` still
dispatched `/fix-bug` on minor issues.

**Where severity is read from had to be defined**, because nothing defined it:
the triage marker carries only `category` and `confidence`, and no code read a
label. It is a `severity:<value>` label, matching the policy's own vocabulary.

**Unreadable severity fails closed**, which the issue names as the safe
default — but only when the policy declares a floor. An absent `min_severity`
leaves the lane exactly as it was, so this cannot quietly stop an existing
deployment from advertising anything. Declaring a floor is opting into the
labelling discipline that floor requires, and every skip is reported with its
reason so an empty lane is explained rather than silent.
"""
from __future__ import annotations

import unittest

from specfuse.loop import agent_policy


class SeverityRank(unittest.TestCase):

    def test_the_vocabulary_is_ordered_lowest_to_highest(self):
        self.assertEqual(
            ("low", "medium", "high", "critical"), agent_policy.SEVERITY_ORDER)

    def test_every_validated_value_has_a_rank(self):
        # The ordering and the validator must not drift apart: a value the
        # validator accepts but the rank does not know would be unfilterable.
        self.assertEqual(
            set(agent_policy.SEVERITY_VALUES), set(agent_policy.SEVERITY_ORDER))


class SeverityFromLabels(unittest.TestCase):

    def test_a_severity_label_is_read(self):
        self.assertEqual(("high", None), agent_policy.read_severity_label(
            ["bug", "severity:high"]))

    def test_an_unknown_severity_value_is_not_read(self):
        # `severity:minor` is real in the wild and is NOT in the vocabulary.
        # Guessing a mapping would be inventing policy; it reads as absent.
        # #3349 added the one way it can read: an operator declaring what the
        # word means under `rules.bugs.severity_aliases`. With no aliases
        # passed, this is unchanged.
        self.assertEqual((None, None), agent_policy.read_severity_label(["severity:minor"]))

    def test_no_severity_label_reads_as_absent(self):
        self.assertEqual((None, None), agent_policy.read_severity_label(["bug", "triage"]))


class MeetsFloor(unittest.TestCase):

    def test_at_or_above_the_floor_passes(self):
        for sev in ("medium", "high", "critical"):
            with self.subTest(sev):
                ok, _ = agent_policy.meets_severity_floor(sev, "medium")
                self.assertTrue(ok)

    def test_below_the_floor_is_refused_with_a_reason(self):
        ok, reason = agent_policy.meets_severity_floor("low", "medium")
        self.assertFalse(ok)
        self.assertIn("low", reason)
        self.assertIn("medium", reason)

    def test_unreadable_severity_fails_closed_when_a_floor_is_set(self):
        ok, reason = agent_policy.meets_severity_floor(None, "medium")
        self.assertFalse(ok)
        self.assertIn("no severity", reason.lower())

    def test_a_floor_at_the_bottom_admits_unlabelled(self):
        # `low` is the bottom of the vocabulary, so nothing is below it: that
        # floor excludes nothing and must not fail closed. This repo's own
        # policy declares `min_severity: low` with no severity labels anywhere
        # — reading that as "advertise nothing" would disable the lane.
        ok, _ = agent_policy.meets_severity_floor(None, "low")
        self.assertTrue(ok)

    def test_no_floor_admits_everything_including_unlabelled(self):
        # The compatibility guarantee: a deployment that never declared
        # min_severity behaves exactly as before.
        for sev in (None, "low", "critical"):
            with self.subTest(sev):
                ok, _ = agent_policy.meets_severity_floor(sev, None)
                self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
