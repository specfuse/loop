#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the `produces:` WU frontmatter field (FEAT-2026-0022/T01).

`produces:` is the author-declared deliverable contract — the file path(s) a WU
is contracted to yield — parsed by load_wu onto WorkUnit.produces, with an
advisory lint WARN when an implementation WU declares none.

Covers:
  - load_wu() parses a list → list[str] (red→green: fails on HEAD with
    AttributeError because WorkUnit has no `produces`)
  - load_wu() normalizes a bare string → one-element list
  - load_wu() treats an absent field as []
  - load_wu() rejects a non-string/non-list value with ValueError
  - lint() emits a non-blocking WARN when an implementation WU declares no
    produces:, and is silent when produces: is declared
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
# load_wu fixture
# ---------------------------------------------------------------------------

def _make_wu_file(tmpdir: str, produces_value: str | None) -> tuple[Path, dict]:
    """Write a minimal WU file and return (feature_dir, ref)."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir(exist_ok=True)
    produces_line = (
        f"produces: {produces_value}\n" if produces_value is not None else ""
    )
    wu_path = feature / "WU-01.md"
    wu_path.write_text(
        "---\n"
        "id: FEAT-2026-9997/T01\n"
        "type: implementation\n"
        "status: pending\n"
        "attempts: 0\n"
        f"{produces_line}"
        "---\n\n"
        "# Produces field test\n\n"
        "**Context.** Test.\n\n"
        "**Acceptance criteria.** Works.\n\n"
        "**Do not touch.** Nothing.\n\n"
        "**Verification.** code.\n\n"
        "**Escalation triggers.** None.\n"
    )
    ref = {"id": "FEAT-2026-9997/T01", "file": "WU-01.md", "depends_on": []}
    return feature, ref


class TestLoadWuProduces(unittest.TestCase):

    def test_load_wu_parses_produces_list(self):
        """A list value is returned verbatim (red on HEAD: no .produces attr)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature, ref = _make_wu_file(tmpdir, '["a.md", "b.md"]')
            wu = loop.load_wu(feature, ref)
            self.assertEqual(wu.produces, ["a.md", "b.md"])

    def test_load_wu_produces_accepts_bare_string(self):
        """A bare string normalizes to a one-element list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature, ref = _make_wu_file(tmpdir, "a.md")
            wu = loop.load_wu(feature, ref)
            self.assertEqual(wu.produces, ["a.md"])

    def test_load_wu_produces_absent_is_empty(self):
        """An absent field defaults to []."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature, ref = _make_wu_file(tmpdir, None)
            wu = loop.load_wu(feature, ref)
            self.assertEqual(wu.produces, [])

    def test_load_wu_produces_rejects_non_string(self):
        """A non-string/non-list value raises ValueError naming the field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature, ref = _make_wu_file(tmpdir, "5")
            with self.assertRaises(ValueError) as ctx:
                loop.load_wu(feature, ref)
            self.assertIn("produces", str(ctx.exception))


# ---------------------------------------------------------------------------
# lint WARN fixture
# ---------------------------------------------------------------------------

def _make_feature(tmpdir: str, produces: str | None = None) -> Path:
    """Build a minimal single-gate feature with one implementation WU."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9997\n"
        "title: produces lint test\n"
        "branch: feat/produces-test\n"
        "roadmap_goal: Verify produces lint.\n"
        "status: active\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9997/T01\n"
        "        file: WU-01-impl.md\n"
        "        depends_on: []\n"
        "      - id: FEAT-2026-9997/G1-CLOSE\n"
        "        file: WU-90-close.md\n"
        "        depends_on: [FEAT-2026-9997/T01]\n"
        "```\n"
    )

    produces_line = f"produces: {produces}\n" if produces else ""
    (feature / "WU-01-impl.md").write_text(
        "---\n"
        "id: FEAT-2026-9997/T01\n"
        "type: implementation\n"
        "status: done\n"
        "attempts: 1\n"
        f"{produces_line}"
        "---\n\n"
        "# Title\n\n"
        "**Context.** Some context.\n\n"
        "**Acceptance criteria.** The code works.\n\n"
        "**Do not touch.** No generated files.\n\n"
        "**Verification.** code gates.\n\n"
        "**Escalation triggers.** Emit blocked if anything is wrong.\n"
    )

    (feature / "WU-90-close.md").write_text(
        "---\n"
        "id: FEAT-2026-9997/G1-CLOSE\n"
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


class TestProducesLint(unittest.TestCase):

    def test_lint_warns_on_missing_produces(self):
        """implementation WU with no produces: → non-blocking WARN, exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, produces=None)
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"WARN must not append to errs; got {errs}")
            produces_warns = [
                ln for ln in stdout.splitlines()
                if "WARN:" in ln and "produces:" in ln
            ]
            self.assertTrue(
                produces_warns,
                f"expected a produces WARN; stdout={stdout!r}",
            )

    def test_lint_silent_when_produces_declared(self):
        """implementation WU declaring produces: → no produces WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, produces="docs/report.md")
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"no errors expected; got {errs}")
            produces_warns = [
                ln for ln in stdout.splitlines()
                if "WARN:" in ln and "deliverable list" in ln
            ]
            self.assertEqual(
                produces_warns, [],
                f"no produces WARN expected; stdout={stdout!r}",
            )


if __name__ == "__main__":
    unittest.main()
