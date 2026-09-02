#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the unobservable-AC lint (FEAT-2026-0084/T03).

Covers:
  - detect_unobservable_ac_bullets() pattern matching
  - backticked check on the same bullet is clean
  - escape hatches: oracle_env (non-local), human_only: true
  - status escalation: pending/ready -> ERROR, draft -> WARN, done -> nothing
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _make_feature(tmpdir: str, status: str, ac_content: str,
                   oracle_env: str | None = None,
                   human_only: bool = False) -> Path:
    """Build a minimal valid single-gate feature for unobservable-AC lint tests."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9998\n"
        "title: Unobservable AC lint test\n"
        "branch: feat/unobservable-ac-test\n"
        "roadmap_goal: Verify unobservable-AC lint.\n"
        "status: active\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9998/T01\n"
        "        file: WU-01-impl.md\n"
        "        depends_on: []\n"
        "      - id: FEAT-2026-9998/G1-CLOSE\n"
        "        file: WU-90-close.md\n"
        "        depends_on: [FEAT-2026-9998/T01]\n"
        "```\n"
    )

    extra_lines = []
    if oracle_env:
        extra_lines.append(f"oracle_env: {oracle_env}\n")
    if human_only:
        extra_lines.append("human_only: true\n")
    extra = "".join(extra_lines)

    (feature / "WU-01-impl.md").write_text(
        "---\n"
        "id: FEAT-2026-9998/T01\n"
        "type: implementation\n"
        f"status: {status}\n"
        "attempts: 0\n"
        f"{extra}"
        "---\n\n"
        "# Title\n\n"
        "**Context.**\n"
        "Test fixture.\n"
        "\n"
        "**Acceptance criteria.**\n"
        f"{ac_content}\n"
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

    (feature / "WU-90-close.md").write_text(
        "---\n"
        "id: FEAT-2026-9998/G1-CLOSE\n"
        "type: close\n"
        "status: done\n"
        "attempts: 1\n"
        "verdict: met\n"
        "---\n\n"
        "# Close\n"
    )

    return feature


class TestDetectUnobservableAcBullets(unittest.TestCase):
    """Unit tests for detect_unobservable_ac_bullets() pure helper."""

    def test_finds_applied_in_prod(self):
        result = lint_plan.detect_unobservable_ac_bullets(
            "- The change is applied in prod.\n"
        )
        self.assertEqual(result, ["The change is applied in prod."])

    def test_backticked_bullet_is_clean(self):
        result = lint_plan.detect_unobservable_ac_bullets(
            "- Applied in prod: `bash scripts/verify-prod.sh` exits 0.\n"
        )
        self.assertEqual(result, [])

    def test_unrelated_bullet_is_clean(self):
        result = lint_plan.detect_unobservable_ac_bullets(
            "- `bash scripts/check-foo.sh` exits 0.\n"
        )
        self.assertEqual(result, [])


class TestAcObservableLintIntegration(unittest.TestCase):
    """Integration tests: lint() ERROR/WARN behaviour with full feature fixtures."""

    def _run_lint(self, feature: Path) -> tuple[list[str], str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            errs = lint_plan.lint(feature)
        return errs, buf.getvalue()

    def test_pending_wu_unobservable_bullet_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, status="pending",
                ac_content="- The change is applied in prod.",
            )
            errs, _ = self._run_lint(feature)
            matches = [e for e in errs if "cannot" in e and "observe" in e]
            self.assertEqual(len(matches), 1, f"errs={errs}")
            self.assertIn("WU-01-impl.md", matches[0])
            self.assertIn("applied in prod", matches[0])

    def test_backticked_check_on_same_bullet_is_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, status="pending",
                ac_content=(
                    "- Applied in prod: `bash scripts/verify-prod.sh` exits 0."
                ),
            )
            errs, stdout = self._run_lint(feature)
            self.assertEqual(errs, [], f"errs={errs}")
            self.assertNotIn("cannot", stdout)

    def test_escape_hatches(self):
        bullet = "- The change is applied in prod."

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, status="pending", ac_content=bullet,
                oracle_env="github_actions_ci",
            )
            errs, _ = self._run_lint(feature)
            self.assertEqual(
                [e for e in errs if "cannot" in e], [],
                "non-local oracle_env must escape-hatch the rule",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, status="pending", ac_content=bullet, human_only=True,
            )
            errs, _ = self._run_lint(feature)
            self.assertEqual(
                [e for e in errs if "cannot" in e], [],
                "human_only: true must escape-hatch the rule",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, status="draft", ac_content=bullet)
            errs, stdout = self._run_lint(feature)
            self.assertEqual(
                [e for e in errs if "cannot" in e], [],
                "draft WU must WARN, not ERROR",
            )
            self.assertIn("WARN:", stdout)
            self.assertIn("cannot", stdout)

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, status="done", ac_content=bullet)
            errs, stdout = self._run_lint(feature)
            self.assertEqual([e for e in errs if "cannot" in e], [])
            self.assertNotIn("cannot", stdout)


if __name__ == "__main__":
    unittest.main()
