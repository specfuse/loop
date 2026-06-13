#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the new closing-WU shapes introduced in FEAT-2026-0015.

Shapes under test:
  - Non-terminal gate: close-intermediate → plan-next  (NEW, silent)
  - Terminal gate:     close              (NEW, any feature size, silent)
  - Any gate:          legacy 4-WU sequence             (LEGACY, WARN but exit 0)
  - Mixed shapes across gates within one feature         (hard ERROR, exit nonzero)
  - close-intermediate not followed by plan-next         (hard ERROR)
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _write_plan(feature_dir: Path, gates_yaml: str) -> None:
    (feature_dir / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9002\n"
        "title: Test close-intermediate shapes\n"
        "slug: test-close-intermediate\n"
        "branch: feat/test-close-intermediate\n"
        "roadmap_goal: Verify new closing shapes in the linter.\n"
        "status: active\n"
        "planned_cost_usd: 0.00\n"
        "---\n"
        "\n"
        "# Plan\n"
        "\n"
        "```yaml\n"
        f"{gates_yaml}\n"
        "```\n"
    )


def _write_wu(feature_dir: Path, filename: str, wu_id: str, wu_type: str) -> None:
    """Minimal WU file; status: done bypasses mandatory-section check."""
    (feature_dir / filename).write_text(
        "---\n"
        f"id: {wu_id}\n"
        f"type: {wu_type}\n"
        "model: claude-sonnet-4-6\n"
        "status: done\n"
        "attempts: 1\n"
        "planned_cost_usd: 0.00\n"
        "---\n"
        "\n"
        f"# {filename}\n"
    )


