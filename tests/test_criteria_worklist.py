#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Re-verification worklist partition — FEAT-2026-0056/T07."""

from __future__ import annotations

import unittest

from specfuse.loop.criteria_state import (
    CriterionStateEntry,
    build_reverification_worklist,
)


def _entry(criterion_id, kind=None, state=None, oracle=None, attempt=None):
    return CriterionStateEntry(
        criterion_id=criterion_id,
        criterion="some criterion text",
        oracle=oracle,
        kind=kind,
        state=state,
        proved_at_sha="deadbeef",
        attempt=attempt,
    )


class TestReverificationWorklist(unittest.TestCase):

    def test_narrow_pass_carries_forward(self):
        entries = [_entry("T01#1", kind="narrow", state="pass", oracle="cmd-a", attempt="1")]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual([e.criterion_id for e in result.carry_forward], ["T01#1"])
        self.assertEqual(result.reverify, [])

    def test_broad_pass_never_carries_forward(self):
        entries = [
            _entry("T01#1", kind="broad", state="pass", oracle="full-suite", attempt="2"),
            _entry("T02#1", kind="broad", state="pass", oracle="full-suite", attempt="1"),
        ]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(result.carry_forward, [])
        self.assertEqual(
            [e.criterion_id for e in result.reverify], ["T01#1", "T02#1"]
        )

    def test_narrow_fail_reverifies(self):
        entries = [_entry("T01#1", kind="narrow", state="fail", oracle="cmd-a", attempt="1")]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(result.carry_forward, [])
        self.assertEqual([e.criterion_id for e in result.reverify], ["T01#1"])

    def test_unverified_reverifies_regardless_of_kind(self):
        entries = [
            _entry("T01#1", kind="narrow", state="unverified", oracle="cmd-a", attempt="1"),
            _entry("T02#1", kind="broad", state="unverified", oracle="cmd-b", attempt="1"),
        ]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(result.carry_forward, [])
        self.assertEqual(
            [e.criterion_id for e in result.reverify], ["T01#1", "T02#1"]
        )

    def test_missing_or_unrecognized_kind_reverifies_without_raising(self):
        entries = [
            _entry("T01#1", kind=None, state="pass", oracle="cmd-a", attempt="1"),
            _entry("T02#1", kind="bogus", state="pass", oracle="cmd-b", attempt="1"),
        ]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(result.carry_forward, [])
        self.assertEqual(
            [e.criterion_id for e in result.reverify], ["T01#1", "T02#1"]
        )

    def test_partition_is_exact_and_preserves_order(self):
        entries = [
            _entry("T01#1", kind="narrow", state="pass", oracle="cmd-a", attempt="1"),
            _entry("T02#1", kind="broad", state="pass", oracle="full-suite", attempt="1"),
            _entry("T03#1", kind="narrow", state="fail", oracle="cmd-c", attempt="1"),
            _entry("T04#1", kind="narrow", state="pass", oracle="cmd-d", attempt="1"),
        ]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(len(result.carry_forward) + len(result.reverify), len(entries))
        carry_ids = {e.criterion_id for e in result.carry_forward}
        reverify_ids = {e.criterion_id for e in result.reverify}
        self.assertEqual(carry_ids & reverify_ids, set())
        self.assertEqual([e.criterion_id for e in result.carry_forward], ["T01#1", "T04#1"])
        self.assertEqual(
            [e.criterion_id for e in result.reverify], ["T02#1", "T03#1"]
        )

    def test_oracle_groups_identical_commands(self):
        entries = [
            _entry("T01#1", kind="narrow", state="fail", oracle="same-cmd", attempt="1"),
            _entry("T02#1", kind="narrow", state="fail", oracle="same-cmd", attempt="1"),
            _entry("T03#1", kind="broad", state="pass", oracle=None, attempt="1"),
        ]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(len(result.oracle_groups), 1)
        oracle_command, criterion_ids = result.oracle_groups[0]
        self.assertEqual(oracle_command, "same-cmd")
        self.assertEqual(criterion_ids, ["T01#1", "T02#1"])
        reverify_ids = [e.criterion_id for e in result.reverify]
        self.assertIn("T03#1", reverify_ids)

    def test_carry_forward_requires_nonempty_oracle_and_attempt(self):
        entries = [
            _entry("T01#1", kind="narrow", state="pass", oracle=None, attempt="1"),
            _entry("T02#1", kind="narrow", state="pass", oracle="cmd-a", attempt=None),
        ]
        result = build_reverification_worklist(entries, current_attempt="2")
        self.assertEqual(result.carry_forward, [])
        self.assertEqual(
            [e.criterion_id for e in result.reverify], ["T01#1", "T02#1"]
        )


if __name__ == "__main__":
    unittest.main()
