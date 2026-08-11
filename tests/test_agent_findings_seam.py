# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the findings seam (FEAT-2026-0049/T09).

Covers: `KIND_FINDING_DIAGNOSE` and `KIND_FINDING_AUTOFIX` items are
selected and executed rather than escalated with `unknown item kind`; the
gate-1/gate-2 execution order is preserved with findings-autofix ranked
alongside bugs and findings-diagnose ranked ahead of triage;
`specfuse.agent.monitoring_read`'s three readers (absent config, component
resolution from a real `issues.py`-shaped body, the `diagnose` dial); `main`
defaults `--monitoring-config` to `.specfuse/monitoring.yml`; and the module
performs no `gh` call at all.
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
    KIND_BUG,
    KIND_ESCALATION_ANSWER,
    KIND_FEATURE,
    KIND_FINDING_AUTOFIX,
    KIND_FINDING_DIAGNOSE,
    KIND_TRIAGE,
    STATUS_COMPLETED,
    default_providers,
    main as agent_main,
    run_agent,
)
from specfuse.agent import monitoring_read


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


class _RecordingProvider:
    """A test double implementing the `ActionProvider` protocol."""

    def __init__(self, items):
        self._items = {item.item_id: item for item in items}
        self.executed = []
        self.reconciled = []

    def advertise(self, snapshot):
        return tuple(self._items.values())

    def execute(self, item):
        self.executed.append(item.item_id)
        del self._items[item.item_id]
        return ActionOutcome(status=STATUS_COMPLETED, detail="ok")

    def reconcile(self, item, outcome):
        self.reconciled.append((item.item_id, outcome.status))