class TestCloseIntermediateShapes(unittest.TestCase):
    """lint_plan.lint() correctly handles new closing-WU shapes."""

    def test_new_2wu_intermediate_passes_silently(self):
        """Non-terminal gate with close-intermediate → plan-next must pass with no errors
        and no WARN output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9002/T02\n"
                "        file: WU-02-close-int.md\n"
                "        depends_on: [FEAT-2026-9002/T01]\n"
                "      - id: FEAT-2026-9002/T03\n"
                "        file: WU-03-plan-next.md\n"
                "        depends_on: [FEAT-2026-9002/T02]\n"
                "  - gate: 2\n"
                "    file: GATE-02.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T04\n"
                "        file: WU-04-impl.md\n"
                "        depends_on: [FEAT-2026-9002/T03]\n"
                "      - id: FEAT-2026-9002/G2-CLOSE\n"
                "        file: WU-90-close.md\n"
                "        depends_on: [FEAT-2026-9002/T04]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9002/T01", "implementation")
            _write_wu(feature, "WU-02-close-int.md", "FEAT-2026-9002/T02", "close-intermediate")
            _write_wu(feature, "WU-03-plan-next.md", "FEAT-2026-9002/T03", "plan-next")
            _write_wu(feature, "WU-04-impl.md", "FEAT-2026-9002/T04", "implementation")
            _write_wu(feature, "WU-90-close.md", "FEAT-2026-9002/G2-CLOSE", "close")

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                errs = lint_plan.lint(feature)
            finally:
                sys.stdout = old_stdout

            self.assertEqual(errs, [],
                             f"2-WU intermediate close must pass lint; errs={errs}")
            self.assertNotIn("WARN", captured.getvalue(),
                             "new 2-WU shape must not emit WARN")

    def test_new_1wu_terminal_passes_for_multigate_feature(self):
        """`close` on a terminal gate must pass for a multi-gate (3-gate) feature,
        removing the old single-gate restriction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9002/T02\n"
                "        file: WU-02-close-int.md\n"
                "        depends_on: [FEAT-2026-9002/T01]\n"
                "      - id: FEAT-2026-9002/T03\n"
                "        file: WU-03-plan-next.md\n"
                "        depends_on: [FEAT-2026-9002/T02]\n"
                "  - gate: 2\n"
                "    file: GATE-02.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T04\n"
                "        file: WU-04-impl.md\n"
                "        depends_on: [FEAT-2026-9002/T03]\n"
                "      - id: FEAT-2026-9002/T05\n"
                "        file: WU-05-close-int.md\n"
                "        depends_on: [FEAT-2026-9002/T04]\n"
                "      - id: FEAT-2026-9002/T06\n"
                "        file: WU-06-plan-next.md\n"
                "        depends_on: [FEAT-2026-9002/T05]\n"
                "  - gate: 3\n"
                "    file: GATE-03.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T07\n"
                "        file: WU-07-impl.md\n"
                "        depends_on: [FEAT-2026-9002/T06]\n"
                "      - id: FEAT-2026-9002/G3-CLOSE\n"
                "        file: WU-90-close.md\n"
                "        depends_on: [FEAT-2026-9002/T07]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9002/T01", "implementation")
            _write_wu(feature, "WU-02-close-int.md", "FEAT-2026-9002/T02", "close-intermediate")
            _write_wu(feature, "WU-03-plan-next.md", "FEAT-2026-9002/T03", "plan-next")
            _write_wu(feature, "WU-04-impl.md", "FEAT-2026-9002/T04", "implementation")
            _write_wu(feature, "WU-05-close-int.md", "FEAT-2026-9002/T05", "close-intermediate")
            _write_wu(feature, "WU-06-plan-next.md", "FEAT-2026-9002/T06", "plan-next")
            _write_wu(feature, "WU-07-impl.md", "FEAT-2026-9002/T07", "implementation")
            _write_wu(feature, "WU-90-close.md", "FEAT-2026-9002/G3-CLOSE", "close")

            errs = lint_plan.lint(feature)
            self.assertEqual(errs, [],
                             f"`close` on terminal gate of 3-gate feature must pass; errs={errs}")

    def test_legacy_4wu_sequence_emits_warn_but_exits_zero(self):
        """Legacy 4-WU closing sequence must pass lint (errs empty) but emit a WARN
        on stdout referencing FEAT-2026-0015."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9002/G1-RETRO\n"
                "        file: WU-80-retro.md\n"
                "        depends_on: [FEAT-2026-9002/T01]\n"
                "      - id: FEAT-2026-9002/G1-LESSONS\n"
                "        file: WU-81-lessons.md\n"
                "        depends_on: [FEAT-2026-9002/G1-RETRO]\n"
                "      - id: FEAT-2026-9002/G1-DOCS\n"
                "        file: WU-82-docs.md\n"
                "        depends_on: [FEAT-2026-9002/G1-LESSONS]\n"
                "      - id: FEAT-2026-9002/G1-PLAN\n"
                "        file: WU-83-plan.md\n"
                "        depends_on: [FEAT-2026-9002/G1-DOCS]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9002/T01", "implementation")
            _write_wu(feature, "WU-80-retro.md", "FEAT-2026-9002/G1-RETRO", "retrospective")
            _write_wu(feature, "WU-81-lessons.md", "FEAT-2026-9002/G1-LESSONS", "lessons")
            _write_wu(feature, "WU-82-docs.md", "FEAT-2026-9002/G1-DOCS", "docs")
            _write_wu(feature, "WU-83-plan.md", "FEAT-2026-9002/G1-PLAN", "plan-next")

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                errs = lint_plan.lint(feature)
            finally:
                sys.stdout = old_stdout

            self.assertEqual(errs, [],
                             f"legacy 4-WU sequence must exit zero (errs empty); errs={errs}")
            output = captured.getvalue()
            self.assertIn("WARN", output, "legacy sequence must emit WARN on stdout")
            self.assertIn("FEAT-2026-0015", output,
                          "WARN must reference FEAT-2026-0015")

    def test_mixed_shapes_emit_error_and_exits_nonzero(self):
        """A feature where gate 1 uses the new 2-WU shape and gate 2 uses the legacy
        4-WU shape must produce a hard ERROR and errs must be non-empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9002/T02\n"
                "        file: WU-02-close-int.md\n"
                "        depends_on: [FEAT-2026-9002/T01]\n"
                "      - id: FEAT-2026-9002/T03\n"
                "        file: WU-03-plan-next.md\n"
                "        depends_on: [FEAT-2026-9002/T02]\n"
                "  - gate: 2\n"
                "    file: GATE-02.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T04\n"
                "        file: WU-04-impl.md\n"
                "        depends_on: [FEAT-2026-9002/T03]\n"
                "      - id: FEAT-2026-9002/G2-RETRO\n"
                "        file: WU-80-retro.md\n"
                "        depends_on: [FEAT-2026-9002/T04]\n"
                "      - id: FEAT-2026-9002/G2-LESSONS\n"
                "        file: WU-81-lessons.md\n"
                "        depends_on: [FEAT-2026-9002/G2-RETRO]\n"
                "      - id: FEAT-2026-9002/G2-DOCS\n"
                "        file: WU-82-docs.md\n"
                "        depends_on: [FEAT-2026-9002/G2-LESSONS]\n"
                "      - id: FEAT-2026-9002/G2-PLAN\n"
                "        file: WU-83-plan.md\n"
                "        depends_on: [FEAT-2026-9002/G2-DOCS]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9002/T01", "implementation")
            _write_wu(feature, "WU-02-close-int.md", "FEAT-2026-9002/T02", "close-intermediate")
            _write_wu(feature, "WU-03-plan-next.md", "FEAT-2026-9002/T03", "plan-next")
            _write_wu(feature, "WU-04-impl.md", "FEAT-2026-9002/T04", "implementation")
            _write_wu(feature, "WU-80-retro.md", "FEAT-2026-9002/G2-RETRO", "retrospective")
            _write_wu(feature, "WU-81-lessons.md", "FEAT-2026-9002/G2-LESSONS", "lessons")
            _write_wu(feature, "WU-82-docs.md", "FEAT-2026-9002/G2-DOCS", "docs")
            _write_wu(feature, "WU-83-plan.md", "FEAT-2026-9002/G2-PLAN", "plan-next")

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                errs = lint_plan.lint(feature)
            finally:
                sys.stdout = old_stdout

            self.assertTrue(errs, "mixed shapes must produce lint errors (non-zero exit)")
            mixed_errs = [e for e in errs if "mixed" in e.lower() or "contract" in e.lower()]
            self.assertTrue(mixed_errs,
                            f"errors must name the mixed-contract problem; errs={errs}")

    def test_forward_mixed_shapes_warn_no_error(self):
        """Forward-migration mix (legacy on earlier gates + NEW on terminal gate)
        is the documented dogfood pattern FEAT-2026-0015 uses on itself. Must
        emit a WARN (stdout) but NOT block via errs list — lint exits 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            # Gate 1 = LEGACY 4-WU, Gate 2 (terminal) = NEW single `close`.
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9003/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9003/G1-RETRO\n"
                "        file: WU-90-retro.md\n"
                "        depends_on: [FEAT-2026-9003/T01]\n"
                "      - id: FEAT-2026-9003/G1-LESSONS\n"
                "        file: WU-91-lessons.md\n"
                "        depends_on: [FEAT-2026-9003/G1-RETRO]\n"
                "      - id: FEAT-2026-9003/G1-DOCS\n"
                "        file: WU-92-docs.md\n"
                "        depends_on: [FEAT-2026-9003/G1-LESSONS]\n"
                "      - id: FEAT-2026-9003/G1-PLAN\n"
                "        file: WU-93-plan.md\n"
                "        depends_on: [FEAT-2026-9003/G1-DOCS]\n"
                "  - gate: 2\n"
                "    file: GATE-02.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9003/T02\n"
                "        file: WU-02-impl.md\n"
                "        depends_on: [FEAT-2026-9003/G1-PLAN]\n"
                "      - id: FEAT-2026-9003/G2-CLOSE\n"
                "        file: WU-94-close.md\n"
                "        depends_on: [FEAT-2026-9003/T02]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9003/T01", "implementation")
            _write_wu(feature, "WU-90-retro.md", "FEAT-2026-9003/G1-RETRO", "retrospective")
            _write_wu(feature, "WU-91-lessons.md", "FEAT-2026-9003/G1-LESSONS", "lessons")
            _write_wu(feature, "WU-92-docs.md", "FEAT-2026-9003/G1-DOCS", "docs")
            _write_wu(feature, "WU-93-plan.md", "FEAT-2026-9003/G1-PLAN", "plan-next")
            _write_wu(feature, "WU-02-impl.md", "FEAT-2026-9003/T02", "implementation")
            _write_wu(feature, "WU-94-close.md", "FEAT-2026-9003/G2-CLOSE", "close")

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                errs = lint_plan.lint(feature)
            finally:
                sys.stdout = old_stdout

            # No errors — forward-mixed is allowed
            mixed_errs = [e for e in errs if "mixed" in e.lower()]
            self.assertFalse(
                mixed_errs,
                f"forward-mixed (legacy earlier + NEW terminal) must NOT produce "
                f"mixed-contract errors; got: {mixed_errs}",
            )
            # WARN is on stdout
            out = captured.getvalue()
            self.assertIn("WARN", out, f"expected WARN on stdout; got: {out!r}")
            self.assertIn("forward-mixed", out)

    def test_close_intermediate_followed_by_non_plan_next_emits_error(self):
        """close-intermediate that is NOT followed by plan-next must produce a lint
        error — the two WUs must appear as an adjacent pair."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = Path(tmpdir) / "feature"
            feature.mkdir()
            # Gate 1: close-intermediate alone (no plan-next) on a non-terminal gate.
            _write_plan(feature, (
                "gates:\n"
                "  - gate: 1\n"
                "    file: GATE-01.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T01\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                "      - id: FEAT-2026-9002/T02\n"
                "        file: WU-02-close-int.md\n"
                "        depends_on: [FEAT-2026-9002/T01]\n"
                "  - gate: 2\n"
                "    file: GATE-02.md\n"
                "    work_units:\n"
                "      - id: FEAT-2026-9002/T03\n"
                "        file: WU-03-impl.md\n"
                "        depends_on: [FEAT-2026-9002/T02]\n"
                "      - id: FEAT-2026-9002/G2-CLOSE\n"
                "        file: WU-90-close.md\n"
                "        depends_on: [FEAT-2026-9002/T03]"
            ))
            _write_wu(feature, "WU-01-impl.md", "FEAT-2026-9002/T01", "implementation")
            _write_wu(feature, "WU-02-close-int.md", "FEAT-2026-9002/T02", "close-intermediate")
            _write_wu(feature, "WU-03-impl.md", "FEAT-2026-9002/T03", "implementation")
            _write_wu(feature, "WU-90-close.md", "FEAT-2026-9002/G2-CLOSE", "close")

            errs = lint_plan.lint(feature)
            self.assertTrue(errs,
                            "close-intermediate without plan-next must produce lint errors")
            ci_errs = [e for e in errs if "close-intermediate" in e]
            self.assertTrue(ci_errs,
                            f"errors must mention close-intermediate; errs={errs}")


if __name__ == "__main__":
    unittest.main()
