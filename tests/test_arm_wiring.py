#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Dial-and-verdict wiring — FEAT-2026-0053/T06.

The normal-completion gate-close site is the only one of the three
`arm_predicate_evaluated` flip sites (FEAT-2026-0053/T04) that may act on the
verdict. `autonomy_default: auto` plus `would_arm: True` there carries T05's
arm transaction (draft->pending flips, gate N awaiting_review->passed) into
the SAME bookkeeping commit that already fires at that site, tag-before-write.
The two escalation sites (preexisting_gate_failure, gate_budget_exceeded)
never consult the dial — they park regardless.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from specfuse.loop.arm_eval import ArmDecision, ClassVerdict
from specfuse.loop.plan_baseline import load_plan_graph, write_baseline_if_absent

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_FEATURE_DIR = (
    REPO_ROOT / ".specfuse/features/FEAT-2026-0053-auto-mode"
)

GATE2_WU_FILES = (
    "WU-05-arm-transaction-module.md",
    "WU-06-dial-and-verdict-wiring.md",
    "WU-07-lint-blocking-under-auto.md",
    "WU-08-feature-review-accumulation.md",
    "WU-09-learnings-staging.md",
    "WU-90-gate-2-close-intermediate.md",
    "WU-91-gate-2-plan-next.md",
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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def write_armable_feature(
    root: Path, feature_id: str, slug: str, autonomy: str,
    gate1_wus: list, gate1_gate_extra: str = "",
) -> Path:
    """A two-gate fixture: gate 1's WUs as given, gate 2 with seven `draft`
    WUs and a clean (empty `open_questions`) review file — a would_arm=True
    setup with no judge-path, no drift, no missing-provenance surface.
    `PLAN.baseline.json` is written up front (matching the activated graph)
    so `run()`'s own first-touch baseline snapshot is a no-op — the only
    commit a clean run produces is the gate close itself.
    """
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    branch = f"feat/{slug}"

    gate2_wus = [
        (f"{feature_id}/T{n:02d}", "implementation", "draft")
        for n in range(11, 18)
    ]

    def _rows(wu_list):
        rows = []
        for i, (wu_id, _wu_type, _wu_status) in enumerate(wu_list):
            tnn = wu_id.split("/")[-1]
            wu_file = f"WU-{tnn}.md"
            deps = "[]" if i == 0 else f"[{wu_list[i - 1][0]}]"
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
roadmap_goal: exercise the live arm wiring
autonomy_default: {autonomy}
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
    gate1_fm = "---\ngate: 1\nstatus: open\n" + gate1_gate_extra + "---\n\n# Gate 1\n"
    (fdir / "GATE-01.md").write_text(gate1_fm)
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
    (fdir / "GATE-02-REVIEW.md").write_text(
        "---\ngate: 2\nopen_questions: []\n---\n\n# Gate 2 review\n")

    write_baseline_if_absent(fdir, load_plan_graph(fdir))

    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".specfuse/.loop.lock" not in existing:
        gitignore.write_text(existing + ".specfuse/.loop.lock\n"
                             ".specfuse/.scratch-*\n"
                             ".specfuse/scripts/__pycache__/\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


def _copy_real_feature(root: Path, autonomy: str) -> Path:
    """A copy of THIS feature's own real folder — real PLAN.baseline.json,
    real WU frontmatter (produces, provenance, cost fields), real
    events.jsonl — rewound to the moment gate 1 is about to close and gate
    2's real seven WUs sit `draft`, not yet armed by a human. Only the
    `autonomy_default` dial and gate 1's status are overridden; every other
    byte, including T05/T06's real `produces:` under `specfuse/loop/` and
    T07's real `human_only: true`, is the real feature as committed.
    """
    dest = root / ".specfuse/features/FEAT-2026-0053-auto-mode"
    shutil.copytree(REAL_FEATURE_DIR, dest)

    plan = dest / "PLAN.md"
    plan.write_text(plan.read_text().replace(
        "autonomy_default: review", f"autonomy_default: {autonomy}"))

    gate1 = dest / "GATE-01.md"
    gate1.write_text(re.sub(
        r"^status: passed$", "status: open", gate1.read_text(),
        count=1, flags=re.MULTILINE))

    for name in GATE2_WU_FILES:
        p = dest / name
        text = re.sub(
            r"^status: .*$", "status: draft", p.read_text(),
            count=1, flags=re.MULTILINE)
        p.write_text(text)

    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".specfuse/.loop.lock" not in existing:
        gitignore.write_text(existing + ".specfuse/.loop.lock\n"
                             ".specfuse/.scratch-*\n"
                             ".specfuse/scripts/__pycache__/\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "real feature fixture, rewound to pre-arm gate 1"],
                   check=True)
    return dest


class TestAutoArm(unittest.TestCase):

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

    def test_auto_feature_arms_next_gate_in_one_commit(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_armable_feature(
                root, "FEAT-2026-9001", "auto-clean", "auto",
                [("FEAT-2026-9001/T01", "implementation", "done")],
            )
            head_before = _git(root, "rev-parse", "HEAD")

            rc = loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(rc, 0)

            gate1_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate1_fm.get("status"), "passed")
            for name in [f"WU-T{n:02d}.md" for n in range(11, 18)]:
                fm = _read_frontmatter(fdir / name)
                self.assertEqual(fm.get("status"), "pending",
                                  f"{name} must flip draft -> pending")

            tag = "pre-arm/FEAT-2026-9001/gate-1"
            tags = _git(root, "tag", "--list", tag)
            self.assertEqual(tags, tag, "revert tag must exist at arm time")

            events = _read_events(fdir / "events.jsonl")
            armed = [e for e in events if e["event_type"] == "gate_auto_armed"]
            self.assertEqual(len(armed), 1)
            payload = armed[0]["payload"]
            self.assertEqual(payload["gate"], 1)
            self.assertEqual(payload["tag"], tag)
            self.assertEqual(payload["predicate_version"], "v1")
            self.assertEqual(
                sorted(payload["armed_wu_ids"]),
                sorted(f"FEAT-2026-9001/T{n:02d}" for n in range(11, 18)),
            )

            # Exactly one commit produced the whole close.
            commit_count = _git(root, "rev-list", "--count",
                                 f"{head_before}..HEAD")
            self.assertEqual(commit_count, "1",
                              "the arm must land in exactly one commit")
            changed = _git(root, "diff", "--name-only",
                            head_before, "HEAD").splitlines()
            self.assertIn(
                ".specfuse/features/FEAT-2026-9001-auto-clean/GATE-01.md",
                changed)
            self.assertIn(
                ".specfuse/features/FEAT-2026-9001-auto-clean/events.jsonl",
                changed)
            for n in range(11, 18):
                self.assertIn(
                    f".specfuse/features/FEAT-2026-9001-auto-clean/WU-T{n:02d}.md",
                    changed)

    def _assert_does_not_arm(self, autonomy: str):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_armable_feature(
                root, f"FEAT-2026-9002-{autonomy}", f"{autonomy}-parked",
                autonomy,
                [(f"FEAT-2026-9002-{autonomy}/T01", "implementation", "done")],
            )
            rc = loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(rc, 0)

            gate1_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate1_fm.get("status"), "awaiting_review")
            for name in [f"WU-T{n:02d}.md" for n in range(11, 18)]:
                fm = _read_frontmatter(fdir / name)
                self.assertEqual(fm.get("status"), "draft")

            tags = _git(root, "tag", "--list", "pre-arm/*")
            self.assertEqual(tags, "", "no pre-arm tag under review/supervised")

            events = _read_events(fdir / "events.jsonl")
            self.assertFalse(
                [e for e in events if e["event_type"] == "gate_auto_armed"])

    def test_review_feature_does_not_arm(self):
        self._assert_does_not_arm("review")

    def test_supervised_feature_does_not_arm(self):
        self._assert_does_not_arm("supervised")

    def test_would_arm_false_parks_with_reason_in_payload(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_armable_feature(
                root, "FEAT-2026-9003", "would-arm-false", "auto",
                [("FEAT-2026-9003/T01", "implementation", "done")],
            )

            def stub_decision(feature_dir, just_closed_gate):
                classes = {
                    name: ClassVerdict("clean", "n/a")
                    for name in (
                        "budget_projection", "judge_editing",
                        "decision_class_paths", "retroactive_edits",
                        "drift_caps", "missing_provenance",
                    )
                }
                classes["open_questions_human_only"] = ClassVerdict(
                    "fired", "TEST_STOP_REASON: human_only flagged: T07")
                return ArmDecision(
                    would_arm=False, classes=classes,
                    feature_id="FEAT-2026-9003", gate_id=just_closed_gate,
                    predicate_version="v1",
                )

            self._patch("evaluate_arm_predicate", stub_decision)
            rc = loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(rc, 0)

            gate1_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate1_fm.get("status"), "awaiting_review")
            for name in [f"WU-T{n:02d}.md" for n in range(11, 18)]:
                fm = _read_frontmatter(fdir / name)
                self.assertEqual(fm.get("status"), "draft")

            events = _read_events(fdir / "events.jsonl")
            arm_events = [e for e in events
                          if e["event_type"] == "arm_predicate_evaluated"]
            self.assertEqual(len(arm_events), 1)
            self.assertFalse(arm_events[0]["payload"]["would_arm"])
            self.assertIn(
                "TEST_STOP_REASON",
                arm_events[0]["payload"]["classes"]["open_questions_human_only"]
                ["reason"],
            )
            self.assertFalse(
                [e for e in events if e["event_type"] == "gate_auto_armed"])

    def test_preexisting_gate_failure_does_not_arm_even_if_would_arm_true(self):
        with integration_workspace() as root:
            os.chdir(root)
            # Rig the `code` set to fail so the pre-flight baseline probe
            # escalates BEFORE the normal-completion arm site is reached.
            (root / ".specfuse/verification.yml").write_text(
                "code:\n  - name: fail\n    command: \"false\"\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            fdir = write_armable_feature(
                root, "FEAT-2026-9004", "preexisting-fail", "auto",
                [("FEAT-2026-9004/T01", "implementation", "done")],
            )
            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            gate1_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate1_fm.get("status"), "awaiting_review")
            for name in [f"WU-T{n:02d}.md" for n in range(11, 18)]:
                fm = _read_frontmatter(fdir / name)
                self.assertEqual(fm.get("status"), "draft",
                                  "escalation must never arm, even under auto")

            tags = _git(root, "tag", "--list", "pre-arm/*")
            self.assertEqual(tags, "")

            events = _read_events(fdir / "events.jsonl")
            reasons = [e["payload"]["reason"] for e in events
                       if e["event_type"] == "human_escalation"]
            self.assertIn("preexisting_gate_failure", reasons)
            self.assertFalse(
                [e for e in events if e["event_type"] == "gate_auto_armed"])

    def test_gate_budget_exceeded_does_not_arm_even_if_would_arm_true(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_armable_feature(
                root, "FEAT-2026-9005", "budget-exceeded", "auto",
                [
                    ("FEAT-2026-9005/T01", "implementation", "done"),
                    ("FEAT-2026-9005/T02", "implementation", "pending"),
                ],
                gate1_gate_extra="cost_budget_usd: 0\n",
            )
            rc = loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(rc, 1)

            gate1_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate1_fm.get("status"), "awaiting_review")
            for name in [f"WU-T{n:02d}.md" for n in range(11, 18)]:
                fm = _read_frontmatter(fdir / name)
                self.assertEqual(fm.get("status"), "draft",
                                  "escalation must never arm, even under auto")

            tags = _git(root, "tag", "--list", "pre-arm/*")
            self.assertEqual(tags, "")

            events = _read_events(fdir / "events.jsonl")
            reasons = [e["payload"]["reason"] for e in events
                       if e["event_type"] == "human_escalation"]
            self.assertIn("gate_budget_exceeded", reasons)
            self.assertFalse(
                [e for e in events if e["event_type"] == "gate_auto_armed"])

    def test_real_feature_directory_parks_on_real_vetoes(self):
        """AC#6: driven against a COPY of this feature's own real folder —
        real `PLAN.baseline.json`, real WU frontmatter, real `events.jsonl` —
        rewound to gate 1's close with gate 2's real seven WUs `draft`, under
        `autonomy_default: auto`. The wiring correctly parks (gate 1 stays
        `awaiting_review`, gate 2 stays `draft`, no tag) because this
        feature's own real drafted WUs genuinely fire two veto classes: T07's
        real `human_only: true` and T05/T06's real `produces:` paths under
        `specfuse/loop/` (the judge-editing class — this feature edits the
        driver it is building). Real production input, not a fabricated
        clean pass — the RETROSPECTIVE's own doubt notes that this feature's
        drafted gate 2 is not, in fact, arm-clean."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _copy_real_feature(root, "auto")
            rc = loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(rc, 0)

            gate1_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate1_fm.get("status"), "awaiting_review",
                              "no arm fired, so gate 1 stays at the ordinary "
                              "close status, not passed")
            for name in GATE2_WU_FILES:
                fm = _read_frontmatter(fdir / name)
                self.assertEqual(fm.get("status"), "draft",
                                  "real vetoes must block the arm")

            events = _read_events(fdir / "events.jsonl")
            arm_events = [e for e in events
                          if e["event_type"] == "arm_predicate_evaluated"
                          and e["payload"].get("gate") == 1]
            self.assertEqual(len(arm_events), 1)
            payload = arm_events[0]["payload"]
            self.assertFalse(payload["would_arm"])
            self.assertEqual(
                payload["classes"]["open_questions_human_only"]["status"],
                "fired", "T07's real human_only: true must veto")
            self.assertEqual(
                payload["classes"]["judge_editing"]["status"],
                "fired", "T05/T06's real produces: under specfuse/loop/ "
                         "must fire the judge-editing class")

            self.assertFalse(
                [e for e in events if e["event_type"] == "gate_auto_armed"])
            tags = _git(root, "tag", "--list", "pre-arm/*")
            self.assertEqual(tags, "")


if __name__ == "__main__":
    unittest.main()
