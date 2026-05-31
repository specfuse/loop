#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Fix 3 — lint_plan.py must reject malformed correlation IDs.

The published pattern (`.specfuse/rules/correlation-ids.md`) admits
FEAT-YYYY-NNNN, FEAT-YYYY-NNNN/TNN (two-digit), and
FEAT-YYYY-NNNN/G<n>-(RETRO|LESSONS|DOCS|PLAN). Anything else — single-digit
ordinals like /T1, lowercase tokens, missing year — must fail lint.

Tests call lint_plan.lint() directly so coverage instrumentation sees the
function bodies; a single CLI-exit-code test at the end preserves the
contract that lint_plan.py is invokable as a script with exit 0/1.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT = REPO_ROOT / ".specfuse/scripts/lint_plan.py"
EXAMPLE_FEATURE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"


def copy_example_to(tmp: Path) -> Path:
    dest = tmp / "feature"
    shutil.copytree(EXAMPLE_FEATURE, dest)
    return dest


def mutate(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, f"sentinel {old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1))


class TestLintCorrelationId(unittest.TestCase):
    """In-process tests against lint_plan.lint() — coverage-visible."""

    def test_well_formed_example_still_passes(self):
        errs = lint_plan.lint(EXAMPLE_FEATURE)
        self.assertEqual(errs, [], f"worked example must lint clean. errs={errs}")

    def test_single_digit_task_id_in_graph_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            # Break the graph: /T01 -> /T1 (single-digit, malformed).
            mutate(feature / "PLAN.md",
                   "id: FEAT-2026-0001/T01",
                   "id: FEAT-2026-0001/T1")
            errs = lint_plan.lint(feature)
            self.assertTrue(errs, "malformed graph id must produce errors")
            joined = "\n".join(errs)
            self.assertIn("malformed correlation id", joined)
            self.assertIn("FEAT-2026-0001/T1", joined)

    def test_malformed_frontmatter_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            # Break the frontmatter: id field, not the graph.
            mutate(feature / "WU-01-health-endpoint.md",
                   "id: FEAT-2026-0001/T01",
                   "id: FEAT-2026-0001/T1")
            errs = lint_plan.lint(feature)
            self.assertTrue(errs)
            joined = "\n".join(errs)
            # The graph still says T01; frontmatter says T1. Expect both an
            # equality-mismatch error AND a malformed-frontmatter-id error.
            self.assertIn("frontmatter id", joined)
            self.assertIn("malformed frontmatter id 'FEAT-2026-0001/T1'", joined)

    def test_lowercase_closing_token_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            mutate(feature / "PLAN.md",
                   "id: FEAT-2026-0001/G1-RETRO",
                   "id: FEAT-2026-0001/G1-retro")
            errs = lint_plan.lint(feature)
            self.assertTrue(errs)
            joined = "\n".join(errs)
            self.assertIn("malformed correlation id", joined)
            self.assertIn("G1-retro", joined)


class TestLintCliContract(unittest.TestCase):
    """One subprocess test preserving the CLI exit-code contract.

    lint_plan.py is consumed by the loop driver as a CLI gate command
    (plannext set runs `python lint_plan.py {feature_dir}`); exit 0 on
    clean / exit 1 on failure is part of that contract. The in-process
    tests above don't exercise the script's main() / argv handling, so
    we keep one end-to-end CLI invocation here.
    """

    def test_cli_exits_zero_on_clean_example(self):
        proc = subprocess.run(
            [sys.executable, str(LINT), str(EXAMPLE_FEATURE)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0,
                         f"CLI must exit 0 on clean example; stderr={proc.stderr}")
        self.assertIn("OK", proc.stdout)

    def test_cli_exits_nonzero_on_malformed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            mutate(feature / "PLAN.md",
                   "id: FEAT-2026-0001/T01",
                   "id: FEAT-2026-0001/T1")
            proc = subprocess.run(
                [sys.executable, str(LINT), str(feature)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("FAIL", proc.stdout)


if __name__ == "__main__":
    unittest.main()
