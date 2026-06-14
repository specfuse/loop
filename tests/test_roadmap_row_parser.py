#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Roadmap row parser tests — regression for issue #15.

The roadmap-row parser inside `auto_archive_feature` and
`fire_terminal_flips` used positional regex (4 capture groups assuming
columns `ID | Title | Status | Folder | Detail`). Projects with extra
columns (e.g. `ID | Title | Priority | Status | Folder` — 5 columns)
had Status read from the Priority column. `fire_terminal_flips` then
saw the priority value (e.g. `P1`) as status, refused the row flip, and
the post-pass invariant guard fired with `roadmap_row_not_done`.

Regression test ensures the parser resolves the Status cell by header
name rather than positional index, so any column ordering works.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


# Five-column roadmap with Priority column between Title and Status.
_ROADMAP_5COL_DONE = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID | Title | Priority | Status | Folder |
    |------------|-------|----------|--------|--------|
    | FEAT-2026-9999 | Test feature | P1 | done | `features/FEAT-2026-9999-test/` |

    ## FEAT-2026-9999 — Test feature

    Some content here.
    """)


# Five-column roadmap, status active (mirrors fire_terminal_flips's row-flip
# path: row in 'active' status must be rewritten to 'done').
_ROADMAP_5COL_ACTIVE = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID | Title | Priority | Status | Folder |
    |------------|-------|----------|--------|--------|
    | FEAT-2026-9999 | Test feature | P1 | active | `features/FEAT-2026-9999-test/` |

    ## FEAT-2026-9999 — Test feature

    Some content here.
    """)


_ARCHIVE_SCAFFOLD = textwrap.dedent("""\
    ---
    project: test
    ---

    # Archived feature details

    <!-- Archived sections appended below -->
    """)


def _make_repo(tmp: str, roadmap: str) -> Path:
    repo = Path(tmp)
    specfuse = repo / ".specfuse"
    specfuse.mkdir()
    (specfuse / "roadmap.md").write_text(roadmap)
    (specfuse / "roadmap-archive.md").write_text(_ARCHIVE_SCAFFOLD)
    return repo


class TestAutoArchive5ColRoadmap(unittest.TestCase):
    """auto_archive_feature on a 5-col (Priority) roadmap."""

    def test_5col_done_row_archives_successfully(self):
        """Issue #15: 5-col roadmap (ID|Title|Priority|Status|Folder, no Detail)
        archives the section. Back-link is skipped because no Detail column exists.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, _ROADMAP_5COL_DONE)
            result = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(
                result, "archived",
                "5-col roadmap with Status='done' must archive cleanly; "
                "positional parser misread Priority='P1' as Status."
            )

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            archive_text = (repo / ".specfuse" / "roadmap-archive.md").read_text()

            # Section moved out of roadmap into archive.
            self.assertNotIn('## FEAT-2026-9999 — ', roadmap_text)
            self.assertIn('<a id="feat-2026-9999"></a>', archive_text)
            self.assertIn('Some content here.', archive_text)
            # No Detail column → no back-link inserted (graceful degrade).
            self.assertNotIn('roadmap-archive.md#', roadmap_text,
                             "no Detail column → no back-link insertion")

    def test_5col_existing_4col_with_detail_still_archives_with_backlink(self):
        """Existing 5-col shape ID|Title|Status|Folder|Detail (with Detail) still works."""
        roadmap = textwrap.dedent("""\
            ---
            project: test
            ---

            # Roadmap

            | Feature ID | Title | Status | Folder | Detail |
            |------------|-------|--------|--------|--------|
            | FEAT-2026-9999 | Test feature | done | — | — |

            ## FEAT-2026-9999 — Test feature

            Some content here.
            """)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, roadmap)
            result = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(result, "archived")

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            self.assertIn(
                '[→ archive](roadmap-archive.md#feat-2026-9999)', roadmap_text,
                "back-link must be inserted into Detail cell when present"
            )


class TestFireTerminalFlips5ColRoadmap(unittest.TestCase):
    """fire_terminal_flips roadmap row flip on a 5-col (Priority) roadmap."""

    def test_5col_active_row_flips_to_done(self):
        """Issue #15: row's Status='active' must flip to 'done' regardless of column position."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, _ROADMAP_5COL_ACTIVE)

            # Build a minimal feature dir so fire_terminal_flips can find the gate file.
            feature_id = "FEAT-2026-9999"
            feature_dir = repo / ".specfuse" / "features" / f"{feature_id}-test"
            feature_dir.mkdir(parents=True)
            (feature_dir / "PLAN.md").write_text(
                f"---\nfeature_id: {feature_id}\nstatus: done\n---\n\n"
                f"```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
                f"    work_units: []\n```\n"
            )
            (feature_dir / "GATE-01.md").write_text(
                "---\ngate: 1\nstatus: awaiting_review\n---\n"
            )

            wu = loop.WorkUnit(
                wu_id=f"{feature_id}/G1-CLOSE",
                file=feature_dir / "WU-close.md",
                depends_on=[],
                type="close",
                model="opus",
                effort="high",
                status="done",
                attempts=1,
                title="Close",
                body="",
                verdict="met",
            )

            loop.fire_terminal_flips(wu, feature_dir, repo)

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            self.assertIn(
                "| FEAT-2026-9999 | Test feature | P1 | done |", roadmap_text,
                "Status cell must flip active → done on 5-col roadmap; "
                "current parser misreads Priority as Status."
            )
            # Priority column must remain unchanged.
            self.assertIn(" P1 ", roadmap_text,
                          "Priority column must NOT be modified")


if __name__ == "__main__":
    unittest.main()
