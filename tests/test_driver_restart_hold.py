#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The sanctioned driver-restart halt (FEAT-2026-0075/T05).

Python caches `specfuse.loop.loop` in `sys.modules` at first import, so a work
unit that edits the driver changes nothing for anything this same process
dispatches next. `T02`/`T03` (gate 1) only ever print a warning; nothing stops
the run, which is why the hazard has cost four real dispatches (see
`RETROSPECTIVE.md`). This unit builds the mechanism that actually halts: a
named reason, a distinguished exit code, a resume instruction, and a durable
event — leaving every remaining work unit `pending` and the gate `open`, so a
fresh process picks the gate back up exactly where it stopped.

`T06` (not this unit) decides WHEN to fire the halt. This test drives the
halt function directly, at the `for wu in pending` seam shape (a sibling of
`_should_halt_for_budget`), not through `loop.run()` — there is no run-loop
wiring yet to drive through.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def _write_minimal_feature(root: Path, feature_id: str, slug: str,
                            branch: str) -> Path:
    """Scaffold a single-gate feature with two pending work units."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"

    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: {branch}\nroadmap_goal: test\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n---\n\n# T01{body}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{body}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


def _read_events(fdir: Path) -> list:
    events_path = fdir / "events.jsonl"
    if not events_path.is_file():
        return []
    return [json.loads(line) for line in events_path.read_text().splitlines()
            if line.strip()]


class TestFormatDriverRestartHaltUnit(unittest.TestCase):

    def test_empty_driver_paths_returns_empty_string(self):
        self.assertEqual(
            loop.format_driver_restart_halt(
                "FEAT-2026-9999/T01", [], ["FEAT-2026-9999/G1-CLOSE"],
                "python3 .specfuse/scripts/loop.py"),
            "")

    def test_names_wu_id(self):
        msg = loop.format_driver_restart_halt(
            "FEAT-2026-9999/T01", ["specfuse/loop/loop.py"],
            ["FEAT-2026-9999/G1-CLOSE"], "python3 .specfuse/scripts/loop.py")
        self.assertIn("FEAT-2026-9999/T01", msg)

    def test_names_every_driver_path(self):
        msg = loop.format_driver_restart_halt(
            "FEAT-2026-9999/T01",
            ["specfuse/loop/loop.py", "specfuse/loop/driver_edit.py"],
            ["FEAT-2026-9999/G1-CLOSE"], "python3 .specfuse/scripts/loop.py")
        self.assertIn("specfuse/loop/loop.py", msg)
        self.assertIn("specfuse/loop/driver_edit.py", msg)

    def test_names_every_remaining_wu_id(self):
        msg = loop.format_driver_restart_halt(
            "FEAT-2026-9999/T01", ["specfuse/loop/loop.py"],
            ["FEAT-2026-9999/T02", "FEAT-2026-9999/G1-CLOSE"],
            "python3 .specfuse/scripts/loop.py")
        self.assertIn("FEAT-2026-9999/T02", msg)
        self.assertIn("FEAT-2026-9999/G1-CLOSE", msg)

    def test_states_process_cannot_execute_the_edit(self):
        msg = loop.format_driver_restart_halt(
            "FEAT-2026-9999/T01", ["specfuse/loop/loop.py"],
            ["FEAT-2026-9999/G1-CLOSE"], "python3 .specfuse/scripts/loop.py")
        self.assertIn("cannot execute", msg)

    def test_names_the_literal_resume_command(self):
        msg = loop.format_driver_restart_halt(
            "FEAT-2026-9999/T01", ["specfuse/loop/loop.py"],
            ["FEAT-2026-9999/G1-CLOSE"],
            "python3 .specfuse/scripts/loop.py --feature FEAT-2026-9999")
        self.assertIn(
            "python3 .specfuse/scripts/loop.py --feature FEAT-2026-9999", msg)


class TestHaltReasonAndExitCode(unittest.TestCase):

    def test_halt_reason_constant(self):
        self.assertEqual(
            loop.HALT_REASON_DRIVER_RESTART, "driver_restart_required")

    def test_exit_code_is_distinguished(self):
        self.assertNotIn(loop.EXIT_DRIVER_RESTART_REQUIRED, (0, 1, 2))


class TestHaltForDriverRestart(unittest.TestCase):
    """Drives the halt function directly at the run-loop seam."""

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_halt_leaves_gate_open_and_units_pending(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9301"
            fdir = _write_minimal_feature(
                root, feature_id, "restart-hold", "feat/restart-hold")
            events_path = fdir / "events.jsonl"
            t01_id = f"{feature_id}/T01"
            close_id = f"{feature_id}/G1-CLOSE"

            rc = loop._halt_for_driver_restart(
                gate_number=1,
                feature_id=feature_id,
                events_path=events_path,
                wu_id=t01_id,
                driver_paths=["specfuse/loop/loop.py"],
                remaining_wu_ids=[close_id],
                resume_command="python3 .specfuse/scripts/loop.py",
            )

            self.assertEqual(rc, loop.EXIT_DRIVER_RESTART_REQUIRED)

            gate_fm, _ = loop.read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm["status"], "open")

            t01_fm, _ = loop.read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm["status"], "pending")
            close_fm, _ = loop.read_frontmatter(fdir / "WU-close.md")
            self.assertEqual(close_fm["status"], "pending")

            events = _read_events(fdir)
            halts = [e for e in events
                     if e["event_type"] == "driver_staleness_detected"]
            self.assertEqual(len(halts), 1)
            payload = halts[0]["payload"]
            self.assertIs(payload["halted"], True)
            self.assertEqual(payload["remaining_wu_ids"], [close_id])
            self.assertEqual(
                payload["resume_command"], "python3 .specfuse/scripts/loop.py")

            # Durability (criterion 8): committed via commit_bookkeeping, so
            # the event survives even if the operator does not re-run
            # immediately — proved by resetting the working tree to HEAD
            # (what the driver's own per-attempt reset does) and re-reading.
            subprocess.run(["git", "-C", str(root), "reset", "--hard"],
                           check=True)
            events_after_reset = _read_events(fdir)
            self.assertEqual(events_after_reset, events)


if __name__ == "__main__":
    unittest.main()
