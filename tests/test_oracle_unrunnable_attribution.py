#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""An oracle the shell cannot run is a configuration problem, not the unit's
fault — FEAT-2026-0101/T05.

`verify()` classifies a failing `feature_oracle` gate by exit status: 127
("command not found") is re-reported as a configuration problem naming the
gate file, everything else stays an ordinary gate failure.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_CODE_CFG = {"code": [{"name": "noop", "command": "true"}]}


def _make_wu() -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id="FEAT-9999/T01",
        file=Path("FAKE-WU.md"),
        depends_on=[],
        type="code",
        model="opus",
        status="pending",
        attempts=0,
        title="test WU",
        body="test",
    )


def _write_gate(fd: Path, extra_frontmatter: str = "") -> Path:
    gate_file = fd / "GATE-01.md"
    gate_file.write_text(
        f"---\ngate: 1\nstatus: open\n{extra_frontmatter}---\n\n# Gate 1\n"
    )
    return gate_file


class TestUnrunnableOracleReportsConfigurationProblem(unittest.TestCase):
    def test_unrunnable_oracle_reports_configuration_problem(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            gate_file = _write_gate(
                fd, 'feature_oracle: "totally-nonexistent-command-zzz"\n',
            )
            wu = _make_wu()
            passed, report = loop.verify(
                wu, fd, cfg=_CODE_CFG, gate_file=gate_file,
            )
            self.assertFalse(passed)
            self.assertNotIn("### feature_oracle: FAIL", report)
            self.assertIn("CONFIGURATION ERROR", report)
            self.assertIn(str(gate_file), report)


class TestOracleThatRunsAndFailsIsStillAnOrdinaryFailure(unittest.TestCase):
    def test_oracle_that_runs_and_fails_is_still_an_ordinary_failure(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            gate_file = _write_gate(
                fd,
                'feature_oracle: "python3 -c \\"import sys; sys.exit(1)\\""\n',
            )
            wu = _make_wu()
            passed, report = loop.verify(
                wu, fd, cfg=_CODE_CFG, gate_file=gate_file,
            )
            self.assertFalse(passed)
            self.assertIn("### feature_oracle: FAIL", report)
            self.assertNotIn("CONFIGURATION ERROR", report)


class TestPrintingCommandNotFoundIsNotMisclassified(unittest.TestCase):
    def test_test_printing_command_not_found_is_not_misclassified(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            gate_file = _write_gate(
                fd,
                'feature_oracle: "python3 -c \\"'
                'print(\'command not found\'); import sys; sys.exit(1)\\""\n',
            )
            wu = _make_wu()
            passed, report = loop.verify(
                wu, fd, cfg=_CODE_CFG, gate_file=gate_file,
            )
            self.assertFalse(passed)
            self.assertIn("### feature_oracle: FAIL", report)
            self.assertNotIn("CONFIGURATION ERROR", report)


class TestEmptyDeclarationPathUnchanged(unittest.TestCase):
    def test_empty_declaration_path_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            gate_file = _write_gate(fd, 'feature_oracle: ""\n')
            wu = _make_wu()
            passed, report = loop.verify(
                wu, fd, cfg=_CODE_CFG, gate_file=gate_file,
            )
            self.assertFalse(passed)
            self.assertIn("CONFIGURATION ERROR", report)
            self.assertIn(str(gate_file), report)
            self.assertIn("empty", report)


if __name__ == "__main__":
    unittest.main()
