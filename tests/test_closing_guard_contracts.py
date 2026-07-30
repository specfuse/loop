#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Binds `close-discipline.md` §4 to the mechanical surfaces it points at
(issue #265, FEAT-2026-0054).

§4 used to restate every closing guard's literal string inline — a table
that was itself a second, hand-maintained copy of `closing_requirements.py`
and drifted from it. FEAT-2026-0054 replaced the table with two mechanical
surfaces (the pre-created dispatch skeleton, and `specfuse-lint --closing`
as the mandatory pre-report check) and made `closing_requirements.py` the
one registry both the driver's guards and the lint read.

This test now checks the doc still points at the real things: the actual
function name that pre-creates the skeleton, the actual registry module,
and the actual lint module — so a rename of any of those fails this test
instead of silently stranding the doc. It also checks the guard-literal
table does NOT come back (the regression this WU exists to fix), and that
the completeness binding between guard code and its registry — not this
doc — is covered by `test_closing_requirements.py`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from specfuse.loop import loop

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "close-discipline.md"


def _doc() -> str:
    """§4's text, whitespace-collapsed so assertions survive line-wrapping."""
    text = _RULE.read_text(encoding="utf-8")
    start = text.find("## 4. What the driver checks")
    assert start >= 0, "close-discipline.md has no '## 4. What the driver checks' section"
    end = text.find("\n## ", start + 1)
    return re.sub(r"\s+", " ", text[start:end if end > 0 else len(text)])


class TestSectionFourPointsAtRealSurfaces(unittest.TestCase):
    def test_names_the_real_skeleton_precreation_function(self):
        self.assertTrue(
            hasattr(loop, "precreate_dispatch_skeleton"),
            "loop.py no longer defines precreate_dispatch_skeleton — §4 names "
            "a function that has moved or been renamed",
        )
        self.assertIn(
            "precreate_dispatch_skeleton", _doc(),
            "§4 does not name the function that pre-creates the closing skeleton",
        )

    def test_names_the_registry_module(self):
        registry_path = _REPO_ROOT / "specfuse" / "loop" / "closing_requirements.py"
        self.assertTrue(registry_path.exists(), "closing_requirements.py registry is missing")
        self.assertIn(
            "closing_requirements.py", _doc(),
            "§4 does not point at closing_requirements.py as the registry of record",
        )

    def test_names_the_lint_command(self):
        lint_path = _REPO_ROOT / "specfuse" / "loop" / "lint_closing.py"
        self.assertTrue(lint_path.exists(), "lint_closing.py is missing")
        self.assertIn(
            "specfuse-lint --closing", _doc(),
            "§4 does not tell the author to run `specfuse-lint --closing` before reporting",
        )

    def test_does_not_reintroduce_the_literal_guard_table(self):
        doc = _doc()
        for guard_name in (
            "assert_retrospective_exists",
            "assert_cost_analysis_section_when_met",
            "assert_gate_review_exists",
            "assert_verdict_well_formed",
        ):
            self.assertNotIn(
                guard_name, doc,
                f"{guard_name} reappeared in §4 — this section documents the two "
                f"mechanical surfaces (skeleton + lint), not a per-guard literal "
                f"table; that table is what drifted and was removed",
            )


if __name__ == "__main__":
    unittest.main()
