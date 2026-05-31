#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Fix 3 — lint_plan.py must reject malformed correlation IDs.

The published pattern (`.specfuse/rules/correlation-ids.md`) admits
FEAT-YYYY-NNNN, FEAT-YYYY-NNNN/TNN (two-digit), and
FEAT-YYYY-NNNN/G<n>-(RETRO|LESSONS|DOCS|PLAN). Anything else — single-digit
ordinals like /T1, lowercase tokens, missing year — must fail lint.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT = REPO_ROOT / ".specfuse/scripts/lint_plan.py"
EXAMPLE_FEATURE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"


def run_lint(feature_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), str(feature_dir)],
        capture_output=True, text=True,
    )


def copy_example_to(tmp: Path) -> Path:
    dest = tmp / "feature"
    shutil.copytree(EXAMPLE_FEATURE, dest)
    return dest


def mutate(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, f"sentinel {old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1))


class TestLintCorrelationId(unittest.TestCase):

    def test_well_formed_example_still_passes(self):
        proc = run_lint(EXAMPLE_FEATURE)
        self.assertEqual(proc.returncode, 0,
                         f"worked example must lint clean. stderr={proc.stderr}")
        self.assertIn("OK", proc.stdout)

    def test_single_digit_task_id_in_graph_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            # Break the graph: /T01 -> /T1 (single-digit, malformed).
            mutate(feature / "PLAN.md",
                   "id: FEAT-2026-0001/T01",
                   "id: FEAT-2026-0001/T1")
            proc = run_lint(feature)
            self.assertNotEqual(proc.returncode, 0,
                                "malformed graph id must fail lint")
            self.assertIn("malformed correlation id", proc.stdout)
            self.assertIn("FEAT-2026-0001/T1", proc.stdout)

    def test_malformed_frontmatter_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            # Break the frontmatter: id field, not the graph.
            mutate(feature / "WU-01-health-endpoint.md",
                   "id: FEAT-2026-0001/T01",
                   "id: FEAT-2026-0001/T1")
            proc = run_lint(feature)
            self.assertNotEqual(proc.returncode, 0)
            # The graph still says T01; frontmatter says T1. Expect both an
            # equality-mismatch error AND a malformed-frontmatter-id error.
            self.assertIn("frontmatter id", proc.stdout)
            self.assertIn("malformed frontmatter id 'FEAT-2026-0001/T1'", proc.stdout)

    def test_lowercase_closing_token_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            mutate(feature / "PLAN.md",
                   "id: FEAT-2026-0001/G1-RETRO",
                   "id: FEAT-2026-0001/G1-retro")
            proc = run_lint(feature)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("malformed correlation id", proc.stdout)
            self.assertIn("G1-retro", proc.stdout)


if __name__ == "__main__":
    unittest.main()
