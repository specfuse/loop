#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the neutral cron-schedule evaluator (FEAT-2026-0040/T07).

``TestDialectIsLoadBearing`` is the criterion-1 red/green anchor: it must
exist and fail on HEAD before this work unit lands (the module and this file
do not yet exist there), then pass once ``specfuse/monitor/schedule.py``
reads the declared dialect rather than inferring it from field count.

Arity-mismatch cases (``TestArityDisagreementRefuses``) are written as direct
``most_recent_firing`` calls rather than dict literals on purpose: the
tree-wide sweep in ``test_monitoring_cron_dialect.py`` flags every Python
dict literal carrying a ``cron`` key whose declared ``dialect`` disagrees
with the expression's field count, and these cases are deliberately
disagreeing.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from specfuse.monitor.schedule import most_recent_firing

_UTC_REF = datetime(2026, 7, 28, 10, 0, 0, tzinfo=timezone.utc)


class TestDialectIsLoadBearing(unittest.TestCase):
    def test_same_expression_under_two_dialects_differs(self):
        six_field = "15 30 2 * * *"
        five_field_truncation = " ".join(six_field.split()[1:])

        under_six = most_recent_firing(
            six_field, "seconds-first-6", "Etc/UTC", _UTC_REF
        )
        under_five = most_recent_firing(
            five_field_truncation, "standard-5", "Etc/UTC", _UTC_REF
        )

        self.assertNotEqual(under_six, under_five)
        self.assertEqual(under_six.second, 15)
        self.assertEqual(under_five.second, 0)


class TestSupportedSyntax(unittest.TestCase):
    def test_wildcard_step_list_and_range_all_parse(self):
        # minute: comma list; hour: */n step; dom: a-b range; month/dow: "*".
        result = most_recent_firing(
            "0,30 */2 1-15 * *", "standard-5", "Etc/UTC", _UTC_REF
        )
        self.assertIsInstance(result, datetime)
        self.assertIn(result.minute, (0, 30))
        self.assertEqual(result.hour % 2, 0)
        self.assertLessEqual(result.day, 15)

    def test_literal_values_parse_in_every_field(self):
        result = most_recent_firing(
            "15 3 10 6 *",
            "standard-5",
            "Etc/UTC",
            datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(
            (result.month, result.day, result.hour, result.minute),
            (6, 10, 3, 15),
        )

    def test_six_field_dialect_supports_the_same_subset(self):
        result = most_recent_firing(
            "0,30 */15 2 1-15 * *", "seconds-first-6", "Etc/UTC", _UTC_REF
        )
        self.assertIsInstance(result, datetime)
        self.assertIn(result.second, (0, 30))


class TestUnsupportedSyntaxRejected(unittest.TestCase):
    # A negative observation each — a silently mis-parsed expression is
    # exactly the failure class this unit exists to prevent (criterion 3).

    def test_rejects_last_day_of_month_L(self):
        with self.assertRaises(ValueError):
            most_recent_firing("0 2 L * *", "standard-5", "Etc/UTC", _UTC_REF)

    def test_rejects_nearest_weekday_W(self):
        with self.assertRaises(ValueError):
            most_recent_firing("0 2 W * *", "standard-5", "Etc/UTC", _UTC_REF)

    def test_rejects_nth_weekday_hash(self):
        with self.assertRaises(ValueError):
            most_recent_firing(
                "0 2 * * 1#3", "standard-5", "Etc/UTC", _UTC_REF
            )

    def test_error_names_the_unsupported_token(self):
        with self.assertRaises(ValueError) as ctx:
            most_recent_firing("0 2 L * *", "standard-5", "Etc/UTC", _UTC_REF)
        self.assertIn("L", str(ctx.exception))


class TestArityDisagreementRefuses(unittest.TestCase):
    def test_five_field_expression_declared_seconds_first_6_raises(self):
        with self.assertRaises(ValueError) as ctx:
            most_recent_firing(
                "0 2 * * *", "seconds-first-6", "Etc/UTC", _UTC_REF
            )
        message = str(ctx.exception)
        self.assertIn("seconds-first-6", message)
        self.assertIn("5", message)

    def test_six_field_expression_declared_standard_5_raises(self):
        with self.assertRaises(ValueError) as ctx:
            most_recent_firing(
                "0 0 2 * * *", "standard-5", "Etc/UTC", _UTC_REF
            )
        message = str(ctx.exception)
        self.assertIn("standard-5", message)
        self.assertIn("6", message)


class TestDefensiveChecks(unittest.TestCase):
    def test_unknown_dialect_raises(self):
        with self.assertRaises(ValueError) as ctx:
            most_recent_firing("0 2 * * *", "fortnightly-9", "Etc/UTC", _UTC_REF)
        self.assertIn("fortnightly-9", str(ctx.exception))

    def test_naive_reference_raises(self):
        with self.assertRaises(ValueError):
            most_recent_firing(
                "0 2 * * *", "standard-5", "Etc/UTC", datetime(2026, 7, 28, 10, 0, 0)
            )

    def test_out_of_range_literal_raises(self):
        with self.assertRaises(ValueError):
            most_recent_firing("99 2 * * *", "standard-5", "Etc/UTC", _UTC_REF)

    def test_out_of_range_step_raises(self):
        with self.assertRaises(ValueError):
            most_recent_firing("*/0 2 * * *", "standard-5", "Etc/UTC", _UTC_REF)

    def test_inverted_range_raises(self):
        with self.assertRaises(ValueError):
            most_recent_firing("0 2 20-10 * *", "standard-5", "Etc/UTC", _UTC_REF)

    def test_dow_only_restriction_matches_by_weekday_alone(self):
        # dom wildcard, dow restricted to Tuesday (2): only the weekday
        # constraint governs (no OR with an unrestricted dom).
        result = most_recent_firing(
            "0 3 * * 2",
            "standard-5",
            "Etc/UTC",
            datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(result.isoweekday(), 2)

    def test_unsatisfiable_expression_raises(self):
        # February never has a 30th day.
        with self.assertRaises(ValueError):
            most_recent_firing("0 2 30 2 *", "standard-5", "Etc/UTC", _UTC_REF)


class TestTimezoneHandling(unittest.TestCase):
    def test_two_zones_same_instant_yield_different_firing_times(self):
        under_utc = most_recent_firing(
            "0 2 * * *", "standard-5", "Etc/UTC", _UTC_REF
        )
        under_tokyo = most_recent_firing(
            "0 2 * * *", "standard-5", "Asia/Tokyo", _UTC_REF
        )
        self.assertNotEqual(
            under_utc.astimezone(timezone.utc),
            under_tokyo.astimezone(timezone.utc),
        )

    def test_dst_transition_reference_computes_correct_instant(self):
        # America/New_York springs forward on 2027-03-14 (02:00 -> 03:00,
        # EST UTC-5 -> EDT UTC-4). A reference shortly after the transition,
        # on an hourly schedule, must resolve using the post-transition
        # offset rather than a fixed one.
        reference = datetime(2027, 3, 14, 8, 15, 0, tzinfo=timezone.utc)
        result = most_recent_firing(
            "0 * * * *", "standard-5", "America/New_York", reference
        )
        expected_utc = datetime(2027, 3, 14, 8, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(result.astimezone(timezone.utc), expected_utc)
        self.assertEqual(result.utcoffset().total_seconds(), -4 * 3600)


if __name__ == "__main__":
    unittest.main()
