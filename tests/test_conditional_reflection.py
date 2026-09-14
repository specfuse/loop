#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Conditional reflection — FEAT-2026-0106/T03.

A close's reflective closing requirements (`## Cost analysis`,
`### Failure-class breakdown`) are only worth writing when the gate went
off-plan — a blocked/escalated WU, a `replan` event, or a cost overrun.
`gate_eval.evaluate_auto_close` already computes that signal, verdict-
independent, from events the driver holds; `loop.reflection_required` reads
it so the closing guards stop demanding reflective prose from a close that
sailed through on plan.

Covers:
  - `reflection_required` unit tests, one per off-plan signal, plus the
    fail-closed default when the predicate cannot be evaluated at all.
  - `assert_cost_analysis_section_when_met` / `assert_failure_class_breakdown_
    when_failures_present` respecting `reflection_required` alongside their
    existing verdict/failures-present conditions.
  - An end-to-end `loop.run()` through an on-plan close: `RETROSPECTIVE.md`'s
    `## Measurements` section is present and non-empty, and
    `judge.build_judge_bundle` returns non-empty measurements over it, with
    no reflective section written.
  - The same harness driven off-plan (a `replan` event on a substantive WU):
    the reflective sections still get written, unchanged from today.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable
from tests.test_gate_eval import _write_event, _write_plan_md, _write_wu_file

from specfuse.loop import judge as judge_mod

loop = load_loop()

DUMMY_HEAD = "0000000000000000000000000000000000000000"


# --------------------------------------------------------------------------- #
# reflection_required — unit tests                                            #
# --------------------------------------------------------------------------- #


class TestReflectionRequired(unittest.TestCase):

    def test_symbol_importable(self):
        self.assertTrue(hasattr(loop, "reflection_required"))

    def test_on_plan_gate_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9930", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9930/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9930/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9930/T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9930/G1-CLOSE", "close")
            _write_event(fdir, "FEAT-2026-9930/T01", "task_completed")
            self.assertFalse(loop.reflection_required(fdir, 1))

    def test_replan_event_is_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9931", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9931/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9931/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9931/T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9931/G1-CLOSE", "close")
            _write_event(fdir, "FEAT-2026-9931/T01", "replan")
            _write_event(fdir, "FEAT-2026-9931/T01", "task_completed")
            self.assertTrue(loop.reflection_required(fdir, 1))

    def test_blocked_human_event_is_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9932", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9932/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9932/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9932/T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9932/G1-CLOSE", "close")
            _write_event(fdir, "FEAT-2026-9932/T01", "blocked_human")
            _write_event(fdir, "FEAT-2026-9932/T01", "task_completed")
            self.assertTrue(loop.reflection_required(fdir, 1))

    def test_cost_overrun_is_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9933", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9933/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9933/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9933/T01", "implementation",
                           cost_usd=10.0, planned_cost_usd=1.0)
            _write_wu_file(fdir, "WU-90.md", "FEAT-2026-9933/G1-CLOSE", "close")
            _write_event(fdir, "FEAT-2026-9933/T01", "task_completed")
            self.assertTrue(loop.reflection_required(fdir, 1))

    def test_missing_plan_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(loop.reflection_required(Path(tmp), 1))

    def test_gate_not_found_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9934", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [],
            }])
            self.assertTrue(loop.reflection_required(fdir, 2))

    def test_missing_wu_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9935", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9935/T01", "file": "WU-01.md", "depends_on": []},
                ],
            }])
            # WU-01.md deliberately never written.
            self.assertTrue(loop.reflection_required(fdir, 1))


# --------------------------------------------------------------------------- #
# Closing guards respect reflection_required alongside their existing         #
# verdict / failures-present conditions                                      #
# --------------------------------------------------------------------------- #


def _wu_body() -> str:
    return ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")


def _make_close_wu(file: Path, wu_id: str = "FEAT-2026-9940/G1-CLOSE") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id, file=file, depends_on=[], type="close", model="opus",
        status="pending", attempts=0, title="Close", body=_wu_body(),
        verdict="met",
    )


