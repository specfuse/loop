# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A published CHANGELOG section is append-only-until-dated (#2727).

Five `fixed` entries were written into `[0.13.0+umbrella.0.13.0]` days after
that release was cut. `parse_changelog` reported `ok` throughout, because it
validates shape and all five entries were well-formed -- they were in the
wrong section, and section membership is not a property of one document.

The rule is on the SET OF TRACES per dated section, not on bytes: adding or
removing an entry is refused, editing prose or a heading is allowed. That
distinction was #2727's open question and it has a live case -- the
`0.13.0+umbrella.0.13.0` and `0.14.0+umbrella.0.14.0` headings name an
umbrella version that was never published (#2757), and correcting them must
not be blocked by the guard against the drift.
"""

from __future__ import annotations

import unittest

from specfuse.loop.changelog import parse_changelog, released_section_drift

_BASE = """## [Unreleased]

### Fixed

- something pending (#100)

## [1.1.0+umbrella.1.1.0] - 2026-02-01

### Added

- a feature (#20)

### Fixed

- a fix (#21)

## [1.0.0+umbrella.1.0.0] - 2026-01-01

### Fixed

- an older fix (#10)
"""


class TestTheDefectIsCaught(unittest.TestCase):
    def test_an_entry_appended_to_a_published_section_is_reported(self):
        head = _BASE.replace(
            "- a fix (#21)", "- a fix (#21)\n\n- snuck in after the tag (#22)")

        findings = released_section_drift(_BASE, head)

        self.assertEqual(len(findings), 1)
        self.assertIn("#22", findings[0])
        self.assertIn("1.1.0", findings[0])
        self.assertIn("Unreleased", findings[0])

    def test_the_same_entry_under_unreleased_is_fine(self):
        """The fix for the defect must not itself be reported."""
        head = _BASE.replace(
            "- something pending (#100)",
            "- something pending (#100)\n\n- snuck in after the tag (#22)")

        self.assertEqual(released_section_drift(_BASE, head), [])

    def test_every_added_entry_is_named_not_just_the_first(self):
        head = _BASE.replace(
            "- a fix (#21)",
            "- a fix (#21)\n\n- one (#22)\n\n- two (#23)")

        findings = released_section_drift(_BASE, head)

        self.assertEqual(len(findings), 2)
        self.assertTrue(any("#22" in f for f in findings))
        self.assertTrue(any("#23" in f for f in findings))

    def test_drift_across_two_published_sections_is_reported_for_both(self):
        head = _BASE.replace("- a fix (#21)", "- a fix (#21)\n\n- x (#22)")
        head = head.replace("- an older fix (#10)", "- an older fix (#10)\n\n- y (#11)")

        findings = released_section_drift(_BASE, head)

        self.assertEqual(len(findings), 2)


class TestLegitimateEditsAreAllowed(unittest.TestCase):
    """The open question from #2727, answered: adding is the defect, editing
    is not. A byte-level freeze would forbid both."""

    def test_rewording_a_published_entry_is_allowed(self):
        head = _BASE.replace("- a fix (#21)", "- a fix, described far better (#21)")

        self.assertEqual(released_section_drift(_BASE, head), [])

    def test_correcting_an_umbrella_coordinate_is_allowed(self):
        """The live #2757 case: the heading names an umbrella never released.

        Sections match on the driver version alone, so this reads as one
        section edited -- not one deleted and another added.
        """
        head = _BASE.replace(
            "## [1.1.0+umbrella.1.1.0] - 2026-02-01",
            "## [1.1.0+umbrella.1.0.0] - 2026-02-01")

        self.assertEqual(released_section_drift(_BASE, head), [])

    def test_fixing_a_typo_in_a_heading_date_is_allowed(self):
        head = _BASE.replace("- 2026-02-01", "- 2026-02-02")

        self.assertEqual(released_section_drift(_BASE, head), [])


class TestRemovalIsAlsoRefused(unittest.TestCase):
    def test_deleting_a_published_entry_is_reported(self):
        head = _BASE.replace("\n- a fix (#21)\n", "\n")

        findings = released_section_drift(_BASE, head)

        self.assertEqual(len(findings), 1)
        self.assertIn("#21", findings[0])
        self.assertIn("removed", findings[0])

    def test_deleting_a_whole_published_section_is_reported(self):
        head = _BASE.split("## [1.0.0")[0]

        findings = released_section_drift(_BASE, head)

        self.assertTrue(any("1.0.0" in f and "removed" in f for f in findings))


class TestCuttingAReleaseIsNotDrift(unittest.TestCase):
    """Stamping is the one sanctioned way a dated section appears."""

    def test_a_new_release_section_is_not_reported(self):
        head = _BASE.replace(
            "## [Unreleased]\n\n### Fixed\n\n- something pending (#100)\n",
            "## [Unreleased]\n\n## [1.2.0+umbrella.1.2.0] - 2026-03-01\n\n"
            "### Fixed\n\n- something pending (#100)\n",
        )
        self.assertIsNotNone(parse_changelog(head).unreleased())

        self.assertEqual(released_section_drift(_BASE, head), [])

    def test_the_real_repository_changelog_is_clean_against_itself(self):
        import pathlib
        text = (pathlib.Path(__file__).parent.parent / "CHANGELOG.md").read_text()

        self.assertEqual(released_section_drift(text, text), [])


class TestItNeverRaises(unittest.TestCase):
    """Same contract as the rest of the module: a checker that crashes cannot
    distinguish "found a problem" from "could not look"."""

    def test_empty_and_garbage_inputs_return_findings_not_exceptions(self):
        for base, head in (("", ""), ("", _BASE), (_BASE, ""), ("###", "not a changelog")):
            with self.subTest(base=base[:12], head=head[:12]):
                self.assertIsInstance(released_section_drift(base, head), list)


if __name__ == "__main__":
    unittest.main()
