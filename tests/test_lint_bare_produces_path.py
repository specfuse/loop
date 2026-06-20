#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the bare/non-root-relative `produces:` path lint guard (#77).

A `produces:` entry that is a bare filename (no '/') silently fails the
driver's presence gate — which resolves paths relative to the repo root —
and spins to a 3-attempt blocked state even when the file is produced in a
subdirectory. The lint guard catches the authoring mistake before dispatch.

Covers:
  - bare filename produces → WARN naming the offending path
  - repo-root-relative path (has '/') → no bare-path WARN
  - string-form produces (single bare value) → WARN
  - the WARN is advisory only (never appended to errs / never fails the lint)
  - non-implementation (close-adjacent) WU with a bare produces → WARN
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _make_feature(tmpdir: str, produces: str, wu_type: str = "implementation") -> Path:
    """Build a minimal single-gate feature whose first WU declares `produces`."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9997\n"
        "title: bare produces path lint test\n"
        "branch: feat/bare-produces\n"
        "roadmap_goal: Verify bare-produces lint guard.\n"
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

    (feature / "WU-01-impl.md").write_text(
        "---\n"
        "id: FEAT-2026-9997/T01\n"
        f"type: {wu_type}\n"
        "status: done\n"
        "attempts: 1\n"
        f"produces: {produces}\n"
        "---\n\n"
        "# Title\n\n"
        "**Context.** Test.\n\n"
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
        "---\n\n# Close\n"
    )

    (feature / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")

    return feature


def _run_lint(feature: Path) -> tuple[list[str], str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        errs = lint_plan.lint(feature)
    return errs, buf.getvalue()


def _bare_warns(stdout: str) -> list[str]:
    return [
        ln for ln in stdout.splitlines()
        if "WARN:" in ln and "bare filename" in ln
    ]


class TestBareProducesPathLint(unittest.TestCase):

    def test_bare_filename_warns(self):
        """produces: [GATE-02-REVIEW.md] (bare) → WARN naming the path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, produces="[GATE-02-REVIEW.md]")
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"WARN must not append to errs; got {errs}")
            warns = _bare_warns(stdout)
            self.assertTrue(warns, f"expected a bare-path WARN; stdout={stdout!r}")
            self.assertIn("GATE-02-REVIEW.md", warns[0])

    def test_root_relative_path_no_warn(self):
        """produces: [.specfuse/features/FEAT/GATE-02-REVIEW.md] → no bare WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                produces="[.specfuse/features/FEAT-2026-9997/GATE-02-REVIEW.md]",
            )
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"no errors expected; got {errs}")
            self.assertEqual(
                _bare_warns(stdout), [],
                f"root-relative path must not warn; stdout={stdout!r}",
            )

    def test_string_form_bare_warns(self):
        """produces: GATE-02-REVIEW.md (scalar string) → WARN."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, produces="GATE-02-REVIEW.md")
            errs, stdout = _run_lint(feature)
            self.assertEqual(errs, [], f"WARN must not append to errs; got {errs}")
            self.assertTrue(
                _bare_warns(stdout), f"expected a bare-path WARN; stdout={stdout!r}",
            )

    def test_bare_warn_on_non_implementation_wu(self):
        """A close-adjacent WU with a bare produces also warns (the incident)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir, produces="[GATE-02-REVIEW.md]", wu_type="review",
            )
            errs, stdout = _run_lint(feature)
            self.assertTrue(
                _bare_warns(stdout),
                f"non-implementation bare produces must warn; stdout={stdout!r}",
            )


if __name__ == "__main__":
    unittest.main()
