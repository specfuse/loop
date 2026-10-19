# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Triage classifies an issue with its comments in view (#3520).

clabonte/generator#2804 and #2762 each carried a maintainer comment folding
the issue into a feature. The classification prompt held only the title and
body, so triage labelled both `bug`; the bug lane dispatched `/fix-bug`, which
read the comment, refused, and re-escalated a decision already made.
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

from specfuse.agent.providers.triage import TriageProvider
from specfuse.agent.state import AgentSnapshot
from specfuse.agent.triage_invoke import build_invocation
from specfuse.loop.triage import list_untriaged

_DECISION = ("**Decision:** option 1, folded into #2768. This issue closes "
             "with the #2768 work.")
_COMMENTS = [{
    "author": {"login": "maintainer"},
    "authorAssociation": "OWNER",
    "body": _DECISION,
}]


def _snapshot():
    return AgentSnapshot(
        queue=(), triage_auto=False, bug_automerge=False, bug_lane_limits={},
        issues=(), issues_error=None, prs=(), prs_error=None, features=(),
    )


class ListingFetchesComments(unittest.TestCase):
    def test_issue_listing_requests_comments(self):
        calls = []

        def runner(argv, check=False):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0, stdout=json.dumps([{
                "number": 2804, "title": "t", "body": "b", "labels": [],
                "comments": _COMMENTS,
            }]), stderr="")

        rows = list_untriaged(runner, "o/r")

        fields = calls[0][calls[0].index("--json") + 1].split(",")
        self.assertIn("comments", fields)
        self.assertEqual(rows[0]["comments"], _COMMENTS)


class PromptCarriesComments(unittest.TestCase):
    def test_comment_text_and_author_reach_the_prompt(self):
        _argv, prompt = build_invocation(2804, "t", "b", "o/r", comments=_COMMENTS)

        self.assertIn(_DECISION, prompt)
        self.assertIn("maintainer", prompt)
        self.assertIn("OWNER", prompt)

    def test_no_comments_leaves_the_prompt_unchanged(self):
        _argv, before = build_invocation(1, "t", "b", "o/r")
        _argv, after = build_invocation(1, "t", "b", "o/r", comments=[])

        self.assertEqual(before, after)


class ProviderPassesCommentsToTheClassifier(unittest.TestCase):
    def test_classification_session_sees_the_maintainer_comment(self):
        prompts = []

        def fake_run_claude(argv, prompt, runner=None):
            prompts.append(prompt)
            return SimpleNamespace(
                text="<!-- specfuse:triage category=feature confidence=high -->",
                usage={},
            )

        def runner(argv, check=False):
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        provider = TriageProvider(repo="o/r", runner=runner)
        row = {
            "number": 2804, "title": "t", "body": "Body.", "labels": [],
            "comments": _COMMENTS,
            "already_structured": False, "needs_repair": False,
        }
        with patch("specfuse.agent.providers.triage.list_untriaged",
                   return_value=[row]), \
             patch("specfuse.agent.providers.triage.run_claude", fake_run_claude), \
             patch.object(TriageProvider, "_rubric_for_run", return_value={}), \
             patch.object(TriageProvider, "_projection_for_run", return_value={}):
            items = provider.advertise(_snapshot())
            provider.execute(items[0])

        self.assertEqual(len(prompts), 1)
        self.assertIn(_DECISION, prompts[0])


if __name__ == "__main__":
    unittest.main()
