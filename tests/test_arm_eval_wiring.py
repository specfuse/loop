#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Shadow wiring — FEAT-2026-0053/T04.

Every gate -> `awaiting_review` flip appends exactly one
`arm_predicate_evaluated` event carrying the full per-class evaluation and
the overall `would_arm`, with zero change to arming/halt control flow. A
predicate exception degrades to an `evaluation_error` field rather than
crashing the gate close.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()

FEATURE_ID = "FEAT-2026-8901"


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list) -> Path:
    """Scaffold a two-gate feature folder — PLAN.md, GATE-01.md, GATE-02.md,
    per-WU files. Gate 1 is non-terminal (gate 2 follows), so it flips to
    `awaiting_review` and STAYS there — no closing-sequence WU types and no
    auto-close ceremony to carry it further to `passed`. That isolates the
    property under test: the arm-predicate shadow event fires at the flip,
    and the flip itself is unaffected by the verdict."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    gate1_wus = list(wus)
    gate2_wus = [(f"{feature_id}/T02", "implementation", "pending")]

    def _rows(wu_list):
        rows = []
        for i, (wu_id, _wu_type, _wu_status) in enumerate(wu_list):
            tnn = wu_id.split("/")[-1]
            wu_file = f"WU-{tnn}.md"
            deps = "[]" if i == 0 else f"[{wu_list[i-1][0]}]"
            rows.append(
                f"      - id: {wu_id}\n        file: {wu_file}\n        "
                f"depends_on: {deps}"
            )
        return rows

    plan = f"""---
feature_id: {feature_id}
title: Arm wiring fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the arm-predicate shadow wiring
status: active
---

# Plan: {slug}

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
{chr(10).join(_rows(gate1_wus))}
  - gate: 2
    file: GATE-02.md
    work_units:
{chr(10).join(_rows(gate2_wus))}
```
"""
    (fdir / "PLAN.md").write_text(plan)
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "GATE-02.md").write_text(
        "---\ngate: 2\nstatus: open\n---\n\n# Gate 2\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in gate1_wus + gate2_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
        )
    # Gate 7's clean verdict needs the next gate's review doc present with an
    # empty open_questions list — mirrors what a real plan-next WU drafts.
    (fdir / "GATE-02-REVIEW.md").write_text(
        "---\nopen_questions: []\n---\n\n# Gate 2 review\n")
    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".specfuse/.loop.lock" not in existing:
        gitignore.write_text(existing + ".specfuse/.loop.lock\n"
                             ".specfuse/.scratch-*\n"
                             ".specfuse/scripts/__pycache__/\n")
    import subprocess
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


class TestShadowWiring(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _run_to_gate_close(self, root: Path, feature_id: str, slug: str):
        fdir = write_minimal_feature(
            root, feature_id, slug, f"feat/{slug}", [
                (f"{feature_id}/T01", "implementation", "pending"),
            ])

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            write_stub_deliverable(wu)
            return "```result\nstatus: complete\n```\n"

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
        rc = loop.run(None, dry_run=False)
        return fdir, rc

    def test_gate_close_emits_arm_predicate_event(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir, rc = self._run_to_gate_close(root, FEATURE_ID, "shadow-wiring")

            self.assertEqual(rc, 0)
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review",
                              "driver must still halt at awaiting_review "
                              "regardless of the arm verdict")

            events = _read_events(fdir / "events.jsonl")
            arm_events = [e for e in events
                          if e["event_type"] == "arm_predicate_evaluated"]
            self.assertEqual(len(arm_events), 1,
                              "exactly one arm_predicate_evaluated event per "
                              "gate close")
            payload = arm_events[0]["payload"]
            self.assertEqual(payload["gate"], 1)
            self.assertIn("would_arm", payload)
            self.assertIn("classes", payload)
            for class_name in (
                "budget_projection", "judge_editing", "decision_class_paths",
                "retroactive_edits", "drift_caps", "missing_provenance",
                "open_questions_human_only",
            ):
                self.assertIn(class_name, payload["classes"])
                self.assertIn("status", payload["classes"][class_name])
                self.assertIn("reason", payload["classes"][class_name])

    def test_would_arm_true_does_not_change_halt_behavior(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir, rc = self._run_to_gate_close(root, "FEAT-2026-8902",
                                                "would-arm-true")
            events = _read_events(fdir / "events.jsonl")
            arm_events = [e for e in events
                          if e["event_type"] == "arm_predicate_evaluated"]
            self.assertEqual(len(arm_events), 1)
            # Terminal gate with a freshly-written matching baseline -> clean
            # verdict on every class -> would_arm True.
            self.assertTrue(arm_events[0]["payload"]["would_arm"])
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review",
                              "would_arm True must not skip the halt — "
                              "acting on the verdict is gate 2, not this WU")

    def test_predicate_exception_degrades_to_evaluation_error(self):
        with integration_workspace() as root:
            os.chdir(root)

            def raise_boom(feature_dir, just_closed_gate):
                raise RuntimeError("boom")

            self._patch("evaluate_arm_predicate", raise_boom)
            fdir, rc = self._run_to_gate_close(root, "FEAT-2026-8903",
                                                "predicate-error")

            self.assertEqual(rc, 0,
                              "a predicate exception must not crash the "
                              "gate close")
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review")

            events = _read_events(fdir / "events.jsonl")
            arm_events = [e for e in events
                          if e["event_type"] == "arm_predicate_evaluated"]
            self.assertEqual(len(arm_events), 1)
            payload = arm_events[0]["payload"]
            self.assertIn("evaluation_error", payload)
            self.assertIn("boom", payload["evaluation_error"])


if __name__ == "__main__":
    unittest.main()
