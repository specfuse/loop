#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests that PLAN.template.md and WU.template.md use the new closing shapes
introduced in FEAT-2026-0015 (close-intermediate + plan-next for non-terminal
gates; close for terminal gates).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_TEMPLATE = REPO_ROOT / ".specfuse" / "templates" / "PLAN.template.md"
WU_TEMPLATE = REPO_ROOT / ".specfuse" / "templates" / "WU.template.md"


class TestPlanTemplateClosingShapes(unittest.TestCase):

    def _plan_template_text(self) -> str:
        return PLAN_TEMPLATE.read_text()

    def test_plan_template_uses_2wu_intermediate_for_gate_1(self):
        """Gate 1 in PLAN.template.md must include close-intermediate + plan-next."""
        text = self._plan_template_text()
        # Must mention close-intermediate as a WU type
        self.assertIn("close-intermediate", text,
                      "PLAN.template.md must reference close-intermediate WU type")
        # The canonical file name for the close-intermediate WU
        self.assertIn("WU-90-gate-1-close-intermediate.md", text,
                      "PLAN.template.md must reference WU-90-gate-1-close-intermediate.md")
        # G1-CLOSE-INTERMEDIATE correlation ID
        self.assertIn("G1-CLOSE-INTERMEDIATE", text,
                      "PLAN.template.md must use G1-CLOSE-INTERMEDIATE as the closing WU ID")
        # plan-next WU immediately after
        self.assertIn("WU-91-gate-1-plan-next.md", text,
                      "PLAN.template.md must reference WU-91-gate-1-plan-next.md")
        self.assertIn("G1-PLAN", text,
                      "PLAN.template.md must include G1-PLAN (plan-next) WU")

    def test_plan_template_uses_1wu_close_for_terminal_gate(self):
        """PLAN.template.md must NOT use the legacy 4-WU closing sequence as default.

        The template shows gate 2 with work_units: [] (drafted by plan-next),
        meaning gate 2 is terminal and gets a single close WU when eventually
        populated. The template should not list RETRO/LESSONS/DOCS as the
        default closing sequence.
        """
        text = self._plan_template_text()
        # Legacy sequence IDs must NOT appear in the template's task graph
        yaml_block_m = re.search(r"```ya?ml\s*\n(.*?)\n```", text, re.DOTALL)
        self.assertIsNotNone(yaml_block_m, "PLAN.template.md must contain a yaml graph block")
        graph_yaml = yaml_block_m.group(1)
        self.assertNotIn("G1-RETRO", graph_yaml,
                         "PLAN.template.md graph must not use legacy G1-RETRO")
        self.assertNotIn("G1-LESSONS", graph_yaml,
                         "PLAN.template.md graph must not use legacy G1-LESSONS")
        self.assertNotIn("G1-DOCS", graph_yaml,
                         "PLAN.template.md graph must not use legacy G1-DOCS")
        # Gate 2 must be empty (terminal gate — close WU drafted by plan-next)
        self.assertIn("work_units: []", graph_yaml,
                      "Gate 2 in PLAN.template.md must have work_units: [] "
                      "(terminal gate, populated by plan-next)")

    def test_plan_template_explains_closing_shape_choice(self):
        """PLAN.template.md must include a comment explaining the closing shape."""
        text = self._plan_template_text()
        self.assertIn("close-intermediate", text)
        # Explanation of non-terminal vs terminal pattern
        self.assertTrue(
            "non-terminal" in text or "terminal gate" in text,
            "PLAN.template.md must explain the non-terminal / terminal gate closing shapes"
        )
        # Pointer to FEAT-2026-0015
        self.assertIn("FEAT-2026-0015", text,
                      "PLAN.template.md must reference FEAT-2026-0015 for context")


class TestWUTemplateClosingShapes(unittest.TestCase):

    def test_wu_template_lists_close_intermediate_in_frontmatter_notes(self):
        """WU.template.md frontmatter notes must document close-intermediate type."""
        text = WU_TEMPLATE.read_text()
        self.assertIn("close-intermediate", text,
                      "WU.template.md must list close-intermediate in type field docs")
        # Explanation of what close-intermediate means
        self.assertTrue(
            "non-terminal" in text or "RETRO+LESSONS+DOCS" in text
            or "folds" in text.lower(),
            "WU.template.md must explain what close-intermediate does "
            "(folds RETRO+LESSONS+DOCS)"
        )
        # close type must still be documented
        self.assertIn("`close`", text,
                      "WU.template.md must still document the `close` type")

    def test_wu_template_close_intermediate_paired_with_plan_next(self):
        """WU.template.md must clarify close-intermediate pairs with plan-next."""
        text = WU_TEMPLATE.read_text()
        # The template should mention plan-next staying separate or pairing
        self.assertTrue(
            "plan-next" in text,
            "WU.template.md must mention plan-next in the context of close-intermediate"
        )

    def test_wu_template_legacy_4wu_documented_as_legacy(self):
        """WU.template.md must note the 4-WU sequence is legacy/emits WARN."""
        text = WU_TEMPLATE.read_text()
        self.assertTrue(
            "legacy" in text.lower() or "warn" in text.upper(),
            "WU.template.md must indicate the legacy 4-WU sequence emits WARN"
        )


if __name__ == "__main__":
    unittest.main()
