#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/roadmap_link_gate.py (FEAT-2026-0034/T02).

Fixtures mirror test_lint_roadmap.py's build-a-temp-repo-root style: a
`.specfuse/roadmap.md` and `.specfuse/roadmap-archive.md` written directly, no
driver involved. This suite drives the entry point, not the invariants
themselves — the invariants are T01's and covered by test_lint_roadmap.py.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from _loop_loader import load_module

roadmap_link_gate = load_module(
    ".specfuse/scripts/roadmap_link_gate.py", "roadmap_link_gate"
)

ROADMAP_HEADER = (
    "---\nproject: test\n---\n\n# Roadmap\n\n"
    "| Feature ID | Title | Status | Folder | Detail |\n"
    "|---|---|---|---|---|\n"
)
ARCHIVE_HEADER = (
    "---\nproject: test\n---\n\n# Archived feature details\n\n"
    "<!-- Archived sections appended below -->\n"
)


def _write_repo(tmp: Path, roadmap_body: str, archive_body: str = "") -> Path:
    specfuse = tmp / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    (specfuse / "roadmap.md").write_text(roadmap_body)
    (specfuse / "roadmap-archive.md").write_text(archive_body or ARCHIVE_HEADER)
    return tmp


def _row(fid: str, status: str, detail: str = "—") -> str:
    return f"| {fid} | Title {fid} | {status} | — | {detail} |\n"


def _run_gate(root: Path):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = roadmap_link_gate.roadmap_link_gate_main(root)
    return code, out.getvalue(), err.getvalue()


class TestRoadmapLinkGate(unittest.TestCase):
    def test_error_finding_exits_1_warn_exits_0(self):
        # Exactly one ERROR: a dead ref with no anchor anywhere.
        error_roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0001", "active", "[→ detail](#feat-2026-0001)")
            + "\nSee [ghost](#feat-2026-9999) for context.\n"
            + '\n<a id="feat-2026-0001"></a>\n'
            + "## FEAT-2026-0001 — Alpha\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = _write_repo(Path(td), error_roadmap)
            code, out, err = _run_gate(root)

        self.assertEqual(code, 1)
        self.assertIn("ERROR:", err)
        self.assertIn("feat-2026-9999", err)

        # Only WARNs: a Blocked-by block on a row whose status is not blocked.
        warn_roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0002", "active", "[→ detail](#feat-2026-0002)")
            + '\n<a id="feat-2026-0002"></a>\n'
            + "## FEAT-2026-0002 — Beta\n\n"
            + "**Blocked by.** [FEAT-2026-0001](#feat-2026-0001)\n"
            + '\n<a id="feat-2026-0001"></a>\n'
            + "## FEAT-2026-0001 — Alpha\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = _write_repo(Path(td), warn_roadmap)
            code, out, err = _run_gate(root)

        self.assertEqual(code, 0)
        self.assertIn("WARN:", out)
        self.assertIn("FEAT-2026-0002", out)

    def test_findings_print_file_line_and_mechanical_fix(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0001", "active", "[→ detail](#feat-2026-0001)")
            + "\nSee [ghost](#feat-2026-9999) for context.\n"
            + '\n<a id="feat-2026-0001"></a>\n'
            + "## FEAT-2026-0001 — Alpha\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = _write_repo(Path(td), roadmap)
            code, out, err = _run_gate(root)

        self.assertEqual(code, 1)
        self.assertIn("roadmap.md:", err)
        self.assertRegex(err, r"roadmap\.md:\d+")
        # T01's message carries the mechanical fix ("no anchor ... found").
        self.assertIn("no anchor", err)

    def test_clean_tree_exits_0_and_prints_summary(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0001", "active", "[→ detail](#feat-2026-0001)")
            + '\n<a id="feat-2026-0001"></a>\n'
            + "## FEAT-2026-0001 — Alpha\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = _write_repo(Path(td), roadmap)
            code, out, err = _run_gate(root)

        self.assertEqual(code, 0)
        self.assertIn("roadmap link lint:", out)
        self.assertIn("0 error(s)", out)
        self.assertIn("0 warning(s)", out)

    def test_real_repo_roadmap_and_archive_pass_clean(self):
        code, out, err = _run_gate(roadmap_link_gate.REPO_ROOT)

        self.assertEqual(code, 0)
        self.assertIn("roadmap link lint:", out)


if __name__ == "__main__":
    unittest.main()
