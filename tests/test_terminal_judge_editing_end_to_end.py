#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""End-to-end oracle for the terminal judge-editing stop (FEAT-2026-0246).

Drives a synthetic single-gate feature through ``loop.run()`` against a real git
repo, stubbing only the agent boundary, in the style of
``test_lifecycle_integration``. The check under test is the terminal gate's
counterpart of arm class 2: when a done substantive unit of the last gate
declares a judge-surface path, the driver halts before the terminal close
instead of letting the model-authored verdict go unreviewed.

T01 owns the firing and clean-control classes; the other classes are skipped
here and named for the unit that fills them.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace
from tests.test_lifecycle_integration import (
    _fake_dispatch,
    _read_events,
    _read_frontmatter,
    _roadmap_row_status,
    _scaffold_feature,
)

loop = load_loop()

FEATURE_ID = "FEAT-2026-9101"
SLUG = "terminal-judge"


def _scaffold(root: Path, *, produces: str, auto_close_disabled: bool = False,
              autonomy: str = "auto", unit_status: str = "done") -> Path:
    """Single-gate feature whose one implementation unit is already done and
    declares ``produces: [<produces>]``."""
    fdir = _scaffold_feature(
        root, feature_id=FEATURE_ID, slug=SLUG, branch=f"feat/{FEATURE_ID}-{SLUG}",
        roadmap_status="active", plan_status="active", detail_section=True,
        auto_close_disabled=auto_close_disabled, commit=False)
    plan = fdir / "PLAN.md"
    plan.write_text(plan.read_text().replace(
        "status: active\n", f"status: active\nautonomy_default: {autonomy}\n", 1))
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {FEATURE_ID}/T01\ntype: implementation\n"
        f"model: claude-haiku-4-5-20251001\nstatus: {unit_status}\nattempts: 0\n"
        f"produces:\n  - {produces}\n---\n\n# T01\n\n"
        "**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold terminal judge fixture"], check=True)
    return fdir


class _Base(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []
        self.dispatched = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _stub_agent(self):
        def _dispatch(wu, failure_note, cost_tracking=True):
            self.dispatched.append(wu.wu_id)
            return _fake_dispatch(wu, failure_note, cost_tracking)

        self._patch("dispatch", _dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
        self._patch(
            "run_judge_session",
            lambda prompt, *, timeout=None: ("```result\nverdict: met\n```", None))


class FiresOnSingleGateJudgeEdit(_Base):
    def test_halts_before_the_close(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="specfuse/loop/arm_eval.py")
            plan_before = (fdir / "PLAN.md").read_text()
            roadmap_before = (root / ".specfuse" / "roadmap.md").read_text()
            self._stub_agent()

            rc = loop.run(None, dry_run=False)

            self.assertNotEqual(rc, 0, "a terminal judge edit must halt the run")
            close_fm = _read_frontmatter(fdir / "WU-G1-CLOSE.md")
            self.assertEqual(close_fm.get("status"), "blocked_human")
            events = _read_events(fdir / "events.jsonl")
            esc = [e for e in events if e["event_type"] == "human_escalation"
                   and e["payload"].get("reason") == "judge_editing_terminal"]
            self.assertEqual(len(esc), 1, "exactly one judge_editing_terminal escalation")
            blob = str(esc[0]["payload"])
            self.assertIn(f"{FEATURE_ID}/T01", blob)
            self.assertIn("specfuse/loop/arm_eval.py", blob)
            self.assertNotIn(f"{FEATURE_ID}/G1-CLOSE", self.dispatched,
                             "the close agent must never be dispatched")
            verdicts = [e for e in events
                        if e["event_type"] == "terminal_judge_editing_evaluated"]
            self.assertEqual(len(verdicts), 1)
            self.assertEqual(verdicts[0]["payload"].get("status"), "fired")
            # The once-per-gate broad run stamps the gate file before the close
            # is reached, so its status — not its bytes — is the invariant.
            self.assertEqual(_read_frontmatter(fdir / "GATE-01.md").get("status"), "open")
            self.assertEqual((fdir / "PLAN.md").read_text(), plan_before)
            self.assertEqual((root / ".specfuse" / "roadmap.md").read_text(),
                             roadmap_before)
            self.assertEqual(_roadmap_row_status(root, FEATURE_ID), "active")


class CleanFeatureClosesUnchanged(_Base):
    def test_closes_as_on_head(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="docs/x.md")
            self._stub_agent()

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0)
            self.assertEqual(_read_frontmatter(fdir / "PLAN.md").get("status"), "done")
            self.assertEqual(_read_frontmatter(fdir / "GATE-01.md").get("status"), "passed")
            self.assertEqual(_roadmap_row_status(root, FEATURE_ID), "done")
            events = _read_events(fdir / "events.jsonl")
            self.assertFalse([e for e in events if e["event_type"] == "human_escalation"
                              and e["payload"].get("reason") == "judge_editing_terminal"])
            verdicts = [e for e in events
                        if e["event_type"] == "terminal_judge_editing_evaluated"]
            self.assertEqual(len(verdicts), 1)
            self.assertEqual(verdicts[0]["payload"].get("status"), "clean")


def _acknowledge(root: Path, fdir: Path, paths: "list[str]", reason: str) -> None:
    """What the operator does: author the field, then `/unblock-wu` flips the
    close unit back to pending."""
    close = fdir / "WU-G1-CLOSE.md"
    text = close.read_text().replace("status: blocked_human", "status: pending", 1)
    text = text.replace(
        "status: pending\n",
        "status: pending\njudge_edit_acknowledged:\n"
        f"  paths: [{', '.join(paths)}]\n  reason: \"{reason}\"\n", 1)
    close.write_text(text)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "ack"], check=True)


