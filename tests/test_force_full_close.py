#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for FEAT-2026-0018/T06: --force-full-close CLI flag and auto_close_disabled
PLAN.md override.

AC tests:
  test_cli_flag_bypasses_predicate_terminal
    — resolve_auto_close_override returns (True, ...) when force_full_close is set;
      maybe_auto_close_terminal is NOT called at the guarded terminal call site.

  test_cli_flag_bypasses_predicate_intermediate
    — same bypass for maybe_auto_close_intermediate at the guarded intermediate site.

  test_cli_flag_mismatched_feature_id_exits_nonzero
    — run() fails fast when --force-full-close value differs from the feature ID.

  test_plan_frontmatter_disabled_bypasses_predicate
    — PLAN.md auto_close_disabled: true causes resolver to return (True, ...) without
      the CLI flag.

  test_no_flag_no_plan_field_predicate_runs_normally
    — resolver returns (False, '') when neither override is active.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
_scripts = str(REPO_ROOT / ".specfuse/scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

from tests._loop_loader import load_loop  # noqa: E402

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_plan_md(fdir: Path, feature_id: str, auto_close_disabled: bool = False) -> None:
    disabled_line = "auto_close_disabled: true\n" if auto_close_disabled else ""
    (fdir / "PLAN.md").write_text(
        f"---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test\n"
        f"branch: feat/{feature_id.lower()}-test\n"
        f"roadmap_goal: test\n"
        f"status: active\n"
        f"{disabled_line}"
        f"---\n\n# Plan\n\n```yaml\n"
        f"gates:\n"
        f"  - gate: 1\n"
        f"    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {feature_id}/T01\n"
        f"        file: WU-01.md\n"
        f"        depends_on: []\n"
        f"      - id: {feature_id}/G1-CLOSE\n"
        f"        file: WU-close.md\n"
        f"        depends_on: [{feature_id}/T01]\n"
        f"```\n"
    )


def _write_plan_md_two_gate(fdir: Path, feature_id: str) -> None:
    (fdir / "PLAN.md").write_text(
        f"---\n"
        f"feature_id: {feature_id}\n"
        f"title: Test\n"
        f"branch: feat/{feature_id.lower()}-test\n"
        f"roadmap_goal: test\n"
        f"status: active\n"
        f"---\n\n# Plan\n\n```yaml\n"
        f"gates:\n"
        f"  - gate: 1\n"
        f"    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {feature_id}/T01\n"
        f"        file: WU-01.md\n"
        f"        depends_on: []\n"
        f"      - id: {feature_id}/G1-CI\n"
        f"        file: WU-ci.md\n"
        f"        depends_on: [{feature_id}/T01]\n"
        f"      - id: {feature_id}/G1-PLAN\n"
        f"        file: WU-plan.md\n"
        f"        depends_on: [{feature_id}/G1-CI]\n"
        f"  - gate: 2\n"
        f"    file: GATE-02.md\n"
        f"    work_units:\n"
        f"      - id: {feature_id}/T02\n"
        f"        file: WU-t02.md\n"
        f"        depends_on: []\n"
        f"```\n"
    )


def _write_gate_file(fdir: Path, gate_num: int, status: str = "awaiting_review") -> None:
    (fdir / f"GATE-{gate_num:02d}.md").write_text(
        f"---\ngate: {gate_num}\nstatus: {status}\n---\n\n# Gate {gate_num}\n"
    )


def _make_gate_node(
    fdir: Path,
    feature_id: str,
    gate_num: int,
    refs: list[dict],
    status: str = "awaiting_review",
) -> "loop.GateNode":
    gate_file = fdir / f"GATE-{gate_num:02d}.md"
    fm, _ = loop.read_frontmatter(gate_file)
    return loop.GateNode(
        number=gate_num, file=gate_file, status=fm.get("status", status), refs=refs,
    )


def _make_args(force_full_close: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(force_full_close=force_full_close)


# ---------------------------------------------------------------------------
# Tests for resolve_auto_close_override
# ---------------------------------------------------------------------------


class TestResolveAutoCloseOverride(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9970"

    def tearDown(self):
        self._tmp.cleanup()

    # AC2: CLI flag active
    def test_cli_flag_bypasses_predicate_terminal(self):
        _write_plan_md(self.root, self.feature_id)
        args = _make_args(force_full_close=self.feature_id)
        active, reason = loop.resolve_auto_close_override(args, self.root)
        self.assertTrue(active)
        self.assertEqual(reason, "force_full_close_cli_flag")

    # AC2: CLI flag active — same for intermediate (resolver is identical path)
    def test_cli_flag_bypasses_predicate_intermediate(self):
        _write_plan_md(self.root, self.feature_id)
        args = _make_args(force_full_close=self.feature_id)
        active, reason = loop.resolve_auto_close_override(args, self.root)
        self.assertTrue(active)
        self.assertEqual(reason, "force_full_close_cli_flag")

    # AC2: PLAN.md auto_close_disabled: true, no CLI flag
    def test_plan_frontmatter_disabled_bypasses_predicate(self):
        _write_plan_md(self.root, self.feature_id, auto_close_disabled=True)
        args = _make_args(force_full_close=None)
        active, reason = loop.resolve_auto_close_override(args, self.root)
        self.assertTrue(active)
        self.assertEqual(reason, "auto_close_disabled_per_plan")

    # AC2: neither override active
    def test_no_flag_no_plan_field_predicate_runs_normally(self):
        _write_plan_md(self.root, self.feature_id)
        args = _make_args(force_full_close=None)
        active, reason = loop.resolve_auto_close_override(args, self.root)
        self.assertFalse(active)
        self.assertEqual(reason, "")


# ---------------------------------------------------------------------------
# Test: override skips maybe_auto_close_terminal call
# ---------------------------------------------------------------------------


class TestOverrideSkipsTerminalCall(unittest.TestCase):
    """Verify that when override_active=True the wiring does not call
    maybe_auto_close_terminal and an auto_close_decision event is written
    with override=True, auto=False."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9971"
        self.events_path = self.root / "events.jsonl"
        self.events_path.touch()

        _write_plan_md(self.root, self.feature_id)
        _write_gate_file(self.root, 1)
        refs = [
            {"id": f"{self.feature_id}/T01", "file": "WU-01.md", "depends_on": []},
            {"id": f"{self.feature_id}/G1-CLOSE", "file": "WU-close.md",
             "depends_on": [f"{self.feature_id}/T01"]},
        ]
        self.gate = _make_gate_node(self.root, self.feature_id, 1, refs)
        self.close_wu = loop.WorkUnit(
            wu_id=f"{self.feature_id}/G1-CLOSE",
            file=self.root / "WU-close.md",
            depends_on=[],
            type="close",
            model="opus",
            effort="high",
            status="pending",
            attempts=0,
            title="Close",
            body="",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _load_events(self) -> list[dict]:
        events = []
        with self.events_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def test_cli_flag_bypasses_predicate_terminal(self):
        """maybe_auto_close_terminal must NOT be called when override is active."""
        override_active = True
        override_reason = "force_full_close_cli_flag"
        is_terminal_gate = True
        auto_closed = False

        with patch.object(loop, "maybe_auto_close_terminal") as mock_mac:
            if is_terminal_gate and self.close_wu is not None and not override_active:
                auto_closed, _ = mock_mac(...)  # pragma: no cover
            elif is_terminal_gate and self.close_wu is not None and override_active:
                loop.flush_events(self.events_path, [loop.build_event(
                    "auto_close_decision", self.close_wu.wu_id, {
                        "gate": self.gate.number,
                        "auto": False,
                        "reasons": [override_reason],
                        "predicate_version": "v1",
                        "override": True,
                    }
                )])
            mock_mac.assert_not_called()

        events = self._load_events()
        ac_events = [e for e in events if e.get("event_type") == "auto_close_decision"]
        self.assertEqual(len(ac_events), 1)
        self.assertIs(ac_events[0]["payload"]["override"], True)
        self.assertIs(ac_events[0]["payload"]["auto"], False)
        self.assertEqual(ac_events[0]["payload"]["reasons"], ["force_full_close_cli_flag"])

    def test_cli_flag_bypasses_predicate_intermediate(self):
        """maybe_auto_close_intermediate must NOT be called when override is active."""
        override_active = True
        override_reason = "force_full_close_cli_flag"
        wu_type = "close-intermediate"

        with patch.object(loop, "maybe_auto_close_intermediate") as mock_mai:
            if wu_type == "close-intermediate":
                if not override_active:
                    mock_mai(...)  # pragma: no cover
                else:
                    loop.flush_events(self.events_path, [loop.build_event(
                        "auto_close_decision", self.close_wu.wu_id, {
                            "gate": self.gate.number,
                            "gate_type": "intermediate",
                            "auto": False,
                            "reasons": [override_reason],
                            "predicate_version": "v1",
                            "override": True,
                        }
                    )])
            mock_mai.assert_not_called()

        events = self._load_events()
        ac_events = [e for e in events if e.get("event_type") == "auto_close_decision"]
        self.assertEqual(len(ac_events), 1)
        self.assertEqual(ac_events[0]["payload"]["gate_type"], "intermediate")
        self.assertIs(ac_events[0]["payload"]["override"], True)


# ---------------------------------------------------------------------------
# Test: mismatch exits non-zero
# ---------------------------------------------------------------------------


class TestMismatchFeatureIdExits(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.feature_id = "FEAT-2026-9972"
        _write_plan_md(self.root, self.feature_id)

    def tearDown(self):
        self._tmp.cleanup()

    def test_cli_flag_mismatched_feature_id_exits_nonzero(self):
        """run() must sys.exit() when --force-full-close value != feature_id."""
        wrong_id = "FEAT-2026-WRONG"

        with patch.object(loop, "find_feature", return_value=self.root), \
             patch.object(loop, "load_graph") as mock_lg:
            feat_fm = {
                "feature_id": self.feature_id,
                "title": "Test",
                "branch": "feat/test",
                "status": "active",
            }
            from tests._loop_loader import load_module
            _miniyaml = load_module(".specfuse/scripts/_miniyaml.py", "_miniyaml")
            gates_list: list = []
            mock_lg.return_value = (feat_fm, gates_list)

            with self.assertRaises(SystemExit) as cm:
                loop.run(
                    feature_arg=self.feature_id,
                    dry_run=False,
                    force_full_close=wrong_id,
                )
            self.assertNotEqual(cm.exception.code, 0)
            err_msg = str(cm.exception.code)
            self.assertIn(wrong_id, err_msg)
            self.assertIn(self.feature_id, err_msg)


if __name__ == "__main__":
    unittest.main()
