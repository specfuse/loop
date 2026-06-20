# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import hashlib
import json
import pathlib
import tempfile
import unittest

from specfuse.loop.scaffold import (
    detect_modified,
    init_specfuse,
    upgrade_specfuse,
)


class TestManifestWrittenOnInit(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"
        self.manifest_path = self.specfuse / ".scaffold-manifest"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_manifest_written_on_init(self):
        self.assertTrue(self.manifest_path.exists(), ".scaffold-manifest not written by init_specfuse")

    def test_manifest_is_valid_json(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)

    def test_manifest_covers_versioned_relpaths(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        # All entries must be under versioned prefixes or exact versioned names
        versioned_prefixes = ("templates/", "rules/", "docs/")
        versioned_exact = {"VERSION", "verification.yml.example"}
        for rel in data:
            ok = any(rel.startswith(p) for p in versioned_prefixes) or rel in versioned_exact
            self.assertTrue(ok, f"non-versioned relpath in manifest: {rel!r}")

    def test_manifest_excludes_user_authored(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        user_authored = {"roadmap.md", "LEARNINGS.md", "verification.yml", "features/.gitkeep"}
        for rel in user_authored:
            self.assertNotIn(rel, data, f"user-authored {rel!r} must not appear in manifest")

    def test_manifest_sha256_values_correct(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertGreater(len(data), 0)
        for rel, expected_sha in data.items():
            on_disk = self.specfuse / rel
            self.assertTrue(on_disk.exists(), f"manifest entry {rel!r} missing on disk")
            actual = hashlib.sha256(on_disk.read_bytes()).hexdigest()
            self.assertEqual(actual, expected_sha, f"sha256 mismatch for {rel!r}")

    def test_manifest_sorted_keys(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        keys = list(data.keys())
        self.assertEqual(keys, sorted(keys))


class TestDetectModifiedFlagsEdit(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_detect_modified_flags_edit(self):
        # Edit a versioned file
        rules_file = self.specfuse / "rules" / "result-contract.md"
        rules_file.write_bytes(b"edited content")
        modified = detect_modified(self.target)
        self.assertIn("rules/result-contract.md", modified)

    def test_detect_modified_clean_returns_empty(self):
        # No edits after init → empty
        modified = detect_modified(self.target)
        self.assertEqual(modified, [])

    def test_detect_modified_returns_sorted(self):
        # Edit two versioned files
        (self.specfuse / "rules" / "result-contract.md").write_bytes(b"x")
        (self.specfuse / "rules" / "never-touch.md").write_bytes(b"y")
        modified = detect_modified(self.target)
        self.assertEqual(modified, sorted(modified))

    def test_detect_modified_missing_manifest_returns_empty(self):
        # Remove manifest → no crash, returns []
        (self.specfuse / ".scaffold-manifest").unlink()
        result = detect_modified(self.target)
        self.assertEqual(result, [])

    def test_detect_modified_no_specfuse_dir_returns_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            result = detect_modified(d)
            self.assertEqual(result, [])

    def test_detect_modified_only_edited_file_reported(self):
        # Edit exactly one file, verify only that one is reported
        target_rel = "rules/never-touch.md"
        (self.specfuse / target_rel).write_bytes(b"changed")
        modified = detect_modified(self.target)
        self.assertEqual(modified, [target_rel])


class TestManifestWrittenOnUpgrade(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"
        # Overwrite manifest with stale data to prove upgrade rewrites it
        manifest_path = self.specfuse / ".scaffold-manifest"
        manifest_path.write_text("{}", encoding="utf-8")
        upgrade_specfuse(self.target)
        self.manifest_path = manifest_path

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_manifest_written_on_upgrade(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        # upgrade includes verification.yml.example (written verbatim)
        self.assertGreater(len(data), 0)

    def test_upgrade_manifest_sha256_values_correct(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        for rel, expected_sha in data.items():
            on_disk = self.specfuse / rel
            self.assertTrue(on_disk.exists(), f"manifest entry {rel!r} missing on disk")
            actual = hashlib.sha256(on_disk.read_bytes()).hexdigest()
            self.assertEqual(actual, expected_sha, f"sha256 mismatch for {rel!r}")


if __name__ == "__main__":
    unittest.main()
