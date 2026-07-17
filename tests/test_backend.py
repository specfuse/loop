#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for Backend lifecycle hooks and make_backend factory.

Uses the same integration_workspace / write_minimal_feature / _patch
patterns as test_driver_integration.py. StubBackend exercises all three
hooks end-to-end through a minimal run() scenario.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, with_deliverable

loop = load_loop()


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                           branch: str, wus: list,
                           gate_status: str = "open") -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = list(wus) + [
        (f"{feature_id}/G1-RETRO", "retrospective", "pending"),
        (f"{feature_id}/G1-LESSONS", "lessons", "pending"),
        (f"{feature_id}/G1-DOCS", "docs", "pending"),
        (f"{feature_id}/G1-PLAN", "plan-next", "pending"),
    ]

    plan_wu_rows = []
    for i, (wu_id, _wu_type, _wu_status) in enumerate(all_wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i-1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Backend hook test fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise backend lifecycle hooks
status: active
---

# Plan: {slug}

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
{chr(10).join(plan_wu_rows)}
```
"""
    (fdir / "PLAN.md").write_text(plan)
    (fdir / "GATE-01.md").write_text(
        f"---\ngate: 1\nstatus: {gate_status}\n---\n\n# Gate 1\n"
    )

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
        )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


# --------------------------------------------------------------------------- #
# StubBackend                                                                  #
# --------------------------------------------------------------------------- #


class StubBackend(loop.Backend):
    """Records every lifecycle hook call to a shared ordered event list."""

    def __init__(self, events: list):
        self._events = events

    def on_feature_start(self, feature_id: str, feat_fm: dict) -> None:
        self._events.append(("on_feature_start", feature_id))

    def on_gate_passed(self, feature_id: str, gate_number: int) -> None:
        self._events.append(("on_gate_passed", feature_id, gate_number))

    def on_feature_complete(self, feature_id: str) -> None:
        self._events.append(("on_feature_complete", feature_id))


# --------------------------------------------------------------------------- #
# Unit tests — Backend no-ops and make_backend factory                        #
# --------------------------------------------------------------------------- #


class TestBackendNoOps(unittest.TestCase):

    def test_on_feature_start_returns_none(self):
        b = loop.Backend()
        result = b.on_feature_start("FEAT-X", {})
        self.assertIsNone(result)

    def test_on_gate_passed_returns_none(self):
        b = loop.Backend()
        result = b.on_gate_passed("FEAT-X", 1)
        self.assertIsNone(result)

    def test_on_feature_complete_returns_none(self):
        b = loop.Backend()
        result = b.on_feature_complete("FEAT-X")
        self.assertIsNone(result)

    def test_make_backend_returns_backend_instance(self):
        b = loop.make_backend({})
        self.assertIsInstance(b, loop.Backend)

    def test_make_backend_returns_backend_instance_with_nonempty_fm(self):
        b = loop.make_backend({"feature_id": "FEAT-X", "branch": "feat/x"})
        self.assertIsInstance(b, loop.Backend)


# --------------------------------------------------------------------------- #
# Integration tests — StubBackend through run()                               #
# --------------------------------------------------------------------------- #


class TestBackendLifecycleIntegration(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        # Dispatch stubs must write a deliverable or the presence gate
        # (FEAT-2026-0022) rejects the WU as hollow. See #150 —
        # `.specfuse/.loop.lock` used to stand in as the deliverable.
        if name == "dispatch":
            replacement = with_deliverable(replacement)
        setattr(loop, name, replacement)

    def test_on_feature_start_fires_before_dispatch_on_blocked_run(self):
        """on_feature_start fires before any dispatch; on_gate_passed and
        on_feature_complete do NOT fire when a WU is blocked."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-8001", "hooks-blocked",
                                  "feat/hooks-blocked", [
                                      ("FEAT-2026-8001/T01", "implementation", "pending"),
                                  ])

            events: list = []
            stub = StubBackend(events)

            def fake_make_backend(feat_fm):
                return stub

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                events.append(("dispatch", wu.wu_id))
                return ("```result\nstatus: blocked\n"
                        "blocked_reason: simulated block\n```\n")

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub)"

            self._patch("make_backend", fake_make_backend)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            event_names = [e[0] for e in events]
            # on_feature_start must appear and be first
            self.assertIn("on_feature_start", event_names)
            self.assertLess(
                event_names.index("on_feature_start"),
                event_names.index("dispatch"),
                "on_feature_start must fire before the first dispatch",
            )
            # gate not completed — on_gate_passed must not fire
            self.assertNotIn("on_gate_passed", event_names)
            # feature not complete — on_feature_complete must not fire
            self.assertNotIn("on_feature_complete", event_names)

    def test_on_gate_passed_fires_after_set_gate(self):
        """on_gate_passed fires after the gate flips to awaiting_review on a
        successful gate run. on_feature_complete does NOT fire (gate is now
        awaiting_review, not passed)."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-8002", "hooks-pass",
                                  "feat/hooks-pass", [
                                      ("FEAT-2026-8002/T01", "implementation", "pending"),
                                  ])

            events: list = []
            stub = StubBackend(events)

            def fake_make_backend(feat_fm):
                return stub

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                events.append(("dispatch", wu.wu_id))
                return "(stub agent output)\n"

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub)"

            self._patch("make_backend", fake_make_backend)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            event_names = [e[0] for e in events]
            self.assertIn("on_feature_start", event_names)
            self.assertIn("on_gate_passed", event_names)
            # Gate is awaiting_review, not passed — feature_complete must not fire
            self.assertNotIn("on_feature_complete", event_names)

    def test_on_feature_complete_fires_when_all_gates_passed(self):
        """on_feature_complete fires (and only it fires, no dispatch) when
        run() finds all gates already passed."""
        with integration_workspace() as root:
            os.chdir(root)
            # Write feature with gate already in 'passed' status.
            write_minimal_feature(root, "FEAT-2026-8003", "hooks-complete",
                                  "feat/hooks-complete", [
                                      ("FEAT-2026-8003/T01", "implementation", "done"),
                                  ], gate_status="passed")

            events: list = []
            stub = StubBackend(events)

            def fake_make_backend(feat_fm):
                return stub

            self._patch("make_backend", fake_make_backend)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            event_names = [e[0] for e in events]
            self.assertIn("on_feature_start", event_names)
            self.assertIn("on_feature_complete", event_names)
            self.assertNotIn("dispatch", event_names)
            self.assertNotIn("on_gate_passed", event_names)


if __name__ == "__main__":
    unittest.main()
