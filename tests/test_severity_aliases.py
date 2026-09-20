# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""An operator can declare what their own `severity:*` labels mean (#3349).

#3339 established that severity is read from a `severity:<value>` label, that
only `SEVERITY_VALUES` are read, and that an unreadable severity fails closed
under a floor. That default is right and is not changed here. What was missing
is any way for an operator to say what a label outside that vocabulary means:
a repository whose labels are `severity:critical|major|minor` — all three
defined, with descriptions, before the policy existed — had 22 bug-marked
issues skipped under a `medium` floor because the words are spelled `major` and
`minor`.

`severity_aliases` is that declaration. Nothing is inferred: an absent key
behaves exactly as before, and an alias pointing outside `SEVERITY_VALUES` is a
validator ERROR rather than a silent drop.
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop.agent_policy import (
    DEFAULT_SEVERITY_ALIASES,
    meets_severity_floor,
    read_severity_label,
    resolve_severity_aliases,
    validate_agent_policy,
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


_ALIASES = textwrap.indent("severity_aliases:\n  major: high\n  minor: low\n", "    ")


class ReadingAnAliasedLabel(unittest.TestCase):

    def test_an_alias_makes_an_out_of_vocabulary_label_readable(self):
        aliases = {"major": "high", "minor": "low"}
        self.assertEqual(read_severity_label(("severity:major",), aliases)[0], "high")
        self.assertEqual(read_severity_label(("severity:minor",), aliases)[0], "low")

    def test_without_aliases_nothing_changes(self):
        self.assertIsNone(read_severity_label(("severity:major",))[0])
        self.assertEqual(read_severity_label(("severity:critical",))[0], "critical")

    def test_a_vocabulary_value_is_never_overridden_by_an_alias(self):
        # An alias that shadows a real value must not redefine the vocabulary.
        self.assertEqual(
            read_severity_label(("severity:high",), {"high": "low"})[0], "high"
        )

    def test_read_severity_label_reports_the_label_an_alias_came_from(self):
        self.assertEqual(
            read_severity_label(("severity:major",), {"major": "high"}),
            ("high", "major"),
        )
        self.assertEqual(
            read_severity_label(("severity:high",), {"major": "high"}),
            ("high", None),
        )
        self.assertEqual(read_severity_label(("bug",), {"major": "high"}), (None, None))


class TheSkipReasonNamesTheAlias(unittest.TestCase):

    def test_a_below_floor_alias_says_which_label_it_came_from(self):
        ok, why = meets_severity_floor("low", "medium", via="minor")
        self.assertFalse(ok)
        self.assertIn("minor", why)
        self.assertIn("low", why)

    def test_an_unaliased_severity_reason_is_unchanged(self):
        ok, why = meets_severity_floor("low", "medium")
        self.assertFalse(ok)
        self.assertEqual(why, "severity low is below the medium floor")


class ResolvingFromPolicy(unittest.TestCase):

    def _write(self, body: str) -> str:
        path = Path(self._tmp.name) / "agent-policy.yml"
        path.write_text(body, encoding="utf-8")
        return str(path)

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_absent_key_resolves_to_the_shipped_table(self):
        # Was `{}` until #3355. An absent key now resolves to
        # DEFAULT_SEVERITY_ALIASES: that is the behaviour change #3355 exists
        # to make, not a regression against #3349's contract.
        self.assertEqual(
            resolve_severity_aliases(self._write(_policy())),
            DEFAULT_SEVERITY_ALIASES,
        )

    def test_a_declared_map_extends_rather_than_replaces_the_shipped_table(self):
        # #3355: declared entries merge over the shipped ones key by key. This
        # policy declares exactly what the table already says, so the result is
        # the table — asserted as a superset relation plus the declared values,
        # so the test does not re-pin the whole table's contents here.
        resolved = resolve_severity_aliases(self._write(_policy(_ALIASES)))
        self.assertEqual(resolved.get("major"), "high")
        self.assertEqual(resolved.get("minor"), "low")
        self.assertTrue(set(DEFAULT_SEVERITY_ALIASES).issubset(resolved))

    def test_a_missing_file_resolves_to_the_shipped_table(self):
        # Same #3355 change: a project with no policy file at all still reads
        # `severity:major`, which is the point.
        self.assertEqual(
            resolve_severity_aliases("/nonexistent/agent-policy.yml"),
            DEFAULT_SEVERITY_ALIASES,
        )


class ValidatingTheMap(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write(self, body: str) -> str:
        path = Path(self._tmp.name) / "agent-policy.yml"
        path.write_text(body, encoding="utf-8")
        return str(path)

    def test_a_valid_map_is_accepted(self):
        self.assertEqual(validate_agent_policy(self._write(_policy(_ALIASES))), [])

    def test_an_alias_pointing_outside_the_vocabulary_is_an_error(self):
        bad = textwrap.indent("severity_aliases:\n  major: enormous\n", "    ")
        findings = validate_agent_policy(self._write(_policy(bad)))
        self.assertTrue(
            any("severity_aliases" in f and "enormous" in f for f in findings),
            f"expected an ERROR naming the bad target, got {findings!r}",
        )

    def test_a_non_mapping_severity_aliases_is_an_error(self):
        bad = textwrap.indent("severity_aliases: \"major\"\n", "    ")
        findings = validate_agent_policy(self._write(_policy(bad)))
        self.assertTrue(
            any("severity_aliases" in f for f in findings),
            f"expected an ERROR, got {findings!r}",
        )


class TheBugLaneAdvertisesAnAliasedIssue(unittest.TestCase):
    """End to end through the provider that reads the policy (#3349).

    The measured case: a repository labelling `severity:major` under a
    `medium` floor. Before the alias key existed, `major` read as absent and
    fail-closed skipped it -- 12 such issues on the repository that surfaced
    this.
    """

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _provider(self, aliases_block: str, reports):
        from specfuse.agent.providers.bugs import BugsProvider

        path = Path(self._tmp.name) / "agent-policy.yml"
        path.write_text(_policy(aliases_block), encoding="utf-8")
        return BugsProvider(
            repo="acme/widget",
            runner=lambda argv, check=False: None,
            policy_path=str(path),
            report=reports.append,
        )

    def _snapshot(self):
        from specfuse.agent.state import AgentSnapshot, IssueSummary

        return AgentSnapshot(
            queue=(),
            triage_auto=False,
            bug_automerge=False,
            bug_lane_limits={},
            issues=(
                IssueSummary(
                    number=7,
                    title="wrong element rendered",
                    labels=("bug", "severity:major"),
                    triage_category="bug",
                    triage_confidence="high",
                ),
            ),
            issues_error=None,
            prs=(),
            prs_error=None,
            features=(),
        )

    def test_without_declared_aliases_the_shipped_table_still_reads_the_label(self):
        # INVERTED BY #3355, deliberately. Before it, a `severity:major` issue
        # with no operator config read as unlabelled and was skipped; this test
        # asserted that skip. The shipped table now resolves `major` to `high`,
        # which clears a `medium` floor, so the issue is advertised with no
        # configuration at all. That is the measured outcome the issue was filed
        # for: `clabonte/generator`'s 12 `severity:major` bugs become eligible
        # without anyone editing its policy file.
        reports = []
        items = self._provider("", reports).advertise(self._snapshot())
        self.assertEqual([item.item_id for item in items], ["bug-7"])
        self.assertEqual(reports, [])

    def test_with_the_alias_the_issue_is_advertised(self):
        reports = []
        items = self._provider(_ALIASES, reports).advertise(self._snapshot())
        self.assertEqual([item.item_id for item in items], ["bug-7"])
        self.assertEqual(reports, [])

    def test_an_alias_below_the_floor_is_skipped_naming_the_operators_label(self):
        from specfuse.agent.state import IssueSummary

        snapshot = self._snapshot()
        snapshot = type(snapshot)(
            **{
                **snapshot.__dict__,
                "issues": (
                    IssueSummary(
                        number=8,
                        title="button is the wrong shade",
                        labels=("bug", "severity:minor"),
                        triage_category="bug",
                        triage_confidence="high",
                    ),
                ),
            }
        )
        reports = []
        items = self._provider(_ALIASES, reports).advertise(snapshot)
        self.assertEqual(list(items), [])
        self.assertTrue(
            any("severity:minor" in line and "below the medium floor" in line
                for line in reports),
            f"the skip must name the operator's own label, got {reports!r}",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
