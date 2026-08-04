#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for lint_roadmap.py (FEAT-2026-0034/T01).

Each fixture builds a self-contained temp repo root with `.specfuse/roadmap.md`
and `.specfuse/roadmap-archive.md` written directly, mirroring test_arm_sweep.py's
fixture style. The load-bearing test is
`test_bidirectional_ref_rot_is_caught_in_both_directions` — a linter that catches
one ref direction and not the other looks correct on a clean tree and misses half
the rot on the next archive run.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.lint_roadmap import (
    SEVERITY_ERROR,
    SEVERITY_WARN,
    lint_roadmap,
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


class TestLintRoadmap(unittest.TestCase):
    def test_bidirectional_ref_rot_is_caught_in_both_directions(self):
        # One violation of EACH direction, both located in roadmap-archive.md:
        #   - a bare #feat-2026-0001 ref whose anchor actually lives in roadmap.md
        #   - a roadmap.md#feat-2026-0002 ref whose anchor actually lives in the
        #     archive itself
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0001", "active", "[→ detail](#feat-2026-0001)")
            + '\n<a id="feat-2026-0001"></a>\n'
            + "## FEAT-2026-0001 — Alpha\n\nBody.\n"
        )
        archive = (
            ARCHIVE_HEADER
            + "\nSee [Alpha](#feat-2026-0001) for context.\n"
            + '\n<a id="feat-2026-0002"></a>\n'
            + "## FEAT-2026-0002 — Beta\n\n"
            + "See [Beta](roadmap.md#feat-2026-0002) for context.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap, archive)
            findings = lint_roadmap(repo)

        errors = [f for f in findings if f.severity == SEVERITY_ERROR]
        bare_ref_hit = any(
            f.file == "roadmap-archive.md" and "#feat-2026-0001" in f.message
            for f in errors
        )
        prefixed_ref_hit = any(
            f.file == "roadmap-archive.md" and "roadmap.md#feat-2026-0002" in f.message
            for f in errors
        )
        self.assertTrue(bare_ref_hit, f"bare-ref direction not caught: {errors}")
        self.assertTrue(prefixed_ref_hit, f"prefixed-ref direction not caught: {errors}")

    def test_invariant_1_unresolvable_blocked_by_link_is_error_naming_fix(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0010", "blocked")
            + '\n<a id="feat-2026-0010"></a>\n'
            + "## FEAT-2026-0010 — Gamma\n\n"
            + "**Blocked by.** [ADR-0099](../docs/adr/0099-does-not-exist.md) — pending.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)

        hits = [
            f for f in findings
            if f.severity == SEVERITY_ERROR and "0099-does-not-exist.md" in f.message
        ]
        self.assertEqual(len(hits), 1, findings)
        self.assertIn("fix the path", hits[0].message)

    def test_invariant_3_anchor_heading_mismatch_is_error_naming_fix(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0011", "active", "[→ detail](#feat-2026-0011)")
            + _row("FEAT-2026-0012", "active", "[→ detail](#feat-2026-0012)")
            + '\n<a id="feat-2026-0011"></a>\n'
            + "## FEAT-2026-0012 — Wrong heading\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)

        hits = [
            f for f in findings
            if f.severity == SEVERITY_ERROR and "feat-2026-0011" in f.message
            and "feat-2026-0012" in f.message
        ]
        self.assertEqual(len(hits), 1, findings)
        self.assertIn("move this anchor", hits[0].message)

    def test_invariant_4_duplicate_id_across_both_files_is_error(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0020", "active", "[→ detail](#feat-2026-0020)")
            + '\n<a id="feat-2026-0020"></a>\n'
            + "## FEAT-2026-0020 — Delta\n\nBody.\n"
        )
        archive = (
            ARCHIVE_HEADER
            + '\n<a id="feat-2026-0020"></a>\n'
            + "## FEAT-2026-0020 — Delta (stale copy)\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap, archive)
            findings = lint_roadmap(repo)

        hits = [
            f for f in findings
            if f.severity == SEVERITY_ERROR and "feat-2026-0020" in f.message
            and "both roadmap.md and roadmap-archive.md" in f.message
        ]
        self.assertEqual(len(hits), 2, findings)  # one finding per occurrence

    def test_invariant_4_duplicate_id_within_one_file_is_error(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0021", "active", "[→ detail](#feat-2026-0021)")
            + '\n<a id="feat-2026-0021"></a>\n'
            + "## FEAT-2026-0021 — Epsilon\n\nBody.\n\n"
            + '<a id="feat-2026-0021"></a>\n'
            + "## FEAT-2026-0021 — Epsilon again\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)

        hits = [
            f for f in findings
            if f.severity == SEVERITY_ERROR and "feat-2026-0021" in f.message
            and "defined twice in roadmap.md" in f.message
        ]
        self.assertEqual(len(hits), 1, findings)

    def test_orphan_section_warns_on_dash_detail_with_existing_section(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0030", "done", "—")
            + '\n<a id="feat-2026-0030"></a>\n'
            + "## FEAT-2026-0030 — Zeta\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)

        hits = [
            f for f in findings
            if f.severity == SEVERITY_WARN and "FEAT-2026-0030" in f.message
            and "Detail cell" in f.message
        ]
        self.assertEqual(len(hits), 1, findings)

    def test_orphan_section_does_not_warn_when_detail_cell_has_link(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0031", "done", "[→ detail](#feat-2026-0031)")
            + '\n<a id="feat-2026-0031"></a>\n'
            + "## FEAT-2026-0031 — Eta\n\nBody.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)

        hits = [f for f in findings if "Detail cell" in f.message]
        self.assertEqual(hits, [])

    def test_blocked_by_on_non_blocked_row_is_warn_not_error(self):
        roadmap = (
            ROADMAP_HEADER
            + _row("FEAT-2026-0040", "active")
            + '\n<a id="feat-2026-0040"></a>\n'
            + "## FEAT-2026-0040 — Theta\n\n"
            + "**Blocked by.** [ADR-0001](../docs/adr/0001-real.md) — pending.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "docs" / "adr").mkdir(parents=True)
            (repo / "docs" / "adr" / "0001-real.md").write_text("# ADR\n")
            _write_repo(repo, roadmap)
            findings = lint_roadmap(repo)

        blocked_by_findings = [f for f in findings if "Blocked by" in f.message]
        self.assertEqual(len(blocked_by_findings), 1, findings)
        self.assertEqual(blocked_by_findings[0].severity, SEVERITY_WARN)

    def test_malformed_truncated_file_does_not_raise(self):
        roadmap = ROADMAP_HEADER + "| FEAT-2026-0050 | Truncated"
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)
        self.assertIsInstance(findings, list)

    def test_malformed_anchor_with_no_heading_anywhere_after_does_not_raise(self):
        roadmap = ROADMAP_HEADER + '\n<a id="feat-2026-0051"></a>\n'
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)
        self.assertIsInstance(findings, list)
        hits = [
            f for f in findings
            if f.severity == SEVERITY_ERROR and "feat-2026-0051" in f.message
        ]
        self.assertEqual(len(hits), 1, findings)

    def test_malformed_row_missing_status_cell_does_not_raise(self):
        roadmap = ROADMAP_HEADER + "| FEAT-2026-0052 | Sparse row |\n"
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), roadmap)
            findings = lint_roadmap(repo)
        self.assertIsInstance(findings, list)

    def test_no_loop_import(self):
        src = Path("specfuse/loop/lint_roadmap.py").read_text()
        for line in src.splitlines():
            stripped = line.strip()
            self.assertFalse(
                stripped.startswith("from .loop") or stripped.startswith("from specfuse.loop.loop")
                or stripped == "import loop",
                f"lint_roadmap.py must not import loop.py: {line!r}",
            )

    def test_real_tree_is_clean_on_all_four_invariants(self):
        repo_root = Path(__file__).resolve().parent.parent
        findings = lint_roadmap(repo_root)
        errors = [f for f in findings if f.severity == SEVERITY_ERROR]
        self.assertEqual(errors, [], f"real-tree run found violations: {errors}")


if __name__ == "__main__":
    unittest.main()
