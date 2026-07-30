#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Dispatch-time closing-skeleton pre-creation — FEAT-2026-0054/T03.

When the driver dispatches a `close`, `close-intermediate`, or `plan-next`
work unit, every artifact shape the post-squash closing guards assert on
must already exist as a stub before the agent session starts, so a fresh
session fills content instead of reconstructing format from prose.
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

_COMPLETE_STDOUT = (
    "(stub)\n```result\nstatus: complete\nsummary: ok\n"
    "files_changed: []\nacceptance_criteria: []\n```\n"
)


def _make_wu(wu_id: str, wu_type: str) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path("FAKE-WU.md"),
        depends_on=[],
        type=wu_type,
        model="opus",
        status="pending",
        attempts=0,
        title="test WU",
        body=_WU_BODY,
    )


def _write_plan(fd: Path, gates_yaml: str) -> None:
    (fd / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-9999\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n{gates_yaml}```\n"
    )


def _two_gate_plan(fd: Path) -> None:
    _write_plan(fd, (
        "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
        "        depends_on: []\n"
        "  - gate: 2\n    file: GATE-02.md\n    work_units: []\n"
    ))


def _single_gate_plan(fd: Path) -> None:
    _write_plan(fd, (
        "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        "      - id: FEAT-9999/G1-CLOSE\n        file: WU-close.md\n"
        "        depends_on: []\n"
    ))


def _fake_verify(wu, feature_dir, *args, **kwargs):
    return True, "(verify was called)"


class TestSkeletonPrecreation(unittest.TestCase):

    def test_plan_next_dispatch_precreates_gate_review_stub(self):
        """On dispatch of a plan-next WU, GATE-(N+1)-REVIEW.md is materialized,
        correctly named for the gate being armed, before the agent runs."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _two_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-PLAN", "plan-next")

            seen_before_dispatch = {}

            def fake_dispatch(w, note):
                seen_before_dispatch["exists"] = (fdir / "GATE-02-REVIEW.md").exists()
                return _COMPLETE_STDOUT

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=fake_dispatch,
                verify_fn=_fake_verify,
            )

            self.assertTrue(seen_before_dispatch["exists"],
                             "review stub must exist before the agent session starts")
            review = fdir / "GATE-02-REVIEW.md"
            self.assertTrue(review.exists())
            self.assertTrue(review.read_text().strip())
            self.assertIn("Gate 2", review.read_text())

    def test_plan_next_dispatch_noop_when_terminal(self):
        """Single-gate (terminal) feature: no next gate → no review stub."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _single_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-PLAN", "plan-next")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            self.assertFalse((fdir / "GATE-02-REVIEW.md").exists())

    def test_gate_review_stub_left_untouched_if_exists(self):
        """A drafted GATE-(N+1)-REVIEW.md is never clobbered by pre-creation."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _two_gate_plan(fdir)
            (fdir / "GATE-02-REVIEW.md").write_text("# Gate 2 review\n\nAlready drafted.\n")
            wu = _make_wu("FEAT-9999/G1-PLAN", "plan-next")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            self.assertEqual(
                (fdir / "GATE-02-REVIEW.md").read_text(),
                "# Gate 2 review\n\nAlready drafted.\n",
            )

    def test_close_intermediate_dispatch_precreates_gate_section(self):
        """close-intermediate dispatch pre-creates the '## Gate N' heading
        RETROSPECTIVE.md needs (assert_retrospective_gate_section)."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _two_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-CLOSE-INTERMEDIATE", "close-intermediate")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro = fdir / "RETROSPECTIVE.md"
            self.assertTrue(retro.exists())
            self.assertTrue(loop.gate_section_heading_re(1).search(retro.read_text()))

    def test_close_dispatch_no_gate_heading_required(self):
        """A terminal 'close' WU does not need a '## Gate N' heading (only
        close-intermediate does) — pre-creation must not invent one."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _single_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-CLOSE", "close")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro = fdir / "RETROSPECTIVE.md"
            if retro.exists():
                self.assertFalse(loop.gate_section_heading_re(1).search(retro.read_text()))

    def test_failure_class_breakdown_precreated_when_failures_present(self):
        """'### Failure-class breakdown' is pre-populated from events.jsonl
        when a substantive WU in this gate failed a prior attempt."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _single_gate_plan(fdir)
            (fdir / "events.jsonl").write_text(
                '{"event_type": "attempt_outcome", "correlation_id": '
                '"FEAT-9999/G1-T01", "payload": {"outcome": "failed", '
                '"failure_class": "verification", "failure_signature": "x"}}\n'
            )
            wu = _make_wu("FEAT-9999/G1-CLOSE", "close")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro_text = (fdir / "RETROSPECTIVE.md").read_text()
            self.assertIn("### Failure-class breakdown", retro_text)
            self.assertIn("verification", retro_text)

    def test_failure_class_breakdown_absent_when_no_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _single_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-CLOSE", "close")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro = fdir / "RETROSPECTIVE.md"
            if retro.exists():
                self.assertNotIn("### Failure-class breakdown", retro.read_text())

    def test_deferral_heading_precreated_when_autoclose_debt_marker_present(self):
        """'## What the loop did NOT verify' is pre-created on a terminal close
        dispatch when an earlier gate's auto-close stub left a debt marker."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _write_plan(fdir, (
                "  - gate: 1\n    file: GATE-01.md\n    work_units: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
                "      - id: FEAT-9999/G2-CLOSE\n        file: WU-close.md\n"
                "        depends_on: []\n"
            ))
            (fdir / "RETROSPECTIVE.md").write_text(
                "<!-- specfuse:autoclose-debt gate=1 wus=T01 criteria=1 "
                "predicate=v1 -->\n\nGate 1 auto-closed on-plan.\n"
            )
            wu = _make_wu("FEAT-9999/G2-CLOSE", "close")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro_text = (fdir / "RETROSPECTIVE.md").read_text()
            self.assertIn("## What the loop did NOT verify", retro_text)
            self.assertIn("gate 1", retro_text.lower())

    def test_no_placeholder_verdict_ever_written(self):
        """Pre-creation never introduces a `verdict:` frontmatter field."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _single_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-CLOSE", "close")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro = fdir / "RETROSPECTIVE.md"
            if retro.exists():
                self.assertNotIn("verdict:", retro.read_text())
            self.assertFalse((fdir / "WU-close.md").exists())

    def test_retrospective_precreation_idempotent_no_duplicate_sections(self):
        """Re-dispatch after a failed attempt (same on-disk state) must not
        duplicate a stub section already written by a prior pre-creation."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _two_gate_plan(fdir)
            wu = _make_wu("FEAT-9999/G1-CLOSE-INTERMEDIATE", "close-intermediate")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )
            first_pass = (fdir / "RETROSPECTIVE.md").read_text()

            loop.execute_unit_attempt(
                wu, fdir, "previous attempt failed verification",
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )
            second_pass = (fdir / "RETROSPECTIVE.md").read_text()

            self.assertEqual(first_pass, second_pass)
            self.assertEqual(
                second_pass.count("## Gate 1"), 1,
                "re-dispatch must not duplicate the Gate 1 stub heading",
            )

    def test_retrospective_precreation_appends_without_disturbing_existing_content(self):
        """A RETROSPECTIVE.md carrying an earlier gate's content is appended
        to, byte-identical existing lines preserved."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            _two_gate_plan(fdir)
            existing = "## Gate 0 — hand-authored notes\n\nSome prior prose.\n"
            (fdir / "RETROSPECTIVE.md").write_text(existing)
            wu = _make_wu("FEAT-9999/G1-CLOSE-INTERMEDIATE", "close-intermediate")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            retro_text = (fdir / "RETROSPECTIVE.md").read_text()
            self.assertTrue(retro_text.startswith(existing))
            self.assertIn("## Gate 1", retro_text)

    def test_precreation_noop_for_non_closing_wu_types(self):
        """implementation / hygiene WUs never trigger skeleton writes."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu("FEAT-9999/T01", "implementation")

            loop.execute_unit_attempt(
                wu, fdir, None,
                dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
                verify_fn=_fake_verify,
            )

            self.assertFalse((fdir / "RETROSPECTIVE.md").exists())
            self.assertFalse((fdir / "GATE-02-REVIEW.md").exists())


if __name__ == "__main__":
    unittest.main()
