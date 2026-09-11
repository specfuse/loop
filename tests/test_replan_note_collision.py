#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Re-plan note collision (FEAT-2026-0104/T08).

`persist_attempt_notes` writes one `work/<wu>/attempt-N.md` per buffered
entry, keyed only by attempt number. A re-planned attempt buffers TWICE
under the SAME attempt number — the failure evidence that triggered the
re-plan (`loop.py` ~10743), then the re-plan turn's own transcript
(`loop.py` ~11005) — so the second write used to clobber the first and the
failure evidence for that attempt was not on disk anywhere, even though the
gate 2 spin-out brief points an operator at exactly these files.

This drives a real `loop.run()` (same seam as `test_replan_end_to_end.py`)
through a re-plan that then goes on to exhaust its attempts, so the
exhausted-attempts escalation path actually calls `persist_attempt_notes`
with a colliding attempt number, and asserts both records land on disk
under distinct names.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_FEATURE_ID = "FEAT-TEST-0104B"
_SLUG = "replan-collision-fixture"
_BRANCH = f"feat/{_FEATURE_ID}-{_SLUG}"
_ORIGINAL_BODY_MARKER = "ORIGINAL BODY — the pre-replan prompt.\n"
_REWRITTEN_BODY_MARKER = "REWRITTEN BODY — the re-plan turn's own output.\n"


def _scaffold(root: Path) -> Path:
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: replan-collision-fixture\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Replan collision fixture | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Replan collision fixture\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: exercise the replan/attempt-note collision path\n"
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
        "```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {_FEATURE_ID}/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "max_attempts: 3\nreplan_stub_trigger: true\n"
        f"---\n\n# T01\n\n{_ORIGINAL_BODY_MARKER}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold replan collision fixture"], check=True)
    return fdir


class ReplanNoteCollisionTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_replanned_attempt_keeps_both_failure_evidence_and_transcript(self):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            if wu.body.startswith(loop._REPLAN_BRIEF_MARKER):
                return _REWRITTEN_BODY_MARKER
            return "```result\nstatus: complete\n```\n"

        def fake_verify(wu, feature_dir, gate_file=None):
            # Every attempt fails, including the re-planned last one, so the
            # unit exhausts its attempts and takes the escalation path that
            # calls persist_attempt_notes with all buffered notes.
            return False, "synthetic failure for the collision test"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "the gate must halt on blocked_human")

            work_dir = feature_dir / "work" / "FEAT-TEST-0104B_T01"
            self.assertTrue(work_dir.is_dir(),
                             f"expected attempt notes under {work_dir}")

            names = sorted(p.name for p in work_dir.iterdir())

            # Attempt 1 (before any re-plan) keeps the unchanged name.
            self.assertIn("attempt-1.md", names)

            # Attempt 2 is the one that got re-planned: its failure evidence
            # and its re-plan transcript must BOTH be on disk, under distinct
            # names, neither clobbering the other.
            self.assertIn("attempt-2.md", names)
            self.assertIn("attempt-2-replan.md", names)

            failure_text = (work_dir / "attempt-2.md").read_text()
            replan_text = (work_dir / "attempt-2-replan.md").read_text()
            self.assertIn("synthetic failure for the collision test",
                          failure_text)
            self.assertIn("Re-plan turn transcript", replan_text)

            # Attempt 3 (the re-planned, last attempt) also failed and kept
            # the unchanged single-entry name.
            self.assertIn("attempt-3.md", names)
            self.assertIn(
                "synthetic failure for the collision test",
                (work_dir / "attempt-3.md").read_text(),
            )


if __name__ == "__main__":
    unittest.main()
