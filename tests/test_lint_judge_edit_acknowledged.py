#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Lint of the operator-authored `judge_edit_acknowledged` field (FEAT-2026-0246/T02)."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

VALID = '  paths: [specfuse/loop/arm_eval.py]\n  reason: "reviewed"\n'


def _feature(tmpdir: str, ack: str, *, on: str = "close") -> Path:
    feature = Path(tmpdir) / "feature"
    feature.mkdir()
    (feature / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9996\ntitle: ack lint\nbranch: feat/ack\n"
        "roadmap_goal: Verify ack lint.\nstatus: active\n---\n\n# Plan\n\n```yaml\n"
        "gates:\n  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        "      - id: FEAT-2026-9996/T01\n        file: WU-01-impl.md\n        depends_on: []\n"
        "      - id: FEAT-2026-9996/G1-CLOSE\n        file: WU-90-close.md\n"
        "        depends_on: [FEAT-2026-9996/T01]\n```\n")
    field = f"judge_edit_acknowledged:\n{ack}" if ack else ""
    body = ("\n# T\n\n**Context.** t.\n\n**Acceptance criteria.** The code works.\n\n"
            "**Do not touch.** none.\n\n**Verification.** code gates.\n\n"
            "**Escalation triggers.** Emit blocked.\n")
    (feature / "WU-01-impl.md").write_text(
        "---\nid: FEAT-2026-9996/T01\ntype: implementation\nstatus: done\nattempts: 1\n"
        f"produces: [docs/x.md]\n{field if on == 'implementation' else ''}---\n{body}")
    (feature / "WU-90-close.md").write_text(
        "---\nid: FEAT-2026-9996/G1-CLOSE\ntype: close\nstatus: pending\nattempts: 0\n"
        f"{field if on == 'close' else ''}---\n\n# Close\n")
    (feature / "GATE-01.md").write_text(
        '---\nstatus: open\nfeature_oracle: "python3 -m unittest -q"\n---\n\n# Gate 1\n')
    return feature


def _ack_errors(ack: str, *, on: str = "close") -> list[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        feature = _feature(tmpdir, ack, on=on)
        with redirect_stdout(io.StringIO()):
            errs = lint_plan.lint(feature)
    return [e for e in errs if "judge_edit_acknowledged" in e]


class JudgeEditAcknowledgedLint(unittest.TestCase):
    def test_valid_passes(self):
        self.assertEqual(_ack_errors(VALID), [])

    def test_missing_reason_errors(self):
        self.assertEqual(_ack_errors(VALID), [])
        self.assertTrue(_ack_errors("  paths: [specfuse/loop/arm_eval.py]\n"))

    def test_empty_reason_errors(self):
        self.assertEqual(_ack_errors(VALID), [])
        self.assertTrue(_ack_errors('  paths: [specfuse/loop/arm_eval.py]\n  reason: ""\n'))

    def test_empty_paths_errors(self):
        self.assertEqual(_ack_errors(VALID), [])
        self.assertTrue(_ack_errors('  paths: []\n  reason: "reviewed"\n'))

    def test_non_list_paths_errors(self):
        self.assertEqual(_ack_errors(VALID), [])
        self.assertTrue(_ack_errors(
            '  paths: specfuse/loop/arm_eval.py\n  reason: "reviewed"\n'))

    def test_on_implementation_unit_errors(self):
        self.assertEqual(_ack_errors(VALID), [])
        self.assertTrue(_ack_errors(VALID, on="implementation"))


if __name__ == "__main__":
    unittest.main()
