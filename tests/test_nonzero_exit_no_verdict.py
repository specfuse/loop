# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Issue #3603 — a gate that exits non-zero without a recognised summary.

A `feature_oracle` script printed `RED: <file> lacks: <text>` lines and exited
1. Its report ended in the NO VERDICT note ("may be unrelated to the failure.
Run the command directly."), and `failure_excerpt` carried that note and the
`### feature_oracle: FAIL` header but none of the oracle's own lines: the
excerpt keeps keyword lines only, `RED:` matches none of the keywords, and the
note does ("pass/fail"). The signature, meanwhile, was the first `RED:` line.

A non-zero exit IS the verdict. The report must say so with the exit code, the
excerpt must carry the command's own last lines, and the no-verdict wording is
kept for a command that exited zero with nothing recognisable. Pass/fail,
failure_class and failure_signature are unchanged.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_RED_ORACLE = (
    "echo 'checking 3 files'; "
    "echo 'RED: docs/guide.md lacks: the new flag'; "
    "echo 'RED: README.md lacks: the install line'; "
    "exit 1"
)


class _InTempDir(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        self.feature_dir = Path("feat")
        self.feature_dir.mkdir()

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _payload(self, command: str, name: str = "feature_oracle") -> tuple[bool, str]:
        results = loop._run_gate_set([{"name": name, "command": command}], self.feature_dir)
        return results[0]["ok"], "\n\n".join(r["report"] for r in results)


class TestNonZeroExitWithoutSummary(_InTempDir):
    def test_report_names_the_exit_code_not_no_verdict(self):
        ok, payload = self._payload(_RED_ORACLE)
        self.assertFalse(ok)
        self.assertNotIn("NO VERDICT FOUND", payload)
        self.assertNotIn("may be unrelated to the failure", payload)
        self.assertIn("exit code 1", payload)

    def test_excerpt_carries_the_commands_own_last_lines(self):
        _, payload = self._payload(_RED_ORACLE)
        excerpt = loop.extract_failure_excerpt(payload)
        self.assertIn("RED: docs/guide.md lacks: the new flag", excerpt)
        self.assertIn("RED: README.md lacks: the install line", excerpt)
        self.assertIn("exit code 1", excerpt)
        self.assertNotIn("NO VERDICT FOUND", excerpt)
        self.assertNotIn("$ echo", excerpt, "the command echo is not the command's output")

    def test_class_and_signature_are_unchanged(self):
        _, payload = self._payload(_RED_ORACLE)
        self.assertEqual(
            loop.parse_gate_failure_signature(payload),
            ("other", "checking 3 files"),
        )

    def test_other_exit_codes_are_named(self):
        _, payload = self._payload("echo 'RED: x'; exit 3")
        self.assertIn("exit code 3", payload)
        self.assertIn("exit code 3", loop.extract_failure_excerpt(payload))


class TestZeroExitWithoutSummaryKeepsTheNote(_InTempDir):
    def test_a_passing_command_with_nothing_recognisable_still_reads_no_verdict(self):
        ok, payload = self._payload("echo 'abc0001 subject'; exit 0", name="recent-commits")
        self.assertTrue(ok)
        self.assertIn(loop._NO_VERDICT_NOTE, payload)

    def test_selector_without_a_return_code_is_unchanged(self):
        # prerun_capture and older callers pass no return code.
        lines = loop.select_gate_report_lines("plain line\n", window=15)
        self.assertEqual(lines, ["plain line", loop._NO_VERDICT_NOTE])


class TestRecognisedSummaryIsUnaffected(_InTempDir):
    def test_a_nonzero_exit_with_a_verdict_line_gets_no_exit_note(self):
        _, payload = self._payload("echo 'FAILED (failures=1)'; exit 1", name="tests")
        self.assertNotIn("exit code 1", payload)
        self.assertNotIn("NO VERDICT FOUND", payload)


if __name__ == "__main__":
    unittest.main()
