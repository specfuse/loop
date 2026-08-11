# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.agent.driver_invoke (FEAT-2026-0049/T13).

Covers: `build_invocation`'s argv shape and its subprocess-command-as-
parameter default, the module's no-in-process-driver structural guarantee,
`classify_halt`'s six-way halt classification (one test per row of WU-13's
table, plus the awaiting-review-vs-feature-done load-bearing case),
`HALT_BLOCKED`/`HALT_DRIVER_ERROR` detail carriage, `advance_feature`'s
single-subprocess-call contract, and the module's no-git/no-gh/no-write
structural guarantees. No test invokes a real `specfuse run` — a stub
runner stands in throughout.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.agent.driver_invoke import (
    HALT_ADVANCED,
    HALT_AWAITING_REVIEW,
    HALT_BLOCKED,
    HALT_DRIVER_ERROR,
    HALT_FEATURE_DONE,
    HALT_NOT_ARMED,
    FeatureState,
    advance_feature,
    build_invocation,
    classify_halt,
)

_PLAN_TEMPLATE = (
    "---\n"
    "feature_id: {feature_id}\n"
    "status: {status}\n"
    "---\n\n"
    "```yaml\n"
    "gates:\n"
    "{gate_lines}"
    "```\n"
)

_GATE_TEMPLATE = "---\nstatus: {status}\n---\n\n# GATE-{num:02d}\n"


class _StubResult:
    def __init__(self, returncode, stderr=""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = ""


class _StubRunner:
    def __init__(self, result, on_call=None):
        self._result = result
        self.calls = []
        self._on_call = on_call

    def __call__(self, argv, check=False):
        self.calls.append(argv)
        if self._on_call:
            self._on_call()
        return self._result


def _write_feature(tmp_root: Path, feature_id: str, plan_status: str,
                    gate_statuses: dict) -> Path:
    feature_dir = tmp_root / feature_id
    feature_dir.mkdir(parents=True, exist_ok=True)
    gate_lines = "".join(
        f"  - gate: {num}\n    file: GATE-{num:02d}.md\n" for num in gate_statuses
    )
    (feature_dir / "PLAN.md").write_text(
        _PLAN_TEMPLATE.format(
            feature_id=feature_id, status=plan_status, gate_lines=gate_lines
        )
    )
    for num, status in gate_statuses.items():
        (feature_dir / f"GATE-{num:02d}.md").write_text(
            _GATE_TEMPLATE.format(status=status, num=num)
        )
    (feature_dir / "events.jsonl").write_text("")
    return feature_dir


def _append_event(feature_dir: Path, event_type: str, correlation_id: str,
                   payload: dict) -> None:
    row = {
        "timestamp": "2026-08-11T00:00:00+00:00",
        "correlation_id": correlation_id,
        "event_type": event_type,
        "source": "driver",
        "source_version": "0.11.0",
        "payload": payload,
    }
    with (feature_dir / "events.jsonl").open("a") as fh:
        fh.write(json.dumps(row) + "\n")


class TestBuildInvocation(unittest.TestCase):
    def test_default_command_argv(self):
        self.assertEqual(
            build_invocation("FEAT-2026-0049"),
            ["specfuse", "run", "--feature", "FEAT-2026-0049"],
        )

    def test_injected_command_argv(self):
        self.assertEqual(
            build_invocation("FEAT-2026-0049", command=("python3", "-m", "specfuse")),
            ["python3", "-m", "specfuse", "--feature", "FEAT-2026-0049"],
        )


class TestModuleStructure(unittest.TestCase):
    def test_no_in_process_driver_import(self):
        source = Path("specfuse/agent/driver_invoke.py").read_text()
        self.assertNotIn("loop.run", source)
        self.assertNotIn("specfuse.loop.loop", source)

    def test_no_git_or_gh_literal(self):
        source = Path("specfuse/agent/driver_invoke.py").read_text()
        self.assertNotIn('"git"', source)
        self.assertNotIn('"gh"', source)


class TestHaltClassification(unittest.TestCase):
    def test_awaiting_review_is_not_confused_with_feature_done(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "open"}, event_count=0)
        after_awaiting = FeatureState(feature_dir=None, plan_status="active",
                                       gates={1: "passed"}, event_count=0)
        halt_class, _ = classify_halt(0, before, after_awaiting, [])
        self.assertEqual(halt_class, HALT_AWAITING_REVIEW)

        after_done = FeatureState(feature_dir=None, plan_status="done",
                                   gates={1: "passed"}, event_count=0)
        halt_class, _ = classify_halt(0, before, after_done, [])
        self.assertEqual(halt_class, HALT_FEATURE_DONE)

    def test_feature_done(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "passed"}, event_count=0)
        after = FeatureState(feature_dir=None, plan_status="done",
                              gates={1: "passed"}, event_count=0)
        halt_class, detail = classify_halt(0, before, after, [])
        self.assertEqual(halt_class, HALT_FEATURE_DONE)

    def test_all_gates_passed_but_plan_not_done_is_awaiting_review(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "open", 2: "passed"}, event_count=0)
        after = FeatureState(feature_dir=None, plan_status="active",
                              gates={1: "passed", 2: "passed"}, event_count=0)
        halt_class, detail = classify_halt(0, before, after, [])
        self.assertEqual(halt_class, HALT_AWAITING_REVIEW)
        self.assertIn("done", detail)

    def test_gate_advanced_from_unpassed_to_passed(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "passed", 2: "open", 3: "open"},
                               event_count=0)
        after = FeatureState(feature_dir=None, plan_status="active",
                              gates={1: "passed", 2: "passed", 3: "open"},
                              event_count=0)
        halt_class, detail = classify_halt(0, before, after, [])
        self.assertEqual(halt_class, HALT_ADVANCED)
        self.assertEqual(detail, {"gate": 2})

    def test_gate_reads_awaiting_review(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "passed", 2: "open"}, event_count=0)
        after = FeatureState(feature_dir=None, plan_status="active",
                              gates={1: "passed", 2: "awaiting_review"}, event_count=0)
        halt_class, _ = classify_halt(0, before, after, [])
        self.assertEqual(halt_class, HALT_AWAITING_REVIEW)

    def test_not_armed_on_rc_2(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "open"}, event_count=0)
        halt_class, _ = classify_halt(2, before, before, [])
        self.assertEqual(halt_class, HALT_NOT_ARMED)

    def test_blocked_on_rc_1_with_human_escalation(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "open"}, event_count=0)
        new_events = [{
            "correlation_id": "FEAT-2026-0049/T99",
            "event_type": "human_escalation",
            "payload": {"reason": "agent_reported_blocked", "blocked_reason": "needs creds"},
        }]
        halt_class, detail = classify_halt(1, before, before, new_events)
        self.assertEqual(halt_class, HALT_BLOCKED)
        self.assertEqual(detail["wu_id"], "FEAT-2026-0049/T99")
        self.assertEqual(detail["reason"], "agent_reported_blocked")

    def test_driver_error_on_rc_1_without_human_escalation(self):
        before = FeatureState(feature_dir=None, plan_status="active",
                               gates={1: "open"}, event_count=0)
        stderr = "another driver holds the lock for this feature"
        halt_class, detail = classify_halt(1, before, before, [], stderr)
        self.assertEqual(halt_class, HALT_DRIVER_ERROR)
        self.assertEqual(detail, stderr)


