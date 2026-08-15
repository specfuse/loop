# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.agent.state (FEAT-2026-0049/T02).

Covers: `queue:` is read from the policy file (the first reader anywhere),
a missing policy file yields empty-queue/default-dials rather than an
exception, a failing/unparseable runner yields an empty section with a
recorded reason rather than a partial object, and the snapshot never issues
a mutating `gh` subcommand.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from specfuse.agent.state import gather_snapshot

_REPO = "acme-widget/example"

_RULES_BLOCK = (
    "rules:\n"
    "  bugs:\n"
    "    preempt: true\n"
    "    min_severity: low\n"
    '    automerge: "off"\n'
    "  features:\n"
    "    gate_review: human\n"
    "    wip_limit: 1\n"
    "  triage:\n"
    "    auto: false\n"
)

_TAIL_BLOCK = (
    "budgets:\n"
    "  max_tokens_per_run: 2000000\n"
    "  max_open_prs: 3\n"
    "  max_items_per_day: 10\n"
    "escalation:\n"
    '  webhook_env: ""\n'
    '  assignee: ""\n'
    '  quiet_hours: ""\n'
    "  sla_hours: 24\n"
)


def _write_policy(tmp: Path, *feat_ids: str) -> Path:
    queue_lines = "".join(f"  - {fid}\n" for fid in feat_ids)
    queue_block = f"queue:\n{queue_lines}" if feat_ids else "queue: []\n"
    text = f"version: 1\n{queue_block}{_RULES_BLOCK}{_TAIL_BLOCK}"
    path = tmp / "agent-policy.yml"
    path.write_text(text)
    return path


class _StubRunner:
    """Records every call and replays a scripted sequence of results."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return self._results.pop(0)


def _list_result(rows):
    return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")


def _empty_features_root(tmp: Path) -> Path:
    root = tmp / "features"
    root.mkdir()
    return root


class TestSnapshot(unittest.TestCase):
    def test_queue_read_from_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy_path = _write_policy(tmp_path, "FEAT-2026-0001", "FEAT-2026-0002")
            runner = _StubRunner([_list_result([]), _list_result([])])

            snapshot = gather_snapshot(
                runner,
                _REPO,
                policy_path=policy_path,
                features_root=_empty_features_root(tmp_path),
            )

            self.assertEqual(snapshot.queue, ("FEAT-2026-0001", "FEAT-2026-0002"))

    def test_missing_policy_yields_empty_queue_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runner = _StubRunner([_list_result([]), _list_result([])])

            snapshot = gather_snapshot(
                runner,
                _REPO,
                policy_path=tmp_path / "does-not-exist.yml",
                features_root=_empty_features_root(tmp_path),
            )

            self.assertEqual(snapshot.queue, ())
            self.assertFalse(snapshot.triage_auto)
            self.assertFalse(snapshot.bug_automerge)
            self.assertIn("max_diff_lines", snapshot.bug_lane_limits)

    def test_failing_runner_yields_empty_section_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy_path = _write_policy(tmp_path)
            failure = SimpleNamespace(returncode=1, stdout="", stderr="gh: not authenticated")
            runner = _StubRunner([failure, _list_result([])])

            snapshot = gather_snapshot(
                runner,
                _REPO,
                policy_path=policy_path,
                features_root=_empty_features_root(tmp_path),
            )

            self.assertEqual(snapshot.issues, ())
            self.assertIsNotNone(snapshot.issues_error)
            self.assertIn("not authenticated", snapshot.issues_error)

    def test_unparseable_runner_output_yields_empty_section_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy_path = _write_policy(tmp_path)
            bad_json = SimpleNamespace(returncode=0, stdout="not json", stderr="")
            runner = _StubRunner([_list_result([]), bad_json])

            snapshot = gather_snapshot(
                runner,
                _REPO,
                policy_path=policy_path,
                features_root=_empty_features_root(tmp_path),
            )

            self.assertEqual(snapshot.prs, ())
            self.assertIsNotNone(snapshot.prs_error)

    def test_no_mutating_gh_subcommand_issued(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy_path = _write_policy(tmp_path, "FEAT-2026-0001")
            runner = _StubRunner([
                _list_result([{"number": 1, "title": "bug", "labels": [], "body": ""}]),
                _list_result([{"number": 2, "title": "pr", "labels": []}]),
            ])

            gather_snapshot(
                runner,
                _REPO,
                policy_path=policy_path,
                features_root=_empty_features_root(tmp_path),
            )

            mutating = {"create", "edit", "comment", "close", "merge", "label"}
            for call in runner.calls:
                self.assertNotIn("--add-label", call)
                self.assertTrue(mutating.isdisjoint(call), f"mutating gh subcommand issued: {call}")
                self.assertIn("list", call)

    def test_issue_carries_triage_marker_and_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy_path = _write_policy(tmp_path)
            marked_body = (
                "<!-- specfuse:triage category=bug confidence=high -->\n\nSomething broke."
            )
            runner = _StubRunner([
                _list_result([
                    {
                        "number": 7,
                        "title": "it broke",
                        "labels": [{"name": "triage:bug"}],
                        "body": marked_body,
                    }
                ]),
                _list_result([]),
            ])

            snapshot = gather_snapshot(
                runner,
                _REPO,
                policy_path=policy_path,
                features_root=_empty_features_root(tmp_path),
            )

            self.assertEqual(len(snapshot.issues), 1)
            issue = snapshot.issues[0]
            self.assertEqual(issue.number, 7)
            self.assertEqual(issue.labels, ("triage:bug",))
            self.assertEqual(issue.triage_category, "bug")
            self.assertEqual(issue.triage_confidence, "high")

    def test_feature_folder_gathers_plan_status_and_gate_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            policy_path = _write_policy(tmp_path)
            features_root = tmp_path / "features"
            features_root.mkdir()
            feature_dir = features_root / "FEAT-2026-0099-example"
            feature_dir.mkdir()
            (feature_dir / "PLAN.md").write_text(
                "---\n"
                "feature_id: FEAT-2026-0099\n"
                "title: example\n"
                "branch: feat/example\n"
                "roadmap_goal: test\n"
                "status: active\n"
                "---\n\n"
                "# Plan\n\n"
                "```yaml\n"
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units: []\n"
                "```\n"
            )
            (feature_dir / "GATE-01.md").write_text(
                "---\nstatus: open\n---\n\n# Gate 1\n"
            )
            runner = _StubRunner([_list_result([]), _list_result([])])

            snapshot = gather_snapshot(
                runner,
                _REPO,
                policy_path=policy_path,
                features_root=features_root,
            )

            self.assertEqual(len(snapshot.features), 1)
            feature = snapshot.features[0]
            self.assertEqual(feature.feature_id, "FEAT-2026-0099")
            self.assertEqual(feature.status, "active")
            self.assertEqual(len(feature.gates), 1)
            self.assertEqual(feature.gates[0].status, "open")
            self.assertEqual(snapshot.features_errors, {})


if __name__ == "__main__":
    unittest.main()
