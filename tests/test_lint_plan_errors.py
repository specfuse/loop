#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Error-arm and regression tests for .specfuse/scripts/lint_plan.py."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._loop_loader import load_lint

lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FEATURE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"

_VALID_FM = """\
---
feature_id: FEAT-2026-0099
title: Test Feature
branch: feat/test
roadmap_goal: Test goal
status: active
---
"""

_CLOSING_WUS = [
    ("FEAT-2026-0099/G1-RETRO",   "WU-90-retro.md",     "retrospective"),
    ("FEAT-2026-0099/G1-LESSONS", "WU-91-lessons.md",    "lessons"),
    ("FEAT-2026-0099/G1-DOCS",    "WU-92-docs.md",       "docs"),
    ("FEAT-2026-0099/G1-PLAN",    "WU-93-plan-next.md",  "plan-next"),
]


def _wu_fm(wid: str, wu_type: str, status: str = "done", extra: str = "") -> str:
    lines = ["---", f"id: {wid}", f"type: {wu_type}", f"status: {status}"]
    if extra:
        lines.append(extra)
    lines.append("---")
    return "\n".join(lines) + "\n"


def _make_graph(work_units: list[dict]) -> str:
    parts = ["```yaml", "gates:", "  - gate: 1", "    work_units:"]
    for wu in work_units:
        parts.append(f"      - id: {wu['id']}")
        parts.append(f"        file: {wu['file']}")
        parts.append("        depends_on: []")
    parts.append("```")
    return "\n".join(parts)


def _build_minimal_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "feat"
    feat.mkdir()
    impl_id = "FEAT-2026-0099/T01"
    impl_file = "WU-01-impl.md"
    all_wus = [{"id": impl_id, "file": impl_file}] + [
        {"id": wid, "file": wfile} for wid, wfile, _ in _CLOSING_WUS
    ]
    (feat / "PLAN.md").write_text(_VALID_FM + "\n" + _make_graph(all_wus) + "\n")
    (feat / impl_file).write_text(_wu_fm(impl_id, "implementation"))
    for wid, wfile, wtype in _CLOSING_WUS:
        (feat / wfile).write_text(_wu_fm(wid, wtype))
    return feat


class TestLintErrorArms(unittest.TestCase):

    def test_plan_missing(self):
        """Line 82: PLAN.md absent → error naming missing file."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            errs = lint_plan.lint(feat)
        self.assertEqual(len(errs), 1)
        self.assertIn("missing", errs[0])

    def test_no_frontmatter(self):
        """Line 71: PLAN.md has no leading --- → read_frontmatter returns {}."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            (feat / "PLAN.md").write_text("No frontmatter here.\n")
            errs = lint_plan.lint(feat)
        self.assertTrue(any("frontmatter missing keys" in e for e in errs),
                        f"expected missing-keys error; errs={errs}")

    def test_plan_fm_missing_keys(self):
        """Line 87: PLAN.md has frontmatter but is missing required keys."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            (feat / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-0099\n---\n\n```yaml\ngates: []\n```\n"
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(any("frontmatter missing keys" in e for e in errs),
                        f"expected missing-keys error; errs={errs}")

    def test_unknown_feature_status_errors(self):
        """#185: a feature status outside the driver's enum is a lint error."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            plan = feat / "PLAN.md"
            plan.write_text(plan.read_text().replace(
                "status: active", "status: paused", 1))
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("'paused'" in e and "feature status" in e for e in errs),
            f"expected feature-status error; errs={errs}")

    def test_known_feature_statuses_do_not_error(self):
        """Every documented feature status passes the vocabulary check."""
        for status in ("planned", "active", "deferred", "done", "abandoned"):
            with tempfile.TemporaryDirectory() as tmp:
                feat = _build_minimal_feature(Path(tmp))
                plan = feat / "PLAN.md"
                plan.write_text(plan.read_text().replace(
                    "status: active", f"status: {status}", 1))
                errs = lint_plan.lint(feat)
            self.assertFalse(
                any("feature status" in e for e in errs),
                f"{status!r} should be a valid feature status; errs={errs}")

    def test_unknown_gate_status_errors(self):
        """#185: a gate status outside the driver's enum is a lint error."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            (feat / "GATE-01.md").write_text(
                "---\nstatus: reviewing\n---\n\n# Gate 1\n")
            # Point the graph's gate at the file so lint reads it.
            plan = feat / "PLAN.md"
            plan.write_text(plan.read_text().replace(
                "  - gate: 1\n", "  - gate: 1\n    file: GATE-01.md\n", 1))
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("'reviewing'" in e and "gate status" in e for e in errs),
            f"expected gate-status error; errs={errs}")

    def test_plan_no_yaml_block(self):
        """Line 91: PLAN.md has valid frontmatter but no fenced yaml graph block."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            (feat / "PLAN.md").write_text(_VALID_FM + "\nNo graph block here.\n")
            errs = lint_plan.lint(feat)
        self.assertTrue(any("no ```yaml graph block" in e for e in errs),
                        f"expected no-yaml-block error; errs={errs}")

    def test_wu_missing_id_or_file(self):
        """Lines 126-127: WU graph entry has empty id → missing id/file error."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            # id: with no value parses as None; triggers the missing-id/file guard.
            graph = (
                "```yaml\ngates:\n  - gate: 1\n    work_units:\n"
                "      - id:\n        file: WU-01.md\n        depends_on: []\n"
                "```\n"
            )
            (feat / "PLAN.md").write_text(_VALID_FM + "\n" + graph)
            errs = lint_plan.lint(feat)
        self.assertTrue(any("missing id/file" in e for e in errs),
                        f"expected missing-id/file error; errs={errs}")

    def test_wu_file_not_found(self):
        """Lines 136-137: WU file referenced in graph does not exist on disk."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            graph = (
                "```yaml\ngates:\n  - gate: 1\n    work_units:\n"
                "      - id: FEAT-2026-0099/T01\n        file: WU-MISSING.md\n"
                "        depends_on: []\n```\n"
            )
            (feat / "PLAN.md").write_text(_VALID_FM + "\n" + graph)
            errs = lint_plan.lint(feat)
        self.assertTrue(any("file not found" in e for e in errs),
                        f"expected file-not-found error; errs={errs}")

    def test_wu_invalid_type(self):
        """Line 148: WU frontmatter has an unrecognised type value."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            (feat / "WU-01-impl.md").write_text(
                _wu_fm("FEAT-2026-0099/T01", "bogus_type")
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(any("invalid type" in e for e in errs),
                        f"expected invalid-type error; errs={errs}")

    def test_wu_invalid_status(self):
        """Line 163: WU frontmatter has an unrecognised status value."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            (feat / "WU-01-impl.md").write_text(
                _wu_fm("FEAT-2026-0099/T01", "implementation", status="unknown_status")
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(any("invalid status" in e for e in errs),
                        f"expected invalid-status error; errs={errs}")

    def test_wu_invalid_effort(self):
        """Line 166: WU has an effort value not in VALID_EFFORT."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            (feat / "WU-01-impl.md").write_text(
                _wu_fm("FEAT-2026-0099/T01", "implementation", extra="effort: enormous")
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(any("invalid effort" in e for e in errs),
                        f"expected invalid-effort error; errs={errs}")

    def test_closing_sequence_wrong(self):
        """Line 189: gate has only implementation WUs → closing sequence mismatch."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            graph = (
                "```yaml\ngates:\n  - gate: 1\n    work_units:\n"
                "      - id: FEAT-2026-0099/T01\n        file: WU-01.md\n"
                "        depends_on: []\n```\n"
            )
            (feat / "PLAN.md").write_text(_VALID_FM + "\n" + graph)
            (feat / "WU-01.md").write_text(_wu_fm("FEAT-2026-0099/T01", "implementation"))
            errs = lint_plan.lint(feat)
        self.assertTrue(any("closing sequence" in e for e in errs),
                        f"expected closing-sequence error; errs={errs}")


