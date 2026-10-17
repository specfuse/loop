# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0205 end-to-end: a diagnosis carries a severity and the finding
gets one `severity:<value>` label."""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.findings_diagnose import FindingsDiagnoseProvider
from specfuse.agent.state import AgentSnapshot, IssueSummary
from specfuse.monitor.diagnose_cli import parse_analysis, render_headless
from specfuse.monitor.diagnosis import Diagnosis, parse, render
from specfuse.monitor.issues import FINDING_LABEL

_CONFIG = {"components": [{"name": "widget-api", "diagnose": "auto"}]}
_BODY = "<!-- specfuse:finding fingerprint=abc123 -->\n**Component:** widget-api\n"


def _analysis(**extra) -> str:
    data = {
        "root_cause": "off-by-one", "evidence": "widget_api.py:42",
        "candidate_fix": "range(n + 1)", "confidence": 0.8, "fix_scope": "small",
    }
    data.update(extra)
    return json.dumps(data)


def _snapshot(labels) -> AgentSnapshot:
    issue = IssueSummary(
        number=7, title="a finding", labels=tuple(labels),
        triage_category=None, triage_confidence=None,
    )
    return AgentSnapshot(
        queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
        issues=(issue,), issues_error=None, prs=(), prs_error=None, features=(),
    )


def _runner(calls, analysis):
    def runner(argv, check: bool = False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps({"body": _BODY, "comments": []}), stderr="",
            )
        if argv[:2] == ["gh", "issue"] or argv[:2] == ["gh", "label"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout=analysis, stderr="")

    return runner


def _execute(analysis: str, labels=(FINDING_LABEL,)) -> list:
    calls: list = []
    provider = FindingsDiagnoseProvider(repo="o/r", runner=_runner(calls, analysis))
    with patch(
        "specfuse.agent.providers.findings_diagnose.load_monitoring_config",
        return_value=_CONFIG,
    ):
        items = provider.advertise(_snapshot(labels))
        provider.execute(items[0])
    return calls


def _comment_body(calls) -> str:
    comment = [c for c in calls if c[:3] == ["gh", "issue", "comment"]][0]
    return comment[comment.index("--body") + 1]


def _edits(calls) -> list:
    return [c for c in calls if c[:3] == ["gh", "issue", "edit"]]


class SeverityIsRecordedAndLabelled(unittest.TestCase):
    def test_marker_carries_severity_and_label_is_added(self):
        calls = _execute(_analysis(severity="high"))
        body = _comment_body(calls)
        self.assertIn("severity=high", body.splitlines()[0])
        self.assertEqual(parse(body).severity, "high")
        self.assertIn(
            ["gh", "label", "create", "severity:high", "--force", "--repo", "o/r"], calls
        )
        edits = _edits(calls)
        self.assertEqual(len(edits), 1)
        self.assertIn("severity:high", edits[0])
        self.assertNotIn("--remove-label", edits[0])

    def test_new_severity_replaces_previous_label(self):
        calls = _execute(_analysis(severity="low"), labels=(FINDING_LABEL, "severity:high"))
        edits = _edits(calls)
        self.assertEqual(len(edits), 1)
        argv = edits[0]
        self.assertEqual(argv[argv.index("--remove-label") + 1], "severity:high")
        self.assertEqual(argv[argv.index("--add-label") + 1], "severity:low")


class OldAndUnknownSeverityReadAsAbsent(unittest.TestCase):
    def test_pre_feature_marker_parses_without_severity(self):
        body = render(Diagnosis("rc", "ev", "fix", 0.5, "small"))
        self.assertTrue(body.startswith("<!-- specfuse:diagnosis confidence=0.5 fix_scope=small -->"))
        self.assertNotIn("Severity", body)
        self.assertIsNone(parse(body).severity)

    def test_unknown_severity_marker_reads_absent(self):
        body = render(Diagnosis("rc", "ev", "fix", 0.5, "small", severity="high")).replace(
            "severity=high", "severity=urgent"
        )
        self.assertIsNone(parse(body).severity)

    def test_unknown_severity_in_analysis_posts_no_label_call(self):
        self.assertIsNone(parse_analysis(_analysis(severity="urgent")).severity)
        calls = _execute(_analysis(severity="urgent"))
        self.assertNotIn("severity=", _comment_body(calls))
        self.assertEqual(_edits(calls), [])
        self.assertEqual([c for c in calls if c[:3] == ["gh", "label", "create"]], [])

    def test_absent_severity_posts_no_label_call(self):
        calls = _execute(_analysis())
        self.assertEqual(_edits(calls), [])
        self.assertEqual(_comment_body(calls), render_headless(_analysis()))

    def test_invalid_severity_is_a_construction_error(self):
        with self.assertRaises(ValueError):
            Diagnosis("rc", "ev", "fix", 0.5, "small", severity="urgent")


class AutofixOrdersBySeverity(unittest.TestCase):
    def test_advertised_most_severe_first(self):
        from specfuse.agent.providers.findings_autofix import FindingsAutofixProvider

        severities = {1: "low", 2: "critical", 3: None}
        issues = tuple(
            IssueSummary(
                number=n, title=f"finding {n}", labels=(FINDING_LABEL,),
                triage_category=None, triage_confidence=None,
            )
            for n in severities
        )
        snapshot = AgentSnapshot(
            queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
            issues=issues, issues_error=None, prs=(), prs_error=None, features=(),
        )

        def runner(argv, check: bool = False):
            number = int(argv[3])
            comment = render(Diagnosis(
                "rc", "ev", "fix", 0.9, "small", severity=severities[number],
            ))
            payload = {"body": _BODY, "comments": [{"body": comment}]}
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

        provider = FindingsAutofixProvider(repo="o/r", runner=runner)
        with patch(
            "specfuse.agent.providers.findings_autofix.load_monitoring_config",
            return_value=_CONFIG,
        ):
            items = provider.advertise(snapshot)
        self.assertEqual(
            [item.item_id for item in items],
            ["finding-autofix-2", "finding-autofix-1", "finding-autofix-3"],
        )


class BugLaneIgnoresFindingSeverity(unittest.TestCase):
    def test_severity_labelled_finding_is_not_advertised(self):
        from specfuse.agent.providers.bugs import BugsProvider

        issue = IssueSummary(
            number=7, title="a finding", labels=(FINDING_LABEL, "severity:critical"),
            triage_category=None, triage_confidence=None,
        )
        snapshot = AgentSnapshot(
            queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
            issues=(issue,), issues_error=None, prs=(), prs_error=None, features=(),
        )
        provider = BugsProvider(repo="o/r", runner=_runner([], _analysis()))
        self.assertEqual(provider.advertise(snapshot), [])


if __name__ == "__main__":
    unittest.main()
