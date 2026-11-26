#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`run()` wires `gate_result` events into events.jsonl (#3599).

`tests/test_gate_timings.py` drives `execute_unit_attempt()`,
`build_attempt_gate_events()` and `build_phase_gate_events()` directly; nothing
there fails if `run()` stops calling them. This module runs `run()` end to end
on a temporary feature — stubbed agent, real gate commands — and reads the
events it flushed:

1. one `phase: attempt` `gate_result` per gate per verified attempt, carrying
   that attempt's number, and none on an attempt that never verified (the
   per-attempt reset of `wu.last_gate_results`);
2. `phase: baseline` events when a failed attempt triggers the retroactive
   baseline probe;
3. `phase: broad` events after the gate's broad run.

The unit's three attempts: (1) leaves a flag file that fails one gate, so the
attempt fails and the baseline probe runs; (2) bills zero input tokens, so
verify() never runs; (3) passes. The close then triggers the broad run and
reports itself blocked, which ends the run.
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

_FEATURE_ID = "FEAT-TEST-3599"
_SLUG = "gate-result-wiring"
_T01 = f"{_FEATURE_ID}/T01"
_CLOSE = f"{_FEATURE_ID}/G1-CLOSE"
_GATES = ["flag-absent", "sleepy"]
_BODY = (
    "\n\n**Objective.** test\n\n**Context.** test\n\n"
    "**Acceptance criteria.** test\n\n**Do not touch.** test\n\n"
    "**Verification.** test\n\n**Escalation triggers.** test\n"
)
_USAGE = {"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.001}


def _scaffold(root: Path) -> Path:
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "verification.yml").write_text(
        "code:\n"
        "  - name: flag-absent\n    command: \"test ! -f broken.flag\"\n"
        "  - name: sleepy\n    command: \"sleep 0.1\"\n"
        "doc:\n  - name: noop\n    command: \"true\"\n"
        "plannext:\n  - name: noop\n    command: \"true\"\n"
    )
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: gate-result-wiring\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Gate result wiring | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {_FEATURE_ID}\ntitle: Gate result wiring\n"
        f"slug: {_SLUG}\nbranch: feat/{_FEATURE_ID}-{_SLUG}\n"
        "roadmap_goal: prove run() flushes gate_result events\n"
        "status: active\n---\n\n"
        f"# Plan: {_SLUG}\n\n```yaml\ngates:\n  - gate: 1\n"
        "    file: GATE-01.md\n    work_units:\n"
        f"      - id: {_T01}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {_CLOSE}\n        file: WU-90-close.md\n"
        f"        depends_on: [{_T01}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {_T01}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\nmax_attempts: 3\n---\n\n# T01{_BODY}")
    (fdir / "WU-90-close.md").write_text(
        f"---\nid: {_CLOSE}\ntype: close\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{_BODY}")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold gate-result-wiring fixture"], check=True)
    return fdir


class RunGateResultWiringTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cwd = os.getcwd()
        patched = {}

        def patch(name, value):
            patched[name] = getattr(loop, name)
            setattr(loop, name, value)

        attempts = {"n": 0}

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            if wu.wu_id == _CLOSE:
                return ("```result\nstatus: blocked\n"
                        "blocked_reason: end of fixture\n```\n", _USAGE)
            attempts["n"] += 1
            if attempts["n"] == 2:
                return ("(simulated empty agent output)\n",
                        {"input_tokens": 0, "output_tokens": 0,
                         "cost_usd": 0.0})
            write_stub_deliverable(wu)
            if attempts["n"] == 1:
                Path("broken.flag").write_text("x\n")
            return "```result\nstatus: complete\n```\n", _USAGE

        try:
            with integration_workspace() as root:
                os.chdir(root)
                fdir = _scaffold(root)
                patch("dispatch", fake_dispatch)
                cls.rc = loop.run(None, dry_run=False)
                events_path = fdir / "events.jsonl"
                cls.events = [json.loads(ln) for ln in
                              events_path.read_text().splitlines() if ln]
                cls.t01_status = loop.load_wu(fdir, {
                    "id": _T01, "file": "WU-T01.md",
                    "depends_on": []}).status
        finally:
            os.chdir(cwd)
            for name, original in patched.items():
                setattr(loop, name, original)

    def _gate_results(self, phase):
        return [e for e in self.events
                if e["event_type"] == "gate_result"
                and e["payload"]["phase"] == phase]

    def test_fixture_ran_as_designed(self):
        outcomes = [e["payload"]["outcome"] for e in self.events
                    if e["event_type"] == "attempt_outcome"
                    and e["correlation_id"] == _T01]
        self.assertEqual(outcomes[0], "failed")
        self.assertEqual(outcomes[-1], "passed")
        self.assertEqual(self.t01_status, "done")
        self.assertTrue(any(e["event_type"] == "broad_run_result"
                            for e in self.events))

    def test_attempt_phase_one_per_gate_per_verified_attempt(self):
        events = self._gate_results("attempt")
        by_attempt: dict = {}
        for e in events:
            self.assertEqual(e["correlation_id"], _T01)
            by_attempt.setdefault(e["payload"]["attempt"], []).append(
                e["payload"])
        self.assertEqual(sorted(by_attempt), [1, 3],
                         "attempt 2 never verified, so it must carry no "
                         "gate_result — stale results from attempt 1 mean "
                         "run() stopped resetting wu.last_gate_results")
        for attempt, payloads in by_attempt.items():
            self.assertEqual(sorted(p["gate"] for p in payloads), _GATES,
                             f"attempt {attempt}")
        first = {p["gate"]: p["ok"] for p in by_attempt[1]}
        third = {p["gate"]: p["ok"] for p in by_attempt[3]}
        self.assertEqual(first, {"flag-absent": False, "sleepy": True})
        self.assertEqual(third, {"flag-absent": True, "sleepy": True})

    def test_baseline_phase_after_failed_attempt(self):
        events = self._gate_results("baseline")
        self.assertEqual(sorted(e["payload"]["gate"] for e in events), _GATES)
        for e in events:
            self.assertEqual(e["correlation_id"], _T01)
            self.assertIsNone(e["payload"]["attempt"])
            self.assertTrue(e["payload"]["ok"],
                            "the probe measures the pre-attempt tree, where "
                            "the flag file does not exist")

    def test_broad_phase_after_broad_run(self):
        events = self._gate_results("broad")
        self.assertEqual(sorted(e["payload"]["gate"] for e in events), _GATES)
        for e in events:
            self.assertEqual(e["correlation_id"], _FEATURE_ID)
            self.assertIsNone(e["payload"]["attempt"])
            self.assertTrue(e["payload"]["ok"])


if __name__ == "__main__":
    unittest.main()