class AcknowledgedStopProceeds(_Base):
    def test_rerun_dispatches_close_and_records_reason(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="specfuse/loop/arm_eval.py")
            self._stub_agent()
            self.assertNotEqual(loop.run(None, dry_run=False), 0)
            _acknowledge(root, fdir, ["specfuse/loop/arm_eval.py"], "reviewed by hand")

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0)
            self.assertIn(f"{FEATURE_ID}/G1-CLOSE", self.dispatched)
            events = _read_events(fdir / "events.jsonl")
            acks = [e for e in events
                    if e["event_type"] == "terminal_judge_editing_acknowledged"]
            self.assertEqual(len(acks), 1)
            self.assertEqual(acks[0]["payload"]["reason"], "reviewed by hand")
            self.assertEqual(acks[0]["payload"]["paths"], ["specfuse/loop/arm_eval.py"])
            self.assertEqual(acks[0]["payload"]["close_unit"], f"{FEATURE_ID}/G1-CLOSE")


class NewPathRefires(_Base):
    def test_added_judge_path_halts_naming_only_the_new_path(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="specfuse/loop/arm_eval.py")
            self._stub_agent()
            self.assertNotEqual(loop.run(None, dry_run=False), 0)
            _acknowledge(root, fdir, ["specfuse/loop/arm_eval.py"], "reviewed by hand")
            wu = fdir / "WU-T01.md"
            wu.write_text(wu.read_text().replace(
                "  - specfuse/loop/arm_eval.py\n",
                "  - specfuse/loop/arm_eval.py\n  - specfuse/loop/judge.py\n", 1))
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "new path"],
                           check=True)
            self.dispatched.clear()

            rc = loop.run(None, dry_run=False)

            self.assertNotEqual(rc, 0)
            self.assertNotIn(f"{FEATURE_ID}/G1-CLOSE", self.dispatched)
            events = _read_events(fdir / "events.jsonl")
            esc = [e for e in events if e["event_type"] == "human_escalation"
                   and e["payload"].get("reason") == "judge_editing_terminal"]
            self.assertEqual(len(esc), 2)
            blob = str(esc[-1]["payload"]["hits"])
            self.assertIn("specfuse/loop/judge.py", blob)
            self.assertNotIn("arm_eval.py", blob)


class EveryAutonomyLevelStops(_Base):
    def test_each_level_halts_without_a_terminal_flip(self):
        for level in ("auto", "review", "supervised"):
            with self.subTest(autonomy=level), integration_workspace() as root:
                os.chdir(root)
                self.dispatched.clear()
                fdir = _scaffold(root, produces="specfuse/loop/arm_eval.py",
                                 autonomy=level)
                self._stub_agent()

                rc = loop.run(None, dry_run=False)

                self.assertNotEqual(rc, 0)
                events = _read_events(fdir / "events.jsonl")
                esc = [e for e in events if e["event_type"] == "human_escalation"
                       and e["payload"].get("reason") == "judge_editing_terminal"]
                self.assertEqual(len(esc), 1)
                self.assertNotEqual(_read_frontmatter(fdir / "PLAN.md").get("status"), "done")
                self.assertEqual(_roadmap_row_status(root, FEATURE_ID), "active")
                self.assertNotIn(f"{FEATURE_ID}/G1-CLOSE", self.dispatched)


class AutoClosePathStops(_Base):
    def test_halts_before_any_auto_close_decision(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="specfuse/loop/arm_eval.py")
            self._stub_agent()

            rc = loop.run(None, dry_run=False)

            self.assertNotEqual(rc, 0)
            events = _read_events(fdir / "events.jsonl")
            self.assertFalse([e for e in events if e["event_type"] == "auto_close_decision"])
            self.assertTrue([e for e in events if e["event_type"] == "human_escalation"
                             and e["payload"].get("reason") == "judge_editing_terminal"])

    def test_positive_control_without_judge_path_auto_closes(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="src/feature.py", unit_status="pending")
            self._stub_agent()

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0)
            events = _read_events(fdir / "events.jsonl")
            self.assertTrue([e for e in events if e["event_type"] == "auto_close_decision"
                             and e["payload"].get("auto") is True])


class BriefHasSixParts(_Base):
    def test_message_is_the_six_part_brief(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _scaffold(root, produces="specfuse/loop/arm_eval.py")
            self._stub_agent()
            loop.run(None, dry_run=False)

            events = _read_events(fdir / "events.jsonl")
            msg = next(e for e in events if e["event_type"] == "human_escalation"
                       and e["payload"].get("reason") == "judge_editing_terminal"
                       )["payload"]["message"]

            positions = [msg.index(f"## {h}") for h in loop.ESCALATION_PART_HEADINGS]
            self.assertEqual(positions, sorted(positions))
            self.assertLess(positions[-1], msg.index("specfuse:escalation id="))
            self.assertEqual(loop.escalation.validate_escalation_body(msg)
                             if hasattr(loop, "escalation") else [], [])
            self.assertIn(f"{FEATURE_ID}/T01", msg)
            self.assertIn("specfuse/loop/arm_eval.py", msg)
            self.assertIn("judge_edit_acknowledged", msg)
            self.assertIn("/unblock-wu", msg)
            self.assertIn("change the code or config that grades it", msg)


@unittest.skip("owned by FEAT-2026-0246/T04")
class DocsNoLongerRecommendReview(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
