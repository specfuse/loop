# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3487: when does a finding get a fresh diagnosis?

Operator decision (2026-10-17): once when its issue was reopened after a fix
(the monitor's reopen comment is newer than the latest diagnosis), and when a
human adds the `rediagnose` label, which the provider consumes. Every other
case — low confidence, flapping, plain occurrence bumps — stays "never".
"""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.findings_diagnose import REDIAGNOSE_LABEL, FindingsDiagnoseProvider
from specfuse.agent.state import AgentSnapshot, IssueSummary
from specfuse.monitor import issues
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.diagnose_cli import render_headless
from specfuse.monitor.issues import FINDING_LABEL, REOPENED_MARKER, is_reopen_comment

_CONFIG = {"components": [{"name": "widget-api", "diagnose": "auto"}]}
_BODY = "<!-- specfuse:finding fingerprint=abc123 -->\n**Component:** widget-api\n"
_LOW = (
    '{"root_cause": "unclear", "evidence": "thin", "candidate_fix": "look closer", '
    '"confidence": 0.2, "fix_scope": "small"}'
)
_NEW = (
    '{"root_cause": "regression in retry loop", "evidence": "widget_api.py:42", '
    '"candidate_fix": "restore range(n + 1)", "confidence": 0.9, "fix_scope": "small"}'
)
_DIAGNOSIS = {"body": render_headless(_LOW)}
_REOPEN = {"body": f"{REOPENED_MARKER}\nRecurred after close: occurrence 3, first seen x, last seen y."}
_BUMP = {"body": "Another occurrence noted by a human."}


def _snapshot(labels):
    issue = IssueSummary(number=7, title="a finding", labels=tuple(labels),
                         triage_category=None, triage_confidence=None)
    return AgentSnapshot(queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
                         issues=(issue,), issues_error=None, prs=(), prs_error=None, features=())


def _runner(calls, comments):
    def run(argv, check=False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"body": _BODY, "comments": comments}), stderr="")
        if argv[:2] == ["gh", "issue"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout=_NEW, stderr="")
    return run


def _advertise(comments, labels=(FINDING_LABEL,)):
    calls = []
    provider = FindingsDiagnoseProvider(repo="o/r", runner=_runner(calls, comments))
    with patch("specfuse.agent.providers.findings_diagnose.load_monitoring_config", return_value=_CONFIG):
        items = provider.advertise(_snapshot(labels))
    return provider, items, calls


class TestReopenTriggersOneRediagnosis(unittest.TestCase):
    def test_reopen_after_the_diagnosis_is_advertised(self):
        _, items, _ = _advertise([_DIAGNOSIS, _REOPEN])
        self.assertEqual([i.item_id for i in items], ["finding-diagnose-7"])

    def test_diagnosis_after_the_reopen_is_not_advertised_again(self):
        # Once: the fresh diagnosis is now newer than the reopen.
        _, items, _ = _advertise([_DIAGNOSIS, _REOPEN, _DIAGNOSIS])
        self.assertEqual(items, [])

    def test_a_second_reopen_gets_its_own_rediagnosis(self):
        _, items, _ = _advertise([_DIAGNOSIS, _REOPEN, _DIAGNOSIS, _REOPEN])
        self.assertEqual(len(items), 1)


class TestEverythingElseStaysNever(unittest.TestCase):
    def test_low_confidence_alone_is_not_rediagnosed(self):
        _, items, _ = _advertise([_DIAGNOSIS])
        self.assertEqual(items, [])

    def test_a_comment_without_the_marker_is_not_a_reopen(self):
        prose = {"body": "Recurred after close: occurrence 3."}
        _, items, _ = _advertise([_DIAGNOSIS, prose, _BUMP])
        self.assertEqual(items, [])


class TestRediagnoseLabel(unittest.TestCase):
    def test_label_rediagnoses_and_is_consumed(self):
        provider, items, calls = _advertise([_DIAGNOSIS], labels=(FINDING_LABEL, REDIAGNOSE_LABEL))
        self.assertEqual(len(items), 1)
        with patch("specfuse.agent.providers.findings_diagnose.load_monitoring_config", return_value=_CONFIG):
            provider.execute(items[0])
        posted = [c for c in calls if c[:3] == ["gh", "issue", "comment"]]
        removed = [c for c in calls if c[:3] == ["gh", "issue", "edit"] and "--remove-label" in c]
        self.assertEqual(len(posted), 1)
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0][removed[0].index("--remove-label") + 1], REDIAGNOSE_LABEL)
        self.assertLess(calls.index(posted[0]), calls.index(removed[0]))

    def test_no_label_no_label_write(self):
        provider, items, calls = _advertise([_DIAGNOSIS, _REOPEN])
        with patch("specfuse.agent.providers.findings_diagnose.load_monitoring_config", return_value=_CONFIG):
            provider.execute(items[0])
        self.assertFalse([c for c in calls if "--remove-label" in c])


class TestReopenCommentCarriesTheMarker(unittest.TestCase):
    def test_record_finding_reopen_comment_is_recognised(self):
        calls = []

        def gh(args, check=True):
            calls.append(args)
            if args[:3] == ["gh", "issue", "list"]:
                body = issues._render_body(
                    "fp", _artifact(), occurrences=2, last_seen=1000.0, first_seen=500.0
                )
                return SimpleNamespace(returncode=0, stdout=json.dumps(
                    [{"number": 9, "body": body, "title": "t", "state": "CLOSED",
                      "closedAt": "1970-01-23T00:00:00Z"}]), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        issues.record_finding("fp", _artifact(), "o/r", runner=gh, now=2_000_000.0)
        comment = next(c for c in calls if c[:3] == ["gh", "issue", "comment"])
        text = comment[comment.index("--body") + 1]
        self.assertTrue(is_reopen_comment(text))
        self.assertIn("Recurred after close", text)

    def test_reader_fails_closed(self):
        for value in (None, "", 42, "<!-- specfuse:finding-reopened", "Recurred after close"):
            with self.subTest(value=value):
                self.assertFalse(is_reopen_comment(value))


def _artifact():
    return FailureArtifact(component="widget-api", check_type="error-logs", failure_class="E",
                           failure_signature="E:boom", observed_text="boom")


if __name__ == "__main__":
    unittest.main()
