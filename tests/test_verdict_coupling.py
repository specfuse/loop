#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Verdict-frontmatter coupling — FEAT-2026-0015/T04.

Verifies:
  1. verdict_permits_terminal_flips() returns True only for 'met'.
  2. load_wu() parses verdict for close-type WUs.
  3. load_wu() returns verdict=None for non-close types.
  4. lint_plan.lint() errors on close WU (status: ready) missing verdict.
  5. lint_plan.lint() errors on close WU (status: ready) with invalid verdict.
  6. lint_plan.lint() skips verdict check for close WU with status: draft.
  7. lint_plan.lint() errors on non-close WU that declares a verdict field.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint, load_loop

loop = load_loop()
lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_wu_file(
    tmp: Path,
    *,
    wu_id: str,
    wu_type: str,
    status: str = "ready",
    verdict: str | None = None,
    filename: str = "WU-T01.md",
) -> Path:
    lines = [
        "---",
        f"id: {wu_id}",
        f"type: {wu_type}",
        "model: claude-sonnet-4-6",
        f"status: {status}",
        "attempts: 0",
    ]
    if verdict is not None:
        lines.append(f"verdict: {verdict}")
    lines.extend([
        "---",
        "",
        f"# {filename}",
        "",
        "## Context",
        "test",
        "",
        "## Acceptance criteria",
        "test",
        "",
        "## Do not touch",
        "test",
        "",
        "## Verification",
        "test",
        "",
        "## Escalation triggers",
        "test",
    ])
    path = tmp / filename
    path.write_text("\n".join(lines) + "\n")
    return path


def _make_single_gate_feature(
    tmp: Path,
    *,
    close_wu_id: str,
    close_wu_type: str,
    close_status: str,
    close_verdict: str | None,
    impl_wu_id: str = "FEAT-2026-9998/T01",
) -> Path:
    """Write a minimal single-gate feature suitable for lint."""
    feat = tmp / "feat"
    feat.mkdir()

    close_file = "WU-90-close.md"
    impl_file = "WU-01-impl.md"

    (feat / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9998\n"
        "title: Verdict coupling test\n"
        "branch: feat/verdict-test\n"
        "roadmap_goal: Test verdict coupling.\n"
        "status: active\n"
        "---\n"
        "\n"
        "# Plan\n"
        "\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    work_units:\n"
        f"      - id: {impl_wu_id}\n"
        f"        file: {impl_file}\n"
        "        depends_on: []\n"
        f"      - id: {close_wu_id}\n"
        f"        file: {close_file}\n"
        f"        depends_on: [{impl_wu_id}]\n"
        "```\n"
    )
    # Implementation WU — done, no verdict
    _write_wu_file(
        feat,
        wu_id=impl_wu_id,
        wu_type="implementation",
        status="done",
        filename=impl_file,
    )
    # Close WU under test
    _write_wu_file(
        feat,
        wu_id=close_wu_id,
        wu_type=close_wu_type,
        status=close_status,
        verdict=close_verdict,
        filename=close_file,
    )
    return feat


# ---------------------------------------------------------------------------
# Tests: verdict_permits_terminal_flips
# ---------------------------------------------------------------------------


class TestVerdictPermitsTerminalFlips(unittest.TestCase):
    """verdict_permits_terminal_flips() must return True only for 'met'."""

    def test_verdict_permits_terminal_flips_only_for_met(self):
        f = loop.verdict_permits_terminal_flips
        # The four enum values
        self.assertTrue(f("met"))
        self.assertFalse(f("met_locally"))
        self.assertFalse(f("partially_met"))
        self.assertFalse(f("not_met"))
        # Edge cases
        self.assertFalse(f(None))
        self.assertFalse(f(""))
        self.assertFalse(f("beautifully_done"))


# ---------------------------------------------------------------------------
# Tests: load_wu verdict parsing
# ---------------------------------------------------------------------------


