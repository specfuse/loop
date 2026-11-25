#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A unit left `in_progress` by a killed run is reset by the next run (#3602).

A unit is `in_progress` only while a driver is running it. A driver killed
mid-attempt (a supervising shell's timeout, Ctrl-C) never moves it to an
outcome, so once that status is committed the next `specfuse run` used to halt
with "never became ready" and tell the operator to reset the frontmatter by
hand. The driver already knows the unit is orphaned: it holds the working
tree's `.specfuse/.loop.lock`, so no other driver in this tree can be running
it. These tests drive a real `loop.run()` on a synthetic feature in a temp git
repo, stubbing only the `claude -p` boundary (`loop.dispatch` / `loop.verify`),
the same seam as `tests/test_replan_end_to_end.py`.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_FEATURE_ID = "FEAT-TEST-3602"
_SLUG = "interrupted-fixture"
_BRANCH = f"feat/{_FEATURE_ID}-{_SLUG}"


def _status(path: Path) -> dict:
    fm, _ = loop.read_frontmatter(path)
    return fm


def _scaffold(root: Path, t01_status: str) -> Path:
    """Two units: T01 in *t01_status* with two attempts already recorded, and
    T02 pending behind it. Committed, as the pre-flight guard requires."""
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: interrupted-fixture\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Interrupted fixture | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Interrupted fixture\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: a killed run's unit is picked up again\n"
        "status: active\n"
        "---\n\n"
        f"# Plan: {_SLUG}\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {_FEATURE_ID}/T01\n"
        "        file: WU-T01.md\n"
        "        depends_on: []\n"
        f"      - id: {_FEATURE_ID}/T02\n"
        "        file: WU-T02.md\n"
        f"        depends_on: [{_FEATURE_ID}/T01]\n"
        "```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {_FEATURE_ID}/T01\ntype: implementation\n"
        f"model: claude-haiku-4-5-20251001\nstatus: {t01_status}\nattempts: 2\n"
        "---\n\n# T01\n\nFirst unit.\n"
    )
    (fdir / "WU-T02.md").write_text(
        f"---\nid: {_FEATURE_ID}/T02\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "---\n\n# T02\n\nSecond unit.\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold interrupted fixture"], check=True)
    return fdir


class InterruptedUnitIsResetTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []
        self.dispatched: list[str] = []

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            self.dispatched.append(wu.wu_id)
            # A real deliverable, so the no-deliverable guard sees work done.
            name = wu.wu_id.split("/")[-1].lower()
            Path(f"{name}.txt").write_text(f"{wu.wu_id}\n")
            return "```result\nstatus: complete\n```\n"

        def fake_verify(wu, feature_dir, gate_file=None):
            return True, "(stub)"

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", fake_verify)

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in reversed(self._patches):
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_a_unit_left_in_progress_is_reset_and_dispatched(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, "in_progress")

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0, "the gate must run, not halt on the unit")
            self.assertEqual(
                self.dispatched,
                [f"{_FEATURE_ID}/T01", f"{_FEATURE_ID}/T02"],
                "the interrupted unit is dispatched, then the one behind it")
            t01 = _status(fdir / "WU-T01.md")
            self.assertEqual(t01.get("status"), "done")
            # The killed attempt does not count: the fresh dispatch is attempt 1.
            self.assertEqual(int(t01.get("attempts")), 1)
            self.assertEqual(_status(fdir / "WU-T02.md").get("status"), "done")

            log = subprocess.run(
                ["git", "-C", str(root), "log", "--format=%s"],
                capture_output=True, text=True, check=True).stdout
            self.assertIn("interrupted", log,
                          "the reset is committed, so it is on record and "
                          "survives a failed attempt's reset to HEAD")

    def test_dry_run_reports_the_unit_without_writing(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, "in_progress")
            before = (fdir / "WU-T01.md").read_text()

            loop.run(None, dry_run=True)

            self.assertEqual((fdir / "WU-T01.md").read_text(), before)
            self.assertEqual(self.dispatched, [])

    def test_a_blocked_unit_is_left_for_the_operator(self):
        # Control: only `in_progress` is provably orphaned. `blocked_human`
        # is a deliberate stop that waits on a human re-arm.
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, "blocked_human")

            loop.run(None, dry_run=False)

            self.assertEqual(self.dispatched, [])
            self.assertEqual(_status(fdir / "WU-T01.md").get("status"),
                             "blocked_human")


if __name__ == "__main__":
    unittest.main()
