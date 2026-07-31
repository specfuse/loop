#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the plan_next_lint veto class (FEAT-2026-0053/T07).

Reuses tests.test_arm_eval's fixture builders — a `_base_feature` with WU-05
flipped to `draft` status is exactly the plan-next-just-produced-a-draft-WU
shape `lint_plan_next_draft` inspects. `_base_feature`'s WU-05 defaults are
already clean under the lint's own checks (well-formed id, positive
planned_cost_usd, valid type, five mandatory sections), so the clean-path
test needs no extra fixture surgery beyond the status flip.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import _miniyaml
from specfuse.loop.arm_eval import CLASS_NAMES, VETO_CLASSES, evaluate_arm_predicate

from tests.test_arm_eval import _base_feature, _write

_MANDATORY_SECTIONS = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _draft_wu(feature: Path, filename: str, title: str, fm_lines: list) -> None:
    """Like tests.test_arm_eval._wu, but with the five mandatory sections
    `lint_plan_next_draft` requires on any `draft`-status WU."""
    fm = "\n".join(fm_lines)
    _write(feature / filename, f"---\n{fm}\n---\n\n# {title}{_MANDATORY_SECTIONS}")


class TestPlanNextLintClass(unittest.TestCase):
    def test_findings_block_arm_under_auto(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            # Draft WU missing planned_cost_usd — the T06-fixture failure
            # mode this WU's scope note calls out.
            _draft_wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: draft",
                "cost_usd: 0.0",
                "produces: [some/new/file.py]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["plan_next_lint"].status, "fired")
            self.assertIn(
                "missing 'planned_cost_usd' frontmatter",
                decision.classes["plan_next_lint"].reason,
            )
            self.assertFalse(decision.would_arm)

    def test_clean_draft_does_not_block_by_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            _draft_wu(feature, "WU-05.md", "Do T05", [
                "type: implementation", "status: draft",
                "cost_usd: 0.0", "planned_cost_usd: 1.0",
                "produces: [some/new/file.py]",
                "provenance: RETRO-1",
            ])
            decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["plan_next_lint"].status, "clean")
            self.assertTrue(decision.would_arm, decision.classes)

    def test_unparseable_review_frontmatter_fires_not_raises(self):
        # `lint_plan_next_draft` itself can raise MiniYAMLError when a
        # GATE-{N+1}-REVIEW.md's frontmatter is malformed (the 26th
        # empirical finding from G1-PLAN's corpus sweep: a raise, not a
        # verdict). Simulated via mock rather than a real malformed fixture
        # file, because arm_eval's own class 7 (open_questions_human_only,
        # untouched by this WU) parses the same review file with its own
        # frontmatter reader and would raise first — a pre-existing gap
        # outside this WU's scope. This isolates class 8's own degradation.
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            _base_feature(feature)
            with mock.patch(
                "specfuse.loop.lint_plan.lint_plan_next_draft",
                side_effect=_miniyaml.MiniYAMLError("line 1: unterminated double-quoted string"),
            ):
                decision = evaluate_arm_predicate(feature, 1)
            self.assertEqual(decision.classes["plan_next_lint"].status, "fired")
            self.assertIn("MiniYAMLError", decision.classes["plan_next_lint"].reason)
            self.assertFalse(decision.would_arm)

    def test_class_registered_in_names_and_veto(self):
        self.assertIn("plan_next_lint", CLASS_NAMES)
        self.assertIn("plan_next_lint", VETO_CLASSES)


if __name__ == "__main__":
    unittest.main()
