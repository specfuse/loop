# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the answered-escalation provider (FEAT-2026-0049/T08).

Covers: selection (one `kind="escalation-answer"` item per open,
`NEEDS_HUMAN_LABEL`-carrying, correlation-marked issue with a comment
selecting a numbered option), the single acknowledgment `gh issue comment`
naming the option and correlation id, `NEEDS_HUMAN_LABEL` never removed,
idempotent re-runs writing nothing on a second pass, an issue with no
matching answer left untouched and not advertised, registration in
`default_providers()`, and no `git` command or `gh issue close` of the
provider's own.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.answers import AnsweredEscalationProvider
from specfuse.agent.run import KIND_ESCALATION_ANSWER, STATUS_COMPLETED, default_providers
from specfuse.agent.state import AgentSnapshot, IssueSummary
from specfuse.loop.escalation import NEEDS_HUMAN_LABEL, render_escalation_body


def _snapshot(issues: tuple) -> AgentSnapshot:
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


def _issue(number: int, title: str = "an escalation") -> IssueSummary:
    return IssueSummary(
        number=number,
        title=title,
        labels=(NEEDS_HUMAN_LABEL,),
        triage_category=None,
        triage_confidence=None,
    )


def _body(correlation_id: str = "corr-1") -> str:
    return render_escalation_body(
        correlation_id,
        category="blocked-wu",
        done_so_far="did things",
        issue_summary="a thing happened",
        decision_needed="pick one",
        why_not_auto="can't decide alone",
        options=[
            ("Do A", "unblocks fast", "costs time"),
            ("Do B", "safer", "slower"),
        ],
        recommendation="Do A",
    )


def _view_runner(body: str, comments: list, calls: list):
    def runner(argv, check: bool = False):
        calls.append(list(argv))
        if argv[:3] == ["gh", "issue", "view"]:
            import json

            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"body": body, "comments": comments}),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


class TestAnsweredEscalations(unittest.TestCase):
    def test_numbered_reply_is_parsed_and_acknowledged(self):
        calls = []
        runner = _view_runner(
            _body("corr-1"),
            [{"body": "1"}],
            calls,
        )
        provider = AnsweredEscalationProvider(repo="o/r", runner=runner)

        items = provider.advertise(_snapshot((_issue(9),)))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, KIND_ESCALATION_ANSWER)
        self.assertEqual(items[0].item_id, "escalation-answer-9")

        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_COMPLETED)

        comment_calls = [
            c for c in calls if c[:3] == ["gh", "issue", "comment"] and "--body" in c
        ]
        self.assertEqual(len(comment_calls), 1)
        body_arg = comment_calls[0][comment_calls[0].index("--body") + 1]
        self.assertIn("corr-1", body_arg)
        self.assertIn("Do A", body_arg)

    def test_needs_human_label_is_not_removed(self):
        calls = []
        runner = _view_runner(_body("corr-2"), [{"body": "2"}], calls)
        provider = AnsweredEscalationProvider(repo="o/r", runner=runner)

        items = provider.advertise(_snapshot((_issue(10),)))
        provider.execute(items[0])

        remove_label_calls = [
            c
            for c in calls
            if c[:3] == ["gh", "issue", "edit"] and "--remove-label" in c
        ]
        self.assertEqual(remove_label_calls, [])

    def test_second_pass_over_acknowledged_issue_writes_nothing(self):
        calls = []
        runner = _view_runner(_body("corr-3"), [{"body": "1"}], calls)
        provider = AnsweredEscalationProvider(repo="o/r", runner=runner)

        items = provider.advertise(_snapshot((_issue(11),)))
        provider.execute(items[0])

        first_pass_calls = len(calls)

        ack_comment_body = calls[-1][calls[-1].index("--body") + 1]
        runner2 = _view_runner(
            _body("corr-3"),
            [{"body": "1"}, {"body": ack_comment_body}],
            calls,
        )
        provider2 = AnsweredEscalationProvider(repo="o/r", runner=runner2)
        items2 = provider2.advertise(_snapshot((_issue(11),)))

        self.assertEqual(items2, [])
        self.assertEqual(len(calls), first_pass_calls + 1)  # only the second view call

    def test_unmatched_comment_is_left_untouched_and_not_advertised(self):
        calls = []
        runner = _view_runner(_body("corr-4"), [{"body": "not a numbered reply"}], calls)
        provider = AnsweredEscalationProvider(repo="o/r", runner=runner)

        items = provider.advertise(_snapshot((_issue(12),)))
        self.assertEqual(items, [])

        writing_calls = [
            c for c in calls if c[:3] in (["gh", "issue", "comment"], ["gh", "issue", "edit"])
        ]
        self.assertEqual(writing_calls, [])

    def test_default_providers_registers_answered_escalation_provider(self):
        providers = default_providers(repo="o/r")

        self.assertIn(
            "AnsweredEscalationProvider", [type(p).__name__ for p in providers]
        )

    def test_execute_issues_no_git_mutation_or_issue_close(self):
        calls = []
        runner = _view_runner(_body("corr-5"), [{"body": "1"}], calls)
        provider = AnsweredEscalationProvider(repo="o/r", runner=runner)

        items = provider.advertise(_snapshot((_issue(13),)))
        provider.execute(items[0])

        self.assertFalse(any(c and c[0] == "git" for c in calls))
        close_calls = [c for c in calls if c[:3] == ["gh", "issue", "close"]]
        self.assertEqual(close_calls, [])


if __name__ == "__main__":
    unittest.main()