def _write_close_wu_file(wu: "loop.WorkUnit") -> None:
    wu.file.write_text(
        f"---\nid: {wu.wu_id}\ntype: close\nstatus: pending\nattempts: 0\n"
        f"verdict: met\n---\n\n{wu.body}"
    )


class TestCostAnalysisGuardRespectsReflection(unittest.TestCase):

    def test_on_plan_met_close_skips_cost_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9940", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9940/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9940/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9940/T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            _write_event(fdir, "FEAT-2026-9940/T01", "task_completed")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Measurements\n\nSuite green.\n"
            )
            wu = _make_close_wu(fdir / "WU-90.md")
            _write_close_wu_file(wu)
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok, f"on-plan close must skip cost analysis: {reason!r}")

    def test_off_plan_met_close_requires_cost_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9941", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9941/T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9941/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9941/T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            _write_event(fdir, "FEAT-2026-9941/T01", "replan")
            _write_event(fdir, "FEAT-2026-9941/T01", "task_completed")
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Measurements\n\nSuite green.\n"
            )
            wu = _make_close_wu(fdir / "WU-90.md", "FEAT-2026-9941/G1-CLOSE")
            _write_close_wu_file(wu)
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok, "off-plan close must still require cost analysis")
            self.assertIn("assert_cost_analysis_section_when_met", reason)

            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Measurements\n\nSuite green.\n\n"
                "## Cost analysis\n\nOn budget.\n"
            )
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok, f"section now present: {reason!r}")