class TestLintMainArms(unittest.TestCase):

    def test_main_no_args(self):
        """Lines 199-200: zero args → SystemExit with usage message."""
        with patch("sys.argv", ["lint_plan.py"]):
            with self.assertRaises(SystemExit):
                lint_plan.main()

    def test_main_pass(self):
        """Line 208: valid fixture → main() returns 0 and prints OK."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            buf = io.StringIO()
            with patch("sys.argv", ["lint_plan.py", str(feat)]):
                with contextlib.redirect_stdout(buf):
                    ret = lint_plan.main()
        self.assertEqual(ret, 0)
        self.assertIn("OK", buf.getvalue())

    def test_main_fail(self):
        """Lines 203-207: malformed fixture → main() returns 1 and prints FAIL."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = Path(tmp) / "feat"
            feat.mkdir()
            (feat / "PLAN.md").write_text("no frontmatter\n")
            buf = io.StringIO()
            with patch("sys.argv", ["lint_plan.py", str(feat)]):
                with contextlib.redirect_stdout(buf):
                    ret = lint_plan.main()
        self.assertEqual(ret, 1)
        self.assertIn("FAIL", buf.getvalue())


class TestLintValidRegression(unittest.TestCase):

    def test_existing_fixture_valid(self):
        """FEAT-2026-0001 fixture must produce no lint errors (regression guard)."""
        errs = lint_plan.lint(EXAMPLE_FEATURE)
        self.assertEqual(errs, [], f"valid fixture produced errors: {errs}")


class TestLintBaseKey(unittest.TestCase):
    """FEAT-2026-0031/T01: optional PLAN.md `base` frontmatter key."""

    def test_base_empty_string_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            plan = (feat / "PLAN.md").read_text()
            plan = plan.replace("status: active\n---", "status: active\nbase: \n---")
            (feat / "PLAN.md").write_text(plan)
            errs = lint_plan.lint(feat)
        self.assertTrue(any("base" in e and "FEAT-2026-0099" in e for e in errs),
                        f"expected base-key error naming the feature; errs={errs}")

    def test_base_whitespace_only_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            plan = (feat / "PLAN.md").read_text()
            plan = plan.replace('status: active\n---', 'status: active\nbase: "   "\n---')
            (feat / "PLAN.md").write_text(plan)
            errs = lint_plan.lint(feat)
        self.assertTrue(any("base" in e for e in errs),
                        f"expected base-key error; errs={errs}")

    def test_base_valid_string_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_minimal_feature(Path(tmp))
            plan = (feat / "PLAN.md").read_text()
            plan = plan.replace("status: active\n---", "status: active\nbase: release/9.9\n---")
            (feat / "PLAN.md").write_text(plan)
            errs = lint_plan.lint(feat)
        self.assertEqual(errs, [], f"valid base value produced errors: {errs}")

    def test_missing_base_key_still_passes(self):
        """Regression fixture (criterion 12): no `base` key at all lints clean."""
        errs = lint_plan.lint(EXAMPLE_FEATURE)
        self.assertEqual(errs, [], f"no-base fixture produced errors: {errs}")

    def test_base_not_in_required_keys(self):
        self.assertNotIn("base", lint_plan.REQUIRED_FEATURE_KEYS)


if __name__ == "__main__":
    unittest.main()
