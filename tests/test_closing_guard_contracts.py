#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Binds `close-discipline.md` §4 to the guards it documents (issue #265).

Closing-WU guards enforce exact string formats — a heading level, a filename,
a frontmatter field. Until §4 existed those requirements were discoverable only
by reading `loop.py` or by paying for a refusal, and the refusal costs a full
re-dispatch because the guard runs *after* the WU has produced its work.

Measured across 158 closing WUs in 9 repositories: **28% of all closing-WU
spend went to refused attempts**, and three guards documented in no authoring
surface accounted for 45% of that waste —

    assert_gate_review_exists                             15 fires  $53.11
    assert_failure_class_breakdown_when_failures_present  10 fires  $23.70
    assert_retrospective_gate_section                      7 fires  $22.49

against `assert_verdict_well_formed` at 10 fires and **$0.00**, because it is
checked before the agent spends anything.

**The guard source is the single source of truth here, not this test and not
the doc.** Each case below extracts the literal the guard actually uses out of
`loop.py`, then asserts the doc states it. So:

  - a guard that changes its literal fails extraction — the test tells you the
    doc is now wrong, rather than the doc silently lying;
  - a doc that drops a literal fails the membership assertion.

Adding a third hand-maintained copy of these strings would have reproduced the
drift the section exists to prevent.
"""

from __future__ import annotations

import inspect
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
    self_check = start >= 0
    assert self_check, "close-discipline.md has no '## 4. What the driver checks' section"
    end = text.find("\n## ", start + 1)
    return re.sub(r"\s+", " ", text[start:end if end > 0 else len(text)])


def _src(fn_name: str) -> str:
    fn = getattr(loop, fn_name)
    return inspect.getsource(fn)


# Guards whose contract is a literal an author must reproduce. The second
# element extracts that literal FROM the guard's own source; the third is a
# human label for the failure message.
_LITERAL_GUARDS = [
    (
        "assert_cost_analysis_section_when_met",
        lambda s: re.search(r'\^##\+ (Cost analysis)', s),
        "the '## Cost analysis' heading",
    ),
    (
        "assert_failure_class_breakdown_when_failures_present",
        lambda s: re.search(r'\^#\{3\} (Failure-class breakdown)', s),
        "the '### Failure-class breakdown' heading",
    ),
    (
        "assert_learnings_appended_or_noop",
        lambda s: re.search(r'"(nothing generalizes)"', s),
        "the 'nothing generalizes' no-op phrase",
    ),
]


class TestGuardLiteralsAreDocumented(unittest.TestCase):
    def test_each_literal_guard_states_its_string_in_the_doc(self):
        doc = _doc()
        for fn_name, extract, label in _LITERAL_GUARDS:
            with self.subTest(guard=fn_name):
                m = extract(_src(fn_name))
                self.assertIsNotNone(
                    m,
                    f"{fn_name} no longer contains the literal this test extracts — "
                    f"close-discipline.md §4 is now describing a guard that changed",
                )
                literal = m.group(1)
                self.assertIn(
                    literal, doc,
                    f"close-discipline.md §4 does not state {label} "
                    f"({literal!r}), which {fn_name} enforces",
                )

    def test_gate_section_heading_depth_is_documented(self):
        """`^#{1,3} Gate N` — the depth range matters and is easy to get wrong."""
        src = _src("assert_retrospective_gate_section")
        self.assertRegex(src, r"\^#\{\{1,3\}\} Gate", "guard's heading pattern changed")
        self.assertIn("#{1,3} Gate", _doc(),
                      "§4 does not state the accepted heading depths for the gate section")

    def test_gate_review_filename_offset_is_documented(self):
        """The +1 offset is the most expensive surprise in the system (#261)."""
        src = _src("assert_gate_review_exists")
        self.assertRegex(
            src, r"gate_n\s*\+\s*1",
            "assert_gate_review_exists no longer computes the next gate's number",
        )
        doc = _doc()
        self.assertIn("GATE-{N+1}-REVIEW.md", doc,
                      "§4 does not state that the review artifact is named for the NEXT gate")

    def test_verdict_values_are_documented(self):
        for value in sorted(loop.VERDICT_VALUES):
            with self.subTest(verdict=value):
                self.assertIn(value, _doc(),
                              f"§4 does not list the accepted verdict {value!r}")


class TestEveryClosingGuardIsListed(unittest.TestCase):
    """Completeness: a new closing guard must be documented when it is added.

    The `(close-x)` / `(close-intermediate-x)` / `(plan-next-x)` docstring tags
    are the code's own marker for "this is a closing-WU guard". Any function
    carrying one must appear by name in §4, so adding a guard without
    documenting it fails here rather than in someone's dispatch budget.
    """

    _TAG = re.compile(r"\((close|close-intermediate|plan-next)-[a-z]\)")

    def _closing_guards(self) -> list[str]:
        found = []
        for name in dir(loop):
            if not name.startswith("assert_"):
                continue
            fn = getattr(loop, name)
            doc = inspect.getdoc(fn) or ""
            if self._TAG.search(doc):
                found.append(name)
        return sorted(found)

    def test_the_tag_convention_still_finds_guards(self):
        """Guards against the completeness test silently matching nothing."""
        self.assertGreaterEqual(
            len(self._closing_guards()), 8,
            "the (close-x)/(plan-next-x) docstring tag convention appears to have "
            "changed; this test would otherwise pass vacuously",
        )

    def test_every_tagged_closing_guard_appears_in_the_doc(self):
        doc = _doc()
        for name in self._closing_guards():
            with self.subTest(guard=name):
                self.assertIn(
                    name, doc,
                    f"{name} is a closing-WU guard but close-discipline.md §4 does "
                    f"not document what it requires — the gap #265 measured at 45% "
                    f"of all closing-WU waste",
                )


if __name__ == "__main__":
    unittest.main()
