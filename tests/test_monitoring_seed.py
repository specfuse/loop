# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0039/T03 — monitoring.yml.example is seeded, opt-in (no rename),
and its validator shim resolves from source without a pip install.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.scaffold import init_specfuse

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIM = REPO_ROOT / ".specfuse" / "scripts" / "lint_monitoring.py"
EXAMPLE = REPO_ROOT / ".specfuse" / "monitoring.yml.example"


class TestMonitoringSeed(unittest.TestCase):
    def test_example_is_seeded_by_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = init_specfuse(tmp)
        self.assertIn("monitoring.yml.example", written)

    def test_example_is_not_renamed_on_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = init_specfuse(tmp)
        self.assertIn("monitoring.yml.example", written)
        self.assertNotIn("monitoring.yml", written)


class TestVerificationExampleGateCommented(unittest.TestCase):
    def test_monitoring_gate_present_and_commented_in_example(self):
        text = (REPO_ROOT / ".specfuse" / "verification.yml.example").read_text(
            encoding="utf-8"
        )
        lines = [
            line for line in text.splitlines()
            if "monitoring-example-lint" in line or "lint_monitoring.py" in line
        ]
        self.assertTrue(lines, "expected a monitoring-example-lint gate reference")
        for line in lines:
            self.assertTrue(
                line.lstrip().startswith("#"),
                f"gate line must be commented out: {line!r}",
            )


class TestLintMonitoringShim(unittest.TestCase):
    def test_shim_resolves_package_from_source_outside_repo(self):
        """Same property lint_plan.py's shim has: no pip install required."""
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SHIM), str(EXAMPLE)],
                capture_output=True, text=True, cwd=tmp, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
