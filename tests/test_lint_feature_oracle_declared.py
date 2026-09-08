#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the feature-oracle-declared lint (FEAT-2026-0101/T03).

A gate carrying no `feature_oracle` is an ERROR when its feature is
`active`, a WARN when `planned`/`blocked`/`deferred`, and skipped when the
gate is `passed` or the feature is `done`/`abandoned`. Graduating by feature
status (not gate status alone) is the whole design — see the WU body.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _make_feature(
    tmpdir: str, feature_status: str, gate_status: str = "open",
    feature_oracle: "str | None" = None,
) -> Path:
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9998\n"
        "title: Feature-oracle-declared lint test\n"
        "branch: feat/feature-oracle-declared-test\n"
        "roadmap_goal: Verify feature-oracle-declared lint.\n"
        f"status: {feature_status}\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units: []\n"
        "```\n"
    )

    gate_lines = ["---\n", "gate: 1\n", f"status: {gate_status}\n"]
    if feature_oracle is not None:
        gate_lines.append(f'feature_oracle: "{feature_oracle}"\n')
    gate_lines.append("---\n\n# Gate 1\n")
    (feature / "GATE-01.md").write_text("".join(gate_lines))

    return feature


class TestLintFeatureOracleDeclared(unittest.TestCase):

    def _run(self, feature: Path) -> tuple[list[str], str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            fm, _ = lint_plan.read_frontmatter(feature / "PLAN.md")
            errs = lint_plan.lint_feature_oracle_declared(feature, fm)
        return errs, buf.getvalue()

    def test_active_feature_missing_oracle_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "active")
            errs, out = self._run(feature)
            self.assertEqual(len(errs), 1, f"errs={errs!r}")
            self.assertIn("GATE-01", errs[0])
            self.assertIn("ERROR", errs[0])
            self.assertNotIn("WARN", out)

    def test_planned_feature_missing_oracle_is_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "planned")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertIn("WARN", out)
            self.assertIn("GATE-01", out)

    def test_blocked_feature_missing_oracle_is_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "blocked")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertIn("WARN", out)

    def test_deferred_feature_missing_oracle_is_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "deferred")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertIn("WARN", out)

    def test_passed_gate_and_done_feature_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "active", gate_status="passed")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("WARN", out)

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "done")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("WARN", out)

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "abandoned")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("WARN", out)

    def test_declared_oracle_reports_nothing(self):
        for status in ("active", "planned", "blocked", "deferred", "done", "abandoned"):
            with tempfile.TemporaryDirectory() as tmpdir:
                feature = _make_feature(
                    tmpdir, status, feature_oracle="python3 -m unittest -q"
                )
                errs, out = self._run(feature)
                self.assertEqual(errs, [], f"status={status} errs={errs!r}")
                self.assertNotIn("WARN", out, f"status={status} out={out!r}")


if __name__ == "__main__":
    unittest.main()
