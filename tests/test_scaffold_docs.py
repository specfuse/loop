# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import pathlib
import shutil
import tempfile
import unittest

from specfuse.loop.scaffold import init_specfuse, read_scaffold, upgrade_specfuse

_DOCS_RELPATHS = [
    "docs/concepts/architecture-addendum-gates-and-iterative-planning.md",
    "docs/concepts/ralph-lineage.md",
    "docs/getting-started.md",
    "docs/methodology.md",
    "docs/skills.md",
]


class TestInitWritesDocs(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.written = init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_init_writes_docs_tree(self):
        for relpath in _DOCS_RELPATHS:
            dest = self.specfuse / relpath
            self.assertTrue(dest.exists(), f"{relpath} not written by init_specfuse")
            self.assertEqual(
                dest.read_bytes(),
                read_scaffold(relpath),
                f"{relpath} differs from read_scaffold({relpath!r})",
            )

    def test_init_docs_in_written_list(self):
        for relpath in _DOCS_RELPATHS:
            self.assertIn(relpath, self.written, f"{relpath} absent from written list")


class TestUpgradeOverlaysDocs(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_upgrade_overlays_docs(self):
        for relpath in _DOCS_RELPATHS:
            dest = self.specfuse / relpath
            dest.write_bytes(b"STALE CONTENT")

        upgrade_specfuse(self.target)

        for relpath in _DOCS_RELPATHS:
            dest = self.specfuse / relpath
            self.assertTrue(dest.exists(), f"{relpath} missing after upgrade")
            self.assertEqual(
                dest.read_bytes(),
                read_scaffold(relpath),
                f"{relpath} not refreshed by upgrade",
            )

    def test_upgrade_adds_missing_docs(self):
        shutil.rmtree(self.specfuse / "docs")
        written = upgrade_specfuse(self.target)
        for relpath in _DOCS_RELPATHS:
            dest = self.specfuse / relpath
            self.assertTrue(dest.exists(), f"{relpath} not written by upgrade")
            self.assertIn(relpath, written)

    def test_upgrade_does_not_touch_user_authored_surfaces(self):
        sentinel = b"USER CONTENT DO NOT OVERWRITE"
        (self.specfuse / "LEARNINGS.md").write_bytes(sentinel)
        (self.specfuse / "roadmap.md").write_bytes(sentinel)
        (self.specfuse / "features" / "my-feature.md").write_bytes(sentinel)

        upgrade_specfuse(self.target)

        self.assertEqual((self.specfuse / "LEARNINGS.md").read_bytes(), sentinel)
        self.assertEqual((self.specfuse / "roadmap.md").read_bytes(), sentinel)
        self.assertEqual(
            (self.specfuse / "features" / "my-feature.md").read_bytes(), sentinel
        )

    def test_upgrade_prunes_removed_docs(self):
        stray = self.specfuse / "docs" / "obsolete-doc.md"
        stray.write_bytes(b"old doc")
        upgrade_specfuse(self.target)
        self.assertFalse(stray.exists(), "stray docs file must be pruned on upgrade")


if __name__ == "__main__":
    unittest.main()
