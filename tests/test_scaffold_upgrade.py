# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import pathlib
import shutil
import tempfile
import unittest

from specfuse.loop.scaffold import (
    ScaffoldDowngradeError,
    init_specfuse,
    read_scaffold,
    scaffold_version,
    upgrade_specfuse,
)

# Versioned seed relpaths and their target names inside .specfuse/
_VERSIONED_OVERLAY = {
    "templates/GATE.template.md": "templates/GATE.template.md",
    "templates/PLAN.template.md": "templates/PLAN.template.md",
    "templates/WU.template.md": "templates/WU.template.md",
    "rules/correlation-ids.md": "rules/correlation-ids.md",
    "rules/never-touch.md": "rules/never-touch.md",
    "rules/result-contract.md": "rules/result-contract.md",
    "rules/security-boundaries.md": "rules/security-boundaries.md",
    "VERSION": "VERSION",
    "verification.yml.example": "verification.yml.example",
}


def _make_target_with_version(version: str) -> tuple:
    tmpdir = tempfile.mkdtemp()
    target = pathlib.Path(tmpdir)
    specfuse = target / ".specfuse"
    specfuse.mkdir()
    (specfuse / "VERSION").write_text(version + "\n", encoding="utf-8")
    return target, specfuse, tmpdir


class TestUpgradeDowngradeRefusal(unittest.TestCase):
    def test_upgrade_refuses_downgrade(self):
        target, _, tmpdir = _make_target_with_version("99.0.0")
        try:
            with self.assertRaises(ScaffoldDowngradeError) as ctx:
                upgrade_specfuse(target)
            err = str(ctx.exception)
            self.assertIn("99.0.0", err)
            self.assertIn(scaffold_version(), err)
        finally:
            shutil.rmtree(tmpdir)

    def test_upgrade_refuses_downgrade_no_write(self):
        target, specfuse, tmpdir = _make_target_with_version("99.0.0")
        try:
            before = {p for p in specfuse.rglob("*") if p.is_file()}
            with self.assertRaises(ScaffoldDowngradeError):
                upgrade_specfuse(target)
            after = {p for p in specfuse.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(tmpdir)

    def test_upgrade_equal_version_proceeds(self):
        target, _, tmpdir = _make_target_with_version(scaffold_version())
        try:
            upgrade_specfuse(target)
        except ScaffoldDowngradeError:
            self.fail("equal version must not raise ScaffoldDowngradeError")
        finally:
            shutil.rmtree(tmpdir)

    def test_upgrade_older_version_proceeds(self):
        target, _, tmpdir = _make_target_with_version("0.0.1")
        try:
            upgrade_specfuse(target)
        except ScaffoldDowngradeError:
            self.fail("older version must not raise ScaffoldDowngradeError")
        finally:
            shutil.rmtree(tmpdir)

    def test_downgrade_error_is_distinct_type(self):
        target, _, tmpdir = _make_target_with_version("99.0.0")
        try:
            with self.assertRaises(ScaffoldDowngradeError):
                upgrade_specfuse(target)
        finally:
            shutil.rmtree(tmpdir)


class TestUpgradeOverlayAndPreserve(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        init_specfuse(self.target)
        self.specfuse = self.target / ".specfuse"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_upgrade_overlays_versioned_preserves_user(self):
        sentinel = b"USER CONTENT DO NOT OVERWRITE"
        (self.specfuse / "LEARNINGS.md").write_bytes(sentinel)
        (self.specfuse / "roadmap.md").write_bytes(sentinel)
        (self.specfuse / "verification.yml").write_bytes(sentinel)
        (self.specfuse / "features" / "my-feature.md").write_bytes(sentinel)

        upgrade_specfuse(self.target)

        self.assertEqual((self.specfuse / "LEARNINGS.md").read_bytes(), sentinel)
        self.assertEqual((self.specfuse / "roadmap.md").read_bytes(), sentinel)
        self.assertEqual((self.specfuse / "verification.yml").read_bytes(), sentinel)
        self.assertEqual(
            (self.specfuse / "features" / "my-feature.md").read_bytes(), sentinel
        )

    def test_upgrade_byte_faithful_overlay(self):
        upgrade_specfuse(self.target)
        for seed_rel, target_rel in _VERSIONED_OVERLAY.items():
            dest = self.specfuse / target_rel
            self.assertTrue(dest.exists(), f"{target_rel} not written")
            self.assertEqual(
                dest.read_bytes(),
                read_scaffold(seed_rel),
                f"{target_rel} differs from read_scaffold({seed_rel!r})",
            )

    def test_upgrade_stamps_version(self):
        upgrade_specfuse(self.target)
        written = (self.specfuse / "VERSION").read_bytes().decode().strip()
        self.assertEqual(written, scaffold_version())

    def test_upgrade_returns_sorted_relpaths(self):
        written = upgrade_specfuse(self.target)
        self.assertEqual(written, sorted(written))

    def test_upgrade_prunes_removed_versioned(self):
        stray = self.specfuse / "rules" / "obsolete.md"
        stray.write_bytes(b"stale content")
        upgrade_specfuse(self.target)
        self.assertFalse(stray.exists(), "stray versioned file must be pruned")

    def test_upgrade_prune_scoped_to_versioned_dirs(self):
        # features/ must never be pruned
        user_file = self.specfuse / "features" / "my-feature.md"
        user_file.write_bytes(b"feature content")
        upgrade_specfuse(self.target)
        self.assertTrue(user_file.exists())

    def test_upgrade_prune_does_not_touch_scripts_dir(self):
        # init.sh-legacy scripts/ dir must be left alone (migration prune out of scope)
        scripts = self.specfuse / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        legacy = scripts / "old-script.sh"
        legacy.write_bytes(b"#!/bin/sh\necho legacy")
        upgrade_specfuse(self.target)
        self.assertTrue(legacy.exists(), "scripts/ dir must not be pruned by upgrade")

    def test_upgrade_seeds_missing_user_authored(self):
        (self.specfuse / "LEARNINGS.md").unlink()
        (self.specfuse / "roadmap.md").unlink()
        (self.specfuse / "verification.yml").unlink()
        shutil.rmtree(self.specfuse / "features")

        written = upgrade_specfuse(self.target)

        self.assertTrue((self.specfuse / "LEARNINGS.md").exists())
        self.assertTrue((self.specfuse / "roadmap.md").exists())
        self.assertTrue((self.specfuse / "verification.yml").exists())
        self.assertTrue((self.specfuse / "features").is_dir())
        self.assertIn("LEARNINGS.md", written)
        self.assertIn("roadmap.md", written)
        self.assertIn("verification.yml", written)
        self.assertIn("features/.gitkeep", written)

    def test_upgrade_no_file_relative_reads(self):
        # AC6: scaffold.py must not use Path(__file__) for resource loading
        import inspect
        from specfuse.loop import scaffold as mod
        source = inspect.getsource(mod)
        self.assertNotIn("__file__", source)


if __name__ == "__main__":
    unittest.main()
