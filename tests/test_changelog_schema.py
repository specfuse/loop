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

    # The one-time since-v0.8.0 exception, frozen. FEAT-2026-0064 shipped this
    # file mid-release-cycle, so the v0.9.0 release would otherwise document
    # only the feature that built the document — while two changes in that same
    # release BREAK a downstream project on upgrade (`close-k` fails a close on
    # a project with no root CHANGELOG.md; `event-type-gate` widened from one
    # field to the whole envelope). Those were backfilled from each feature's
    # RETROSPECTIVE.md § "Consumer-visible contract changes" — the enumeration
    # its close was already required to write — never from commit subjects.
    #
    # This set is a grandfather list, NOT a relaxation. It is pinned to the
    # v0.9.0 released section below for EXACT equality, so the historical block
    # can never grow a 26th entry. Do not add to it: the collection points (the
    # close ceremony, `fix-bug`) are the only way into any later release.
    _V090_SECTION = "0.9.0+umbrella.0.9.0"
    _GRANDFATHERED_SINCE_V080 = {
        "#259", "#280", "#314", "#360", "#465", "#519", "#562",
        "FEAT-2026-0034", "FEAT-2026-0034/T02",
        "FEAT-2026-0041", "FEAT-2026-0041/T01", "FEAT-2026-0041/T03",
        "FEAT-2026-0042", "FEAT-2026-0042/T02", "FEAT-2026-0042/T03",
        "FEAT-2026-0059", "FEAT-2026-0059/T01",
        "FEAT-2026-0060", "FEAT-2026-0061", "FEAT-2026-0062",
        "FEAT-2026-0063/T01", "FEAT-2026-0063/T02",
        "FEAT-2026-0068",
        "FEAT-2026-0073", "FEAT-2026-0073/T01", "FEAT-2026-0073/T02",
    }

    def test_frozen_exception_entries_all_remain(self):
        """No grandfathered entry may vanish from the document.

        The exception cannot be quietly widened by editing the list instead of
        the file, nor narrowed by deleting inconvenient history.
        """
        result = parse_changelog((REPO_ROOT / "CHANGELOG.md").read_text())
        present = {e.trace for s in result.sections for e in s.entries}
        self.assertEqual(
            self._GRANDFATHERED_SINCE_V080 - present,
            set(),
            "grandfathered since-v0.8.0 entries went missing",
        )

    def test_v090_section_holds_exactly_the_frozen_exception(self):
        """The one release carrying backfill is pinned, entry for entry.

        Scoped to the v0.9.0 section by version, not to "released sections" at
        large: stamping moves EVERY entry into a released section, so position
        cannot distinguish a backfilled entry from a forward-collected one, and
        a released-sections-wide rule would fail every future release. Nothing
        constrains v0.10.0 and later -- they have collection points, which is
        the whole point of FEAT-2026-0064.

        `#562` is in the frozen set but is not backfill: it is the first entry
        the `fix-bug` collection point ever appended, and it landed before the
        stamp. The set pins what v0.9.0 shipped; the comment above records
        which part of it was the exception.
        """
        result = parse_changelog((REPO_ROOT / "CHANGELOG.md").read_text())
        section = next(
            (s for s in result.sections if s.version == self._V090_SECTION), None
        )
        self.assertIsNotNone(section, f"no {self._V090_SECTION} section found")
        found = {
            e.trace
            for e in section.entries
            if not e.trace.startswith("FEAT-2026-0064")
        }
        self.assertEqual(
            found,
            self._GRANDFATHERED_SINCE_V080,
            "the v0.9.0 released section drifted from its frozen contents",
        )

    def test_shipped_changelog_explains_no_backfill_before_first_entry(self):
        text = (REPO_ROOT / "CHANGELOG.md").read_text()
        comment_pos = text.find("No backfill")
        first_entry_pos = text.find("## [Unreleased]")
        self.assertNotEqual(comment_pos, -1, "no 'No backfill' explanation found")
        self.assertLess(comment_pos, first_entry_pos)


if __name__ == "__main__":
    unittest.main()
