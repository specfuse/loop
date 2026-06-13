#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Reference implementation and tests for the roadmap-archive skill algorithm.

The skill moves a feature's inline detail section from roadmap.md to
roadmap-archive.md, updates the Detail cell with a back-link, and is
idempotent on re-invocation.

Exercises:
  (a) archiving a `done` row succeeds and detail moves with anchor prepended
  (b) the Detail cell is updated to a back-link
  (c) second invocation reports "already archived" with zero edits
  (d) attempting to archive a `planned` row is refused
"""

from __future__ import annotations

import re
import textwrap
import tempfile
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# Reference implementation of the archive algorithm
# ---------------------------------------------------------------------------

def archive_feature(roadmap_path: Path, archive_path: Path, feat_id: str) -> str:
    """Archive one feature's inline detail section.

    Returns one of:
      'archived'
      'already archived'
      'refused (status=<status>)'

    Raises ValueError if feat_id is not found in the roadmap table.
    """
    roadmap_text = roadmap_path.read_text()
    archive_text = archive_path.read_text()

    anchor_id = feat_id.lower()  # FEAT-2026-0003 -> feat-2026-0003
    back_link = f"[→ archive](roadmap-archive.md#{anchor_id})"

    # 1. Locate table row
    row_re = re.compile(
        r"^\| *" + re.escape(feat_id) + r" *\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|",
        re.MULTILINE,
    )
    row_m = row_re.search(roadmap_text)
    if not row_m:
        raise ValueError(f"{feat_id}: not found in roadmap table")

    status = row_m.group(2).strip()
    detail = row_m.group(4).strip()

    # 2. Idempotency: already archived?
    if "roadmap-archive.md#" in detail:
        return "already archived"

    # 3. Status guard
    if status in ("planned", "active"):
        return f"refused (status={status})"

    # 4. Find inline section
    sec_re = re.compile(r"^## " + re.escape(feat_id) + r" — ", re.MULTILINE)
    sec_m = sec_re.search(roadmap_text)
    if not sec_m:
        return "already archived"

    sec_start = sec_m.start()
    first_nl = roadmap_text.index("\n", sec_start) + 1
    nxt = re.search(r"^## ", roadmap_text[first_nl:], re.MULTILINE)
    sec_end = first_nl + nxt.start() if nxt else len(roadmap_text)

    section = roadmap_text[sec_start:sec_end].rstrip() + "\n"

    # 5. Build and insert archive entry
    insertion = f"\n<a id=\"{anchor_id}\"></a>\n{section}"
    marker = "<!-- Archived sections appended below -->"
    if marker not in archive_text:
        raise ValueError(f"insertion marker not found in {archive_path}")
    new_archive = archive_text.replace(marker, marker + insertion, 1)

    # 6. Remove section from roadmap, normalize blank lines
    new_roadmap = roadmap_text[:sec_start] + roadmap_text[sec_end:]
    new_roadmap = re.sub(r"\n{3,}", "\n\n", new_roadmap)

    # 7. Update Detail cell in the (now-shortened) roadmap
    row_m2 = row_re.search(new_roadmap)
    assert row_m2, f"{feat_id}: row missing after section removal"
    old_row = row_m2.group(0)
    rel_s = row_m2.start(4) - row_m2.start()
    rel_e = row_m2.end(4) - row_m2.start()
    new_row = old_row[:rel_s] + f" {back_link} " + old_row[rel_e:]
    new_roadmap = new_roadmap.replace(old_row, new_row, 1)

    # 8. Write
    roadmap_path.write_text(new_roadmap)
    archive_path.write_text(new_archive)

    return "archived"


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_ROADMAP_STUB = textwrap.dedent("""\
    ---
    project: test
    ---

    # Roadmap

    | Feature ID     | Title          | Status  | Folder | Detail |
    |----------------|----------------|---------|--------|--------|
    | FEAT-2026-0001 | Done feature   | done    | —      | —      |
    | FEAT-2026-0002 | Planned thing  | planned | —      | —      |

    ## FEAT-2026-0001 — Done feature

    **Why.** Testing archiving.

    **Status: done.** Completed.

    ## Notes

    Notes.
