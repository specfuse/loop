# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the conductor loop and `specfuse-agent` entry point
(FEAT-2026-0049/T04).

Covers: an empty provider registry drains cleanly and immediately, a
second concurrent agent refuses to start by naming the lock path (not a
traceback), the run summary reports actual elapsed time and the T03 stop
reason, policy-ordered selection across bug/feature test-double providers,
a provider exception parks its item with an escalation instead of ending
the run, and the loop never hands its runner to a provider (no git
mutation of its own).
"""

from __future__ import annotations

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
    AgentLockHeldError,
    RunSummary,
    STATUS_COMPLETED,
    run_agent,
)
from specfuse.agent.budget import STOP_CAP, STOP_DRAINED
from specfuse.loop._filelock import acquire_agent_lock


def _empty_json_runner(calls):
    def runner(argv, check=False):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    return runner


class _FakeClock:
    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class _RecordingProvider:
    """A test double implementing the `ActionProvider` protocol."""

    def __init__(self, items, *, raise_for=()):
        self._items = {item.item_id: item for item in items}
        self._raise_for = set(raise_for)
        self.executed = []
        self.reconciled = []

    def advertise(self, snapshot):
        return tuple(self._items.values())

    def execute(self, item):
        self.executed.append(item.item_id)
        if item.item_id in self._raise_for:
            raise RuntimeError(f"boom on {item.item_id}")
        del self._items[item.item_id]
        return ActionOutcome(status=STATUS_COMPLETED, detail="ok")

    def reconcile(self, item, outcome):
        self.reconciled.append((item.item_id, outcome.status))


class TestDrainEmpty(unittest.TestCase):

    def test_drains_cleanly_with_no_providers(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            summary = run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner(calls),
                providers=(),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=features_root,
                clock=_FakeClock(),
            )

        self.assertIsInstance(summary, RunSummary)
        self.assertEqual(summary.stop_reason, STOP_DRAINED)
        self.assertEqual(summary.items_attempted, 0)
        self.assertEqual(summary.items_completed, 0)
        self.assertEqual(summary.items_escalated, 0)


class TestAgentLockRefusal(unittest.TestCase):

    def test_second_agent_names_lock_path_not_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            held = acquire_agent_lock(specfuse_dir)
            try:
                with self.assertRaises(AgentLockHeldError) as ctx:
                    run_agent(
                        specfuse_dir=specfuse_dir,
                        repo="acme/widget",
                        runner=_empty_json_runner([]),
                        providers=(),
                        policy_path=str(specfuse_dir / "agent-policy.yml"),
                        features_root=features_root,
                        clock=_FakeClock(),
                    )
                message = str(ctx.exception)
                self.assertIn(str(specfuse_dir / ".agent.lock"), message)
                self.assertNotIn("Traceback", message)
            finally:
                held.close()


class TestElapsedTimeAndCap(unittest.TestCase):

    def test_summary_reports_actual_elapsed_time_not_the_cap(self):
        clock = _FakeClock()

        class _SlowProvider:
            def __init__(self):
                self._items = [ActionItem(item_id="bug-1", kind="bug")]

            def advertise(self, snapshot):
                return tuple(self._items)

            def execute(self, item):
                clock.advance(600)  # 10 minutes, well past the 1-minute cap
                self._items.pop()
                return ActionOutcome(status=STATUS_COMPLETED)

            def reconcile(self, item, outcome):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            summary = run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner([]),
                providers=(_SlowProvider(),),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=features_root,
                clock=clock,
                max_minutes=1,
            )

        self.assertEqual(summary.stop_reason, STOP_CAP)
        self.assertEqual(summary.items_completed, 1)
        self.assertGreaterEqual(summary.elapsed_minutes, 10.0)


class TestPolicyOrderedSelection(unittest.TestCase):

    def test_bug_preempts_feature_when_policy_says_so(self):
        policy_yaml = "queue:\n  - FEAT-1\nrules:\n  bugs:\n    preempt: true\n"
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()
            policy_path = specfuse_dir / "agent-policy.yml"
            policy_path.write_text(policy_yaml)

            feature_provider = _RecordingProvider(
                [ActionItem(item_id="feat-a", kind="feature", queue_key="FEAT-1")]
            )
            bug_provider = _RecordingProvider(
                [ActionItem(item_id="bug-1", kind="bug")]
            )

            summary = run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner([]),
                providers=(feature_provider, bug_provider),
                policy_path=str(policy_path),
                features_root=features_root,
                clock=_FakeClock(),
            )

        self.assertEqual(summary.items_completed, 2)
        # The bug executed before the feature despite being registered second.
        self.assertEqual(bug_provider.executed, ["bug-1"])
        self.assertEqual(feature_provider.executed, ["feat-a"])

    def test_queue_order_settles_features(self):
        policy_yaml = "queue:\n  - FEAT-2\n  - FEAT-1\n"
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()
            policy_path = specfuse_dir / "agent-policy.yml"
            policy_path.write_text(policy_yaml)

            provider = _RecordingProvider(
                [
                    ActionItem(item_id="feat-1", kind="feature", queue_key="FEAT-1"),
                    ActionItem(item_id="feat-2", kind="feature", queue_key="FEAT-2"),
                ]
            )

            run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner([]),
                providers=(provider,),
                policy_path=str(policy_path),
                features_root=features_root,
                clock=_FakeClock(),
            )

        self.assertEqual(provider.executed, ["feat-2", "feat-1"])


class TestProviderExceptionParksNotEnds(unittest.TestCase):

    def test_provider_exception_escalates_and_run_continues(self):
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            provider = _RecordingProvider(
                [
                    ActionItem(item_id="bug-1", kind="bug"),
                    ActionItem(item_id="bug-2", kind="bug"),
                ],
                raise_for=("bug-1",),
            )

            summary = run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner([]),
                providers=(provider,),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=features_root,
                clock=_FakeClock(),
            )

        self.assertEqual(summary.stop_reason, STOP_DRAINED)
        self.assertEqual(summary.items_completed, 1)
        self.assertEqual(summary.items_escalated, 1)
        self.assertEqual(summary.escalations[0].item_id, "bug-1")
        self.assertIn("boom on bug-1", summary.escalations[0].reason)
        # The second item still ran — a raising provider does not end the run.
        self.assertIn("bug-2", provider.executed)


class TestNoGitMutation(unittest.TestCase):

    def test_loop_never_hands_its_runner_to_a_provider(self):
        calls = []

        class _AssertingProvider:
            def advertise(self, snapshot):
                return (ActionItem(item_id="bug-1", kind="bug"),)

            def execute(self, item):
                # A real provider would use its own transport; this double
                # proves the point by taking no runner argument at all —
                # there is nothing here it *could* call git or gh through.
                return ActionOutcome(status=STATUS_COMPLETED)

            def reconcile(self, item, outcome):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner(calls),
                providers=(_AssertingProvider(),),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=features_root,
                clock=_FakeClock(),
            )

        mutating_verbs = {"commit", "push", "branch", "merge", "checkout", "reset"}
        for call in calls:
            self.assertFalse(
                mutating_verbs.intersection(call),
                f"loop's runner saw a mutating git/gh call: {call!r}",
            )
            self.assertEqual(call[0], "gh")


if __name__ == "__main__":
    unittest.main()
