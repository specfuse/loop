#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for lint_close_verdict_not_predecided (FEAT-2026-0100/T05).

Covers:
  - detect_predecided_verdict_phrases() pattern matching
  - status escalation: pending/ready -> ERROR, draft -> WARN, done -> nothing
  - describing the mechanism (who decides) is not a match
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _make_feature(tmpdir: str, status: str, close_body: str) -> Path:
    """Build a minimal valid single-gate feature with one terminal `close` WU."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9997\n"
        "title: Predecided verdict lint test\n"
        "branch: feat/predecided-verdict-test\n"
        "roadmap_goal: Verify predecided-verdict lint.\n"
        "status: active\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9997/G1-CLOSE\n"
        "        file: WU-90-close.md\n"
        "        depends_on: []\n"
        "```\n"
    )

    (feature / "WU-90-close.md").write_text(
        "---\n"
        "id: FEAT-2026-9997/G1-CLOSE\n"
        "type: close\n"
        f"status: {status}\n"
        "attempts: 0\n"
        "---\n\n"
        "# Close\n\n"
        "**Context.**\n"
        "Test fixture.\n"
        "\n"
        "**Acceptance criteria.**\n"
        f"{close_body}\n"
        "\n"
        "**Do not touch.**\n"
        "No generated files.\n"
        "\n"
        "**Verification.**\n"
        "N/A.\n"
        "\n"
        "**Escalation triggers.**\n"
        "N/A.\n"
    )

    return feature


class TestDetectPredecidedVerdictPhrases(unittest.TestCase):
    """Unit tests for detect_predecided_verdict_phrases() pure helper."""

    def test_finds_verdict_colon_met(self):
        result = lint_plan.detect_predecided_verdict_phrases(
            "Write verdict: met in RETROSPECTIVE.md."
        )
        self.assertEqual(result, ["verdict: met"])

    def test_finds_the_verdict_is(self):
        result = lint_plan.detect_predecided_verdict_phrases(
            "The verdict is hedged, and this is the finding it exists to record."
        )
        self.assertTrue(result, f"result={result}")

    def test_describing_mechanism_is_clean(self):
        result = lint_plan.detect_predecided_verdict_phrases(
            "The judge writes the verdict; measure, do not decide."
        )
        self.assertEqual(result, [])


class TestPredecidedVerdictLintIntegration(unittest.TestCase):
    """Integration tests: lint() ERROR/WARN behaviour with full feature fixtures."""

    def _run_lint(self, feature: Path) -> tuple[list[str], str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            errs = lint_plan.lint(feature)
        return errs, buf.getvalue()

    def test_pending_close_naming_its_verdict_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, status="pending",
                close_body="- Write verdict: met once the criteria are satisfied.",
            )
            errs, _ = self._run_lint(feature)
            matches = [e for e in errs if "predecided verdict" in e]
            self.assertEqual(len(matches), 1, f"errs={errs}")
            self.assertIn("WU-90-close.md", matches[0])
            self.assertIn("ERROR", matches[0])

    def test_draft_is_warn_and_done_is_skipped(self):
        body = "- Write verdict: met once the criteria are satisfied."

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, status="draft", close_body=body)
            errs, stdout = self._run_lint(feature)
            self.assertEqual(
                [e for e in errs if "predecided verdict" in e], [],
                "draft close must WARN, not ERROR",
            )
            self.assertIn("WARN:", stdout)
            self.assertIn("predecided verdict", stdout)

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, status="done", close_body=body)
            errs, stdout = self._run_lint(feature)
            self.assertEqual([e for e in errs if "predecided verdict" in e], [])
            self.assertNotIn("predecided verdict", stdout)

    def test_describing_the_mechanism_is_not_a_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, status="pending",
                close_body="- The judge writes the verdict; measure, do not decide.",
            )
            errs, stdout = self._run_lint(feature)
            self.assertEqual([e for e in errs if "predecided verdict" in e], [])
            self.assertNotIn("predecided verdict", stdout)


if __name__ == "__main__":
    unittest.main()
