# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""#3576: the backlog-snapshot emission contract is documented, not only queried.

The ``backlog-stalled`` adapter recognises one telemetry shape: a custom event
with a fixed name, carrying the backlog's name, the age of its oldest pending
item and, optionally, its pending count in fixed properties, emitted under the
component's role name. These tests hold the adapter's constants, the query it
builds, the design-for-diagnosis rule and the derive-monitoring skill to the
same values, so the documented contract and the queried one cannot drift into
two unlinked copies. Modeled on ``test_heartbeat_emission_contract.py``.
"""

import pathlib
import unittest

from specfuse.monitor.providers import azure_app_insights

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "design-for-diagnosis.md"
_SKILL_DIR = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring"

_EXPECTED = {
    "BACKLOG_EVENT_NAME": "BacklogSnapshot",
    "BACKLOG_NAME_PROPERTY": "backlogName",
    "BACKLOG_AGE_PROPERTY": "oldestPendingAgeSeconds",
    "BACKLOG_COUNT_PROPERTY": "pendingCount",
}


def _contract() -> dict:
    return {name: getattr(azure_app_insights, name, None) for name in _EXPECTED}


class TestAdapterExposesContractConstants(unittest.TestCase):
    def test_constants_exist(self):
        self.assertEqual(_contract(), _EXPECTED)

    def test_query_is_built_from_the_constants(self):
        contract = _contract()
        query = azure_app_insights._backlog_stalled_query("acme-orders")
        self.assertIn(f"Name == '{contract['BACKLOG_EVENT_NAME']}'", query)
        for key in ("BACKLOG_NAME_PROPERTY", "BACKLOG_AGE_PROPERTY", "BACKLOG_COUNT_PROPERTY"):
            with self.subTest(property=key):
                self.assertIn(f"Properties.{contract[key]}", query)
        self.assertIn("AppRoleName == 'acme-orders'", query)


class TestRuleDocumentsTheContract(unittest.TestCase):
    def setUp(self):
        self.text = _RULE.read_text(encoding="utf-8")

    def _section(self) -> str:
        sections = self.text.split("\n## ")
        matches = [s for s in sections if "`BacklogSnapshot`" in s]
        self.assertEqual(len(matches), 1, "exactly one rule section documents the contract")
        return matches[0]

    def test_rule_names_event_and_every_property(self):
        section = self._section()
        for value in _contract().values():
            self.assertIsNotNone(value, "adapter is missing a contract constant")
            self.assertIn(f"`{value}`", section)

    def test_rule_says_pending_count_is_never_a_threshold(self):
        section = self._section().lower()
        self.assertIn("never compared", section)

    def test_section_sits_after_the_heartbeat_contract(self):
        headings = [line for line in self.text.splitlines() if line.startswith("## ")]
        heartbeat = next(i for i, h in enumerate(headings) if "heartbeat" in h.lower())
        backlog = next(i for i, h in enumerate(headings) if "backlog" in h.lower())
        self.assertGreater(backlog, heartbeat)

    def test_rule_lists_the_check_type(self):
        self.assertIn("`backlog-stalled`", self.text)


class TestDeriveMonitoringAuditsBacklogEmission(unittest.TestCase):
    def test_skill_and_prompt_audit_backlog_emission(self):
        event = _contract()["BACKLOG_EVENT_NAME"]
        self.assertIsNotNone(event, "adapter exposes no BACKLOG_EVENT_NAME")
        for name in ("SKILL.md", "PROMPT.md"):
            text = (_SKILL_DIR / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIn("backlog-emission", text)
                self.assertIn("backlog-stalled", text)
                self.assertIn(f"`{event}`", text)


if __name__ == "__main__":
    unittest.main()