class TestAdvanceFeature(unittest.TestCase):
    def test_issues_exactly_one_subprocess_with_build_invocations_argv(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            _write_feature(tmp_root, "FEAT-2026-0099", "active", {1: "open"})
            runner = _StubRunner(_StubResult(2))

            result = advance_feature(
                runner, "FEAT-2026-0099", features_root=tmp_root
            )

            self.assertEqual(len(runner.calls), 1)
            self.assertEqual(
                runner.calls[0],
                build_invocation("FEAT-2026-0099"),
            )
            self.assertEqual(result.halt_class, HALT_NOT_ARMED)

    def test_reads_state_before_and_after_and_classifies_advanced(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            feature_dir = _write_feature(
                tmp_root, "FEAT-2026-0099", "active", {1: "open", 2: "open"}
            )

            def _flip_gate_passed():
                (feature_dir / "GATE-01.md").write_text(
                    _GATE_TEMPLATE.format(status="passed", num=1)
                )

            runner = _StubRunner(_StubResult(0), on_call=_flip_gate_passed)
            result = advance_feature(
                runner, "FEAT-2026-0099", features_root=tmp_root
            )
            self.assertEqual(result.halt_class, HALT_ADVANCED)
            self.assertEqual(result.detail, {"gate": 1})

    def test_blocked_reads_the_appended_human_escalation_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            feature_dir = _write_feature(
                tmp_root, "FEAT-2026-0099", "active", {1: "open"}
            )

            def _append_escalation():
                _append_event(
                    feature_dir, "human_escalation", "FEAT-2026-0099/T01",
                    {"reason": "agent_reported_blocked", "blocked_reason": "needs creds"},
                )

            runner = _StubRunner(_StubResult(1), on_call=_append_escalation)
            result = advance_feature(
                runner, "FEAT-2026-0099", features_root=tmp_root
            )
            self.assertEqual(result.halt_class, HALT_BLOCKED)
            self.assertEqual(result.detail["wu_id"], "FEAT-2026-0099/T01")
            self.assertEqual(result.detail["reason"], "agent_reported_blocked")

    def test_lock_held_stderr_reaches_detail_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            _write_feature(tmp_root, "FEAT-2026-0099", "active", {1: "open"})
            stderr = "another driver holds the lock for FEAT-2026-0099"
            runner = _StubRunner(_StubResult(1, stderr=stderr))
            result = advance_feature(
                runner, "FEAT-2026-0099", features_root=tmp_root
            )
            self.assertEqual(result.halt_class, HALT_DRIVER_ERROR)
            self.assertEqual(result.detail, stderr)


if __name__ == "__main__":
    unittest.main()
