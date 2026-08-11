# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the provider seam (FEAT-2026-0049/T05).

Covers: the kind vocabulary gains `triage` and `escalation-answer` without
disturbing gate 1's bug/feature ranking, an unknown kind is still parked
with an escalation, a provider's reported spend reaches `RunBudget` and the
run summary, `default_providers()` is the empty seam `main()` wires in, and
an escalated outcome either files a needs-human issue exactly once (even
across two runs of the same item) or is reported as summary-only when the
provider supplies no payload.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import (
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    KIND_BUG,
    KIND_ESCALATION_ANSWER,
    KIND_FEATURE,
    KIND_TRIAGE,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    default_providers,
    run_agent,
)


class _FakeClock:
    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now


def _snapshot_only_runner(calls=None):
    def runner(argv, check=False):
        if calls is not None:
            calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    return runner


class _RecordingProvider:
    def __init__(self, items):
        self._items = {item.item_id: item for item in items}
        self.executed = []

    def advertise(self, snapshot):
        return tuple(self._items.values())

    def execute(self, item):
        self.executed.append(item.item_id)
        del self._items[item.item_id]
        return ActionOutcome(status=STATUS_COMPLETED)

    def reconcile(self, item, outcome):
        pass


def _run(providers, policy_yaml=None, **kwargs):
    with tempfile.TemporaryDirectory() as tmp:
        specfuse_dir = Path(tmp) / ".specfuse"
        specfuse_dir.mkdir()
        features_root = specfuse_dir / "features"
        features_root.mkdir()
        policy_path = specfuse_dir / "agent-policy.yml"
        if policy_yaml is not None:
            policy_path.write_text(policy_yaml)

        return run_agent(
            specfuse_dir=specfuse_dir,
            repo="acme/widget",
            runner=kwargs.pop("runner", _snapshot_only_runner()),
            providers=providers,
            policy_path=str(policy_path),
            features_root=features_root,
            clock=kwargs.pop("clock", _FakeClock()),
            **kwargs,
        )


class TestKindVocabulary(unittest.TestCase):

    def test_triage_item_is_selected_not_escalated(self):
        provider = _RecordingProvider(
            [ActionItem(item_id="triage-1", kind=KIND_TRIAGE)]
        )
        summary = _run((provider,))
        self.assertEqual(provider.executed, ["triage-1"])
        self.assertEqual(summary.items_completed, 1)
        self.assertEqual(summary.items_escalated, 0)

    def test_escalation_answer_ranks_before_a_preempting_bug(self):
        provider = _RecordingProvider(
            [
                ActionItem(item_id="bug-1", kind=KIND_BUG),
                ActionItem(item_id="answer-1", kind=KIND_ESCALATION_ANSWER),
            ]
        )
        _run((provider,), policy_yaml="rules:\n  bugs:\n    preempt: true\n")
        self.assertEqual(provider.executed[0], "answer-1")

    def test_gate1_ranking_unchanged_bugs_preempt_true(self):
        provider = _RecordingProvider(
            [
                ActionItem(item_id="feat-a", kind=KIND_FEATURE, queue_key="FEAT-1"),
                ActionItem(item_id="bug-1", kind=KIND_BUG),
            ]
        )
        _run(
            (provider,),
            policy_yaml="queue:\n  - FEAT-1\nrules:\n  bugs:\n    preempt: true\n",
        )
        self.assertEqual(provider.executed, ["bug-1", "feat-a"])

    def test_gate1_ranking_unchanged_bugs_preempt_false(self):
        provider = _RecordingProvider(
            [
                ActionItem(item_id="bug-1", kind=KIND_BUG),
                ActionItem(item_id="feat-a", kind=KIND_FEATURE, queue_key="FEAT-1"),
            ]
        )
        _run((provider,), policy_yaml="queue:\n  - FEAT-1\n")
        self.assertEqual(provider.executed, ["feat-a", "bug-1"])

    def test_unknown_kind_still_parked_with_escalation(self):
        provider = _RecordingProvider(
            [ActionItem(item_id="mystery-1", kind="something-new")]
        )
        summary = _run((provider,))
        self.assertEqual(provider.executed, [])
        self.assertEqual(summary.items_completed, 0)
        self.assertEqual(summary.items_escalated, 1)
        self.assertEqual(summary.escalations[0].item_id, "mystery-1")
        self.assertIn("unknown item kind", summary.escalations[0].reason)


