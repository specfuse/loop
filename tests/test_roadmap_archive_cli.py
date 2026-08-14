#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""specfuse.loop.roadmap_archive — CLI reachability for auto_archive_feature.

auto_archive_feature (loop.py) was reachable from exactly one call site
(fire_terminal_flips) and not from any command line. This module adds a
thin main() wrapper; it must not change archiving behaviour.
"""

from __future__ import annotations

import io
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.loop import roadmap_archive

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


class TestArchiveCLI(unittest.TestCase):

    def test_archives_a_done_feature(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                exit_code = roadmap_archive.main(
                    ["FEAT-2026-9999", "--repo", str(repo)]
                )
            self.assertEqual(exit_code, 0)
            self.assertIn("archived", out.getvalue())

            roadmap_text = (repo / ".specfuse" / "roadmap.md").read_text()
            archive_text = (repo / ".specfuse" / "roadmap-archive.md").read_text()

            self.assertIn(
                '[→ archive](roadmap-archive.md#feat-2026-9999)', roadmap_text
            )
            self.assertNotIn('## FEAT-2026-9999 — ', roadmap_text)
            self.assertIn('<a id="feat-2026-9999"></a>', archive_text)
            anchor_pos = archive_text.index('<a id="feat-2026-9999"></a>')
            section_pos = archive_text.index('## FEAT-2026-9999 — ')
            self.assertLess(anchor_pos, section_pos)
            self.assertIn('Some content here.', archive_text)

    def test_reports_three_outcomes_distinctly(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp)

            out = io.StringIO()
            with redirect_stdout(out):
                first_exit = roadmap_archive.main(
                    ["FEAT-2026-9999", "--repo", str(repo)]
                )
            self.assertEqual(first_exit, 0)
            self.assertIn("archived", out.getvalue())

            out = io.StringIO()
            with redirect_stdout(out):
                second_exit = roadmap_archive.main(
                    ["FEAT-2026-9999", "--repo", str(repo)]
                )
            self.assertEqual(second_exit, 0)
            self.assertIn("already archived", out.getvalue())

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = _make_repo(tmp, roadmap=_ROADMAP_PLANNED)
            out = io.StringIO()
            with redirect_stdout(out):
                exit_code = roadmap_archive.main(
                    ["FEAT-2026-9999", "--repo", str(repo)]
                )
            self.assertNotEqual(exit_code, 0)
            self.assertIn("refused: status=planned", out.getvalue())


if __name__ == "__main__":
    unittest.main()
