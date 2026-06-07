#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Effort-field acceptance — FEAT-2026-0007/T02.

Verifies that:
  1. load_wu() accepts a valid effort value ('low') and passes it through; the
     dispatched command includes '--effort low'.
  2. load_wu() raises ValueError mentioning the invalid value when effort is
     set to something outside {low, medium, high, xhigh, max}.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _write_wu(tmp: Path, effort: str | None = None) -> Path:
    effort_line = f"effort: {effort}\n" if effort is not None else ""
    path = tmp / "WU-T02.md"
    path.write_text(
        f"---\nid: FEAT-2026-9999/T02\ntype: implementation\n"
        f"model: claude-sonnet-4-6\n{effort_line}"
        f"status: pending\nattempts: 0\n---\n\n"
        "# Test effort unit\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    return path


class TestEffortFieldPositive(unittest.TestCase):

    def test_effort_low_loads_and_dispatches(self):
        """effort: low loads without error; --effort low appears in the dispatched command."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), effort="low")
            ref = {"id": "FEAT-2026-9999/T02", "file": "WU-T02.md", "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)

            self.assertEqual(wu.effort, "low")

            captured = {}

            def fake_dispatch(wu_arg, failure_note):
                cmd = [p.replace("{model}", wu_arg.model).replace("{effort}", wu_arg.effort)
                       for p in loop.CLAUDE_CMD]
                captured["cmd"] = cmd
                return (
                    "(stub)\n```result\nstatus: complete\nsummary: ok\n"
                    "files_changed: []\nacceptance_criteria: []\n```\n"
                )

            loop.execute_unit_attempt(
                wu, Path(tmp), None,
                dispatch_fn=fake_dispatch,
                verify_fn=lambda wu, fd, cfg=None: (True, "pass"),
            )

            cmd = captured["cmd"]
            self.assertIn("--effort", cmd)
            effort_idx = cmd.index("--effort")
            self.assertEqual(cmd[effort_idx + 1], "low")

    def test_effort_absent_defaults_to_medium(self):
        """Omitting effort from frontmatter gives wu.effort == 'medium'."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), effort=None)
            ref = {"id": "FEAT-2026-9999/T02", "file": "WU-T02.md", "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)
            self.assertEqual(wu.effort, "medium")


class TestEffortFieldNegative(unittest.TestCase):

    def test_invalid_effort_raises_value_error(self):
        """effort: xxx raises ValueError naming the invalid value."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), effort="xxx")
            ref = {"id": "FEAT-2026-9999/T02", "file": "WU-T02.md", "depends_on": []}
            with self.assertRaises(ValueError) as ctx:
                loop.load_wu(Path(tmp), ref)
            self.assertIn("xxx", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
