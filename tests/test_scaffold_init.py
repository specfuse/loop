# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import pathlib
import tempfile
import unittest

from specfuse.loop.scaffold import (
    ScaffoldExistsError,
    init_specfuse,
    read_scaffold,
    scaffold_version,
)

_EXPECTED_TREE = {
    "templates/GATE.template.md",
    "templates/PLAN.template.md",
    "templates/WU.template.md",
    "rules/correlation-ids.md",
    "rules/never-touch.md",
    "rules/result-contract.md",
    "rules/security-boundaries.md",
    "VERSION",
    "verification.yml",
    "roadmap.md",
    "LEARNINGS.md",
    "features/.gitkeep",
}

# Seed relpaths for versioned files and their target relpaths inside .specfuse/
_VERSIONED_SEED_TO_TARGET = {
    "templates/GATE.template.md": "templates/GATE.template.md",
    "templates/PLAN.template.md": "templates/PLAN.template.md",
    "templates/WU.template.md": "templates/WU.template.md",
    "rules/correlation-ids.md": "rules/correlation-ids.md",
    "rules/never-touch.md": "rules/never-touch.md",
    "rules/result-contract.md": "rules/result-contract.md",
    "rules/security-boundaries.md": "rules/security-boundaries.md",
    "VERSION": "VERSION",
    "verification.yml.example": "verification.yml",
}


class TestScaffoldInitRefusal(unittest.TestCase):
    def test_init_refuses_when_specfuse_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".specfuse").mkdir()
            with self.assertRaises(ScaffoldExistsError) as ctx:
                init_specfuse(target)
            self.assertIn("specfuse upgrade", str(ctx.exception))
            # No partial writes — dir must still be empty
            self.assertEqual(list((target / ".specfuse").iterdir()), [])

    def test_refusal_error_is_distinct_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".specfuse").mkdir()
            with self.assertRaises(ScaffoldExistsError):
                init_specfuse(target)


class TestScaffoldInitWritesTree(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.written = init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_init_writes_full_tree(self):
        self.assertEqual(set(self.written), _EXPECTED_TREE)

    def test_features_dir_created(self):
        self.assertTrue((self.specfuse / "features").is_dir())

    def test_version_matches_scaffold_version(self):
        version_bytes = (self.specfuse / "VERSION").read_bytes()
        self.assertEqual(version_bytes.decode().strip(), scaffold_version())

    def test_versioned_files_byte_match_read_scaffold(self):
        for seed_rel, target_rel in _VERSIONED_SEED_TO_TARGET.items():
            dest = self.specfuse / target_rel
            self.assertTrue(dest.exists(), f"{target_rel} not written")
            self.assertEqual(
                dest.read_bytes(),
                read_scaffold(seed_rel),
                f"{target_rel} differs from read_scaffold({seed_rel!r})",
            )

    def test_roadmap_seeded_from_template(self):
        roadmap = self.specfuse / "roadmap.md"
        self.assertTrue(roadmap.exists())
        self.assertEqual(roadmap.read_bytes(), read_scaffold("roadmap.template.md"))

    def test_learnings_seeded_from_template(self):
        learnings = self.specfuse / "LEARNINGS.md"
        self.assertTrue(learnings.exists())
        self.assertEqual(learnings.read_bytes(), read_scaffold("LEARNINGS.template.md"))

    def test_verification_yml_seeded_from_example(self):
        vyml = self.specfuse / "verification.yml"
        self.assertTrue(vyml.exists())
        self.assertEqual(vyml.read_bytes(), read_scaffold("verification.yml.example"))

    def test_second_call_raises_scaffold_exists_error(self):
        with self.assertRaises(ScaffoldExistsError):
            init_specfuse(self.target)

    def test_returns_sorted_relpaths(self):
        self.assertEqual(self.written, sorted(self.written))

    def test_gitignore_snippet_not_written(self):
        self.assertFalse((self.specfuse / "gitignore.snippet").exists())

    def test_no_partial_write_preserved_after_refusal(self):
        # After the tree is written, a second call must not add/remove anything
        before = set(p.relative_to(self.specfuse) for p in self.specfuse.rglob("*") if p.is_file())
        with self.assertRaises(ScaffoldExistsError):
            init_specfuse(self.target)
        after = set(p.relative_to(self.specfuse) for p in self.specfuse.rglob("*") if p.is_file())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
