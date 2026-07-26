#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the per-type planning-WU cost floors (issue #260).

§5's floors are set from a **population**, not from a feature. Across 158
closing WUs in 9 repositories, the cost of attempts that PASSED is:

    plan-next            n=62  first-try 74%  median $3.57  p90 $6.10
    close                n=61  first-try 69%  median $2.73  p90 $5.42
    close-intermediate   n=35  first-try 51%  median $2.01  p90 $4.34

Two earlier revisions of §5 each generalised from one feature — a flat $5.00
from FEAT-2026-0049, then $12.00/$8.00 from FEAT-2026-0069, whose plan-next
cost $16.44 (4.6x the population median). Both were outlier-driven. The floors
asserted here sit at roughly p90.

The improvement lever is NOT the floor: 28% of closing-WU spend goes to
attempts the driver refused, and three guards whose format requirements appear
in no authoring surface account for 45% of that waste.

Two things are asserted here, and the second is the load-bearing one:

1. Each surface states the corrected per-type floors.
2. **The two surfaces agree with each other.** §5 is the rule;
   `WU.template.md`'s frontmatter comment is what a drafting agent actually
   reads. A revision that changes one and not the other changes nothing in
   practice — which is exactly how the flat $5.00 survived FEAT-2026-0049
   producing the evidence against it.

The `.specfuse/` ↔ `specfuse/loop/data/` copy pairs are already guarded by
`tests/test_scaffold_data_in_sync.py`; this module does not re-assert that.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "planning-discipline.md"
_TEMPLATE = _REPO_ROOT / ".specfuse" / "templates" / "WU.template.md"

# The corrected floors: each at roughly the p90 of PASSING attempts across 158
# closing WUs in 9 repos (medians $3.57 / $2.73 / $2.01). An earlier revision of
# this file asserted $12.00/$8.00, derived from one outlier feature whose
# plan-next cost 4.6x the population median — see the module docstring.
EXPECTED_FLOORS = {"plan-next": "6.00", "close": "5.00", "close-intermediate": "4.50"}

# `$12.00` / `$8.00` adjacent to the WU type that carries it. Both surfaces are
# prose, so this matches the figure and the type name within one sentence rather
# than assuming a fixed layout.
_FLOOR_RE = re.compile(r"\$(\d+\.\d{2})")


def _norm(text: str) -> str:
    """Collapse whitespace so assertions survive prose line-wrapping."""
    return re.sub(r"\s+", " ", text)


def _floors_stated_in(path: Path) -> set[str]:
    """Every dollar figure the file presents as a planning-WU floor."""
    text = path.read_text(encoding="utf-8")
    return set(_FLOOR_RE.findall(text))


class TestPerTypeFloorsAreStated(unittest.TestCase):
    def test_rule_states_the_plan_next_floor(self):
        self.assertIn(f"${EXPECTED_FLOORS['plan-next']}", _RULE.read_text(encoding="utf-8"))

    def test_rule_states_the_close_floor(self):
        self.assertIn(f"${EXPECTED_FLOORS['close']}", _RULE.read_text(encoding="utf-8"))

    def test_template_states_the_plan_next_floor(self):
        self.assertIn(f"${EXPECTED_FLOORS['plan-next']}", _TEMPLATE.read_text(encoding="utf-8"))

    def test_template_states_the_close_floor(self):
        self.assertIn(f"${EXPECTED_FLOORS['close']}", _TEMPLATE.read_text(encoding="utf-8"))


class TestFlatFloorIsRetired(unittest.TestCase):
    """The flat $5.00 must not survive as a *floor* on either surface.

    It may still appear as historical provenance ("ran 2.8-5.2x their $2-3
    estimates"), so this asserts on the floor-setting phrasing specifically
    rather than banning the string outright.
    """

    def test_rule_no_longer_sets_a_flat_five_dollar_floor(self):
        text = _RULE.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"floor of \$5\.00")

    def test_template_no_longer_sets_a_flat_five_dollar_floor(self):
        text = _TEMPLATE.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"floor of \$5\.00")


class TestBothSurfacesAgree(unittest.TestCase):
    """The load-bearing guard.

    §5 is the rule; `WU.template.md`'s comment is the surface a drafting agent
    reads. If a future revision moves one figure and not the other, the rule
    says one thing and the template teaches another — and the template wins in
    practice, because it is what gets read at draft time. Issue #260 names this
    as the reason the flat $5.00 survived its own counter-evidence.
    """

    def test_rule_and_template_state_the_same_floor_figures(self):
        rule_floors = _floors_stated_in(_RULE)
        template_floors = _floors_stated_in(_TEMPLATE)
        for expected in EXPECTED_FLOORS.values():
            with self.subTest(floor=expected):
                self.assertIn(expected, rule_floors,
                              f"planning-discipline.md §5 does not state ${expected}")
                self.assertIn(expected, template_floors,
                              f"WU.template.md does not state ${expected}")

    def test_neither_surface_states_a_floor_the_other_omits(self):
        """Catches the asymmetric revision directly.

        Compares only figures in the floor set, so unrelated dollar amounts in
        provenance prose do not make this brittle.
        """
        floor_values = set(EXPECTED_FLOORS.values())
        rule = _floors_stated_in(_RULE) & floor_values
        template = _floors_stated_in(_TEMPLATE) & floor_values
        self.assertEqual(
            rule, template,
            "planning-discipline.md §5 and WU.template.md disagree on the "
            "planning-WU floors; a drafting agent reads the template, so an "
            "asymmetric revision silently keeps the old behaviour (#260)",
        )


class TestBudgetCorollaryIsStated(unittest.TestCase):
    def test_rule_states_the_budget_rule(self):
        text = _RULE.read_text(encoding="utf-8")
        self.assertRegex(
            text, r"(?i)re-?attempt",
            "§5 does not state how cost_budget_usd follows from the floors "
            "(sum of estimates plus one re-attempt of the largest WU)",
        )


class TestRetryIsFramedAsADefect(unittest.TestCase):
    """The floors must not be presented as absorbing a second attempt.

    This is the guard against the correction being un-corrected. The obvious
    reading of "closing WUs often retry" is "raise the floor until it covers
    the retry" — which makes 28% of closing spend invisible and permanent, and
    is how the previous revision reached $12.00. Both surfaces must state the
    opposite: a retry is a defect to diagnose.
    """

    def test_rule_frames_retry_as_a_defect(self):
        text = _RULE.read_text(encoding="utf-8")
        self.assertRegex(_norm(text), r"(?i)defect to diagnose, not a cost to budget for")

    def test_template_warns_against_raising_floors_to_absorb_a_retry(self):
        text = _TEMPLATE.read_text(encoding="utf-8")
        self.assertRegex(_norm(text), r"(?i)defect to diagnose, not a cost to budget for")


if __name__ == "__main__":
    unittest.main()
