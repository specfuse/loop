#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Consistency check for the retain-and-repair docs (FEAT-2026-0103/T04).

Pure documentation change (§12 red-test exemption applies) — this asserts the
shape the docs must have, not any driver behaviour.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLE = (
    _REPO_ROOT / "specfuse" / "loop" / "data" / "verification.yml.example"
)
_METHODOLOGY = _REPO_ROOT / "docs" / "methodology.md"

_OUTCOMES = (
    "deliverable_missing",
    "no_deliverable_files",
    "produces_not_in_diff",
    "files_changed_mismatch",
)


class TestVerificationExampleDocumentsDefault(unittest.TestCase):
    def test_defaults_block_names_the_key_and_all_four_outcomes(self):
        text = _EXAMPLE.read_text(encoding="utf-8")
        self.assertRegex(
            text, r"defaults:\n(?:.*\n){0,10}?.*retain_on_guard_refusal:",
            "verification.yml.example has no `defaults:` block containing "
            "retain_on_guard_refusal",
        )
        for outcome in _OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertIn(
                    outcome, text,
                    f"verification.yml.example's retain_on_guard_refusal "
                    f"comment does not name {outcome!r}",
                )


class TestMethodologyDocumentsRetainAndRepair(unittest.TestCase):
    def _section(self) -> str:
        text = _METHODOLOGY.read_text(encoding="utf-8")
        start = text.find("### Per-attempt outcome events")
        self.assertGreaterEqual(
            start, 0, "methodology.md has no per-attempt outcome section")
        end = text.find("\n### ", start + 1)
        return text[start:end if end > 0 else len(text)]

    def test_section_mentions_tree_retained(self):
        self.assertIn("tree_retained", self._section())

    def test_section_mentions_auto_repaired_files_changed(self):
        self.assertIn("auto_repaired_files_changed", self._section())


if __name__ == "__main__":
    unittest.main()