class TestSpendLedger(unittest.TestCase):

    def test_reported_spend_reaches_budget_and_summary(self):
        class _SpendingProvider:
            def advertise(self, snapshot):
                return (ActionItem(item_id="bug-1", kind=KIND_BUG),)

            def execute(self, item):
                return ActionOutcome(status=STATUS_COMPLETED, spend=1234)

            def reconcile(self, item, outcome):
                pass

        summary = _run((_SpendingProvider(),))
        self.assertEqual(summary.tokens_spent, 1234)

    def test_no_spend_reported_leaves_total_zero(self):
        provider = _RecordingProvider([ActionItem(item_id="bug-1", kind=KIND_BUG)])
        summary = _run((provider,))
        self.assertEqual(summary.tokens_spent, 0)


class TestDefaultProviders(unittest.TestCase):

    def test_default_providers_returns_empty_registry(self):
        self.assertEqual(tuple(default_providers()), ())

    def test_run_agent_providers_default_is_empty_tuple(self):
        import inspect

        from specfuse.agent.run import run_agent as fn

        sig = inspect.signature(fn)
        self.assertEqual(sig.parameters["providers"].default, ())


class _EscalationGHRunner:
    """Fakes `gh issue list` / `gh issue create` well enough to exercise
    `emit_escalation`'s idempotency from inside `run_agent`."""

    def __init__(self):
        self.body = None
        self.create_calls = 0

    def __call__(self, argv, check=False):
        if argv[:3] == ["gh", "issue", "list"]:
            if self.body is not None:
                payload = [{"number": "42", "body": self.body}]
                return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        if argv[:3] == ["gh", "issue", "create"]:
            self.create_calls += 1
            self.body = argv[argv.index("--body") + 1]
            return SimpleNamespace(
                returncode=0, stdout="https://github.com/acme/widget/issues/42\n", stderr=""
            )
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")


def _escalating_provider(item_id, payload):
    class _Provider:
        def advertise(self, snapshot):
            return (ActionItem(item_id=item_id, kind=KIND_BUG),)

        def execute(self, item):
            return ActionOutcome(status=STATUS_ESCALATED, detail="needs a call", escalation=payload)

        def reconcile(self, item, outcome):
            pass

    return _Provider()


_PAYLOAD = EscalationPayload(
    done_so_far="Advertised bug-1, attempted a fix.",
    issue_summary="bug-1 needs an operator decision",
    decision_needed="Which of two remediation paths to take.",
    why_not_auto="Both paths have irreversible side effects.",
    options=[("path A", "fast", "riskier"), ("path B", "safe", "slower")],
    recommendation="path B",
)


class TestEscalationEmission(unittest.TestCase):

    def test_escalated_outcome_with_payload_files_one_issue_not_two(self):
        gh_runner = _EscalationGHRunner()
        provider = _escalating_provider("bug-1", _PAYLOAD)

        summary1 = _run((provider,), runner=gh_runner)
        self.assertEqual(gh_runner.create_calls, 1)
        self.assertIn("filed as issue 42", summary1.escalations[0].reason)

        provider2 = _escalating_provider("bug-1", _PAYLOAD)
        summary2 = _run((provider2,), runner=gh_runner)
        self.assertEqual(gh_runner.create_calls, 1)  # unchanged: found, not re-created
        self.assertIn("filed as issue 42", summary2.escalations[0].reason)

    def test_escalated_outcome_without_payload_is_summary_only(self):
        gh_runner = _EscalationGHRunner()
        provider = _escalating_provider("bug-2", None)

        summary = _run((provider,), runner=gh_runner)

        self.assertEqual(gh_runner.create_calls, 0)
        self.assertIn("summary only, no issue filed", summary.escalations[0].reason)


if __name__ == "__main__":
    unittest.main()