class TestLoadWUVerdictParsing(unittest.TestCase):

    def test_load_wu_parses_verdict_for_close_type(self):
        ref = {"id": "FEAT-2026-9998/G1-CLOSE", "file": "WU-90-close.md", "depends_on": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_wu_file(
                Path(tmpdir),
                wu_id="FEAT-2026-9998/G1-CLOSE",
                wu_type="close",
                status="done",
                verdict="met_locally",
                filename="WU-90-close.md",
            )
            wu = loop.load_wu(Path(tmpdir), ref)
            self.assertEqual(wu.verdict, "met_locally")

    def test_load_wu_verdict_is_none_for_implementation_type(self):
        ref = {"id": "FEAT-2026-9998/T01", "file": "WU-T01.md", "depends_on": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write with verdict in frontmatter — load_wu must ignore it for non-close type
            _write_wu_file(
                Path(tmpdir),
                wu_id="FEAT-2026-9998/T01",
                wu_type="implementation",
                status="done",
                verdict="met",
                filename="WU-T01.md",
            )
            wu = loop.load_wu(Path(tmpdir), ref)
            self.assertIsNone(wu.verdict)


# ---------------------------------------------------------------------------
# Tests: lint_plan verdict validation
# ---------------------------------------------------------------------------


class TestLintVerdictValidation(unittest.TestCase):

    def test_lint_close_missing_verdict_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = _make_single_gate_feature(
                Path(tmpdir),
                close_wu_id="FEAT-2026-9998/G1-CLOSE",
                close_wu_type="close",
                close_status="ready",
                close_verdict=None,
            )
            errs = lint_plan.lint(feat)
            self.assertTrue(errs, "missing verdict on ready close WU must produce errors")
            verdict_errs = [e for e in errs if "verdict" in e and "close-type" in e]
            self.assertTrue(
                verdict_errs,
                f"errors must name the verdict problem; errs={errs}",
            )
            self.assertIn(
                "met, met_locally, partially_met, not_met",
                verdict_errs[0],
                f"error must list allowed values; err={verdict_errs[0]!r}",
            )

    def test_lint_close_invalid_verdict_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = _make_single_gate_feature(
                Path(tmpdir),
                close_wu_id="FEAT-2026-9998/G1-CLOSE",
                close_wu_type="close",
                close_status="ready",
                close_verdict="beautifully_done",
            )
            errs = lint_plan.lint(feat)
            self.assertTrue(errs, "invalid verdict on ready close WU must produce errors")
            verdict_errs = [e for e in errs if "verdict" in e and "close-type" in e]
            self.assertTrue(
                verdict_errs,
                f"errors must name the verdict problem; errs={errs}",
            )

    def test_lint_close_draft_status_skips_verdict_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = _make_single_gate_feature(
                Path(tmpdir),
                close_wu_id="FEAT-2026-9998/G1-CLOSE",
                close_wu_type="close",
                close_status="draft",
                close_verdict=None,
            )
            errs = lint_plan.lint(feat)
            verdict_errs = [e for e in errs if "verdict" in e and "close-type" in e]
            self.assertFalse(
                verdict_errs,
                f"draft close WU must not trigger verdict check; errs={errs}",
            )

    def test_lint_verdict_on_non_close_type_errors(self):
        ref_id = "FEAT-2026-9998/T02"
        impl_id = "FEAT-2026-9998/T01"
        with tempfile.TemporaryDirectory() as tmpdir:
            feat = Path(tmpdir) / "feat"
            feat.mkdir()
            (feat / "PLAN.md").write_text(
                "---\n"
                "feature_id: FEAT-2026-9998\n"
                "title: verdict on non-close test\n"
                "branch: feat/verdict-test\n"
                "roadmap_goal: Test verdict on non-close WU.\n"
                "status: active\n"
                "---\n"
                "\n"
                "# Plan\n"
                "\n"
                "```yaml\n"
                "gates:\n"
                "  - gate: 1\n"
                "    work_units:\n"
                f"      - id: {impl_id}\n"
                "        file: WU-01-impl.md\n"
                "        depends_on: []\n"
                f"      - id: {ref_id}\n"
                "        file: WU-02-bad.md\n"
                f"        depends_on: [{impl_id}]\n"
                # Need a close WU for a valid closing sequence
                "      - id: FEAT-2026-9998/G1-CLOSE\n"
                "        file: WU-90-close.md\n"
                f"        depends_on: [{ref_id}]\n"
                "```\n"
            )
            _write_wu_file(
                feat,
                wu_id=impl_id,
                wu_type="implementation",
                status="done",
                filename="WU-01-impl.md",
            )
            # Implementation WU with a verdict field — must error
            _write_wu_file(
                feat,
                wu_id=ref_id,
                wu_type="implementation",
                status="done",
                verdict="met",
                filename="WU-02-bad.md",
            )
            _write_wu_file(
                feat,
                wu_id="FEAT-2026-9998/G1-CLOSE",
                wu_type="close",
                status="done",
                filename="WU-90-close.md",
            )
            errs = lint_plan.lint(feat)
            self.assertTrue(errs, "verdict on non-close WU must produce errors")
            verdict_errs = [e for e in errs if "only meaningful for closing types" in e]
            self.assertTrue(
                verdict_errs,
                f"error must name 'only meaningful for closing types'; errs={errs}",
            )


if __name__ == "__main__":
    unittest.main()
