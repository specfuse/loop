#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Terminal PLAN-flip ownership tests — FEAT-2026-0023/T01.

`fire_terminal_flips` is the single driver-side owner of every terminal flip,
now including `PLAN.md status -> done`. These tests pin the three behaviours:

  - test_auto_close_terminal_flips_plan_done  (AC 1/4): the auto-close path —
    where the close WU is never dispatched, so its in-memory verdict is None and
    only the on-disk WU frontmatter carries verdict=met (written by
    mark_close_wu_auto_closed) — ends with PLAN.md `done`, GATE `passed`, roadmap
    row `done`. RED on HEAD: pre-fix fire_terminal_flips never touched PLAN.md,
    so the agent-less auto-close path left it `active` (the #49 shape).
  - test_dispatched_close_flips_plan_done  (AC 5): a normal close WU passing with
    verdict=met ends with PLAN `done` via the driver, no longer dependent on the
    agent's own edit.
  - test_hedged_verdict_leaves_plan_active  (AC 6): a close WU whose verdict does
    not permit terminal flips leaves PLAN `active`.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _make_repo_with_feature(
    root: Path,
    feature_id: str,
    *,
    gate_num: int = 2,
    gate_status: str = "awaiting_review",
    roadmap_row_status: str = "active",
    plan_status: str = "active",
    close_verdict: str = "met",
) -> tuple[Path, Path]:
    """Write a synthetic .specfuse scaffold + terminal feature dir.

    Returns (feature_dir, repo_root). No git repo needed — fire_terminal_flips
    only does file operations.
    """
    specfuse = root / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    feature_dir = specfuse / "features" / f"{feature_id}-test"
    feature_dir.mkdir(parents=True)

    gate_file = f"GATE-{gate_num:02d}.md"
    close_id = f"{feature_id}/G{gate_num}-CLOSE"

    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nbranch: feat/test\n"
        f"roadmap_goal: test\nstatus: {plan_status}\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n  - gate: {gate_num}\n    file: {gate_file}\n"
        f"    work_units:\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: []\n```\n"
    )
    (feature_dir / gate_file).write_text(
        f"---\ngate: {gate_num}\nstatus: {gate_status}\n---\n\n# Gate {gate_num}\n"
    )
    (feature_dir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: done\nattempts: 1\nverdict: {close_verdict}\n---\n\n"
        f"# Close{_WU_BODY}"
    )

    (specfuse / "roadmap.md").write_text(
        f"---\nproject: test\n---\n\n# Roadmap\n\n"
        f"| Feature ID | Title | Status | Folder | Detail |\n"
        f"|------------|-------|--------|--------|--------|\n"
        f"| {feature_id} | Test feature | {roadmap_row_status} | — | — |\n\n"
        f"## {feature_id} — Test feature\n\nContent.\n"
    )
    (specfuse / "roadmap-archive.md").write_text(
        "---\nproject: test\n---\n\n# Archived\n\n"
        "<!-- Archived sections appended below -->\n"
    )

    return feature_dir, root


def _close_wu(feature_dir: Path, feature_id: str, gate_num: int,
              verdict: str | None) -> loop.WorkUnit:
    """Construct the in-memory close WorkUnit the driver hands fire_terminal_flips.

    `verdict` is the *in-memory* value: None mimics the auto-close path (close WU
    never dispatched, so wu.verdict was never populated from disk), a concrete
    string mimics the dispatched path (loop.run re-reads the agent's verdict into
    wu.verdict post-squash).
    """
    return loop.WorkUnit(
        wu_id=f"{feature_id}/G{gate_num}-CLOSE",
        file=feature_dir / "WU-close.md",
        depends_on=[],
        type="close",
        model="opus",
        effort="high",
        status="done",
        attempts=1,
        title="Close",
        body="",
        verdict=verdict,
    )


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


class TestTerminalPlanFlipOwnership(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_auto_close_terminal_flips_plan_done(self):
        """Auto-close path: PLAN done, GATE passed, roadmap row done (AC 1/4).

        RED on HEAD — the pre-fix fire_terminal_flips never touched PLAN.md, so
        the agent-less auto-close path left it `active` (the #49 shape). The
        in-memory close WU carries verdict=None (never dispatched); only the
        on-disk WU frontmatter has verdict=met.
        """
        feature_id = "FEAT-2026-9981"
        feature_dir, repo_root = _make_repo_with_feature(
            self.root, feature_id, gate_num=2, gate_status="awaiting_review",
            roadmap_row_status="active", plan_status="active",
            close_verdict="met",
        )
        # Auto-close path: in-memory verdict is None (WU never dispatched), disk
        # carries verdict=met (mark_close_wu_auto_closed wrote it).
        wu = _close_wu(feature_dir, feature_id, 2, verdict=None)

        loop.fire_terminal_flips(wu, feature_dir, repo_root)

        plan_fm = _read_frontmatter(feature_dir / "PLAN.md")
        self.assertEqual(
            plan_fm.get("status"), "done",
            "auto-close path must flip PLAN.md status to done",
        )
        gate_fm = _read_frontmatter(feature_dir / "GATE-02.md")
        self.assertEqual(gate_fm.get("status"), "passed",
                         "terminal gate must be flipped to passed")
        roadmap_text = (repo_root / ".specfuse" / "roadmap.md").read_text()
        self.assertIn(f"| {feature_id} | Test feature | done |", roadmap_text,
                      "roadmap row must be flipped to done")

    def test_dispatched_close_flips_plan_done(self):
        """Dispatched close (verdict met): PLAN flipped to done via the driver (AC 5)."""
        feature_id = "FEAT-2026-9982"
        feature_dir, repo_root = _make_repo_with_feature(
            self.root, feature_id, gate_num=2, gate_status="awaiting_review",
            roadmap_row_status="active", plan_status="active",
            close_verdict="met",
        )
        # Dispatched path: loop.run re-reads the agent's verdict into wu.verdict.
        wu = _close_wu(feature_dir, feature_id, 2, verdict="met")

        loop.fire_terminal_flips(wu, feature_dir, repo_root)

        plan_fm = _read_frontmatter(feature_dir / "PLAN.md")
        self.assertEqual(
            plan_fm.get("status"), "done",
            "dispatched close with verdict=met must flip PLAN.md to done via driver",
        )

    def test_hedged_verdict_leaves_plan_active(self):
        """Hedged verdict: PLAN stays active — the flip is gated (AC 6)."""
        feature_id = "FEAT-2026-9983"
        feature_dir, repo_root = _make_repo_with_feature(
            self.root, feature_id, gate_num=2, gate_status="awaiting_review",
            roadmap_row_status="active", plan_status="active",
            close_verdict="partially_met",
        )
        wu = _close_wu(feature_dir, feature_id, 2, verdict="partially_met")

        loop.fire_terminal_flips(wu, feature_dir, repo_root)

        plan_fm = _read_frontmatter(feature_dir / "PLAN.md")
        self.assertEqual(
            plan_fm.get("status"), "active",
            "hedged verdict must NOT flip PLAN.md to done",
        )


if __name__ == "__main__":
    unittest.main()
