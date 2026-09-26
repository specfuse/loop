#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""End-to-end fix-unit insertion on a blocked RESULT (FEAT-2026-0115/T01).

Drives a real `loop.run()` against a synthetic single-gate feature in a temp
git repo, stubbing only the `claude -p` boundary (`loop.dispatch` /
`loop.verify`, same seam as `tests/test_replan_end_to_end.py`), and proves the
walking-skeleton path end to end: a blocked RESULT that names a valid
`blocked_next:` fix unit gets it inserted ahead of the blocked unit, the
blocked unit is re-armed behind it, and the gate keeps dispatching with no
human escalation — dispatch order T01, T05, T01, both ending `done`.

Two more cases guard the fallback: a blocked RESULT with no `blocked_next:`
escalates exactly as before, and the SAME `blocked_next:` under
`autonomy_default: review` also escalates, leaving the draft untouched.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()

_FEATURE_ID = "FEAT-2026-9915"
_SLUG = "fix-unit-insertion"
_BRANCH = f"feat/{_FEATURE_ID}-{_SLUG}"
_T01_ID = f"{_FEATURE_ID}/T01"
_T05_ID = f"{_FEATURE_ID}/T05"

_BLOCKED_WITH_FIX_RESULT = f"""```result
status: blocked
blocked_reason: needs a generator defect fixed first
blocked_next:
  kind: fix_unit
  file: WU-05-fix-unit.md
  id: {_T05_ID}
```
"""

_BLOCKED_NO_FIX_RESULT = """```result
status: blocked
blocked_reason: spec ambiguity, needs a human decision
```
"""

_COMPLETE_RESULT = """```result
status: complete
summary: done
```
"""


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


def _read_events(feature_dir: Path) -> list[dict]:
    path = feature_dir / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _scaffold(root: Path, *, autonomy_default: str = "auto",
              with_draft: bool = True) -> Path:
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: fix-unit-insertion\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Fix unit insertion fixture | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Fix unit insertion fixture\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: exercise the fix-unit insertion path end to end\n"
        f"autonomy_default: {autonomy_default}\n"
        "status: active\n"
        "---\n\n"
        f"# Plan: {_SLUG}\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {_FEATURE_ID}/T00\n"
        "        file: WU-00-filler.md\n"
        "        depends_on: []\n"
        f"      - id: {_T01_ID}\n"
        "        file: WU-01-T01.md\n"
        "        depends_on: []\n"
        "```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    # A second baseline WU (already `done`) so the arm predicate's drift-cap
    # class (FEAT-2026-0115/T02) has a baseline count > 1 to compare a single
    # inserted fix unit against — with only T01 in the baseline, ANY
    # insertion would exceed the 0.5x count ceiling and refuse.
    (fdir / "WU-00-filler.md").write_text(
        f"---\nid: {_FEATURE_ID}/T00\ntype: implementation\n"
        "status: done\nattempts: 1\nplanned_cost_usd: 2.0\n"
        f"---\n\n# T00\n\nAlready-done filler baseline unit.\n"
    )
    (fdir / "WU-01-T01.md").write_text(
        f"---\nid: {_T01_ID}\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "max_attempts: 3\nplanned_cost_usd: 2.0\n"
        f"---\n\n# T01\n\nDo the thing.\n"
    )
    if with_draft:
        (fdir / "WU-05-fix-unit.md").write_text(
            f"---\nid: {_T05_ID}\ntype: implementation\n"
            "model: claude-haiku-4-5-20251001\nstatus: draft\nattempts: 0\n"
            "provenance: drafted by T01's blocked session\n"
            "planned_cost_usd: 1.0\n"
            f"---\n\n# T05\n\n"
            "## Context\n\nFix the generator defect T01 hit.\n\n"
            "## Acceptance criteria\n\n1. The defect is fixed.\n\n"
            "## Do not touch\n\nNothing else.\n\n"
            "## Verification\n\nThe `code` gates.\n\n"
            "## Escalation triggers\n\nNone expected.\n"
        )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fix-unit-insertion fixture"], check=True)
    return fdir


