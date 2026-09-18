# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Gate 2's `feature_oracle` (FEAT-2026-0113/T02H): the tracer bullet for
`TriageProvider.execute`'s run-level write sequence.

Severity does not exist on this path yet -- this module pins only what a run
issues **today** for one untriaged issue: the triage marker written via
`gh issue edit --body`, then the category label via `--add-label`, in that
order. `FEAT-2026-0113/T06` extends this module with the severity assertions
its own criteria name; it does not rewrite the harness built here.
"""

from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.providers.triage import TriageProvider
from specfuse.agent.run import STATUS_COMPLETED
from specfuse.agent.state import AgentSnapshot


def _snapshot(triage_auto: bool = False) -> AgentSnapshot:
    return AgentSnapshot(
        queue=(),
        triage_auto=triage_auto,
        bug_automerge=False,
        bug_lane_limits={},
        issues=(),
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


def _row(number: int, title: str = "an issue", body: str = "body text"):
    return {
        "number": number,
        "title": title,
        "body": body,
        "labels": [],
        "already_structured": False,
        "needs_repair": False,
        "category": None,
        "confidence": "high",
    }


class TestTriageSeverityEndToEnd(unittest.TestCase):
    """The gate's thinnest end-to-end path: no live `gh` call, no network
    read -- an injected runner drives one untriaged issue through
    `TriageProvider.execute`, the double shape already used in
    `tests/test_agent_provider_triage.py`."""

    def test_execute_writes_marker_then_label_in_order(self):
        calls = []

        def runner(argv, check: bool = False):
            calls.append(list(argv))
            if argv[:3] == ["gh", "issue", "edit"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            # the headless classification invocation
            return SimpleNamespace(
                returncode=0,
                stdout="<!-- specfuse:triage category=bug confidence=high -->",
                stderr="",
            )

        provider = TriageProvider(repo="o/r", runner=runner)

        with patch(
            "specfuse.agent.providers.triage.list_untriaged",
            return_value=[_row(11)],
        ):
            items = provider.advertise(_snapshot())
            outcome = provider.execute(items[0])

        self.assertEqual(outcome.status, STATUS_COMPLETED)

        edit_calls = [c for c in calls if c[:3] == ["gh", "issue", "edit"]]
        self.assertEqual(len(edit_calls), 2)

        marker_call, label_call = edit_calls
        self.assertIn("--body", marker_call)
        self.assertNotIn("--add-label", marker_call)
        self.assertIn("--add-label", label_call)
        self.assertNotIn("--body", label_call)

        body_arg = marker_call[marker_call.index("--body") + 1]
        self.assertIn("category=bug", body_arg)
        self.assertIn("confidence=high", body_arg)

        label_arg = label_call[label_call.index("--add-label") + 1]
        self.assertEqual(label_arg, "triage:bug")


if __name__ == "__main__":
    unittest.main()
