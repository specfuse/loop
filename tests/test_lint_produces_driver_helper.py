#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for produces_driver_helper frontmatter field and lint WARN (FEAT-2026-0017/T02).

Covers:
  - detect_driver_wiring() pattern matching
  - lint() emits WARN when implementation WU mentions wiring keywords and
    produces_driver_helper is absent/empty
  - lint() is silent when produces_driver_helper is declared
  - non-implementation types (e.g. close) are exempt
  - empty body with no wiring keywords → no WARN
  - load_wu() normalizes string and list shapes to list[str]
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint, load_loop

lint_plan = load_lint()
loop = load_loop()


# ---------------------------------------------------------------------------
# Fixture builder
# ---------------------------------------------------------------------------

def _make_feature(
    tmpdir: str,
    wu_type: str = "implementation",
    body_extra: str = "",
    produces_driver_helper: str | None = None,
) -> Path:
    """Build a minimal valid single-gate feature for produces_driver_helper tests."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9998\n"
        "title: produces_driver_helper lint test\n"
        "branch: feat/pdh-test\n"
        "roadmap_goal: Verify produces_driver_helper lint.\n"
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

    pdh_line = f"produces_driver_helper: {produces_driver_helper}\n" if produces_driver_helper else ""
    (feature / "WU-01-impl.md").write_text(
        "---\n"
        "id: FEAT-2026-9998/T01\n"
        f"type: {wu_type}\n"
        "status: done\n"
        "attempts: 1\n"
        f"{pdh_line}"
        "---\n\n"
        "# Title\n\n"
        "**Context.**\n"
        f"{body_extra}\n"
        "\n"
        "**Acceptance criteria.**\n"
        "The code works.\n"
        "\n"
        "**Do not touch.**\n"
        "No generated files.\n"
        "\n"
        "**Verification.**\n"
        "code gates.\n"
        "\n"
        "**Escalation triggers.**\n"
        "Emit blocked if anything is wrong.\n"
    )

    (feature / "WU-90-close.md").write_text(
        "---\n"
        "id: FEAT-2026-9998/G1-CLOSE\n"
        "type: close\n"
        "status: done\n"
        "attempts: 1\n"
        "---\n\n"
        "# Close\n"
    )

    (feature / "GATE-01.md").write_text(
        "---\n"
        "status: open\n"
        "---\n\n"
        "# Gate 1\n"
    )

    return feature


def _run_lint(feature: Path) -> tuple[list[str], str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        errs = lint_plan.lint(feature)
    return errs, buf.getvalue()


# ---------------------------------------------------------------------------
# detect_driver_wiring() unit tests
# ---------------------------------------------------------------------------

class TestDetectDriverWiring(unittest.TestCase):

    def test_detects_loop_py(self):
        result = lint_plan.detect_driver_wiring("This WU edits loop.py directly.")
        self.assertTrue(result)
        self.assertTrue(any("loop.py" in v for v in result))

    def test_detects_MODEL_BY_TYPE(self):
        result = lint_plan.detect_driver_wiring("Add a key to MODEL_BY_TYPE.")
        self.assertTrue(result)
        self.assertTrue(any("MODEL_BY_TYPE" in v for v in result))

    def test_detects_fire_terminal_flips(self):
        result = lint_plan.detect_driver_wiring("Call fire_terminal_flips after pass.")
        self.assertTrue(result)
        self.assertTrue(any("fire_terminal_flips" in v for v in result))

    def test_detects_squash_commit(self):
        result = lint_plan.detect_driver_wiring("squash_commit is called by the driver.")
        self.assertTrue(result)

    def test_detects_POST_PASS_INVARIANTS_BY_TYPE(self):
        result = lint_plan.detect_driver_wiring("Adds POST_PASS_INVARIANTS_BY_TYPE constant.")
        self.assertTrue(result)

    def test_case_insensitive(self):
        result = lint_plan.detect_driver_wiring("modifies model_by_type mapping.")
        self.assertTrue(result, "pattern must be case-insensitive")

    def test_returns_empty_on_unrelated_text(self):
        result = lint_plan.detect_driver_wiring("No wiring here; just normal prose.")
        self.assertEqual(result, [])

    def test_empty_body_returns_empty(self):
        result = lint_plan.detect_driver_wiring("")
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# Lint integration tests
# ---------------------------------------------------------------------------

class TestProducesDriverHelperLint(unittest.TestCase):

    def test_implementation_wu_with_wiring_mention_and_declaration_passes_silently(self):
        """WU declares produces_driver_helper and mentions loop.py → no WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="implementation",
                body_extra="This WU adds a field to loop.py.",
                produces_driver_helper='["foo"]',
            )
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"no errors expected; got {errs}")
            pdh_warns = [ln for ln in stdout.splitlines()
                         if "WARN:" in ln and "produces_driver_helper" in ln]
            self.assertEqual(pdh_warns, [],
                             f"no produces_driver_helper WARN expected; stdout={stdout!r}")

    def test_implementation_wu_with_wiring_mention_no_declaration_warns(self):
        """WU body mentions MODEL_BY_TYPE but produces_driver_helper absent → WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="implementation",
                body_extra="Adds a key to MODEL_BY_TYPE in loop.py.",
                produces_driver_helper=None,
            )
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"no hard errors expected; got {errs}")
            self.assertIn("WARN:", stdout)
            self.assertIn("produces_driver_helper", stdout)
            self.assertIn("MODEL_BY_TYPE", stdout)

    def test_close_wu_with_wiring_mention_no_declaration_no_warn(self):
        """close type is exempt from produces_driver_helper WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="implementation",
                body_extra="No wiring keywords here.",
                produces_driver_helper=None,
            )
            # Rewrite the close WU to mention wiring and check it doesn't warn.
            # (The close WU in our fixture is status=done which skips section checks.)
            # Actually our fixture only puts wiring in WU-01-impl.md (implementation).
            # Let's test a plain close WU with wiring in body.
            close_path = feature / "WU-90-close.md"
            close_path.write_text(
                "---\n"
                "id: FEAT-2026-9998/G1-CLOSE\n"
                "type: close\n"
                "status: done\n"
                "attempts: 1\n"
                "---\n\n"
                "# Close\n\n"
                "This close WU documents changes to MODEL_BY_TYPE in loop.py.\n"
            )
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"no errors expected; got {errs}")
            # The implementation WU has no wiring keywords → no pdh WARN from it.
            # The close WU has wiring keywords but is exempt → no pdh WARN.
            pdh_warns = [ln for ln in stdout.splitlines()
                         if "WARN:" in ln and "produces_driver_helper" in ln]
            self.assertEqual(pdh_warns, [],
                             f"close type must not warn; stdout={stdout!r}")

    def test_empty_body_no_warn(self):
        """No wiring keywords → no WARN regardless of produces_driver_helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                wu_type="implementation",
                body_extra="No special terms here.",
                produces_driver_helper=None,
            )
            errs, stdout = _run_lint(feature)
            pdh_warns = [ln for ln in stdout.splitlines()
                         if "WARN:" in ln and "produces_driver_helper" in ln]
            self.assertEqual(pdh_warns, [],
                             f"no wiring keywords → no WARN; stdout={stdout!r}")


# ---------------------------------------------------------------------------
# load_wu normalization tests
# ---------------------------------------------------------------------------

class TestLoadWuProducesDriverHelper(unittest.TestCase):

    def _make_wu_file(self, tmpdir: str, pdh_value: str | None) -> tuple[Path, dict]:
        """Write a minimal WU file and return (feature_dir, ref)."""
        feature = Path(tmpdir) / "feature"
        feature.mkdir(exist_ok=True)
        pdh_line = f"produces_driver_helper: {pdh_value}\n" if pdh_value is not None else ""
        wu_path = feature / "WU-01.md"
        wu_path.write_text(
            "---\n"
            "id: FEAT-2026-9998/T01\n"
            "type: implementation\n"
            "status: pending\n"
            "attempts: 0\n"
            f"{pdh_line}"
            "---\n\n"
            "# Load wu test\n\n"
            "**Context.** Test.\n\n"
            "**Acceptance criteria.** Works.\n\n"
            "**Do not touch.** Nothing.\n\n"
            "**Verification.** code.\n\n"
            "**Escalation triggers.** None.\n"
        )
        ref = {"id": "FEAT-2026-9998/T01", "file": "WU-01.md", "depends_on": []}
        return feature, ref

    def test_load_wu_accepts_string_or_list_produces_driver_helper(self):
        """load_wu normalizes string → list[str] and list → list[str]."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # String form
            feature, ref = self._make_wu_file(tmpdir, "my_helper_function")
            wu = loop.load_wu(feature, ref)
            self.assertEqual(wu.produces_driver_helper, ["my_helper_function"])

        with tempfile.TemporaryDirectory() as tmpdir:
            # List form
            feature, ref = self._make_wu_file(tmpdir, "[foo, bar]")
            wu = loop.load_wu(feature, ref)
            self.assertEqual(wu.produces_driver_helper, ["foo", "bar"])

        with tempfile.TemporaryDirectory() as tmpdir:
            # Missing → empty list
            feature, ref = self._make_wu_file(tmpdir, None)
            wu = loop.load_wu(feature, ref)
            self.assertEqual(wu.produces_driver_helper, [])


if __name__ == "__main__":
    unittest.main()