""")

_ARCHIVE_STUB = textwrap.dedent("""\
    ---
    project: test
    ---

    # Archived feature details

    ## Conventions

    - **Anchor format.** `<a id="feat-yyyy-nnnn"></a>`
    - **Back-link form.** `[→ archive](roadmap-archive.md#feat-yyyy-nnnn)`

    <!-- Archived sections appended below -->
""")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestArchiveFeature(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        d = Path(self._tmpdir.name)
        self.roadmap = d / "roadmap.md"
        self.archive = d / "roadmap-archive.md"
        self.roadmap.write_text(_ROADMAP_STUB)
        self.archive.write_text(_ARCHIVE_STUB)

    def tearDown(self):
        self._tmpdir.cleanup()

    # (a) archiving a done row succeeds; detail section moves with anchor prepended
    def test_archive_done_row_returns_archived(self):
        result = archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        self.assertEqual(result, "archived")

    def test_detail_section_appended_to_archive(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        text = self.archive.read_text()
        self.assertIn("## FEAT-2026-0001 — Done feature", text)
        self.assertIn("**Why.** Testing archiving.", text)

    def test_anchor_prepended_before_heading_in_archive(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        text = self.archive.read_text()
        self.assertIn('<a id="feat-2026-0001"></a>', text)
        anchor_pos = text.index('<a id="feat-2026-0001"></a>')
        heading_pos = text.index("## FEAT-2026-0001 — Done feature")
        self.assertLess(anchor_pos, heading_pos)

    def test_anchor_on_own_line_directly_above_heading(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        lines = self.archive.read_text().splitlines()
        anchor_idx = lines.index('<a id="feat-2026-0001"></a>')
        self.assertEqual(lines[anchor_idx + 1], "## FEAT-2026-0001 — Done feature")

    def test_detail_section_removed_from_roadmap(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        text = self.roadmap.read_text()
        self.assertNotIn("## FEAT-2026-0001 — Done feature", text)
        self.assertNotIn("**Why.** Testing archiving.", text)

    def test_notes_section_preserved_in_roadmap(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        text = self.roadmap.read_text()
        self.assertIn("## Notes", text)
        self.assertIn("Notes.", text)

    # (b) Detail cell updated with back-link
    def test_detail_cell_updated_to_backlink(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        text = self.roadmap.read_text()
        self.assertIn("[→ archive](roadmap-archive.md#feat-2026-0001)", text)

    def test_table_row_still_present_after_archive(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        text = self.roadmap.read_text()
        self.assertIn("FEAT-2026-0001", text)
        self.assertIn("Done feature", text)

    # (c) second invocation is idempotent
    def test_idempotent_second_invocation_returns_already_archived(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        result = archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        self.assertEqual(result, "already archived")

    def test_idempotent_second_invocation_makes_zero_file_edits(self):
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        roadmap_snapshot = self.roadmap.read_text()
        archive_snapshot = self.archive.read_text()
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0001")
        self.assertEqual(self.roadmap.read_text(), roadmap_snapshot)
        self.assertEqual(self.archive.read_text(), archive_snapshot)

    # (d) planned row is refused
    def test_planned_row_refused(self):
        result = archive_feature(self.roadmap, self.archive, "FEAT-2026-0002")
        self.assertEqual(result, "refused (status=planned)")

    def test_planned_row_refusal_makes_no_file_edits(self):
        roadmap_snapshot = self.roadmap.read_text()
        archive_snapshot = self.archive.read_text()
        archive_feature(self.roadmap, self.archive, "FEAT-2026-0002")
        self.assertEqual(self.roadmap.read_text(), roadmap_snapshot)
        self.assertEqual(self.archive.read_text(), archive_snapshot)


if __name__ == "__main__":
    unittest.main()
