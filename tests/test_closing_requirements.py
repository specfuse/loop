#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Closing-requirement registry — FEAT-2026-0054/T01.

Two things this file guards:

  TestRegistryShape — the registry in `specfuse/loop/closing_requirements.py`
    names every guard function `loop.py` actually registers in
    `CLOSING_ASSERTIONS_BY_TYPE` and `POST_PASS_INVARIANTS_BY_TYPE`, so a later
    lint mode (T02) or skeleton writer (T03) reading the registry can never
    drift from what the guards enforce.

  TestRegistryEquivalence — the refactor that moved literals (headings,
    filename templates, verdict values) out of the guard bodies into the
    registry did not change what any guard accepts. Each case here is a
    fixture the pre-refactor guard was already known to reject/accept; if the
    refactor silently changed behavior, these turn red.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests.test_closing_deliverable_guard import (
    DUMMY_HEAD,
    _make_wu,
    _setup_substantive_commit,
)

loop = load_loop()

from specfuse.loop.closing_requirements import CLOSING_REQUIREMENTS  # noqa: E402
from specfuse.loop import closing_requirements as creq  # noqa: E402
from specfuse.loop import lint_closing  # noqa: E402


class TestRegistryShape(unittest.TestCase):

    def test_registry_covers_all_registered_guards(self):
        for wu_type, fns in loop.CLOSING_ASSERTIONS_BY_TYPE.items():
            enforced = {r.enforced_by for r in CLOSING_REQUIREMENTS.get(wu_type, [])}
            for fn in fns:
                self.assertIn(
                    fn.__name__, enforced,
                    f"{fn.__name__} is registered for wu_type={wu_type!r} in "
                    f"CLOSING_ASSERTIONS_BY_TYPE but has no matching entry in "
                    f"CLOSING_REQUIREMENTS[{wu_type!r}]",
                )

    def test_registry_covers_all_post_pass_invariants(self):
        for wu_type, fns in loop.POST_PASS_INVARIANTS_BY_TYPE.items():
            enforced = {
                r.enforced_by for r in CLOSING_REQUIREMENTS.get(wu_type, [])
                if r.phase == "post-pass"
            }
            for fn in fns:
                self.assertIn(
                    fn.__name__, enforced,
                    f"{fn.__name__} is registered as a post-pass invariant for "
                    f"wu_type={wu_type!r} but has no matching phase='post-pass' "
                    f"entry in CLOSING_REQUIREMENTS[{wu_type!r}]",
                )

    def test_every_requirement_names_a_real_guard_function(self):
        # Most requirements are enforced both post-squash (a `loop.py`
        # driver guard) and pre-squash (a `lint_closing.py` checker of the
        # same name). `criteria_artifact_present` requirements are lint-only
        # — FEAT-2026-0056/T03 deliberately does not wire a driver-side
        # `assert_*` for them (see WU-03's Do-not-touch on `loop.py`) — so
        # their guard function lives in `lint_closing` instead.
        for req in creq.all_requirements():
            self.assertTrue(
                hasattr(loop, req.enforced_by) or hasattr(lint_closing, req.enforced_by),
                f"registry requirement {req.id} names enforced_by="
                f"{req.enforced_by!r}, which exists in neither loop.py nor "
                f"lint_closing.py",
            )

    def test_every_wu_type_has_entries(self):
        for wu_type in ("close", "close-intermediate", "plan-next"):
            self.assertTrue(
                CLOSING_REQUIREMENTS.get(wu_type),
                f"CLOSING_REQUIREMENTS has no entries for wu_type={wu_type!r}",
            )


class TestRegistryEquivalence(unittest.TestCase):
    """Each guard, exercised through its registry-declared shape, on a fixture."""

    def test_missing_retrospective_fails_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            head_before = _setup_substantive_commit(root, {
                "feature/agent-output.txt": "some output\n",
                "feature/WU-close.md": (
                    "---\nid: FEAT-9999/G1-CLOSE\ntype: close\n"
                    "status: done\nattempts: 1\nverdict: met\n---\n\n"
                    "# Close ceremony\n"
                ),
            })
            fdir = root / "feature"
            fdir.mkdir(exist_ok=True)
            wu = _make_wu(
                file=root / "feature/WU-close.md", wu_type="close", verdict="met",
            )
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(wu, fdir, root, head_before)
            finally:
                os.chdir(old_cwd)
            self.assertFalse(ok)
            self.assertIn("assert_retrospective_exists", reason)
            close_reqs = {r.enforced_by for r in CLOSING_REQUIREMENTS["close"]}
            self.assertIn("assert_retrospective_exists", close_reqs)

    def test_missing_verdict_fails_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(file=fdir / "WU.md", verdict=None)
            wu.file.write_text("---\nid: FEAT-9999/G1-CLOSE\ntype: close\n"
                                "status: pending\nattempts: 0\n---\n")
            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_verdict_well_formed", reason)
            req = next(
                r for r in CLOSING_REQUIREMENTS["close"]
                if r.enforced_by == "assert_verdict_well_formed"
            )
            self.assertEqual(req.frontmatter_field, "verdict")
            self.assertEqual(req.allowed_values, loop.VERDICT_VALUES)

    def test_verdict_met_without_cost_analysis_heading_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text("# Retro\n\nNo cost section here.\n")
            wu = _make_wu(file=fdir / "WU.md", verdict="met")
            wu.file.write_text("---\nid: FEAT-9999/G1-CLOSE\ntype: close\n"
                                "status: pending\nattempts: 0\nverdict: met\n---\n")
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_cost_analysis_section_when_met", reason)
            req = next(
                r for r in CLOSING_REQUIREMENTS["close"]
                if r.enforced_by == "assert_cost_analysis_section_when_met"
            )
            self.assertEqual(req.heading, creq.COST_ANALYSIS_HEADING)
            self.assertEqual(req.applies_when, "verdict_met")

    def test_failed_attempts_gate_without_failure_class_heading_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text("# Retro\n\nNo breakdown here.\n")
            events = [
                '{"event_type": "attempt_outcome", "correlation_id": '
                '"FEAT-9999/G1-T01", "payload": {"outcome": "failed", '
                '"failure_class": "verification", "failure_signature": "x"}}',
            ]
            (fdir / "events.jsonl").write_text("\n".join(events) + "\n")
            wu = _make_wu(wu_type="close", wu_id="FEAT-9999/G1-CLOSE", verdict="met")
            ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_failure_class_breakdown_when_failures_present", reason)
            req = next(
                r for r in CLOSING_REQUIREMENTS["close"]
                if r.enforced_by == "assert_failure_class_breakdown_when_failures_present"
            )
            self.assertEqual(req.heading, creq.FAILURE_CLASS_HEADING)
            self.assertEqual(req.applies_when, "failures_present")

    def test_plan_next_without_next_gate_review_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\ntitle: Test\n"
                "branch: feat/test\nroadmap_goal: test\nstatus: active\n---\n\n"
                "# Plan\n\n```yaml\ngates:\n"
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
                "      - id: FEAT-9999/T01\n        file: WU-T01.md\n"
                "        depends_on: []\n```\n"
            )
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_gate_review_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_gate_review_exists", reason)
            self.assertIn(creq.gate_review_filename(2), reason)
            req = next(
                r for r in CLOSING_REQUIREMENTS["plan-next"]
                if r.enforced_by == "assert_gate_review_exists"
            )
            self.assertEqual(req.file_derivation, creq.GATE_REVIEW_FILENAME_TEMPLATE)


if __name__ == "__main__":
    unittest.main()
