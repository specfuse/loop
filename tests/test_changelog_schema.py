#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0064/T01: schema tests for CHANGELOG.md's parser.

Covers the WU's acceptance criteria 1-7: trace enforcement, the four entry
classes, Unreleased-vs-released distinguishability, malformed input never
raising, the shipped CHANGELOG.md parsing clean, and no backfilled entries.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from specfuse.loop.changelog import ENTRY_CLASSES, parse_changelog

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestChangelogSchema(unittest.TestCase):
    # -- criteria 1/2: trace enforcement --

    def test_entry_without_a_trace_is_rejected(self):
        text = (
            "## [Unreleased]\n"
            "### Added\n"
            "- did a thing with no trace\n"
        )
        result = parse_changelog(text)
        self.assertTrue(result.findings)
        self.assertTrue(
            any("trace" in f for f in result.findings), result.findings,
        )
        self.assertEqual(result.unreleased().entries, [])

    def test_entry_with_feat_id_trace_is_accepted(self):
        text = (
            "## [Unreleased]\n"
            "### Added\n"
            "- did a thing (FEAT-2026-0064/T01)\n"
        )
        result = parse_changelog(text)
        self.assertEqual(result.findings, [])
        entries = result.unreleased().entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].trace, "FEAT-2026-0064/T01")

    def test_entry_with_issue_number_trace_is_accepted(self):
        text = (
            "## [Unreleased]\n"
            "### Fixed\n"
            "- fixed a thing (#473)\n"
        )
        result = parse_changelog(text)
        self.assertEqual(result.findings, [])
        entries = result.unreleased().entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].trace, "#473")

    # -- criterion 3: the four entry classes --

    def test_each_legal_class_parses(self):
        for cls in ENTRY_CLASSES:
            with self.subTest(cls=cls):
                text = (
                    "## [Unreleased]\n"
                    f"### {cls.capitalize()}\n"
                    f"- an entry (FEAT-2026-0064/T01)\n"
                )
                result = parse_changelog(text)
                self.assertEqual(result.findings, [])
                entries = result.unreleased().entries
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0].entry_class, cls)

    def test_unrecognised_class_is_a_finding_naming_four_legal_values(self):
        text = (
            "## [Unreleased]\n"
            "### Removed\n"
            "- an entry (FEAT-2026-0064/T01)\n"
        )
        result = parse_changelog(text)
        self.assertTrue(result.findings)
        finding = result.findings[0]
        for cls in ENTRY_CLASSES:
            self.assertIn(cls, finding)

    # -- criterion 4: Unreleased vs released --

    def test_unreleased_distinguishable_from_released(self):
        text = (
            "## [Unreleased]\n"
            "### Added\n"
            "- pending (FEAT-2026-0064/T01)\n"
            "## [0.9.0] - 2026-09-01\n"
            "### Fixed\n"
            "- shipped (#100)\n"
        )
        result = parse_changelog(text)
        self.assertEqual(result.findings, [])
        self.assertEqual(len(result.sections), 2)
        unreleased, released = result.sections
        self.assertTrue(unreleased.is_unreleased)
        self.assertFalse(released.is_unreleased)

    def test_released_section_version_and_date_readable(self):
        text = (
            "## [0.9.0] - 2026-09-01\n"
            "### Fixed\n"
            "- shipped (#100)\n"
        )
        result = parse_changelog(text)
        self.assertEqual(result.findings, [])
        released = result.sections[0]
        self.assertEqual(released.version, "0.9.0")
        self.assertEqual(released.date, "2026-09-01")

    # -- criterion 5: malformed input produces findings, never raises --

    def test_truncated_file_produces_finding_not_traceback(self):
        # No try/except: parse_changelog is guaranteed never to raise. A
        # crash here is a real test failure, not something to catch.
        text = (
            "## [Unreleased]\n"
            "### Added\n"
            "- an entry that trails off with no closing trace paren"
        )
        result = parse_changelog(text)
        self.assertTrue(result.findings)

    def test_section_with_no_entries_produces_finding_not_traceback(self):
        text = "## [Unreleased]\n## [0.9.0] - 2026-09-01\n"
        result = parse_changelog(text)
        self.assertTrue(result.findings)
        self.assertTrue(any("no entries" in f for f in result.findings))

    def test_entry_under_no_section_heading_produces_finding_not_traceback(self):
        text = "### Added\n- an entry (FEAT-2026-0064/T01)\n"
        result = parse_changelog(text)
        self.assertTrue(result.findings)
        self.assertEqual(result.sections, [])

    # -- criterion 6: the shipped document satisfies its own schema --

    def test_shipped_changelog_parses_clean_and_has_unreleased(self):
        text = (REPO_ROOT / "CHANGELOG.md").read_text()
        result = parse_changelog(text)
        self.assertEqual(result.findings, [])
        self.assertIsNotNone(result.unreleased())

    # -- criterion 7: no backfill --

    def test_shipped_changelog_has_no_pre_feature_entries(self):
        text = (REPO_ROOT / "CHANGELOG.md").read_text()
        result = parse_changelog(text)
        for section in result.sections:
            for entry in section.entries:
                self.assertTrue(
                    entry.trace.startswith("FEAT-2026-0064"),
                    f"unexpected backfilled entry: {entry.trace}",
                )

    def test_shipped_changelog_explains_no_backfill_before_first_entry(self):
        text = (REPO_ROOT / "CHANGELOG.md").read_text()
        comment_pos = text.find("No backfill")
        first_entry_pos = text.find("## [Unreleased]")
        self.assertNotEqual(comment_pos, -1, "no 'No backfill' explanation found")
        self.assertLess(comment_pos, first_entry_pos)


if __name__ == "__main__":
    unittest.main()
