# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A shipped default alias table, extended and overridden by policy (#3355).

#3339 declined to map `severity:minor` to `low` on the grounds that it would be
"inventing policy on an operator's behalf". That conflated two things, and the
same conflation was caught once already at FEAT-2026-0113's gate-2 arm
checkpoint: **where the floor sits** (`rules.bugs.min_severity`) is the
operator's decision because it gates unattended action, but **what an English
word means** is a published vocabulary — and specfuse already ships one
(`DEFAULT_SEVERITY_RUBRIC`).

Measured consequence of the wider reading: `clabonte/generator` labels
`critical`/`major`/`minor`, only `critical` is in `SEVERITY_VALUES`, so its
rubric had a single entry and a severity classifier could answer `critical` or
nothing — 4 of 5 sampled candidates skipped in the live dry run.

Numbered and lettered schemes are deliberately absent from the table: `P0`,
`S1`, `sev1` encode **priority**, a different axis, and vary per organisation.
An operator whose repo uses them declares them, because that is a real judgment
about their own scheme.
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop.agent_policy import (
    DEFAULT_SEVERITY_ALIASES,
    SEVERITY_VALUES,
    read_severity_label,
    resolve_severity_aliases,
)

_BASE = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: medium
    automerge: "off"
{aliases}  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 100000
  max_open_prs: 5
  max_items_per_day: 10
escalation:
  provider: none
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
  silence_hours: 24
"""


def _policy(aliases_block: str = "") -> str:
    return _BASE.format(aliases=aliases_block)


class TheShippedTable(unittest.TestCase):

    def test_every_target_is_a_real_severity_value(self):
        for word, target in DEFAULT_SEVERITY_ALIASES.items():
            with self.subTest(word=word):
                self.assertIn(target, SEVERITY_VALUES)

    def test_no_key_is_itself_a_severity_value(self):
        # An alias onto a vocabulary word could never apply; the vocabulary wins.
        self.assertEqual(set(DEFAULT_SEVERITY_ALIASES) & set(SEVERITY_VALUES), set())

    def test_the_common_word_synonyms_are_covered(self):
        for word, target in (
            ("blocker", "critical"), ("urgent", "critical"),
            ("major", "high"),
            ("normal", "medium"), ("moderate", "medium"),
            ("minor", "low"), ("trivial", "low"),
        ):
            with self.subTest(word=word):
                self.assertEqual(DEFAULT_SEVERITY_ALIASES.get(word), target)

    def test_priority_coded_schemes_are_deliberately_absent(self):
        # P0/S1/sev1 encode priority, a different axis, and vary per org.
        for word in ("p0", "p1", "p2", "s1", "s2", "sev1", "sev2"):
            with self.subTest(word=word):
                self.assertNotIn(word, DEFAULT_SEVERITY_ALIASES)


class ResolutionMergesShippedAndDeclared(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write(self, aliases_block: str = "") -> str:
        path = Path(self._tmp.name) / "agent-policy.yml"
        path.write_text(_policy(aliases_block), encoding="utf-8")
        return str(path)

    def test_absent_config_resolves_to_the_shipped_table(self):
        # The behaviour change, and the point of the issue: absent config is no
        # longer an empty map.
        self.assertEqual(resolve_severity_aliases(self._write()), DEFAULT_SEVERITY_ALIASES)

    def test_a_missing_file_still_resolves_to_the_shipped_table(self):
        self.assertEqual(
            resolve_severity_aliases("/nonexistent/agent-policy.yml"),
            DEFAULT_SEVERITY_ALIASES,
        )

    def test_declared_aliases_extend_the_table(self):
        block = textwrap.indent("severity_aliases:\n  showstopper: critical\n", "    ")
        resolved = resolve_severity_aliases(self._write(block))
        self.assertEqual(resolved.get("showstopper"), "critical")
        self.assertEqual(resolved.get("major"), "high")  # shipped entry survives

    def test_a_declared_alias_overrides_the_shipped_one_key_by_key(self):
        block = textwrap.indent("severity_aliases:\n  major: critical\n", "    ")
        resolved = resolve_severity_aliases(self._write(block))
        self.assertEqual(resolved.get("major"), "critical")
        self.assertEqual(resolved.get("minor"), "low")  # others untouched


class ReadingThroughTheTable(unittest.TestCase):

    def test_an_out_of_vocabulary_label_reads_with_no_operator_config(self):
        self.assertEqual(
            read_severity_label(("severity:major",), DEFAULT_SEVERITY_ALIASES),
            ("high", "major"),
        )

    def test_the_vocabulary_still_wins_over_the_shipped_table(self):
        self.assertEqual(
            read_severity_label(("severity:high",), DEFAULT_SEVERITY_ALIASES),
            ("high", None),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class TheRubricResolvesAliasedLabels(unittest.TestCase):
    """The measured case: a repository whose labels are mostly out of vocabulary.

    `clabonte/generator` declares `severity:critical`/`major`/`minor`. Only
    `critical` is in `SEVERITY_VALUES`, so before #3355 its rubric had one entry
    and the classifier could answer `critical` or nothing — 4 of 5 sampled
    candidates skipped in FEAT-2026-0113's live dry run (T11).
    """

    from types import SimpleNamespace

    def _runner(self, labels):
        import json as _json

        def runner(argv, check=False, cwd=None):
            if argv[:3] == ["gh", "label", "list"]:
                return self.SimpleNamespace(
                    returncode=0, stdout=_json.dumps(labels), stderr=""
                )
            return self.SimpleNamespace(returncode=0, stdout="", stderr="")

        return runner

    def test_an_out_of_vocabulary_label_contributes_its_own_description(self):
        from specfuse.loop.labels import read_severity_rubric

        rubric = read_severity_rubric(
            ".",
            runner=self._runner([
                {"name": "severity:critical", "description": "Does not compile"},
                {"name": "severity:major", "description": "Wrong behavior"},
                {"name": "severity:minor", "description": "Cosmetic"},
            ]),
            repo="acme/widget",
        )
        self.assertEqual(rubric.get("critical"), "Does not compile")
        self.assertEqual(rubric.get("high"), "Wrong behavior")
        self.assertEqual(rubric.get("low"), "Cosmetic")

    def test_a_vocabulary_label_is_never_displaced_by_an_aliased_one(self):
        from specfuse.loop.labels import read_severity_rubric

        rubric = read_severity_rubric(
            ".",
            runner=self._runner([
                {"name": "severity:high", "description": "the repo's own high"},
                {"name": "severity:major", "description": "aliased to high"},
            ]),
            repo="acme/widget",
        )
        self.assertEqual(
            rubric.get("high"), "the repo's own high",
            "an explicit in-vocabulary label wins over one that merely aliases "
            "onto the same value",
        )
