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

_ROADMAP_DONE_WITH_ANCHOR = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID | Title | Status | Folder | Detail |
    |------------|-------|--------|--------|--------|
    | FEAT-2026-9999 | Test feature | done | — | — |

    <a id="feat-2026-9999"></a>
    ## FEAT-2026-9999 — Test feature

    Some content here.

    ## Notes

    Trailing content.
    """)

_ROADMAP_DONE_NO_SECTION = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID | Title | Status | Folder | Detail |
    |------------|-------|--------|--------|--------|
    | FEAT-2026-9999 | Test feature | done | — | — |

    ## Notes

    Unrelated trailing content.
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

    def test_preexisting_anchor_not_orphaned(self):
        """A feature blocked via /block-feature carries an explicit <a id> above
        its heading; archiving must remove it, not strand it in roadmap.md."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, roadmap=_ROADMAP_DONE_WITH_ANCHOR)
            result = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(result, "archived")

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            archive_text = (repo / ".specfuse" / "roadmap-archive.md").read_text()

            # No orphan anchor left behind in roadmap.md.
            self.assertNotIn('<a id="feat-2026-9999"></a>', roadmap_text)
            self.assertNotIn('## FEAT-2026-9999 — ', roadmap_text)
            # Unrelated content survives.
            self.assertIn('## Notes', roadmap_text)
            # Archive carries exactly one anchor for the feature.
            self.assertEqual(archive_text.count('<a id="feat-2026-9999"></a>'), 1)

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

    def test_row_only_done_synthesizes_anchor(self):
        """done row with NO inline section → 'archived', anchor + stub still written.

        Regression for FEAT-2026-0022: a feature drafted via /draft-feature has
        a roadmap row but no inline detail section. Without the synthesize path,
        auto_archive_feature returned 'already archived' WITHOUT writing the
        anchor, leaving assert_terminal_flips_fired unsatisfiable and halting
        the driver on archive_anchor_missing.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, roadmap=_ROADMAP_DONE_NO_SECTION)
            result = loop.auto_archive_feature("FEAT-2026-9999", repo)
            self.assertEqual(result, "archived")

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            archive_text = (repo / ".specfuse" / "roadmap-archive.md").read_text()

            # Back-link replaced the '—' Detail cell.
            self.assertIn(
                '[→ archive](roadmap-archive.md#feat-2026-9999)',
                roadmap_text,
            )
            # The anchor the post-pass invariant demands is present.
            self.assertIn('<a id="feat-2026-9999"></a>', archive_text)
            # A stub heading was synthesized in the archive.
            self.assertIn('## FEAT-2026-9999 — Test feature', archive_text)
            # Unrelated roadmap content untouched (nothing wrongly stripped).
            self.assertIn('## Notes', roadmap_text)
            self.assertIn('Unrelated trailing content.', roadmap_text)

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
