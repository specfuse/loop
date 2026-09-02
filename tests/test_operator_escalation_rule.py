#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The operator-escalation rule is seeded, imported, and referenced.

A rule that ships but is never read changes nothing in practice. That is not a
hypothesis here — it is what #265 measured: three driver guards enforced exact
formats that appeared in no authoring surface, and they accounted for $99.30, 45%
of all closing-WU waste. The guards were in the source the whole time.

So this module asserts the three places the rule has to reach to have any effect:

1. it exists in `.specfuse/rules/` and in the packaged seed, byte-identical;
2. it is NOT loaded into every dispatch — FEAT-2026-0084/T01 took it out of
   `scaffold._RULES_BLOCK`, because it governs what a skill says to a human and
   an implementing session says nothing to a human;
3. every skill that halts for a human decision points at it.

The third is the one that would rot silently. A new escalating skill added later
gets no pointer unless something fails. The second is what makes the third load-
bearing: the rule now reaches a session only through a skill that names it.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from specfuse.loop import scaffold

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "operator-escalation.md"
_PACKAGED = _REPO_ROOT / "specfuse" / "loop" / "data" / "rules" / "operator-escalation.md"
_CANONICAL_SKILLS = _REPO_ROOT / "plugins" / "specfuse" / "skills"
_VENDORED_SKILLS = _REPO_ROOT / ".specfuse" / "skills"

# Skills that halt for a human decision. Enumerated rather than globbed: adding
# an escalating skill should be a conscious decision to point it at the rule,
# and a glob would silently absolve a new one.
_ESCALATING_SKILLS = (
    "arm-gate",             # accept/revise/reject each drafted WU
    "gate-status",          # recommends, never decides
    "accept-hedged-close",  # records the operator's own reason
    "attention",            # the needs-a-human inbox
    "answer-escalation",    # dispositions one parked issue
    "wrap-feature",    # refuses non-done features
    "unblock-wu",      # requires an operator rationale
    "abandon-feature", # single up-front confirmation
    "block-feature",   # names a blocker
    "pick-feature",    # presents candidates, human picks
    "draft-feature",   # decision questions with pros/cons
    "fix-bug",         # refuses feature-scoped work
)

# The six parts the rule requires. Regexes rather than substrings so the rule can
# be reworded without the test dictating its prose — the first version of this
# test asserted "what the issue is about" and failed on the better-written "what
# THIS issue is about", which is the test being brittle, not the rule being wrong.
_SIX_PARTS = (
    (r"what has been done so far", "part 1 — the state so far"),
    (r"what th(is|e) issue is about", "part 2 — what the issue is about"),
    (r"what decision is needed", "part 3 — the decision"),
    (r"did not,? or could not,? close automatically|did not close automatically",
     "part 4 — why it did not close automatically"),
    (r"pros and cons", "part 5 — options with trade-offs"),
    (r"recommendation", "part 6 — the recommendation"),
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

    def test_rule_states_all_six_parts(self):
        text = re.sub(r"\s+", " ", _RULE.read_text(encoding="utf-8")).lower()
        for pattern, label in _SIX_PARTS:
            with self.subTest(part=label):
                self.assertRegex(text, pattern, f"the rule does not state {label}")


class TestItIsNotInTheDispatchPath(unittest.TestCase):
    """Was: "every new project gets it @-imported".

    Inverted by FEAT-2026-0084/T01. The rule binds on what a skill says to a
    human; a dispatched work-unit session says nothing to a human, and the
    seven @-imported rules cost 7,213 words of every dispatch. The rule still
    ships in `.specfuse/rules/` and is retired from an existing project's
    CLAUDE.md on upgrade, so no project ends up carrying both blocks.
    """

    _IMPORT = "@.specfuse/rules/operator-escalation.md"

    def test_scaffold_does_not_seed_the_import_line(self):
        self.assertNotIn(self._IMPORT, scaffold._RULES_BLOCK)

    def test_this_repo_does_not_import_it_either(self):
        """Dogfood: the repo that authors the rule follows its own diet."""
        claude_md = (_REPO_ROOT / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertNotIn(self._IMPORT, claude_md)

    def test_an_existing_project_has_the_import_retired_on_upgrade(self):
        """Otherwise every already-scaffolded project keeps loading it."""
        self.assertIn(self._IMPORT, scaffold._RETIRED_RULE_IMPORTS)


class TestEscalatingSkillsPointAtIt(unittest.TestCase):
    """The part most likely to rot.

    A skill added later, or one whose escalation path grows, gets no pointer
    unless a test fails. Both the canonical and vendored copies are checked —
    the vendored copy is what a scaffolded project actually reads.
    """

    def test_the_skill_list_still_resolves(self):
        """Vacuity guard: a renamed skill would otherwise pass silently."""
        for name in _ESCALATING_SKILLS:
            with self.subTest(skill=name):
                self.assertTrue(
                    (_CANONICAL_SKILLS / name / "SKILL.md").is_file(),
                    f"{name} is no longer at the canonical path; this test would "
                    f"otherwise assert nothing about it",
                )

    def test_every_escalating_skill_references_the_rule(self):
        for name in _ESCALATING_SKILLS:
            with self.subTest(skill=name):
                text = (_CANONICAL_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(
                    "operator-escalation.md", text,
                    f"{name} halts for a human decision but does not point at the "
                    f"escalation-framing rule, so its output is unconstrained",
                )

    def test_vendored_copies_match_canonical(self):
        """`scripts/sync-scaffold.sh` output — the copy a project reads."""
        for name in _ESCALATING_SKILLS:
            canonical = _CANONICAL_SKILLS / name / "SKILL.md"
            vendored = _VENDORED_SKILLS / name / "SKILL.md"
            with self.subTest(skill=name):
                self.assertTrue(vendored.is_file(), f"{name} is not vendored")
                self.assertEqual(
                    canonical.read_bytes(), vendored.read_bytes(),
                    f"{name}'s vendored copy is stale — run scripts/sync-scaffold.sh",
                )


class TestTheThreeNamedFailures(unittest.TestCase):
    """The rule's value is the three failures it names, not the six-part list.

    Anyone can reorder a template. The reason this rule exists is that each of
    these was observed: options presented without a call, a working safety catch
    reported as a malfunction, and an agent drafting the human's own reason for a
    field that exists to capture the human's reason.
    """

    def test_rule_names_all_three(self):
        text = re.sub(r"\s+", " ", _RULE.read_text(encoding="utf-8")).lower()
        for marker in (
            "without a recommendation",
            "refusal reported as a malfunction",
            "human's own justification",
        ):
            with self.subTest(failure=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
