#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Per-criterion close state schema/parser/renderer — FEAT-2026-0056/T01."""

from __future__ import annotations

import unittest

from specfuse.loop.criteria_state import (
    CRITERION_STATES,
    ORACLE_KINDS,
    criterion_id_for,
    parse_criteria_state,
    render_criteria_state,
)

FIXTURE = """\
### T03#2

- **criterion:** `specfuse lint --closing` exits 0 on a legacy close with no artifact
- **oracle:** `python3 -m unittest tests.test_lint_closing_criteria -v`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `85c36e8803932c7e358780b8524cff22eaf62846`
- **attempt:** `2`

### T02#1

- **criterion:** the full suite passes
- **oracle:** `python3 -m unittest discover -s tests -v -b`
- **kind:** `broad`
- **state:** `pass`
- **proved_at_sha:** `85c36e8803932c7e358780b8524cff22eaf62846`
- **attempt:** `2`

### T01#3

- **criterion:** an entry missing kind still parses
- **oracle:** `python3 -m unittest tests.test_criteria_state -v`
- **state:** `unverified`
- **proved_at_sha:** `85c36e8803932c7e358780b8524cff22eaf62846`
- **attempt:** `1`
"""


class TestSchema(unittest.TestCase):

    def test_oracle_kinds(self):
        self.assertEqual(ORACLE_KINDS, frozenset({"narrow", "broad"}))

    def test_criterion_states(self):
        self.assertEqual(CRITERION_STATES, frozenset({"pass", "fail", "unverified"}))

    def test_criterion_id_for(self):
        self.assertEqual(criterion_id_for("T03", 2), "T03#2")


class TestParse(unittest.TestCase):

    def test_parse_document_order(self):
        entries = parse_criteria_state(FIXTURE)
        self.assertEqual(
            [e.criterion_id for e in entries], ["T03#2", "T02#1", "T01#3"]
        )

    def test_missing_field_is_none(self):
        entries = parse_criteria_state(FIXTURE)
        missing_kind = next(e for e in entries if e.criterion_id == "T01#3")
        self.assertIsNone(missing_kind.kind)
        self.assertEqual(missing_kind.state, "unverified")


class TestRoundTrip(unittest.TestCase):

    def test_parse_round_trips_render(self):
        entries = parse_criteria_state(FIXTURE)
        kinds_present = {e.kind for e in entries if e.kind is not None}
        self.assertIn("narrow", kinds_present)
        self.assertIn("broad", kinds_present)
        self.assertTrue(any(e.kind is None for e in entries))

        rendered = render_criteria_state(entries)
        round_tripped = parse_criteria_state(rendered)
        self.assertEqual(entries, round_tripped)


if __name__ == "__main__":
    unittest.main()
