#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""close-intermediate WU type — FEAT-2026-0015/T01.

Verifies that MODEL_BY_TYPE, EFFORT_BY_TYPE, and GATES_FOR_TYPE include
the new 'close-intermediate' key, and that load_wu() honours its defaults.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


class TestCloseIntermediateInDicts(unittest.TestCase):

    def test_close_intermediate_in_model_by_type(self):
        self.assertEqual(loop.MODEL_BY_TYPE["close-intermediate"], "opus")

    def test_close_intermediate_in_effort_by_type(self):
        self.assertEqual(loop.EFFORT_BY_TYPE["close-intermediate"], "high")

    def test_close_intermediate_in_gates_for_type(self):
        self.assertEqual(loop.GATES_FOR_TYPE["close-intermediate"], "plannext")


class TestLoadWuCloseIntermediate(unittest.TestCase):

    def _write_wu(self, tmp: Path) -> Path:
        path = tmp / "WU-CI01.md"
        path.write_text(
            "---\nid: FEAT-2026-9999/CI01\ntype: close-intermediate\n"
            "status: pending\nattempts: 0\n---\n\n"
            "# Close-intermediate test unit\n\n"
            "**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n"
        )
        return path

    def test_load_wu_accepts_close_intermediate_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_wu(Path(tmp))
            ref = {"id": "FEAT-2026-9999/CI01", "file": "WU-CI01.md",
                   "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)
            self.assertEqual(wu.type, "close-intermediate")
            self.assertEqual(wu.model, "opus")
            self.assertEqual(wu.effort, "high")