class TestFailureClassGuardRespectsReflection(unittest.TestCase):

    def test_on_plan_failure_skips_breakdown(self):
        """A transient failed-then-passed attempt alone is not an off-plan
        signal (only blocked/escalated, replan, and cost-overrun are), so an
        on-plan gate need not carry the breakdown even with a failed attempt
        in its history."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9942", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9942/G1-T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9942/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9942/G1-T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            (fdir / "events.jsonl").write_text(
                json.dumps({
                    "event_type": "attempt_outcome",
                    "correlation_id": "FEAT-2026-9942/G1-T01",
                    "payload": {"outcome": "failed", "failure_class": "tests",
                                "failure_signature": "x"},
                }) + "\n"
                + json.dumps({
                    "event_type": "task_completed",
                    "correlation_id": "FEAT-2026-9942/G1-T01",
                }) + "\n"
            )
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Measurements\n\nSuite green.\n"
            )
            wu = _make_close_wu(fdir / "WU-90.md", "FEAT-2026-9942/G1-CLOSE")
            _write_close_wu_file(wu)
            ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok, f"on-plan close must skip the breakdown: {reason!r}")

    def test_off_plan_failure_requires_breakdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan_md(fdir, "FEAT-2026-9943", gates=[{
                "gate": 1, "file": "GATE-01.md", "work_units": [
                    {"id": "FEAT-2026-9943/G1-T01", "file": "WU-01.md", "depends_on": []},
                    {"id": "FEAT-2026-9943/G1-CLOSE", "file": "WU-90.md", "depends_on": []},
                ],
            }])
            _write_wu_file(fdir, "WU-01.md", "FEAT-2026-9943/G1-T01", "implementation",
                           cost_usd=1.0, planned_cost_usd=1.0)
            (fdir / "events.jsonl").write_text(
                json.dumps({
                    "event_type": "attempt_outcome",
                    "correlation_id": "FEAT-2026-9943/G1-T01",
                    "payload": {"outcome": "failed", "failure_class": "tests",
                                "failure_signature": "x"},
                }) + "\n"
                + json.dumps({
                    "event_type": "replan",
                    "correlation_id": "FEAT-2026-9943/G1-T01",
                }) + "\n"
                + json.dumps({
                    "event_type": "task_completed",
                    "correlation_id": "FEAT-2026-9943/G1-T01",
                }) + "\n"
            )
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Measurements\n\nSuite green.\n"
            )
            wu = _make_close_wu(fdir / "WU-90.md", "FEAT-2026-9943/G1-CLOSE")
            _write_close_wu_file(wu)
            ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok, "off-plan gate with a real failure must require the breakdown")
            self.assertIn("assert_failure_class_breakdown_when_failures_present", reason)


# --------------------------------------------------------------------------- #
# End-to-end: loop.run() through an on-plan vs off-plan close                #
# --------------------------------------------------------------------------- #

from tests.test_lifecycle_integration import (  # noqa: E402
    _scaffold_feature,
    _read_events,
    _read_frontmatter,
)

_ON_PLAN_RETRO = (
    "# Retrospective\n\n## Measurements\n\nSuite green.\n\n"
    "Nothing generalizes from this gate.\n"
)

_OFF_PLAN_RETRO = (
    "# Retrospective\n\n## Measurements\n\nSuite green.\n\n"
    "## Cost analysis\n\nOn budget once the replan settled.\n\n"
    "Nothing generalizes from this gate.\n"
)


class TestConditionalReflectionEndToEnd(unittest.TestCase):
    """A real `loop.run()` through a two-unit gate: T01 then a dispatched
    close, reusing `test_lifecycle_integration`'s scaffold. `loop.dispatch` /
    `loop.verify` / `loop.run_judge_session` are stubbed at the same seam
    every integration test in this suite stubs; everything else — squash,
    the closing guards, judge dispatch, terminal flips — is the real driver.
    """

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

    def _stub_agent(self, retro_text: str, pre_close_hook=None) -> None:
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            if wu.type == "implementation":
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"
            if wu.type == "close":
                if pre_close_hook is not None:
                    pre_close_hook(wu.file.parent)
                (wu.file.parent / "RETROSPECTIVE.md").write_text(retro_text)
                loop.write_frontmatter_field(wu.file, "verdict", "met")
                return "```result\nstatus: complete\n```\n"
            return "```result\nstatus: complete\n```\n"

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
        self._patch(
            "run_judge_session",
            lambda prompt, *, timeout=None: ("```result\nverdict: met\n```", None),
        )

    def test_on_plan_gate_writes_measurements_only(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9950"
            fdir = _scaffold_feature(
                root, feature_id=feature_id, slug="on-plan-fixture",
                branch=f"feat/{feature_id.lower()}-on-plan-fixture",
                roadmap_status="active", plan_status="active",
                detail_section=True, auto_close_disabled=True)
            self._stub_agent(_ON_PLAN_RETRO)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertFalse(
                loop.reflection_required(fdir, 1),
                "fixture must actually be on-plan for this test to mean anything",
            )

            retro_text = (fdir / "RETROSPECTIVE.md").read_text()
            self.assertIn("## Measurements", retro_text)
            self.assertNotIn("## Cost analysis", retro_text)

            bundle = judge_mod.build_judge_bundle(fdir, 1, diff_text="")
            self.assertTrue(bundle.measurements.strip())

            close_fm = _read_frontmatter(fdir / "WU-G1-CLOSE.md")
            self.assertEqual(close_fm.get("verdict"), "met")

    def test_off_plan_gate_keeps_full_reflective_output(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9951"
            fdir = _scaffold_feature(
                root, feature_id=feature_id, slug="off-plan-fixture",
                branch=f"feat/{feature_id.lower()}-off-plan-fixture",
                roadmap_status="active", plan_status="active",
                detail_section=True, auto_close_disabled=True)

            def seed_replan(feature_dir: Path) -> None:
                with (feature_dir / "events.jsonl").open("a") as fh:
                    fh.write(json.dumps({
                        "event_type": "replan",
                        "correlation_id": f"{feature_id}/T01",
                    }) + "\n")

            self._stub_agent(_OFF_PLAN_RETRO, pre_close_hook=seed_replan)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertTrue(
                loop.reflection_required(fdir, 1),
                "fixture must actually be off-plan for this test to mean anything",
            )

            retro_text = (fdir / "RETROSPECTIVE.md").read_text()
            self.assertIn("## Measurements", retro_text)
            self.assertIn("## Cost analysis", retro_text)

            events = _read_events(fdir / "events.jsonl")
            self.assertTrue(any(
                e["event_type"] == "replan" for e in events
            ))


if __name__ == "__main__":
    unittest.main()
