#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The RESULT block reaches a parser, or it is not emitted.

`result-contract.md` calls the block "the agent-to-driver interface", and the
driver reads it from a dispatched work-unit session's stdout
(`loop.parse_result_block`). Eleven human-invoked skills nevertheless ended
with it unconditionally, where no driver is listening — the operator got a
fenced slab of `status:` / `acceptance_criteria:` / `evidence:` to scroll past
after every `/pick-feature` or `/gate-status`.

That `attention` — just as human-facing — never emitted one is what shows the
inconsistency was accidental rather than designed.

Guarded here: every emitting skill states the condition, none states it bare,
and the one skill with a real machine consumer keeps its unconditional
contract.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKILL_DIRS = (
    _REPO_ROOT / "plugins" / "specfuse" / "skills",
    _REPO_ROOT / ".specfuse" / "skills",
)

# Skills that reference the block and must gate it on a non-interactive run.
# Enumerated, not globbed: a skill added later should be a conscious decision
# about who reads its output, and a glob would absolve it silently.
_CONDITIONAL = (
    "abandon-feature",
    "adopt-feature",
    "arm-gate",
    "block-feature",
    "draft-feature",
    "feature-conversion",
    "gate-status",
    "learnings-curate",
    "pick-feature",
    "unblock-wu",
)

# The canonical clause. One phrasing across every skill so this can be checked
# mechanically and so the instruction reads identically wherever it appears.
_CLAUSE = "Emit the RESULT block only when this skill was invoked **non-interactively**"

# The unconditional form this replaced. Its return would be the regression.
_BARE = "End with the RESULT block"


def _text(root: Path, skill: str) -> str:
    return (root / skill / "SKILL.md").read_text(encoding="utf-8")


class TestConditionalSkills(unittest.TestCase):
    def test_skill_list_still_resolves(self):
        """Vacuity guard: a renamed skill would otherwise assert nothing."""
        for root in _SKILL_DIRS:
            for skill in _CONDITIONAL:
                with self.subTest(root=root.name, skill=skill):
                    self.assertTrue(
                        (root / skill / "SKILL.md").is_file(),
                        f"{skill} is no longer at {root}",
                    )

    def test_each_states_the_condition(self):
        for root in _SKILL_DIRS:
            for skill in _CONDITIONAL:
                with self.subTest(root=root.name, skill=skill):
                    self.assertIn(
                        _CLAUSE, _text(root, skill),
                        f"{skill} does not gate the RESULT block on a "
                        f"non-interactive run",
                    )

    def test_none_states_it_unconditionally(self):
        offenders = []
        for root in _SKILL_DIRS:
            for path in sorted(root.glob("*/SKILL.md")):
                if _BARE in path.read_text(encoding="utf-8"):
                    offenders.append(str(path.relative_to(_REPO_ROOT)))
        self.assertEqual(
            offenders, [],
            f"these skills tell the agent to emit the RESULT block "
            f"unconditionally, including on an interactive run: {offenders}",
        )

    def test_each_points_the_interactive_run_at_the_human_output_rule(self):
        """Dropping the block is only half the fix — something must replace it."""
        for root in _SKILL_DIRS:
            for skill in _CONDITIONAL:
                with self.subTest(root=root.name, skill=skill):
                    self.assertIn("human-output.md", _text(root, skill))

    def test_each_still_references_the_contract(self):
        """The block's shape is still defined in one place, not restated."""
        for root in _SKILL_DIRS:
            for skill in _CONDITIONAL:
                with self.subTest(root=root.name, skill=skill):
                    self.assertIn("result-contract.md", _text(root, skill))


class TestSkillsWithARealParserAreUntouched(unittest.TestCase):
    """`fix-bug` headless is consumed by `autofix_invoke.classify_outcome`.

    Its RESULT is read by a program, so it must NOT be made conditional. This
    is the guard against over-applying the change.
    """

    def test_fix_bug_still_reports_unconditionally(self):
        for root in _SKILL_DIRS:
            with self.subTest(root=root.name):
                text = _text(root, "fix-bug")
                self.assertIn("RESULT", text)
                self.assertNotIn(_CLAUSE, text)

    def test_the_classifier_still_exists(self):
        """Vacuity guard: if the consumer went away, the exemption is stale."""
        from specfuse.monitor import autofix_invoke

        self.assertTrue(hasattr(autofix_invoke, "classify_outcome"))
        self.assertEqual(
            autofix_invoke.classify_outcome(""), "could_not_proceed",
            "the classifier no longer fails closed on empty output",
        )


class TestContractStatesTheAudienceRule(unittest.TestCase):
    """The skills defer to the contract; the rule has to be stated there."""

    _RULE = _REPO_ROOT / ".specfuse" / "rules" / "result-contract.md"
    _PACKAGED = (
        _REPO_ROOT / "specfuse" / "loop" / "data" / "rules" / "result-contract.md"
    )

    def test_contract_says_when_to_emit(self):
        text = self._RULE.read_text(encoding="utf-8").lower()
        self.assertIn("machine interface", text)
        self.assertIn("do **not** emit it on an interactive run".lower(), text)

    def test_contract_points_at_the_human_output_rule(self):
        self.assertIn("human-output.md", self._RULE.read_text(encoding="utf-8"))

    def test_packaged_copy_is_byte_identical(self):
        self.assertEqual(self._RULE.read_bytes(), self._PACKAGED.read_bytes())


if __name__ == "__main__":
    unittest.main()
