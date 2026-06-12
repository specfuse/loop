#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Per-WU unsandboxed opt-in — FEAT-2026-0014 follow-on.

Verifies that:
  1. load_wu() defaults unsandboxed=False and rationale="" when fields absent.
  2. load_wu() reads unsandboxed=true + rationale into the WorkUnit.
  3. load_wu() raises ValueError when unsandboxed=true but rationale missing/blank.
  4. dispatch() injects `--dangerously-skip-permissions` AFTER `-p` when
     wu.unsandboxed is True; omits it otherwise.
  5. The run() attempt loop emits an `unsandboxed_dispatch` event whose payload
     carries the rationale verbatim, before the first attempt.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop

loop = load_loop()


def _write_wu(
    tmp: Path,
    *,
    unsandboxed: bool | None = None,
    rationale: str | None = None,
    filename: str = "WU-T01.md",
) -> Path:
    extra = ""
    if unsandboxed is not None:
        extra += f"unsandboxed: {str(unsandboxed).lower()}\n"
    if rationale is not None:
        extra += f'unsandboxed_rationale: "{rationale}"\n'
    path = tmp / filename
    path.write_text(
        f"---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
        f"model: claude-sonnet-4-6\neffort: medium\n"
        f"status: pending\nattempts: 0\n{extra}---\n\n"
        "# Test unsandboxed unit\n\n**Context.** test\n\n"
        "**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    return path


_REF = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md", "depends_on": []}


class TestLoadWUDefaults(unittest.TestCase):
    def test_unsandboxed_default_false_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp))
            wu = loop.load_wu(Path(tmp), _REF)
            self.assertFalse(wu.unsandboxed)
            self.assertEqual(wu.unsandboxed_rationale, "")


class TestLoadWUReadsOptIn(unittest.TestCase):
    def test_unsandboxed_true_with_rationale_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(
                Path(tmp),
                unsandboxed=True,
                rationale="gh CLI auth requires unsandboxed subprocess",
            )
            wu = loop.load_wu(Path(tmp), _REF)
            self.assertTrue(wu.unsandboxed)
            self.assertEqual(
                wu.unsandboxed_rationale,
                "gh CLI auth requires unsandboxed subprocess",
            )


class TestLoadWURefusesUnjustified(unittest.TestCase):
    def test_unsandboxed_true_without_rationale_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), unsandboxed=True)
            with self.assertRaises(ValueError) as cx:
                loop.load_wu(Path(tmp), _REF)
            self.assertIn("unsandboxed", str(cx.exception))
            self.assertIn("rationale", str(cx.exception))

    def test_unsandboxed_true_with_blank_rationale_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), unsandboxed=True, rationale="   ")
            with self.assertRaises(ValueError):
                loop.load_wu(Path(tmp), _REF)


class TestDispatchCmdBuilding(unittest.TestCase):
    """Exercise dispatch() with subprocess.run mocked so we can capture argv."""

    def _build_wu(self, unsandboxed: bool, rationale: str = ""):
        return loop.WorkUnit(
            wu_id="FEAT-2026-9999/T01",
            file=Path("WU-T01.md"),
            depends_on=[],
            type="implementation",
            model="claude-sonnet-4-6",
            effort="medium",
            status="pending",
            attempts=0,
            title="t",
            body="body",
            unsandboxed=unsandboxed,
            unsandboxed_rationale=rationale,
        )

    def test_unsandboxed_true_injects_flag_after_dash_p(self):
        wu = self._build_wu(True, "rationale here")
        fake_proc = mock.MagicMock(stdout="ignored", returncode=0)
        with mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
            loop.dispatch(wu, failure_note=None, cost_tracking=False)
        args, _ = run.call_args
        cmd = args[0]
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertEqual(cmd[0], "claude")
        self.assertEqual(cmd[1], "-p")
        # Flag must come AFTER -p (claude's flag-ordering requirement)
        self.assertEqual(cmd[2], "--dangerously-skip-permissions")
        # Subsequent flags still present
        self.assertIn("--model", cmd)
        self.assertIn("claude-sonnet-4-6", cmd)
        self.assertIn("--effort", cmd)
        self.assertIn("medium", cmd)

    def test_unsandboxed_false_omits_flag(self):
        wu = self._build_wu(False)
        fake_proc = mock.MagicMock(stdout="ignored", returncode=0)
        with mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
            loop.dispatch(wu, failure_note=None, cost_tracking=False)
        args, _ = run.call_args
        cmd = args[0]
        self.assertNotIn("--dangerously-skip-permissions", cmd)


class TestUnsandboxedDispatchEventBuilt(unittest.TestCase):
    """The audit event's shape — built by build_event with the rationale payload."""

    def test_event_carries_rationale(self):
        evt = loop.build_event(
            "unsandboxed_dispatch",
            "FEAT-2026-9999/T01",
            {"rationale": "gh CLI auth requires unsandboxed subprocess"},
        )
        self.assertEqual(evt["event_type"], "unsandboxed_dispatch")
        self.assertEqual(evt["correlation_id"], "FEAT-2026-9999/T01")
        self.assertEqual(
            evt["payload"]["rationale"],
            "gh CLI auth requires unsandboxed subprocess",
        )
        # JSON-serializable (events.jsonl is line-delimited JSON)
        json.dumps(evt)


if __name__ == "__main__":
    unittest.main()
