#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The human-output rule is seeded, imported, and reaches existing projects.

Users reported skill output as too verbose and written in the loop's internal
vocabulary. The cause was structural: `operator-escalation.md` says how to
address a human, but binds only when work *stops for a decision*, so the other
90% of output had no rule and each skill invented its own register.

This module asserts the three places the rule has to reach to have any effect,
mirroring `test_operator_escalation_rule.py`:

1. it exists in `.specfuse/rules/` and in the packaged seed, byte-identical;
2. it is NOT loaded into every dispatch — FEAT-2026-0084/T01 took it out of
   `scaffold._RULES_BLOCK`; it binds on skill output, and the skills that
   produce that output name it themselves;
3. an EXISTING project has the import RETIRED on upgrade, so a project
   scaffolded before the block shrank ends on the new set rather than carrying
   old and new at once. The insert half of that reconciliation still runs and
   is asserted here too — it is what keeps a genuinely new rule from shipping
   unread to every project already scaffolded.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import scaffold

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "human-output.md"
_PACKAGED = _REPO_ROOT / "specfuse" / "loop" / "data" / "rules" / "human-output.md"
_IMPORT = "@.specfuse/rules/human-output.md"
_CANONICAL_SKILLS = _REPO_ROOT / "plugins" / "specfuse" / "skills"

# The human-facing skills that must carry the pointer now that the dispatch
# path does not load the rule. Enumerated, not globbed, for the same reason as
# in `test_operator_escalation_rule.py`: a new skill should be a conscious
# decision, and a glob would absolve it.
_HUMAN_FACING_SKILLS = (
    "arm-gate",
    "gate-status",
    "accept-hedged-close",
    "attention",
    "answer-escalation",
)

# The five rules the file must state. Regexes, not substrings, so the prose can
# be reworded without the test dictating it.
_RULES = (
    (r"answer first", "rule 1 — answer before derivation"),
    (r"short by default", "rule 2 — short, with detail on request"),
    (r"not schema keys", "rule 3 — domain words over field names"),
    (r"runnable as printed", "rule 4 — commands must work when pasted"),
)


class TestRuleShipsAndStaysInSync(unittest.TestCase):
    def test_rule_exists_and_is_non_empty(self):
        self.assertTrue(_RULE.is_file(), "the rule is missing from .specfuse/rules/")
        self.assertGreater(len(_RULE.read_text(encoding="utf-8")), 500)

    def test_packaged_seed_is_byte_identical(self):
        """A downstream project gets the seeded copy, not this one."""
        self.assertTrue(_PACKAGED.is_file(), "the rule is not in the packaged seed")
        self.assertEqual(
            _RULE.read_bytes(), _PACKAGED.read_bytes(),
            "the .specfuse/ rule and its packaged copy have diverged; a new "
            "project would receive different text than this repo follows",
        )

    def test_rule_states_each_numbered_rule(self):
        text = re.sub(r"\s+", " ", _RULE.read_text(encoding="utf-8")).lower()
        for pattern, label in _RULES:
            with self.subTest(rule=label):
                self.assertRegex(text, pattern, f"the rule does not state {label}")

    def test_rule_carries_the_translation_table(self):
        """Rule 3 is unactionable without concrete substitutions."""
        text = _RULE.read_text(encoding="utf-8")
        for key in ("blocked_human", "awaiting_review", "met_locally", "failure_class"):
            with self.subTest(key=key):
                self.assertIn(key, text, f"{key} has no plain-English rendering")

    def test_rule_still_allows_naming_the_next_command(self):
        """Guard against over-correction.

        Telling the reader what to run next is the point of the output, not
        noise to strip. The rule must constrain the FORM of a command, never
        forbid naming one.
        """
        text = _RULE.read_text(encoding="utf-8")
        self.assertIn("is expected", text)
        self.assertIn("specfuse run", text)


