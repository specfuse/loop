# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""#3470: the heartbeat emission contract is documented, not only queried.

The ``heartbeat`` adapter recognises one telemetry shape: a custom event with
a fixed name, carrying the schedule's name in a fixed property, emitted under
the component's role name. These tests hold the adapter's constants, the query
it builds, the design-for-diagnosis rule, and the derive-monitoring skill to
the same two values, so the documented contract and the queried one cannot
drift into two unlinked copies.
"""

import pathlib
import unittest

from specfuse.monitor.providers import azure_app_insights

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "design-for-diagnosis.md"
_SKILL_DIR = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring"


def _contract():
    event = getattr(azure_app_insights, "HEARTBEAT_EVENT_NAME", None)
    prop = getattr(azure_app_insights, "HEARTBEAT_SCHEDULE_PROPERTY", None)
    return event, prop


class TestAdapterExposesContractConstants(unittest.TestCase):
    def test_constants_exist(self):
        event, prop = _contract()
        self.assertEqual(event, "ScheduleHeartbeat")
        self.assertEqual(prop, "scheduleName")

    def test_query_is_built_from_the_constants(self):
        event, prop = _contract()
        query = azure_app_insights._heartbeat_query("acme-functions-host")
        self.assertIn(f"Name == '{event}'", query)
        self.assertIn(f"Properties.{prop}", query)
        self.assertIn("AppRoleName == 'acme-functions-host'", query)


class TestRuleDocumentsTheContract(unittest.TestCase):
    def setUp(self):
        self.text = _RULE.read_text(encoding="utf-8")

    def test_rule_names_event_and_property(self):
        event, prop = _contract()
        self.assertIsNotNone(event, "adapter exposes no HEARTBEAT_EVENT_NAME")
        self.assertIn(f"`{event}`", self.text)
        self.assertIn(f"`{prop}`", self.text)

    def test_contract_section_follows_the_role_name_rule(self):
        headings = [
            line for line in self.text.splitlines() if line.startswith("## ")
        ]
        role_idx = next(
            i for i, h in enumerate(headings) if "role names" in h.lower()
        )
        heartbeat = [i for i, h in enumerate(headings) if "heartbeat" in h.lower()]
        self.assertEqual(
            heartbeat, [role_idx + 1],
            "a heartbeat emission section must directly follow the role-name rule",
        )


class TestDeriveMonitoringAuditsHeartbeatEmission(unittest.TestCase):
    def test_skill_and_prompt_audit_heartbeat_emission(self):
        event, _ = _contract()
        self.assertIsNotNone(event, "adapter exposes no HEARTBEAT_EVENT_NAME")
        for name in ("SKILL.md", "PROMPT.md"):
            text = (_SKILL_DIR / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIn("heartbeat-emission", text)
                self.assertIn(f"`{event}`", text)


if __name__ == "__main__":
    unittest.main()
