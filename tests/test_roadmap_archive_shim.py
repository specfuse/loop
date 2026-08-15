#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
""".specfuse/scripts/roadmap_archive.py — shim resolves specfuse.loop from source.

Mirrors the gate_eval.py shim shape verbatim: it path-inserts the repo root
so `specfuse.loop` resolves even with no pip install and PYTHONPATH unset.
Invoked as a subprocess from a cwd outside the repo, with the package absent
from sys.path/PYTHONPATH, to prove the shim — not the ambient environment —
is what makes the import work.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

_SHIM = REPO_ROOT / ".specfuse" / "scripts" / "roadmap_archive.py"

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

_ARCHIVE_SCAFFOLD = textwrap.dedent("""\
    ---
    project: test
    ---

    # Archived feature details

    <!-- Archived sections appended below -->
    """)


class TestShimResolvesFromSource(unittest.TestCase):

    def test_shim_archives_with_no_pip_install_on_path(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            repo = Path(tmp) / "target-repo"
            specfuse = repo / ".specfuse"
            specfuse.mkdir(parents=True)
            (specfuse / "roadmap.md").write_text(_ROADMAP_DONE)
            (specfuse / "roadmap-archive.md").write_text(_ARCHIVE_SCAFFOLD)

            env = {"PATH": "/usr/bin:/bin"}  # PYTHONPATH deliberately absent

            result = subprocess.run(
                [sys.executable, str(_SHIM), "FEAT-2026-9999", "--repo", str(repo)],
                cwd=tmp,  # cwd outside the specfuse repo entirely
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("archived", result.stdout)
            self.assertIn(
                '[→ archive](roadmap-archive.md#feat-2026-9999)',
                (specfuse / "roadmap.md").read_text(),
            )


if __name__ == "__main__":
    unittest.main()
