#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`evaluate_fix_unit_insertion` refuses a drafted fix unit it judged unsafe
to arm (FEAT-2026-0115/T02).

Drives real `loop.run()` calls against a synthetic single-gate feature, same
harness shape as `tests/test_fix_unit_insertion_e2e.py`: stub the `claude -p`
boundary, blocked RESULT names a `blocked_next:` fix unit, and this proves
one refusal per stop class — `missing_provenance`, `judge_editing`,
`max_fix_units_per_unit`, `cost_budget` — each ending `blocked_human` with
`human_escalation.insertion_refused.class` naming it, the draft file still
`status: draft`, and PLAN.md's graph without the draft. A fifth case proves a
clean draft still inserts and the gate continues — T01's oracle is not
narrowed by the new checks.
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

_FEATURE_ID = "FEAT-2026-9951"
_SLUG = "fix-unit-refused"
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

_COMPLETE_RESULT = """```result
status: complete
summary: done
```
"""

_DRAFT_BODY = (
    "\n\n## Context\n\nFix the generator defect T01 hit.\n\n"
    "## Acceptance criteria\n\n1. The defect is fixed.\n\n"
    "## Do not touch\n\nNothing else.\n\n"
    "## Verification\n\nThe `code` gates.\n\n"
    "## Escalation triggers\n\nNone expected.\n"
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


def _read_events(feature_dir: Path) -> list[dict]:
    path = feature_dir / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _write_event(fdir: Path, correlation_id: str, event_type: str) -> None:
    ev = json.dumps({
        "event_type": event_type,
        "correlation_id": correlation_id,
        "timestamp": "2026-01-01T00:00:00Z",
    })
    with (fdir / "events.jsonl").open("a") as f:
        f.write(ev + "\n")


def _scaffold(
    root: Path,
    *,
    draft_frontmatter_extra: str = "",
    prior_fix_unit_insertions: int = 0,
    gate_cost_budget_usd: "float | None" = None,
) -> Path:
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: fix-unit-refused\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Fix unit refused fixture | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Fix unit refused fixture\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: exercise evaluate_fix_unit_insertion's refusal classes\n"
        "autonomy_default: auto\n"
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
    gate_fm_extra = (
        f"cost_budget_usd: {gate_cost_budget_usd}\n"
        if gate_cost_budget_usd is not None else ""
    )
    (fdir / "GATE-01.md").write_text(
        f"---\ngate: 1\nstatus: open\n{gate_fm_extra}---\n\n# Gate 1\n")
    # A second baseline WU, both with a nonzero planned_cost_usd, so the arm
    # predicate's drift-cap class (count AND planned-cost ceilings) has
    # enough baseline headroom for a single small fix-unit insertion to stay
    # clean — the class under test in each scenario below is never drift_caps.
    (fdir / "WU-00-filler.md").write_text(
        f"---\nid: {_FEATURE_ID}/T00\ntype: implementation\n"
        "status: done\nattempts: 1\nplanned_cost_usd: 20.0\n"
        f"---\n\n# T00\n\nAlready-done filler baseline unit.\n"
    )
    (fdir / "WU-01-T01.md").write_text(
        f"---\nid: {_T01_ID}\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "max_attempts: 3\nplanned_cost_usd: 20.0\n"
        f"---\n\n# T01\n\nDo the thing.\n"
    )
    (fdir / "WU-05-fix-unit.md").write_text(
        f"---\nid: {_T05_ID}\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: draft\nattempts: 0\n"
        "planned_cost_usd: 1.0\n"
        f"{draft_frontmatter_extra}"
        f"---\n\n# T05\n{_DRAFT_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fix-unit-refused fixture"], check=True)
    for _ in range(prior_fix_unit_insertions):
        _write_event(fdir, _T01_ID, "fix_unit_inserted")
    if prior_fix_unit_insertions:
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "seed prior fix_unit_inserted events"], check=True)
    return fdir