class FixUnitInsertionEndToEndTest(unittest.TestCase):
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

    def test_blocked_with_valid_blocked_next_inserts_and_continues(self):
        dispatch_order: list[str] = []
        t01_calls = {"n": 0}

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            dispatch_order.append(wu.wu_id)
            if wu.wu_id == _T01_ID:
                t01_calls["n"] += 1
                if t01_calls["n"] == 1:
                    return _BLOCKED_WITH_FIX_RESULT
                write_stub_deliverable(wu)
                return _COMPLETE_RESULT
            write_stub_deliverable(wu)
            return _COMPLETE_RESULT

        def fake_verify(wu, feature_dir, gate_file=None):
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0, "the gate must run to completion, not halt")
            self.assertEqual(
                dispatch_order, [_T01_ID, _T05_ID, _T01_ID],
                "dispatch order must be T01 (blocked), T05, T01 (retry)")

            t01_fm = _read_frontmatter(feature_dir / "WU-01-T01.md")
            t05_fm = _read_frontmatter(feature_dir / "WU-05-fix-unit.md")
            self.assertEqual(t01_fm.get("status"), "done")
            self.assertEqual(t05_fm.get("status"), "done")

            events = _read_events(feature_dir)
            fix_inserted = [e for e in events if e["event_type"] == "fix_unit_inserted"]
            rearm_dispatched = [e for e in events if e["event_type"] == "re_arm_dispatched"]
            human_escalation = [e for e in events if e["event_type"] == "human_escalation"]
            self.assertEqual(len(fix_inserted), 1)
            self.assertEqual(fix_inserted[0]["correlation_id"], _T01_ID)
            self.assertEqual(fix_inserted[0]["payload"]["fix_unit_id"], _T05_ID)
            rearm_for_t01 = [e for e in rearm_dispatched if e["correlation_id"] == _T01_ID]
            self.assertEqual(len(rearm_for_t01), 1)
            self.assertEqual(rearm_for_t01[0]["payload"].get("reason"), "fix_unit_inserted")
            self.assertEqual(human_escalation, [])

            plan_text = (feature_dir / "PLAN.md").read_text()
            self.assertIn(_T05_ID, plan_text)
            self.assertIn("WU-05-fix-unit.md", plan_text)
            self.assertIn(f"depends_on: [{_T05_ID}]", plan_text)

            gate_fm = _read_frontmatter(feature_dir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review")

    def test_blocked_without_blocked_next_escalates_unchanged(self):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            return _BLOCKED_NO_FIX_RESULT

        def fake_verify(wu, feature_dir, gate_file=None):
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root, with_draft=False)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 1, "a plain block must halt the gate")
            t01_fm = _read_frontmatter(feature_dir / "WU-01-T01.md")
            self.assertEqual(t01_fm.get("status"), "blocked_human")

            events = _read_events(feature_dir)
            human_escalation = [e for e in events if e["event_type"] == "human_escalation"]
            self.assertEqual(len(human_escalation), 1)
            self.assertEqual(human_escalation[0]["payload"].get("reason"),
                             "agent_reported_blocked")
            self.assertEqual(
                [e for e in events if e["event_type"] == "fix_unit_inserted"], [])

    def test_blocked_with_blocked_next_under_review_autonomy_escalates(self):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            return _BLOCKED_WITH_FIX_RESULT

        def fake_verify(wu, feature_dir, gate_file=None):
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root, autonomy_default="review")
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 1, "review autonomy must escalate, not insert")
            t01_fm = _read_frontmatter(feature_dir / "WU-01-T01.md")
            self.assertEqual(t01_fm.get("status"), "blocked_human")
            t05_fm = _read_frontmatter(feature_dir / "WU-05-fix-unit.md")
            self.assertEqual(t05_fm.get("status"), "draft",
                             "the draft must stay untouched under review autonomy")

            events = _read_events(feature_dir)
            human_escalation = [e for e in events if e["event_type"] == "human_escalation"]
            self.assertEqual(len(human_escalation), 1)
            self.assertEqual(
                [e for e in events if e["event_type"] == "fix_unit_inserted"], [])


if __name__ == "__main__":
    unittest.main()
