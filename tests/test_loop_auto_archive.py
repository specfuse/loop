#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""auto_archive_feature end-to-end tests — FEAT-2026-0010/T05.

Covers:
  (a) happy path — done row with '—' Detail cell and inline section:
      returns "archived", roadmap.md Detail cell is the exact back-link
      literal, roadmap-archive.md has the exact anchor literal above the
      moved section.
  (b) idempotency — second call returns "already archived" and makes zero
      further file edits (verified by byte-equal compare).
  (c) refusal — planned row returns "refused: status=planned" and makes
      zero file edits.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_ROADMAP_DONE = textwrap.dedent("""\
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

_ROADMAP_PLANNED = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID | Title | Status | Folder | Detail |
    |------------|-------|--------|--------|--------|
    | FEAT-2026-9999 | Test feature | planned | — | — |

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


def _make_repo(tmp: str, *, roadmap: str = _ROADMAP_DONE) -> Path:
    repo = Path(tmp)
    specfuse = repo / ".specfuse"
    specfuse.mkdir()
    (specfuse / "roadmap.md").write_text(roadmap)
    (specfuse / "roadmap-archive.md").write_text(_ARCHIVE_SCAFFOLD)
    return repo


class TestAutoArchiveFeature(unittest.TestCase):

    def test_happy_path_archived(self):
        """done row + inline section → 'archived', exact literals in both files."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp)
            result = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(result, "archived")

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            archive_text = (repo / ".specfuse" / "roadmap-archive.md").read_text()

            # Exact back-link literal in roadmap Detail cell.
            self.assertIn(
                '[→ archive](roadmap-archive.md#feat-2026-9999)',
                roadmap_text,
            )
            # Inline section removed from roadmap.md.
            self.assertNotIn('## FEAT-2026-9999 — ', roadmap_text)

            # Exact anchor literal precedes moved section in archive.
            self.assertIn('<a id="feat-2026-9999"></a>', archive_text)
            anchor_pos = archive_text.index('<a id="feat-2026-9999"></a>')
            section_pos = archive_text.index('## FEAT-2026-9999 — ')
            self.assertLess(anchor_pos, section_pos,
                            "anchor must appear before section heading in archive")
            self.assertIn('Some content here.', archive_text)

    def test_idempotent_second_call(self):
        """Second call returns 'already archived' and makes zero file edits."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp)

            first = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(first, "archived")

            # Snapshot after first call.
            roadmap_snap = (repo / ".specfuse" / "roadmap.md").read_bytes()
            archive_snap = (repo / ".specfuse" / "roadmap-archive.md").read_bytes()

            second = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(second, "already archived")

            # Byte-equal: no writes occurred.
            self.assertEqual(
                (repo / ".specfuse" / "roadmap.md").read_bytes(),
                roadmap_snap,
                "roadmap.md must be unchanged on second call",
            )
            self.assertEqual(
                (repo / ".specfuse" / "roadmap-archive.md").read_bytes(),
                archive_snap,
                "roadmap-archive.md must be unchanged on second call",
            )

    def test_refused_planned_status(self):
        """planned row returns 'refused: status=planned' and makes zero file edits."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, roadmap=_ROADMAP_PLANNED)

            roadmap_before = (repo / ".specfuse" / "roadmap.md").read_bytes()
            archive_before = (repo / ".specfuse" / "roadmap-archive.md").read_bytes()

            result = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(result, "refused: status=planned")

            # No file edits.
            self.assertEqual(
                (repo / ".specfuse" / "roadmap.md").read_bytes(),
                roadmap_before,
                "roadmap.md must be unchanged on refusal",
            )
            self.assertEqual(
                (repo / ".specfuse" / "roadmap-archive.md").read_bytes(),
                archive_before,
                "roadmap-archive.md must be unchanged on refusal",
            )


if __name__ == "__main__":
    unittest.main()
