"""This repository opts in to changelog fragments (FEAT-LOOP-2026-0249/T07)."""

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _get(key):
    out = subprocess.run(
        [sys.executable, "-m", "specfuse.loop.layout", "get", key],
        cwd=REPO, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


class RepoChangelogOptIn(unittest.TestCase):
    def test_mode_is_fragments(self):
        self.assertEqual(_get("changelog.mode"), "fragments")

    def test_ids_key_unchanged(self):
        self.assertEqual(_get("ids.key"), "LOOP")


if __name__ == "__main__":
    unittest.main()
