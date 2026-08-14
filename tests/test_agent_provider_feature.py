# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.agent.providers.feature (FEAT-2026-0049/T14).

Covers: `advertise`'s live re-read of feature state (a gate advance between
two calls changes `item_id`), `execute`'s halt-class-to-outcome table (one
test per row), `NEEDS_DRAFTING`/`BLOCKED`/`UNREADABLE` escalation shape, the
`gate_review`/`wip_limit` dials read through `queue_read`, registration in
`default_providers`, and the provider's no-git/no-mutating-gh structural
guarantee. No test invokes a real `specfuse run` -- a stub runner stands in
throughout, and every fixture feature folder lives under a temporary
directory.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.agent.providers.feature import FeatureProvider
from specfuse.agent.run import (
    KIND_FEATURE,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    default_providers,
)
from specfuse.agent.state import AgentSnapshot

_PLAN_TEMPLATE = (
    "---\n"
    "feature_id: {feature_id}\n"
    "status: {status}\n"
    "---\n\n"
    "```yaml\n"
    "gates:\n"
    "{gate_lines}"
    "```\n"
)

_GATE_TEMPLATE = "---\nstatus: {status}\n---\n\n# GATE-{num:02d}\n"


class _StubResult:
    def __init__(self, returncode, stderr=""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = ""


class _RecordingRunner:
    """Injected `runner`; `on_call` mutates fixture state to simulate what
    a real `specfuse run` subprocess would have written to disk."""

    def __init__(self, result, on_call=None):
        self._result = result
        self.calls = []
        self._on_call = on_call

    def __call__(self, argv, check=False):
        self.calls.append(argv)
        if self._on_call is not None:
            self._on_call()
        return self._result


def _write_feature(tmp_root: Path, feature_id: str, plan_status: str, gate_statuses: dict) -> Path:
    feature_dir = tmp_root / feature_id
    feature_dir.mkdir(parents=True, exist_ok=True)
    gate_lines = "".join(
        f"  - gate: {num}\n    file: GATE-{num:02d}.md\n" for num in gate_statuses
    )
    (feature_dir / "PLAN.md").write_text(
        _PLAN_TEMPLATE.format(feature_id=feature_id, status=plan_status, gate_lines=gate_lines)
    )
    for num, status in gate_statuses.items():
        (feature_dir / f"GATE-{num:02d}.md").write_text(_GATE_TEMPLATE.format(status=status, num=num))
    (feature_dir / "events.jsonl").write_text("")
    return feature_dir


def _set_gate_status(feature_dir: Path, num: int, status: str) -> None:
    (feature_dir / f"GATE-{num:02d}.md").write_text(_GATE_TEMPLATE.format(status=status, num=num))


def _set_plan_status(feature_dir: Path, feature_id: str, status: str, gate_statuses: dict) -> None:
    gate_lines = "".join(
        f"  - gate: {num}\n    file: GATE-{num:02d}.md\n" for num in gate_statuses
    )
    (feature_dir / "PLAN.md").write_text(
        _PLAN_TEMPLATE.format(feature_id=feature_id, status=status, gate_lines=gate_lines)
    )


def _append_event(feature_dir: Path, event_type: str, correlation_id: str, payload: dict) -> None:
    row = {
        "timestamp": "2026-08-11T00:00:00+00:00",
        "correlation_id": correlation_id,
        "event_type": event_type,
        "source": "driver",
        "source_version": "0.11.0",
        "payload": payload,
    }
    with (feature_dir / "events.jsonl").open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def _write_policy(tmp_root: Path, *, wip_limit: int = 1, gate_review: str = "human") -> Path:
    path = tmp_root / "agent-policy.yml"
    path.write_text(
        "version: 1\n"
        "queue: []\n"
        "rules:\n"
        "  features:\n"
        f"    gate_review: {gate_review}\n"
        f"    wip_limit: {wip_limit}\n"
    )
    return path


def _snapshot(queue: tuple) -> AgentSnapshot:
    return AgentSnapshot(
        queue=queue,
        triage_auto=False,
        bug_automerge=False,
        bug_lane_limits={},
        issues=(),
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


class TestFeatureProvider(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_awaiting_review_escalates_and_the_next_queue_entry_is_advertised(self):
        feat_a = _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        feat_b = _write_feature(self.root, "FEAT-B", "active", {1: "open", 2: "open"})
        policy_path = _write_policy(self.root, wip_limit=2, gate_review="human")

        provider = FeatureProvider(
            repo="o/r", runner=_RecordingRunner(_StubResult(0)),
            policy_path=str(policy_path), features_root=self.root,
        )

        items = provider.advertise(_snapshot(("FEAT-A", "FEAT-B")))
        by_queue_key = {item.queue_key: item for item in items}
        self.assertIn("FEAT-A", by_queue_key)
        self.assertIn("FEAT-B", by_queue_key)

        def _flip_a_to_awaiting_review():
            _set_gate_status(feat_a, 1, "awaiting_review")

        provider._runner = _RecordingRunner(_StubResult(0), on_call=_flip_a_to_awaiting_review)
        outcome_a = provider.execute(by_queue_key["FEAT-A"])
        self.assertEqual(outcome_a.status, STATUS_ESCALATED)
        self.assertEqual(outcome_a.escalation.category, "gate-review")

        def _advance_b():
            _set_gate_status(feat_b, 1, "passed")

        provider._runner = _RecordingRunner(_StubResult(0), on_call=_advance_b)
        outcome_b = provider.execute(by_queue_key["FEAT-B"])
        self.assertEqual(outcome_b.status, STATUS_COMPLETED)

    def test_item_id_shape_for_workable_entry(self):
        _write_feature(self.root, "FEAT-A", "active", {1: "open", 2: "open"})
        provider = FeatureProvider(repo="o/r", runner=_RecordingRunner(_StubResult(0)), features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_id, "feature-FEAT-A-g1")
        self.assertEqual(items[0].kind, KIND_FEATURE)
        self.assertEqual(items[0].queue_key, "FEAT-A")

    def test_advertise_rereads_live_state_and_item_id_changes_between_calls(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open", 2: "open"})
        provider = FeatureProvider(repo="o/r", runner=_RecordingRunner(_StubResult(0)), features_root=self.root)

        first = provider.advertise(_snapshot(("FEAT-A",)))
        self.assertEqual(first[0].item_id, "feature-FEAT-A-g1")

        _set_gate_status(feat_dir, 1, "passed")

        second = provider.advertise(_snapshot(("FEAT-A",)))
        self.assertEqual(second[0].item_id, "feature-FEAT-A-g2")
        self.assertNotEqual(first[0].item_id, second[0].item_id)

    def test_halt_advanced_completes_with_no_escalation(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open", 2: "open"})
        runner = _RecordingRunner(_StubResult(0), on_call=lambda: _set_gate_status(feat_dir, 1, "passed"))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)

    def test_halt_feature_done_completes_with_no_escalation(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "passed"})
        runner = _RecordingRunner(
            _StubResult(0),
            on_call=lambda: _set_plan_status(feat_dir, "FEAT-A", "done", {1: "passed"}),
        )
        # Force a workable classification with an unpassed gate so advertise
        # produces an item; the feature completes during execute.
        _set_gate_status(feat_dir, 1, "open")
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)

    def test_halt_awaiting_review_under_human_escalates_gate_review(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        policy_path = _write_policy(self.root, gate_review="human")
        runner = _RecordingRunner(_StubResult(0), on_call=lambda: _set_gate_status(feat_dir, 1, "awaiting_review"))
        provider = FeatureProvider(repo="o/r", runner=runner, policy_path=str(policy_path), features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertIsNotNone(outcome.escalation)
        self.assertEqual(outcome.escalation.category, "gate-review")

    def test_halt_awaiting_review_under_auto_completes_with_no_escalation(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        policy_path = _write_policy(self.root, gate_review="auto")
        runner = _RecordingRunner(_StubResult(0), on_call=lambda: _set_gate_status(feat_dir, 1, "awaiting_review"))
        provider = FeatureProvider(repo="o/r", runner=runner, policy_path=str(policy_path), features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_COMPLETED)
        self.assertIsNone(outcome.escalation)
        self.assertIn("awaiting_review", outcome.detail)

    def test_halt_not_armed_escalates_gate_review(self):
        _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        runner = _RecordingRunner(_StubResult(2))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "gate-review")
        self.assertIn("arm-gate", outcome.escalation.recommendation)

    def test_halt_blocked_escalates_blocked_wu_with_wu_id_and_reason(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open"})

        def _emit_block():
            _append_event(
                feat_dir, "human_escalation", "FEAT-A/T01",
                {"reason": "ambiguous spec"},
            )

        runner = _RecordingRunner(_StubResult(1), on_call=_emit_block)
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "blocked-wu")
        self.assertIn("FEAT-A/T01", outcome.detail)
        self.assertIn("ambiguous spec", outcome.detail)

    def test_halt_driver_error_escalates_blocked_wu_with_stderr(self):
        _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        runner = _RecordingRunner(_StubResult(1, stderr="Traceback: boom"))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "blocked-wu")
        self.assertIn("boom", outcome.detail)

    def test_needs_drafting_reaches_no_driver_invocation(self):
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-MISSING",)))
        self.assertEqual(len(items), 1)
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "drafting-needed")
        self.assertIn("FEAT-2026-0050", outcome.escalation.why_not_auto)
        self.assertEqual(runner.calls, [])
        for argv in runner.calls:
            self.assertNotIn("draft-feature", argv)

    def test_blocked_entry_escalates_blocked_wu_with_disposition_in_detail(self):
        _write_feature(self.root, "FEAT-A", "blocked", {1: "open"})
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "blocked-wu")
        self.assertIn("blocked", outcome.detail)
        self.assertEqual(runner.calls, [])

    def test_unreadable_entry_escalates_blocked_wu_with_disposition_in_detail(self):
        feature_dir = self.root / "FEAT-BAD"
        feature_dir.mkdir()
        (feature_dir / "PLAN.md").write_text("not frontmatter at all")
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-BAD",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_ESCALATED)
        self.assertEqual(outcome.escalation.category, "blocked-wu")
        self.assertIn("unreadable", outcome.detail)
        self.assertEqual(runner.calls, [])

    def test_wip_limit_dial_caps_workable_items(self):
        _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        _write_feature(self.root, "FEAT-B", "active", {1: "open"})
        policy_path = _write_policy(self.root, wip_limit=1)
        provider = FeatureProvider(repo="o/r", runner=_RecordingRunner(_StubResult(0)), policy_path=str(policy_path), features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A", "FEAT-B")))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].queue_key, "FEAT-A")

    def test_gate_review_dial_switches_between_human_and_auto(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        auto_policy = _write_policy(self.root, gate_review="auto")

        runner = _RecordingRunner(_StubResult(0), on_call=lambda: _set_gate_status(feat_dir, 1, "awaiting_review"))
        provider = FeatureProvider(repo="o/r", runner=runner, policy_path=str(auto_policy), features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        self.assertEqual(outcome.status, STATUS_COMPLETED)

    def test_execute_only_invokes_driver_for_workable_items(self):
        _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-MISSING",)))
        provider.execute(items[0])
        self.assertEqual(runner.calls, [])

    def test_registered_in_default_providers(self):
        providers = default_providers(repo="o/r")
        self.assertIn("FeatureProvider", [type(p).__name__ for p in providers])

    def test_only_driver_invocation_no_git_or_mutating_gh(self):
        feat_dir = _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        runner = _RecordingRunner(_StubResult(0), on_call=lambda: _set_gate_status(feat_dir, 1, "passed"))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        provider.execute(items[0])
        self.assertEqual(len(runner.calls), 1)
        # One call, and it is the driver being advanced -- not `git`, not a
        # mutating `gh`. The argv's leading command is no longer fixed: a
        # conductor standing in a source checkout dispatches that source
        # rather than whatever `specfuse` is on PATH (#2186).
        self.assertEqual(runner.calls[0][-2:], ["--feature", "FEAT-A"])
        self.assertNotIn("git", runner.calls[0])
        self.assertNotIn("gh", runner.calls[0])

    def test_reconcile_is_a_noop(self):
        _write_feature(self.root, "FEAT-A", "active", {1: "open"})
        runner = _RecordingRunner(_StubResult(0))
        provider = FeatureProvider(repo="o/r", runner=runner, features_root=self.root)
        items = provider.advertise(_snapshot(("FEAT-A",)))
        outcome = provider.execute(items[0])
        calls_before = list(runner.calls)
        result = provider.reconcile(items[0], outcome)
        self.assertIsNone(result)
        self.assertEqual(runner.calls, calls_before)


if __name__ == "__main__":
    unittest.main()
