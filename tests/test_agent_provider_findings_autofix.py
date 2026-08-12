# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the findings-autofix provider (FEAT-2026-0049/T11).

Covers: selection (one `kind="finding-autofix"` item per open
`monitoring-finding` issue with a resolvable component and an existing
diagnosis comment), the outcome mapping from `AutofixRunResult` to
`ActionOutcome` for every decision/outcome combination, that the provider
re-decides nothing of its own (no local copy of the predicate's
thresholds/caps/fingerprint comparison), registration in
`default_providers()`, and no git mutation of the provider's own.
"""

from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.findings_autofix import FindingsAutofixProvider
from specfuse.agent.run import KIND_FINDING_AUTOFIX, STATUS_COMPLETED, STATUS_ESCALATED, default_providers
from specfuse.agent.state import AgentSnapshot, IssueSummary
from specfuse.monitor.autofix_state import AUTOFIX_FAILED_LABEL
from specfuse.monitor.diagnosis import Diagnosis, render
from specfuse.monitor.issues import FINDING_LABEL

_REPO = "o/r"
_COMPONENT = "widget-api"
_FINGERPRINT = "abc123fingerprint"

_MONITORING_CONFIG_ON = {"components": [{"name": _COMPONENT, "autofix": "on"}]}
_MONITORING_CONFIG_OFF = {"components": [{"name": _COMPONENT, "autofix": "off"}]}


def _finding_body(fingerprint: str = _FINGERPRINT, component: str = _COMPONENT) -> str:
    return (
        f"<!-- specfuse:finding fingerprint={fingerprint} -->\n"
        f"**Component:** {component}\n"
    )


def _diagnosis_comment(*, confidence: float = 1.0, fix_scope: str = "small") -> dict:
    body = render(
        Diagnosis(
            root_cause="root",
            evidence="evidence",
            candidate_fix="candidate",
            confidence=confidence,
            fix_scope=fix_scope,
        )
    )
    return {"body": body}


def _snapshot(issues: tuple = ()) -> AgentSnapshot:
    return AgentSnapshot(
        queue=(),
        triage_auto=False,
        bug_automerge=False,
        bug_lane_limits={},
        issues=issues,
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


def _finding_issue(number: int, labels=(FINDING_LABEL,), title: str = "a finding"):
    return IssueSummary(
        number=number,
        title=title,
        labels=tuple(labels),
        triage_category=None,
        triage_confidence=None,
    )


class _Result:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout


class FakeRunner:
    """Answers `gh` reads/writes and the fired `fix-bug` session launch.

    `session_stdout` is what a fired session's `claude -p ...` call
    returns -- `autofix_invoke.classify_outcome` reads it to decide
    `refused` / `could_not_proceed` / `completed`.
    """

    def __init__(self, *, comments, fingerprint=_FINGERPRINT, session_stdout="completed"):
        self.calls: list[list[str]] = []
        self._comments = comments
        self._fingerprint = fingerprint
        self._session_stdout = session_stdout
        self._row = {"number": 1, "body": _finding_body(fingerprint=fingerprint)}

    def __call__(self, argv, check=False):
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            return _Result(
                0,
                json.dumps(
                    {
                        "body": _finding_body(fingerprint=self._fingerprint),
                        "comments": self._comments,
                    }
                ),
            )
        if argv[:3] == ["gh", "issue", "list"]:
            return _Result(0, json.dumps([self._row]))
        if argv[:3] == ["gh", "issue", "edit"] and "--body" in argv:
            self._row["body"] = argv[argv.index("--body") + 1]
            return _Result(0, "")
        if argv[:3] == ["gh", "issue", "edit"]:
            return _Result(0, "")
        # the fired headless fix-bug session
        return _Result(0, self._session_stdout)


class TestFindingsAutofixProvider(unittest.TestCase):
    def test_decline_does_not_invoke_fix_bug(self):
        runner = FakeRunner(comments=[_diagnosis_comment()])
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_OFF,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(10),)))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].kind, KIND_FINDING_AUTOFIX)

            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIn("dial_off", outcome.detail)
        write_calls = [c for c in runner.calls if c[:3] == ["gh", "issue", "edit"]]
        self.assertEqual(write_calls, [])

    def test_fire_completed_reports_completed(self):
        runner = FakeRunner(comments=[_diagnosis_comment()], session_stdout="completed")
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_ON,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(11),)))
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)

    def test_fire_refused_escalates_with_payload_and_one_label(self):
        runner = FakeRunner(comments=[_diagnosis_comment()], session_stdout="refused")
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_ON,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(12),)))
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        # Carries a payload since #1970, recorded on the finding's own issue.
        # It previously carried none, on the reasoning that AUTOFIX_FAILED_LABEL
        # was already applied -- but a label says WHICH issues failed, never
        # what was attempted or what the operator's options are, and nothing
        # assigns it. The label still ships; both are asserted here.
        self.assertIsNotNone(outcome.escalation)
        self.assertEqual(outcome.escalation.target_issue, 12)
        label_calls = [c for c in runner.calls if c[:3] == ["gh", "issue", "edit"] and "--add-label" in c]
        self.assertEqual(len(label_calls), 1)
        self.assertIn(AUTOFIX_FAILED_LABEL, label_calls[0])

    def test_fire_could_not_proceed_escalates_with_payload_and_one_label(self):
        runner = FakeRunner(comments=[_diagnosis_comment()], session_stdout="could_not_proceed")
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_ON,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(13),)))
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        # Carries a payload since #1970, recorded on the finding's own issue.
        # It previously carried none, on the reasoning that AUTOFIX_FAILED_LABEL
        # was already applied -- but a label says WHICH issues failed, never
        # what was attempted or what the operator's options are, and nothing
        # assigns it. The label still ships; both are asserted here.
        self.assertIsNotNone(outcome.escalation)
        self.assertEqual(outcome.escalation.target_issue, 13)
        label_calls = [c for c in runner.calls if c[:3] == ["gh", "issue", "edit"] and "--add-label" in c]
        self.assertEqual(len(label_calls), 1)

    def test_route_to_human_escalates_naming_the_finding_issue(self):
        runner = FakeRunner(comments=[_diagnosis_comment(fix_scope="large")])
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_ON,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(14),)))
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIsNotNone(outcome.escalation)
        self.assertIn("14", outcome.escalation.issue_summary)
        self.assertGreaterEqual(len(outcome.escalation.options), 2)
        invoke_calls = [
            c for c in runner.calls
            if c and c[0] == "claude"
        ]
        self.assertEqual(invoke_calls, [])

    def test_undiagnosed_finding_not_advertised(self):
        runner = FakeRunner(comments=[])
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_ON,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(15),)))

        self.assertEqual(list(items), [])

    def test_unresolvable_component_not_advertised(self):
        runner = FakeRunner(comments=[_diagnosis_comment()])
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value={"components": [{"name": "some-other-component", "autofix": "on"}]},
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(16),)))

        self.assertEqual(list(items), [])

    def test_no_monitoring_config_advertises_nothing(self):
        runner = FakeRunner(comments=[_diagnosis_comment()])
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=None,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(17),)))

        self.assertEqual(list(items), [])

    def test_non_finding_issue_not_advertised(self):
        runner = FakeRunner(comments=[_diagnosis_comment()])
        provider = FindingsAutofixProvider(repo=_REPO, runner=runner)

        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_MONITORING_CONFIG_ON,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(18, labels=()),)))

        self.assertEqual(list(items), [])

    def test_registered_in_default_providers(self):
        providers = default_providers(repo=_REPO)
        kinds = [type(p).__name__ for p in providers]
        self.assertIn("FindingsAutofixProvider", kinds)

    def test_module_re_decides_nothing_of_its_own(self):
        import specfuse.agent.providers.findings_autofix as module
        from pathlib import Path

        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("CONFIDENCE_THRESHOLD", "FIX_SCOPES", "DAILY_CAP"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("has_prior_attempt", source)
        self.assertNotIn("fingerprint ==", source)


if __name__ == "__main__":
    unittest.main()