class FixUnitInsertionRefusedTest(unittest.TestCase):
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

    def _run_blocked(self, **scaffold_kwargs):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            return _BLOCKED_WITH_FIX_RESULT

        def fake_verify(wu, feature_dir, gate_file=None):
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root, **scaffold_kwargs)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            t01_fm = _read_frontmatter(feature_dir / "WU-01-T01.md")
            t05_fm = _read_frontmatter(feature_dir / "WU-05-fix-unit.md")
            events = _read_events(feature_dir)
            plan_text = (feature_dir / "PLAN.md").read_text()
            human_escalation = [
                e for e in events if e["event_type"] == "human_escalation"]
            fix_inserted = [
                e for e in events if e["event_type"] == "fix_unit_inserted"]

            return {
                "rc": rc,
                "t01_fm": t01_fm,
                "t05_fm": t05_fm,
                "plan_text": plan_text,
                "human_escalation": human_escalation,
                "fix_inserted": fix_inserted,
            }

    def _assert_refused(
        self, result: dict, expected_class: str, *, seeded_prior_insertions: int = 0,
    ) -> None:
        self.assertEqual(result["rc"], 1, "a refused insertion must halt the gate")
        self.assertEqual(result["t01_fm"].get("status"), "blocked_human")
        self.assertEqual(result["t05_fm"].get("status"), "draft",
                          "a refused draft must stay untouched on disk")
        self.assertNotIn(_T05_ID, result["plan_text"],
                          "a refused draft must not remain in PLAN.md's graph")
        self.assertEqual(len(result["human_escalation"]), 1)
        insertion_refused = result["human_escalation"][0]["payload"].get(
            "insertion_refused")
        self.assertIsNotNone(insertion_refused)
        self.assertEqual(insertion_refused.get("class"), expected_class)
        # Fixture-seeded `fix_unit_inserted` events (for the
        # max_fix_units_per_unit case) are not this run's own — only that
        # this run added none beyond what the fixture seeded.
        self.assertEqual(len(result["fix_inserted"]), seeded_prior_insertions)

    def test_missing_provenance_refuses(self):
        result = self._run_blocked(draft_frontmatter_extra="")
        self._assert_refused(result, "missing_provenance")

    def test_judge_editing_refuses(self):
        result = self._run_blocked(
            draft_frontmatter_extra=(
                "provenance: drafted by T01's blocked session\n"
                "produces:\n  - specfuse/loop/loop.py\n"
            ),
        )
        self._assert_refused(result, "judge_editing")

    def test_max_fix_units_per_unit_refuses_third_insertion(self):
        result = self._run_blocked(
            draft_frontmatter_extra=(
                "provenance: drafted by T01's blocked session\n"),
            prior_fix_unit_insertions=2,
        )
        self._assert_refused(result, "max_fix_units_per_unit",
                              seeded_prior_insertions=2)

    def test_cost_budget_refuses(self):
        result = self._run_blocked(
            draft_frontmatter_extra=(
                "provenance: drafted by T01's blocked session\n"),
            gate_cost_budget_usd=0.5,
        )
        self._assert_refused(result, "cost_budget")

    def test_clean_draft_still_inserts_and_continues(self):
        t01_calls = {"n": 0}

        def fake_dispatch(wu, failure_note, cost_tracking=True):
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
            feature_dir = _scaffold(
                root,
                draft_frontmatter_extra=(
                    "provenance: drafted by T01's blocked session\n"),
            )
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0, "a clean insertion must not narrow T01's oracle")
            t01_fm = _read_frontmatter(feature_dir / "WU-01-T01.md")
            t05_fm = _read_frontmatter(feature_dir / "WU-05-fix-unit.md")
            self.assertEqual(t01_fm.get("status"), "done")
            self.assertEqual(t05_fm.get("status"), "done")

            events = _read_events(feature_dir)
            fix_inserted = [
                e for e in events if e["event_type"] == "fix_unit_inserted"]
            human_escalation = [
                e for e in events if e["event_type"] == "human_escalation"]
            self.assertEqual(len(fix_inserted), 1)
            self.assertEqual(fix_inserted[0]["payload"]["fix_unit_id"], _T05_ID)
            self.assertEqual(human_escalation, [])

            plan_text = (feature_dir / "PLAN.md").read_text()
            self.assertIn(_T05_ID, plan_text)


if __name__ == "__main__":
    unittest.main()
