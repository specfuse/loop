#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-LOOP-2026-0251 gate 1 oracle — a missing deliverable is refused before
the verification gates run. One class per Definition-of-done clause in
GATE-01.md. T01 implements clause 1; the rest are skipped naming their owning
unit.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

FEATURE_ID = "FEAT-2026-9251"
T01 = f"{FEATURE_ID}/T01"

_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
_COMPLETE = "```result\nstatus: complete\n```\n"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def _write_feature(root: Path) -> Path:
    fdir = root / f".specfuse/features/{FEATURE_ID}-fail-fast"
    fdir.mkdir(parents=True)
    close_id = f"{FEATURE_ID}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {FEATURE_ID}\ntitle: Fixture\nslug: fail-fast\n"
        "branch: feat/fail-fast\nroadmap_goal: test\nstatus: active\n---\n\n"
        "# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {T01}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{T01}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# G\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {T01}\ntype: implementation\nmodel: sonnet\n"
        "status: pending\nattempts: 0\nproduces:\n  - src/rule.py\n---\n\n"
        f"# T01{_BODY}")
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{_BODY}")
    Path(root, "src").mkdir(exist_ok=True)
    Path(root, "src/rule.py").write_text("SEVERITY = 'WARNING'\n")
    _git("add", ".")
    _git("commit", "-q", "-m", "scaffold")
    return fdir


class _Case(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in reversed(self._patches):
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _workspace(self):
        ws = integration_workspace()
        root = ws.__enter__()
        self.addCleanup(ws.__exit__, None, None, None)
        os.chdir(root)
        return root, _write_feature(root)


class TestProducesNotInDiffEarly(_Case):
    """Clause 1 — refused before `verify_fn`, same record as the late path."""

    def _attempt(self, touch: str, stdout: str = _COMPLETE):
        _, fdir = self._workspace()
        wu = loop.load_wu(fdir, {"id": T01, "file": "WU-T01.md",
                                 "depends_on": []})
        head = _git("rev-parse", "HEAD")
        calls = []

        def dispatch_fn(w, note):
            Path(touch).parent.mkdir(exist_ok=True)
            Path(touch).write_text("changed\n")
            return stdout

        def verify_fn(w, fd):
            calls.append(w.wu_id)
            return True, "(stub)"

        outcome, payload, usage = loop.execute_unit_attempt(
            wu, fdir, None, dispatch_fn=dispatch_fn, verify_fn=verify_fn,
            cost_tracking=False, head_before=head, prerun_cfg={},
            untracked_before=loop.untracked_paths())
        return wu, outcome, payload, usage, calls

    def test_untouched_path_is_refused_without_verifying(self):
        wu, outcome, payload, usage, calls = self._attempt("docs/notes.md")
        self.assertEqual(outcome, "produces_not_in_diff")
        self.assertEqual(payload["remaining"], ["src/rule.py"])
        self.assertIn("docs/notes.md", payload["touched"])
        self.assertEqual(calls, [])
        self.assertEqual(usage["verify_seconds"], 0)
        self.assertEqual(loop.build_attempt_gate_events(wu, 1), [])

    def test_changed_path_verifies_once_and_passes(self):
        _, outcome, _, _, calls = self._attempt("src/rule.py")
        self.assertEqual(outcome, "passed")
        self.assertEqual(calls, [T01])

    def test_justified_path_still_verifies(self):
        _, outcome, _, _, calls = self._attempt(
            "docs/notes.md",
            "```result\nstatus: complete\nproduces_unchanged:\n"
            "  - path: src/rule.py\n    justification: already holds\n```\n")
        self.assertEqual(outcome, "passed")
        self.assertEqual(calls, [T01])

    def test_index_is_left_alone(self):
        self._attempt("docs/notes.md")
        self.assertEqual(_git("diff", "--cached", "--name-only"), "")

    def _run_driver(self, early: bool):
        """`loop.run()` over an attempt that never touches `src/rule.py`.
        `early=False` silences the pre-verify check, leaving the late site."""
        _, fdir = self._workspace()
        verified = []

        def dispatch(wu, note, ct=True):
            if wu.wu_id == T01:
                Path("docs").mkdir(exist_ok=True)
                Path("docs/notes.md").write_text("notes\n")
            return _COMPLETE

        def verify(wu, fd, cfg=None):
            verified.append(wu.wu_id)
            return True, "(stub)"

        self._patch("dispatch", dispatch)
        self._patch("verify", verify)
        if not early:
            self._patch("early_produces_refusal", lambda *a, **k: None)
        self.assertEqual(loop.run(None, dry_run=False), 1)
        events = [json.loads(line) for line in
                  (fdir / "events.jsonl").read_text().splitlines() if line]
        refusals = [
            e["payload"] for e in events
            if e["event_type"] == "attempt_outcome"
            and e["payload"]["outcome"] == "produces_not_in_diff"]
        self.assertTrue(refusals)
        self.assertEqual(
            [e for e in events if e["event_type"] == "gate_result"
             and e["correlation_id"] == T01
             and e["payload"]["phase"] == "attempt"], [])
        return refusals[0], verified

    def test_early_record_equals_late_record(self):
        early, early_verified = self._run_driver(early=True)
        late, late_verified = self._run_driver(early=False)
        self.assertEqual(early_verified, [])
        self.assertIn(T01, late_verified)
        self.assertEqual(early["verify_seconds"], 0)
        for key in ("failure_class", "failure_signature", "summary"):
            self.assertEqual(early[key], late[key], key)


@unittest.skip("FEAT-LOOP-2026-0251/T02")
class TestPresenceEarly(unittest.TestCase):
    """Clause 2 — `deliverable_missing` / `no_deliverable_files` early."""

    def test_pending(self):
        self.fail("T02")


@unittest.skip("FEAT-LOOP-2026-0251/T02")
class TestOptOut(unittest.TestCase):
    """Clause 3 — `defaults.fail_fast_deliverables: false`."""

    def test_pending(self):
        self.fail("T02")


@unittest.skip("FEAT-LOOP-2026-0251/T03")
class TestTreeAndNote(unittest.TestCase):
    """Clause 4 — tree handling and retry note."""

    def test_pending(self):
        self.fail("T03")


@unittest.skip("FEAT-LOOP-2026-0251/T04")
class TestArmTimeWarning(unittest.TestCase):
    """Clause 5 — arm-time WARN for an unmentioned `produces:` path."""

    def test_pending(self):
        self.fail("T04")


if __name__ == "__main__":
    unittest.main()