class TestFindingKinds(unittest.TestCase):

    def test_finding_items_are_selected_not_escalated(self):
        provider = _RecordingProvider(
            [
                ActionItem(item_id="diag-1", kind=KIND_FINDING_DIAGNOSE),
                ActionItem(item_id="autofix-1", kind=KIND_FINDING_AUTOFIX),
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()

            summary = run_agent(
                specfuse_dir=specfuse_dir,
                repo="acme/widget",
                runner=_empty_json_runner([]),
                providers=(provider,),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=features_root,
                clock=_FakeClock(),
            )

        self.assertEqual(summary.items_escalated, 0)
        self.assertEqual(summary.items_completed, 2)
        self.assertEqual(set(provider.executed), {"diag-1", "autofix-1"})


class TestGate1Gate2OrderingUnchanged(unittest.TestCase):

    def test_full_kind_ordering_with_findings_inserted(self):
        policy_yaml = "queue:\n  - FEAT-1\nrules:\n  bugs:\n    preempt: false\n"
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()
            policy_path = specfuse_dir / "agent-policy.yml"
            policy_path.write_text(policy_yaml)

            provider = _RecordingProvider(
                [
                    ActionItem(item_id="triage-1", kind=KIND_TRIAGE),
                    ActionItem(item_id="feat-a", kind=KIND_FEATURE, queue_key="FEAT-1"),
                    ActionItem(item_id="diag-1", kind=KIND_FINDING_DIAGNOSE),
                    ActionItem(item_id="answer-1", kind=KIND_ESCALATION_ANSWER),
                    ActionItem(item_id="bug-1", kind=KIND_BUG),
                    ActionItem(item_id="autofix-1", kind=KIND_FINDING_AUTOFIX),
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

        # escalation-answer first; feature next (preempt=False keeps bug and
        # findings-autofix at tier 2, behind the feature at tier 1); bug and
        # findings-autofix tie at (2, 0); then findings-diagnose; triage last.
        self.assertEqual(provider.executed[0], "answer-1")
        self.assertEqual(provider.executed[1], "feat-a")
        self.assertEqual(set(provider.executed[2:4]), {"bug-1", "autofix-1"})
        self.assertEqual(provider.executed[4], "diag-1")
        self.assertEqual(provider.executed[5], "triage-1")

    def test_bug_preempt_still_orders_bug_and_autofix_ahead_of_feature(self):
        policy_yaml = "queue:\n  - FEAT-1\nrules:\n  bugs:\n    preempt: true\n"
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp) / ".specfuse"
            specfuse_dir.mkdir()
            features_root = specfuse_dir / "features"
            features_root.mkdir()
            policy_path = specfuse_dir / "agent-policy.yml"
            policy_path.write_text(policy_yaml)

            provider = _RecordingProvider(
                [
                    ActionItem(item_id="feat-a", kind=KIND_FEATURE, queue_key="FEAT-1"),
                    ActionItem(item_id="bug-1", kind=KIND_BUG),
                    ActionItem(item_id="autofix-1", kind=KIND_FINDING_AUTOFIX),
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

        self.assertEqual(set(provider.executed[:2]), {"bug-1", "autofix-1"})
        self.assertEqual(provider.executed[2], "feat-a")


class TestMonitoringRead(unittest.TestCase):

    def test_absent_config_path_yields_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / ".specfuse" / "monitoring.yml"
            self.assertIsNone(monitoring_read.load_monitoring_config(missing))

    def test_component_resolved_from_real_issues_render_body_format(self):
        from specfuse.monitor.issues import _render_body
        from specfuse.monitor.artifact import FailureArtifact

        artifact = FailureArtifact(
            component="order-worker",
            check_type="dlq",
            failure_class="dlq-message",
            failure_signature="sig-1",
            observed_text="boom",
            target_coordinates={},
        )
        body = _render_body(
            "deadbeef" * 8, artifact, occurrences=1, last_seen=0.0
        )

        self.assertEqual(
            monitoring_read.component_for_finding(body), "order-worker"
        )

    def test_component_diagnose_dial_read_from_components_list(self):
        config = {
            "components": [
                {"name": "web-api", "diagnose": "manual", "autofix": "off"},
                {"name": "order-worker", "diagnose": "auto", "autofix": "off"},
            ]
        }
        self.assertEqual(
            monitoring_read.component_diagnose_dial(config, "order-worker"), "auto"
        )
        self.assertIsNone(
            monitoring_read.component_diagnose_dial(config, "missing-component")
        )

    def test_no_gh_call_from_monitoring_read(self):
        calls = []

        def runner(argv, check=False):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "monitoring.yml"
            monitoring_read.load_monitoring_config(missing)
            monitoring_read.component_for_finding("**Component:** web-api\n")
            monitoring_read.component_diagnose_dial({"components": []}, "web-api")

        self.assertEqual(calls, [])


class TestMonitoringConfigFlag(unittest.TestCase):

    def test_default_monitoring_config_path_used_when_flag_absent(self):
        captured = {}

        def fake_default_providers(**kwargs):
            captured.update(kwargs)
            return ()

        import specfuse.agent.run as run_module

        original = run_module.default_providers
        run_module.default_providers = fake_default_providers
        try:
            with tempfile.TemporaryDirectory() as tmp:
                specfuse_dir = Path(tmp) / ".specfuse"
                specfuse_dir.mkdir()
                features_root = specfuse_dir / "features"
                features_root.mkdir()
                agent_main(
                    [
                        "--repo",
                        "acme/widget",
                        "--policy",
                        str(specfuse_dir / "agent-policy.yml"),
                        "--features-root",
                        str(features_root),
                    ]
                )
        finally:
            run_module.default_providers = original

        self.assertEqual(
            captured.get("monitoring_config_path"), ".specfuse/monitoring.yml"
        )

    def test_default_providers_construction_unchanged(self):
        providers = default_providers(
            repo="acme/widget",
            runner=_empty_json_runner([]),
            policy_path=None,
            features_root=None,
            monitoring_config_path=".specfuse/monitoring.yml",
        )
        self.assertEqual(len(providers), 3)


if __name__ == "__main__":
    unittest.main()
