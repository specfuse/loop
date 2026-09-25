#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Work units whose deliverable is a validated tree (#3407).

A repository whose deliverable IS a spec tree runs the loop with work units that
author spec files. Those units fail differently from code units, and the rules
did not say how, so a consuming project decomposed them the way code units are
decomposed and lost the money twice:

    gate 2 — parent entity and children in separate WUs   $5.37, files_touched: []
    WU-04  — entity reshaped without its snapshot        $29.30, 6 refused, abandoned

Neither was an ordinary authoring mistake. Both were toolchain atomicity
constraints: a child's `belongsTo` needs the parent's `hasMany` in the same
unit, and every snapshot field is validated against the entity its label names.
Split them and the unit cannot pass, because the tree cannot validate in
between.

Two rules came out of it, and neither is specific to specs. "No work unit
leaves the shared artifact broken" and "a structural assertion replaces the red
test where there is no test framework" hold for any repository whose deliverable
is a validated tree — a spec bundle, a Terraform plan, a schema registry. That
is why they belong in the work-unit contract rather than in a section of their
own, and it is what this guard pins.

The §12 half matters most. A spec repo has no unit-test framework, so the
existing "Skip when" list would swallow these units under `Red-test exempt: no
test framework` — quietly removing the loop's cheapest hollow-pass guard for a
whole class of repository. The answer is a SUBSTITUTE, not an exemption.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "plugins/specfuse/skills/authoring-work-units/SKILL.md"
MIRROR = REPO_ROOT / ".specfuse/skills/authoring-work-units/SKILL.md"
METHODOLOGY = REPO_ROOT / "docs/methodology.md"
VENDORED_METHODOLOGY = REPO_ROOT / "specfuse/loop/data/docs/methodology.md"


def _section(text: str, number: int) -> str:
    match = re.search(
        rf"^## {number}\. .*?$(.*?)(?=^## )", text, re.S | re.M)
    assert match, f"the authoring skill has no '## {number}.' section"
    return match.group(1)


class TheSpecFrontEndRowIsThreeValued(unittest.TestCase):
    """§10's loop column could not express "the spec tree is the deliverable"."""

    def _row(self) -> str:
        for line in METHODOLOGY.read_text(encoding="utf-8").splitlines():
            if line.startswith("| Spec front-end"):
                return line
        self.fail("docs/methodology.md has no 'Spec front-end' row in §10")

    def test_the_loop_column_names_all_three_modes(self):
        row = self._row().lower()

        for mode in ("none", "consumed", "authored"):
            self.assertIn(
                mode, row,
                f"the loop's spec front-end has three modes and {mode!r} is "
                f"missing — a repository whose deliverable is the spec tree is "
                f"neither 'optional' nor 'authored directly' (#3407)",
            )

    def test_the_authored_mode_says_work_units_author_spec_files(self):
        self.assertIn("deliverable", self._row().lower())

    def test_the_vendored_copy_agrees(self):
        self.assertEqual(
            METHODOLOGY.read_text(encoding="utf-8"),
            VENDORED_METHODOLOGY.read_text(encoding="utf-8"),
            "docs/methodology.md and its specfuse/loop/data/ copy diverged — "
            "run scripts/sync-scaffold.sh",
        )


class TheWholeTreeMustValidate(unittest.TestCase):
    """§6 — the constraint that cuts the opposite way from sizing."""

    def test_section_6_says_a_unit_leaves_the_tree_validating(self):
        body = _section(SKILL.read_text(encoding="utf-8"), 6).lower()

        self.assertIn("validat", body)
        self.assertTrue(
            "indivisible" in body or "cannot be split" in body
            or "one unit" in body,
            "§6 measures whether a unit is small enough. Some units are "
            "INDIVISIBLE regardless of size, because the shared artifact "
            "cannot validate in between — that is the half §6 was missing "
            "(#3407)",
        )

    def test_it_names_why_a_partial_state_is_not_available(self):
        body = _section(SKILL.read_text(encoding="utf-8"), 6).lower()

        self.assertTrue(
            "failing test" in body or "partial" in body,
            "the rule only lands if it says what a code WU may do that one of "
            "these may not: leave a partial state for the next unit",
        )


class TheRedTestGetsASubstituteNotAnExemption(unittest.TestCase):
    """§12 — the half most likely to be got wrong."""

    def test_section_12_refuses_no_test_framework_as_an_exemption(self):
        # Asserted on what the section SAYS, not on the absence of a string:
        # the prose quotes `Red-test exempt: no test framework` precisely in
        # order to rule it out, so a naive "must not appear" check fails on
        # correct prose. A first version of this test did exactly that.
        body = _section(SKILL.read_text(encoding="utf-8"), 12).lower()

        self.assertIn("no test framework", body, "the case must be named")
        self.assertTrue(
            "not one of those reasons" in body or "takes a substitute" in body,
            "§12 must say that having no test framework does not earn an "
            "exemption — it earns a substitute. An exemption removes the "
            "cheapest hollow-pass guard for a whole class of repository "
            "(#3407)",
        )
        self.assertIn(
            "red-test substitute", body,
            "the section must name what an author writes instead",
        )

    def test_it_points_at_the_structural_assertion_instead(self):
        body = _section(SKILL.read_text(encoding="utf-8"), 12).lower()

        self.assertIn("structural assertion", body)
        self.assertIn("§9", _section(SKILL.read_text(encoding="utf-8"), 12))


class TheStructuralAssertionIsSpelledOut(unittest.TestCase):
    """§9 — already the right shape; it needed the tree case naming."""

    def test_section_9_covers_identifiers_resolving_in_a_rebuilt_artifact(self):
        body = _section(SKILL.read_text(encoding="utf-8"), 9).lower()

        self.assertIn("structural assertion", body)
        self.assertTrue(
            "regenerat" in body or "rebuil" in body or "bundle" in body,
            "the substitute has to assert the identifiers resolve in the "
            "REGENERATED artifact — asserting them in the source files the WU "
            "just wrote is the hollow pass this section exists to stop",
        )

    def test_it_keeps_the_blocked_trigger(self):
        body = _section(SKILL.read_text(encoding="utf-8"), 9)

        self.assertIn("status: blocked", body)


class TheMirrorAgrees(unittest.TestCase):

    def test_the_scaffold_copy_matches(self):
        self.assertEqual(
            SKILL.read_text(encoding="utf-8"),
            MIRROR.read_text(encoding="utf-8"),
            "plugins/ and .specfuse/ copies diverged — run "
            "scripts/sync-scaffold.sh",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
