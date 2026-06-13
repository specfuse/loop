#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the `close` WU type in lint_plan.py.

Three assertions:
  (a) lint accepts a single-gate feature whose gate closes with one `close` WU
  (b) lint rejects a `close` WU on a non-terminal gate (terminal gate with
      `close` is now valid for any feature size — single- or multi-gate)
  (c) lint still accepts the four-WU [retrospective, lessons, docs, plan-next]
      closing sequence — regression guard (emits WARN, exits zero)
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FEATURE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"


def _write_plan(feature_dir: Path, gates_yaml: str) -> None:
    (feature_dir / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9001\n"
        "title: Test close WU\n"
        "slug: test-close\n"
        "branch: feat/test-close\n"
        "roadmap_goal: Verify the close WU type in the linter.\n"
        "status: active\n"
        "---\n"
        "\n"
        "# Plan\n"
        "\n"
        "```yaml\n"
        f"{gates_yaml}\n"
        "```\n"
    )


def _write_wu(feature_dir: Path, filename: str, wu_id: str, wu_type: str) -> None:
    """Write a minimal WU file. status: done avoids the mandatory-section check."""
    (feature_dir / filename).write_text(
        "---\n"
        f"id: {wu_id}\n"
        f"type: {wu_type}\n"
        "model: claude-sonnet-4-6\n"
        "status: done\n"
        "attempts: 1\n"
        "---\n"
        "\n"
        f"# {filename}\n"
    )


class TestCloseWuLint(unittest.TestCase):
    """lint_plan.lint() correctly handles the `close` WU type."""

    def test_single_gate_close_passes(self):
        """(a) Single-gate feature with a `close` WU must pass lint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9001/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9001/G1-CLOSE\n"
                "        file: WU-90-close.md\n"
                "        depends_on: [FEAT-2026-9001/T01]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9001/T01", "implementation")
            _write_wu(feature, "WU-90-close.md", "FEAT-2026-9001/G1-CLOSE", "close")
            errs = lint_plan.lint(feature)
            self.assertEqual(errs, [],
                             f"single-gate close WU must pass lint; errs={errs}")

    def test_non_terminal_gate_close_rejected(self):
        """(b) `close` WU on a non-terminal gate must produce a lint error naming
        the terminal-gate constraint.  The terminal gate's `close` is now valid
        for any feature size (FEAT-2026-0015)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9001/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9001/G1-CLOSE\n"
                "        file: WU-90-close.md\n"
                "        depends_on: [FEAT-2026-9001/T01]\n"
                "  - gate: 2\n"
                "    file: GATE-02.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9001/T02\n"
                "        file: WU-02-impl.md\n"
                "        depends_on: [FEAT-2026-9001/T01]\n"
                "      - id: FEAT-2026-9001/G2-CLOSE\n"
                "        file: WU-91-close.md\n"
                "        depends_on: [FEAT-2026-9001/T02]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9001/T01", "implementation")
            _write_wu(feature, "WU-90-close.md", "FEAT-2026-9001/G1-CLOSE", "close")
            _write_wu(feature, "WU-02-impl.md", "FEAT-2026-9001/T02", "implementation")
            _write_wu(feature, "WU-91-close.md", "FEAT-2026-9001/G2-CLOSE", "close")
            errs = lint_plan.lint(feature)
            self.assertTrue(errs, "close WU on non-terminal gate must produce lint errors")
            close_errs = [e for e in errs if "`close`" in e or "terminal" in e]
            self.assertTrue(
                close_errs,
                f"errors must name the terminal-gate constraint; errs={errs}",
            )

    def test_four_wu_closing_sequence_still_passes(self):
        """(c) Regression: four-WU [retrospective, lessons, docs, plan-next] closing
        sequence must still pass lint after the `close` type was introduced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            shutil.copytree(EXAMPLE_FEATURE, feature)
            errs = lint_plan.lint(feature)
            self.assertEqual(errs, [],
                             f"four-WU closing sequence must still pass lint; errs={errs}")


if __name__ == "__main__":
    unittest.main()