class TestItIsNotInTheDispatchPath(unittest.TestCase):
    """Was: "every new project gets it @-imported".

    Inverted by FEAT-2026-0084/T01. The rule binds on what a human reads, and
    a dispatched work-unit session writes for the driver — so it was paying
    648 words of every dispatch to constrain output that dispatch never
    produces. The rule still ships, and the skills that do write for a human
    name it, which is what the three assertions below and
    `TestHumanFacingSkillsPointAtIt` together hold.
    """

    def test_scaffold_does_not_seed_the_import_line(self):
        self.assertNotIn(_IMPORT, scaffold._RULES_BLOCK)

    def test_this_repo_does_not_import_it_either(self):
        """Dogfood: the repo that authors the rule follows its own diet."""
        claude_md = (_REPO_ROOT / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertNotIn(_IMPORT, claude_md)

    def test_fresh_wiring_does_not_write_the_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            scaffold.wire_claude(target)
            claude_md = (target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertNotIn(_IMPORT, claude_md)


class TestHumanFacingSkillsPointAtIt(unittest.TestCase):
    """The pointer is now the only path from the rule to a run that reads it."""

    def test_the_skill_list_still_resolves(self):
        """Vacuity guard: a renamed skill would otherwise assert nothing."""
        for name in _HUMAN_FACING_SKILLS:
            with self.subTest(skill=name):
                self.assertTrue((_CANONICAL_SKILLS / name / "SKILL.md").is_file())

    def test_each_names_the_rule(self):
        for name in _HUMAN_FACING_SKILLS:
            with self.subTest(skill=name):
                text = (_CANONICAL_SKILLS / name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "human-output.md", text,
                    f"{name} writes for a human but does not point at the rule "
                    f"that governs how, and the dispatch path no longer loads it",
                )


class TestExistingProjectsConvergeOnTheCurrentBlock(unittest.TestCase):
    """Both halves of the reconciliation the sentinel short-circuit used to skip.

    `_write_claude_md` returns early when the sentinel is present, which is
    what stops it clobbering a project's own CLAUDE.md. That early return also
    meant a project scaffolded yesterday never learned about a rule added
    today (the insert half), and — once FEAT-2026-0084/T01 shrank the block —
    would have kept @-importing rules the block no longer carries, ending up
    with old set and new at once (the retire half).
    """

    # A project wired against the pre-diet seven-rule block, plus its own
    # rules-local import and prose.
    _LEGACY = (
        "# Project notes\n"
        "\n"
        "Some prose the project wrote itself.\n"
        "\n"
        "## Specfuse binding rules (read before any work-unit dispatch)\n"
        "@.specfuse/rules/result-contract.md\n"
        "@.specfuse/rules/correlation-ids.md\n"
        "@.specfuse/rules/never-touch.md\n"
        "@.specfuse/rules/security-boundaries.md\n"
        "@.specfuse/rules/verification-discipline.md\n"
        "@.specfuse/rules/operator-escalation.md\n"
        "@.specfuse/rules/human-output.md\n"
        "@.specfuse/rules-local/house-style.md\n"
        "\n"
        "Trailing project prose.\n"
    )

    # The same project, minus a rule the current block DOES carry — the input
    # that still exercises the insert half.
    _LEGACY_MISSING_A_CURRENT_RULE = _LEGACY.replace(
        "@.specfuse/rules/security-boundaries.md\n", ""
    )

    def _wire(self, text: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            claude_dir = target / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "CLAUDE.md").write_text(text, encoding="utf-8")
            scaffold.wire_claude(target)
            return (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")

    def test_an_old_block_ends_as_the_new_block_once_not_both(self):
        """The upgrade case: neither a leftover import nor a duplicated one."""
        result = self._wire(self._LEGACY)
        rules = [
            ln.strip() for ln in result.splitlines()
            if ln.strip().startswith("@.specfuse/rules/")
        ]
        self.assertEqual(
            rules, scaffold._rule_import_lines(),
            "an upgraded project's rule imports are not exactly the current "
            "block — a retired rule was left behind, or one was duplicated",
        )

    def test_retired_imports_are_removed(self):
        result = self._wire(self._LEGACY)
        for line in scaffold._RETIRED_RULE_IMPORTS:
            with self.subTest(retired=line):
                self.assertNotIn(line, result)

    def test_missing_import_is_still_backfilled(self):
        """The insert half: a rule the block gained must still reach a project."""
        result = self._wire(self._LEGACY_MISSING_A_CURRENT_RULE)
        self.assertIn("@.specfuse/rules/security-boundaries.md", result)

    def test_project_content_is_preserved(self):
        result = self._wire(self._LEGACY)
        self.assertIn("Some prose the project wrote itself.", result)
        self.assertIn("Trailing project prose.", result)
        self.assertIn("@.specfuse/rules-local/house-style.md", result)

    def test_the_rules_block_stays_contiguous(self):
        """Reconciliation must not scatter the imports or displace the local one."""
        lines = [ln.strip() for ln in
                 self._wire(self._LEGACY_MISSING_A_CURRENT_RULE).splitlines()]
        rules = [i for i, ln in enumerate(lines) if ln.startswith("@.specfuse/rules/")]
        self.assertEqual(
            rules, list(range(min(rules), max(rules) + 1)),
            "rule imports are no longer contiguous",
        )
        local = lines.index("@.specfuse/rules-local/house-style.md")
        self.assertGreater(local, max(rules), "the local import was displaced")

    def test_reconciliation_is_idempotent(self):
        once = self._wire(self._LEGACY)
        twice = self._wire(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("@.specfuse/rules/result-contract.md"), 1)

    def test_untouched_when_already_current(self):
        current = (
            "## Specfuse binding rules (read before any work-unit dispatch)\n"
            + "".join(ln + "\n" for ln in scaffold._rule_import_lines())
        )
        self.assertEqual(self._wire(current), current)

    def test_settings_json_still_written_for_a_legacy_claude_md(self):
        """Vacuity guard: wire_claude must still be doing its other work."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            claude_dir = target / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "CLAUDE.md").write_text(self._LEGACY, encoding="utf-8")
            scaffold.wire_claude(target)
            data = json.loads((claude_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertIn("Bash(specfuse:*)", data["permissions"]["allow"])


if __name__ == "__main__":
    unittest.main()
