#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature oracle walking skeleton — FEAT-2026-0101/T01.

A gate declares one `feature_oracle` command in its `GATE-NN.md` frontmatter.
`verify()` reads it (via `read_gate_feature_oracle`), synthesizes a
one-element gate list, and hands it to the existing `_run_gate_set` — no
second execution path. These tests drive real units through `verify()` and
prove the oracle actually ran via a side effect it writes to disk, never by
asserting on a mock.
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


class TestDeclaredOracleRuns(unittest.TestCase):
    def test_declared_oracle_runs_during_unit_verification(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            marker = fd / "oracle-ran.marker"
            gate_file = _write_gate(
                fd,
                f'feature_oracle: "python3 -c \\"open(\'{marker}\', \'w\').write(\'ran\')\\""\n',
            )
            wu = _make_wu()
            passed, report = loop.verify(
                wu, fd, cfg=_CODE_CFG, gate_file=gate_file,
            )
            self.assertTrue(passed, report)
            self.assertTrue(
                marker.is_file(),
                "oracle command did not run — no side-effect file written",
            )
            self.assertEqual(marker.read_text(), "ran")


class TestFailingOracleFailsUnit(unittest.TestCase):
    def test_failing_oracle_fails_the_unit(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            gate_file = _write_gate(fd, 'feature_oracle: "exit 1"\n')
            wu = _make_wu()
            passed, report = loop.verify(
                wu, fd, cfg=_CODE_CFG, gate_file=gate_file,
            )
            self.assertFalse(passed)
            self.assertIn("feature_oracle", report)


class TestGateWithoutOracleUnchanged(unittest.TestCase):
    def test_gate_without_oracle_is_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            fd = Path(td)
            gate_file = _write_gate(fd)
            wu = _make_wu()
            with_gate_file = loop.verify(wu, fd, cfg=_CODE_CFG, gate_file=gate_file)
            without_gate_file = loop.verify(wu, fd, cfg=_CODE_CFG, gate_file=None)
            self.assertEqual(with_gate_file, without_gate_file)


class TestEmptyOracleIsConfigurationError(unittest.TestCase):
    def test_empty_oracle_is_configuration_error(self):
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


if __name__ == "__main__":
    unittest.main()
