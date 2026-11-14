# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""#3578: a component's data store is monitored through the component.

The scope decision lives in three surfaces that must say the same thing: the
design-for-diagnosis rule (what a component owes), the monitoring concept doc
(what the monitor will and will not watch), and the derive-monitoring skill
(what a drafting session asks and reports). These tests hold each surface to
the decision's load-bearing parts: the monitor never connects to a data store,
component-owned signals are emitted by the component, platform health routes
to infrastructure alerting, and the "pull request on the component" test.
"""

import pathlib
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_RULE = _REPO_ROOT / ".specfuse" / "rules" / "design-for-diagnosis.md"
_CONCEPT = _REPO_ROOT / "docs" / "concepts" / "monitoring-schema.md"
_SKILL_DIR = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring"

# Platform-health signals the decision names as out of scope.
_PLATFORM_HEALTH = ("CPU", "storage", "connections", "deadlock", "replication lag", "failover")


def _section(text, needle):
    """Return the '## ' section whose heading contains ``needle`` (case-insensitive)."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines)
         if line.startswith("## ") and needle in line.lower()),
        None,
    )
    if start is None:
        return None
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


class _DecisionAssertions:
    path = None

    def setUp(self):
        text = self.path.read_text(encoding="utf-8")
        self.section = _section(text, "data store")
        self.assertIsNotNone(
            self.section, f"{self.path.name} has no '## ' section about data stores"
        )
        # Prose wraps at any word; compare against single-spaced text.
        self.section = " ".join(self.section.split())

    def test_monitor_never_connects(self):
        self.assertIn("never connects", self.section)

    def test_owned_signals_are_emitted_by_the_component(self):
        for token in ("`backlog-stalled`", "`dependency-regression`", "`invariant`",
                      "migration"):
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_companion_checks_are_named_as_planned(self):
        self.assertIn("#3576", self.section)
        self.assertIn("#3577", self.section)
        self.assertIn("planned", self.section)

    def test_platform_health_is_out_of_scope(self):
        self.assertIn("out of scope", self.section)
        self.assertIn("infrastructure alerting", self.section)
        for token in _PLATFORM_HEALTH:
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_states_the_pull_request_test(self):
        self.assertIn("pull request on the component", self.section)


class TestRuleStatesTheDataStoreScope(_DecisionAssertions, unittest.TestCase):
    path = _RULE

    def test_section_sits_next_to_the_component_misbehaviour_boundary(self):
        self.assertIn("not metrics or infrastructure", self.section)


class TestConceptDocStatesTheDataStoreScope(_DecisionAssertions, unittest.TestCase):
    path = _CONCEPT

    def test_section_sits_next_to_the_component_misbehaviour_boundary(self):
        self.assertIn("not metrics or infrastructure", self.section)


class TestDeriveMonitoringAuditsDataStoreSignals(unittest.TestCase):
    def test_skill_and_prompt_audit_owned_data_store_signals(self):
        for name in ("SKILL.md", "PROMPT.md"):
            raw = (_SKILL_DIR / name).read_text(encoding="utf-8")
            text = " ".join(raw.split())
            with self.subTest(file=name):
                self.assertIn("data-store-signals", text)
                for token in ("backlog", "invariant", "migration"):
                    self.assertIn(token, text)
                self.assertIn("never propose a direct", text.lower())
                self.assertIn("infrastructure alerting", text)
                self.assertIn(
                    "\n## Out of scope (route to infrastructure alerting)\n", raw
                )


if __name__ == "__main__":
    unittest.main()
