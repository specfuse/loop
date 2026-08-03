# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0041/T03: the headless diagnosis entry point.

`test_both_entry_points_render_identical_body` is the load-bearing test —
byte-identical string comparison, not "both parse to equal fields" — since a
whitespace or ordering drift between the interactive and headless paths is
exactly the failure this work unit exists to prevent.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from specfuse.monitor.diagnosis import Diagnosis, render
from specfuse.monitor.diagnose_cli import (
    AnalysisParseError,
    main,
    parse_analysis,
    render_headless,
)

_MODULE_PATH = Path(__file__).resolve().parent.parent / "specfuse" / "monitor" / "diagnose_cli.py"

_ANALYSIS = {
    "root_cause": "the worker retried a poisoned message without a backoff",
    "evidence": "dlq depth climbed from 0 to 40 over five minutes",
    "candidate_fix": "add exponential backoff to the retry loop",
    "confidence": 0.75,
    "fix_scope": "small",
}


class TestDiagnoseHeadless(unittest.TestCase):
    def test_both_entry_points_render_identical_body(self):
        diagnosis = Diagnosis(
            root_cause=_ANALYSIS["root_cause"],
            evidence=_ANALYSIS["evidence"],
            candidate_fix=_ANALYSIS["candidate_fix"],
            confidence=_ANALYSIS["confidence"],
            fix_scope=_ANALYSIS["fix_scope"],
        )

        interactive_body = render(diagnosis)
        headless_body = render_headless(json.dumps(_ANALYSIS))

        self.assertEqual(headless_body, interactive_body)

    def test_headless_module_has_no_literal_marker_or_heading_template(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("specfuse:diagnosis", source)
        self.assertNotIn("**Root cause:**", source)
        self.assertNotIn("**Evidence:**", source)
        self.assertNotIn("**Candidate fix:**", source)
        self.assertNotIn("**Confidence:**", source)
        self.assertNotIn("**Fix scope:**", source)

    def test_unparseable_finding_fails_loudly(self):
        with self.assertRaises(AnalysisParseError):
            parse_analysis("not json at all {{{")

    def test_missing_fix_scope_is_rejected_not_defaulted(self):
        analysis = {k: v for k, v in _ANALYSIS.items() if k != "fix_scope"}
        with self.assertRaises(AnalysisParseError):
            parse_analysis(json.dumps(analysis))

    def test_unparseable_fix_scope_is_rejected_not_defaulted(self):
        analysis = dict(_ANALYSIS, fix_scope="gigantic")
        with self.assertRaises(AnalysisParseError):
            parse_analysis(json.dumps(analysis))

    def test_no_gh_subprocess_or_network_call_in_headless_module(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        matches = re.findall(r"subprocess|gh |requests|urllib", source)
        self.assertEqual(matches, [], f"forbidden token found in diagnose_cli.py: {matches!r}")

    def test_main_reads_file_argument_and_prints_body(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(_ANALYSIS, handle)
            path = handle.name

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main([path])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().rstrip("\n"), render_headless(json.dumps(_ANALYSIS)))

    def test_main_exits_nonzero_and_prints_named_error_on_bad_input(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write("not json")
            path = handle.name

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main([path])

        self.assertEqual(exit_code, 1)
        self.assertIn("diagnose_cli:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
