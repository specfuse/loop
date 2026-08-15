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
2. every new project gets it @-imported, via `scaffold._RULES_BLOCK`;
3. an EXISTING project gains the import on upgrade — the case the sentinel
   short-circuit used to skip, which would have shipped the rule unread to
   every project already scaffolded.
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


class TestEveryNewProjectImportsIt(unittest.TestCase):
    def test_scaffold_seeds_the_import_line(self):
        self.assertIn(
            _IMPORT, scaffold._RULES_BLOCK,
            "scaffold._RULES_BLOCK does not @-import the rule, so a scaffolded "
            "project ships it unread",
        )

    def test_this_repo_imports_it_too(self):
        """Dogfood: the repo that authors the rule must follow it."""
        claude_md = (_REPO_ROOT / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(_IMPORT, claude_md)

    def test_fresh_wiring_writes_the_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            scaffold.wire_claude(target)
            claude_md = (target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn(_IMPORT, claude_md)


class TestExistingProjectsGainTheImport(unittest.TestCase):
    """The case the sentinel short-circuit used to skip.

    `_write_claude_md` returns early when the sentinel is present, which is
    what stops it clobbering a project's own CLAUDE.md. Before the backfill,
    that early return also meant a project scaffolded yesterday never learned
    about a rule added today.
    """

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
        "@.specfuse/rules-local/house-style.md\n"
        "\n"
        "Trailing project prose.\n"
    )

    def _wire(self, text: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            claude_dir = target / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "CLAUDE.md").write_text(text, encoding="utf-8")
            scaffold.wire_claude(target)
            return (claude_dir / "CLAUDE.md").read_text(encoding="utf-8")

    def test_missing_import_is_backfilled(self):
        self.assertIn(_IMPORT, self._wire(self._LEGACY))

    def test_backfill_preserves_project_content(self):
        result = self._wire(self._LEGACY)
        self.assertIn("Some prose the project wrote itself.", result)
        self.assertIn("Trailing project prose.", result)
        self.assertIn("@.specfuse/rules-local/house-style.md", result)

    def test_backfill_keeps_the_rules_block_contiguous(self):
        """The new import lands with the other rules, not after the local one."""
        lines = [ln.strip() for ln in self._wire(self._LEGACY).splitlines()]
        rules = [i for i, ln in enumerate(lines) if ln.startswith("@.specfuse/rules/")]
        self.assertEqual(
            rules, list(range(min(rules), max(rules) + 1)),
            "rule imports are no longer contiguous",
        )
        local = lines.index("@.specfuse/rules-local/house-style.md")
        self.assertGreater(local, max(rules), "the local import was displaced")

    def test_backfill_is_idempotent(self):
        once = self._wire(self._LEGACY)
        twice = self._wire(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count(_IMPORT), 1)

    def test_untouched_when_nothing_is_missing(self):
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
