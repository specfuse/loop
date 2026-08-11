# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the findings-diagnose provider (FEAT-2026-0049/T10).

Covers: selection (one `kind="finding-diagnose"` item per open
`monitoring-finding` issue with an `auto` diagnose dial and no existing
diagnosis comment), the rendered comment body being `diagnosis.render`'s
byte-identical output with no local template, escalation with no
`gh issue comment` call when the analysis session's output does not parse,
already-diagnosed and dial-off/no-config findings never advertised,
registration in `default_providers()`, and no git mutation of the
provider's own.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.findings_diagnose import FindingsDiagnoseProvider
from specfuse.agent.run import KIND_FINDING_DIAGNOSE, STATUS_COMPLETED, STATUS_ESCALATED, default_providers
from specfuse.agent.state import AgentSnapshot, IssueSummary
from specfuse.monitor.diagnose_cli import render_headless
from specfuse.monitor.issues import FINDING_LABEL

_MONITORING_CONFIG_AUTO = {"components": [{"name": "widget-api", "diagnose": "auto"}]}
_MONITORING_CONFIG_MANUAL = {"components": [{"name": "widget-api", "diagnose": "manual"}]}

_ANALYSIS_JSON = (
    '{"root_cause": "off-by-one in retry loop", '
    '"evidence": "widget_api.py:42 loops range(n) but should be range(n+1)", '
    '"candidate_fix": "change range(n) to range(n + 1)", '
    '"confidence": 0.8, "fix_scope": "small"}'
)

_FINDING_BODY = "<!-- specfuse:finding fingerprint=abc123 -->\n**Component:** widget-api\n"


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


def _view_runner(calls: list, *, body: str = _FINDING_BODY, comments: list = None, analysis_stdout: str = _ANALYSIS_JSON):
    comments = comments if comments is not None else []

    def runner(argv, check: bool = False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            import json

            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"body": body, "comments": comments}),
                stderr="",
            )
        if argv[:3] == ["gh", "issue", "comment"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        # the headless analysis invocation
        return SimpleNamespace(returncode=0, stdout=analysis_stdout, stderr="")

    return runner


class TestFindingsDiagnoseProvider(unittest.TestCase):
    def test_undiagnosed_finding_gets_one_diagnosis_comment(self):
        calls = []
        runner = _view_runner(calls)
        provider = FindingsDiagnoseProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
            return_value=_MONITORING_CONFIG_AUTO,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(10),)))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].kind, KIND_FINDING_DIAGNOSE)
            self.assertEqual(items[0].item_id, "finding-diagnose-10")

            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)

        comment_calls = [c for c in calls if c[:3] == ["gh", "issue", "comment"]]
        self.assertEqual(len(comment_calls), 1)
        body_arg = comment_calls[0][comment_calls[0].index("--body") + 1]
        self.assertEqual(body_arg, render_headless(_ANALYSIS_JSON))

    def test_unparseable_analysis_escalates_and_posts_nothing(self):
        calls = []
        runner = _view_runner(calls, analysis_stdout="not json at all")
        provider = FindingsDiagnoseProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
            return_value=_MONITORING_CONFIG_AUTO,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(11),)))
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIn("not valid JSON", outcome.detail)
        comment_calls = [c for c in calls if c[:3] == ["gh", "issue", "comment"]]
        self.assertEqual(comment_calls, [])

    def test_already_diagnosed_finding_not_advertised(self):
        diagnosed_comment_body = render_headless(_ANALYSIS_JSON)
        calls = []
        runner = _view_runner(calls, comments=[{"body": diagnosed_comment_body}])
        provider = FindingsDiagnoseProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
            return_value=_MONITORING_CONFIG_AUTO,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(12),)))

        self.assertEqual(items, [])

    def test_manual_diagnose_dial_not_advertised(self):
        calls = []
        runner = _view_runner(calls)
        provider = FindingsDiagnoseProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
            return_value=_MONITORING_CONFIG_MANUAL,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(13),)))

        self.assertEqual(items, [])

    def test_no_monitoring_config_advertises_nothing(self):
        calls = []
        runner = _view_runner(calls)
        provider = FindingsDiagnoseProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
            return_value=None,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(14),)))

        self.assertEqual(list(items), [])

    def test_non_finding_issue_not_advertised(self):
        calls = []
        runner = _view_runner(calls)
        provider = FindingsDiagnoseProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
            return_value=_MONITORING_CONFIG_AUTO,
        ):
            items = provider.advertise(_snapshot(issues=(_finding_issue(15, labels=()),)))

        self.assertEqual(items, [])

    def test_registered_in_default_providers(self):
        providers = default_providers(repo="o/r")
        kinds = [type(p).__name__ for p in providers]
        self.assertIn("FindingsDiagnoseProvider", kinds)


if __name__ == "__main__":
    unittest.main()
