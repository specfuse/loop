#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the oracle_env frontmatter field and lint WARN (FEAT-2026-0015/T05).

Covers:
  - detect_oracle_verbs() pattern matching
  - AC-section slicing (verbs outside AC section do not fire)
  - lint() emits WARN when oracle AC present and oracle_env absent
  - lint() is silent when oracle_env is declared
  - lessons/docs/retrospective types are exempt
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _make_feature(tmpdir: str, wu_type: str, ac_content: str,
                  oracle_env: str | None = None) -> Path:
    """Build a minimal valid single-gate feature for oracle_env lint tests."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9999\n"
        "title: Oracle env lint test\n"
        "branch: feat/oracle-env-test\n"
        "roadmap_goal: Verify oracle_env lint.\n"
        "status: active\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9999/T01\n"
        "        file: WU-01-impl.md\n"
        "        depends_on: []\n"
        "      - id: FEAT-2026-9999/G1-CLOSE\n"
        "        file: WU-90-close.md\n"
        "        depends_on: [FEAT-2026-9999/T01]\n"
        "```\n"
    )

    env_line = f"oracle_env: {oracle_env}\n" if oracle_env else ""
    (feature / "WU-01-impl.md").write_text(
        "---\n"
        "id: FEAT-2026-9999/T01\n"
        f"type: {wu_type}\n"
        "status: done\n"
        "attempts: 1\n"
        f"{env_line}"
        "---\n\n"
        "# Title\n\n"
        "**Acceptance criteria.**\n"
        f"{ac_content}\n"
        "\n"
        "**Do not touch.**\n"
        "No generated files.\n"
    )

    (feature / "WU-90-close.md").write_text(
        "---\n"
        "id: FEAT-2026-9999/G1-CLOSE\n"
        "type: close\n"
        "status: done\n"
        "attempts: 1\n"
        "---\n\n"
        "# Close\n"
    )

    return feature


class TestDetectOracleVerbs(unittest.TestCase):
    """Unit tests for detect_oracle_verbs() pure helper."""

    def test_detect_oracle_verbs_finds_test_loop(self):
        text = "Run the test loop 50× and record pass rate."
        result = lint_plan.detect_oracle_verbs(text)
        self.assertTrue(result, "should detect 'test loop'")
        self.assertTrue(any("test loop" in v.lower() for v in result))

    def test_detect_oracle_verbs_case_insensitive_audit(self):
        result = lint_plan.detect_oracle_verbs("Audit the output on each run.")
        self.assertTrue(result, "should detect 'audit' (case-insensitive)")
        self.assertTrue(any("audit" in v.lower() for v in result))

    def test_detect_oracle_verbs_finds_recursive_run_N_times(self):
        # 'run N times' shape
        result = lint_plan.detect_oracle_verbs("Run 10 times and confirm no diff.")
        self.assertTrue(result, "should detect 'run N times'")
        self.assertTrue(any("run" in v.lower() for v in result))

    def test_detect_oracle_verbs_skips_outside_ac_section(self):
        """Oracle verb in Context does not fire when AC section is clean."""
        body = (
            "**Context.**\n"
            "This task will audit the pipeline runs.\n"
            "\n"
            "**Acceptance criteria.**\n"
            "The command exits 0 with no errors.\n"
            "\n"
            "**Do not touch.**\n"
            "No generated files.\n"
        )
        ac_slice = lint_plan._slice_ac_section(body)
        result = lint_plan.detect_oracle_verbs(ac_slice)
        self.assertEqual(result, [], f"verb in Context must not fire; ac_slice={ac_slice!r}")

    def test_detect_oracle_verbs_returns_empty_on_unrelated_text(self):
        result = lint_plan.detect_oracle_verbs("hello world, no special verbs here")
        self.assertEqual(result, [])

    def test_detect_oracle_verbs_finds_e2e(self):
        result = lint_plan.detect_oracle_verbs("Run e2e against the staging stack.")
        self.assertTrue(result, "should detect 'e2e'")

    def test_detect_oracle_verbs_finds_oracle_keyword(self):
        result = lint_plan.detect_oracle_verbs("The oracle must confirm the output matches.")
        self.assertTrue(result, "should detect 'oracle' keyword")


class TestOracleEnvLintIntegration(unittest.TestCase):
    """Integration tests: lint() WARN behaviour with full feature fixtures."""

    def _run_lint(self, feature: Path) -> tuple[list[str], str]:
        """Return (errs, stdout) from lint_plan.lint()."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            errs = lint_plan.lint(feature)
        return errs, buf.getvalue()

    def test_lint_warns_on_oracle_ac_without_env_field(self):
        """implementation WU with oracle AC but no oracle_env → WARN, exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="implementation",
                ac_content="Run the test loop 50 times and record pass rates.",
                oracle_env=None,
            )
            errs, stdout = self._run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            self.assertIn("WARN:", stdout, "must emit a WARN to stdout")
            self.assertIn("oracle_env", stdout, "WARN must mention 'oracle_env'")

    def test_lint_no_warn_when_oracle_env_present(self):
        """Same WU with oracle_env: linux_docker → no WARN, exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="implementation",
                ac_content="Run the test loop 50 times and record pass rates.",
                oracle_env="linux_docker",
            )
            errs, stdout = self._run_lint(feature)
            self.assertEqual(errs, [], f"must be no FAILs; errs={errs}")
            # The oracle_env WARN must NOT appear; other WARNs (closing shape) may.
            oracle_warns = [line for line in stdout.splitlines()
                            if "WARN:" in line and "oracle_env" in line]
            self.assertEqual(oracle_warns, [],
                             f"must emit no oracle_env WARN; stdout={stdout!r}")

    def test_lint_no_warn_for_lessons_type_even_with_oracle_verbs(self):
        """lessons WU is exempt even when AC contains oracle verbs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="lessons",
                ac_content="Audit the integration test runs and record learnings.",
                oracle_env=None,
            )
            errs, stdout = self._run_lint(feature)
            oracle_warns = [line for line in stdout.splitlines()
                            if "WARN:" in line and "oracle_env" in line]
            self.assertEqual(oracle_warns, [],
                             f"lessons type must be exempt; stdout={stdout!r}")


if __name__ == "__main__":
    unittest.main()
