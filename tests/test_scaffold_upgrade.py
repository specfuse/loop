# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import contextlib
import io
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


class TestUnmanagedLegacyWarning(unittest.TestCase):
    """#165: upgrade advances VERSION but never manages scripts/ or skills/.

    Only pre-PyPI (init.sh-era) repos carry full copies; upgrade leaves them
    stale while VERSION moves on. A warning must surface that drift; a clean
    (post-migration) project must stay silent.
    """

    def _upgrade_capturing_stderr(self, target) -> str:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            upgrade_specfuse(target)
        return err.getvalue()

    def test_warns_when_legacy_scripts_and_skills_present(self):
        target, specfuse, tmpdir = _make_target_with_version("0.0.1")
        try:
            (specfuse / "scripts").mkdir()
            (specfuse / "scripts" / "loop.py").write_text("# legacy 0.2.0\n")
            (specfuse / "skills" / "draft-feature").mkdir(parents=True)
            (specfuse / "skills" / "draft-feature" / "SKILL.md").write_text("x")
            out = self._upgrade_capturing_stderr(target)
            self.assertIn("scripts/", out)
            self.assertIn("skills/", out)
            # Names the version it advanced to, so the drift is legible.
            self.assertIn(scaffold_version(), out)
        finally:
            shutil.rmtree(tmpdir)

    def test_warns_when_only_scripts_present(self):
        target, specfuse, tmpdir = _make_target_with_version("0.0.1")
        try:
            (specfuse / "scripts").mkdir()
            (specfuse / "scripts" / "loop.py").write_text("# legacy\n")
            out = self._upgrade_capturing_stderr(target)
            self.assertIn("scripts/", out)
            self.assertNotIn("skills/", out)
        finally:
            shutil.rmtree(tmpdir)

    def test_silent_on_clean_project(self):
        # A post-migration project (init_specfuse ships neither dir).
        tmpdir = tempfile.mkdtemp()
        target = pathlib.Path(tmpdir)
        try:
            init_specfuse(target)
            self.assertFalse((target / ".specfuse" / "scripts").exists())
            self.assertFalse((target / ".specfuse" / "skills").exists())
            out = self._upgrade_capturing_stderr(target)
            self.assertNotIn("not managed", out.lower())
        finally:
            shutil.rmtree(tmpdir)

    def test_empty_legacy_dir_does_not_warn(self):
        # An empty scripts/ dir (no files) is not drift.
        target, specfuse, tmpdir = _make_target_with_version("0.0.1")
        try:
            (specfuse / "scripts").mkdir()
            out = self._upgrade_capturing_stderr(target)
            self.assertNotIn("not managed", out.lower())
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
        """A file the seed once shipped (in the manifest) but no longer
        carries is pruned. Manifest membership is the ownership proof (#214)."""
        import json as _json
        stray = self.specfuse / "rules" / "obsolete.md"
        stray.write_bytes(b"stale content")
        manifest = self.specfuse / ".scaffold-manifest"
        entries = _json.loads(manifest.read_text())
        entries["rules/obsolete.md"] = (
            "0" * 64  # sha irrelevant to prune — membership is the proof
        )
        manifest.write_text(_json.dumps(entries))
        upgrade_specfuse(self.target)
        self.assertFalse(stray.exists(), "manifest-owned removed file must be pruned")

    def test_upgrade_keeps_unmanaged_file_in_rules_with_warning(self):
        """A project-authored file dropped into rules/ (never written by
        specfuse — absent from the manifest) survives upgrade, with a stderr
        warning pointing at rules-local/ (#214)."""
        user_rule = self.specfuse / "rules" / "our-own-rule.md"
        user_rule.write_bytes(b"# project rule\n")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            upgrade_specfuse(self.target)
        self.assertTrue(user_rule.exists(),
                        "unmanaged file must NOT be pruned")
        self.assertEqual(user_rule.read_bytes(), b"# project rule\n")
        err = stderr.getvalue()
        self.assertIn("rules/our-own-rule.md", err)
        self.assertIn("rules-local", err)

    def test_upgrade_warns_before_overwriting_modified_versioned(self):
        """A locally-modified shipped file is still overwritten (versioned-dir
        contract) but loudly (#214)."""
        target_file = self.specfuse / "rules" / "result-contract.md"
        target_file.write_bytes(b"locally modified\n")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            upgrade_specfuse(self.target)
        self.assertEqual(target_file.read_bytes(),
                         read_scaffold("rules/result-contract.md"),
                         "versioned file must still be overwritten")
        err = stderr.getvalue()
        self.assertIn("locally-modified", err)
        self.assertIn("rules/result-contract.md", err)

    def test_upgrade_legacy_no_manifest_keeps_unknown_silently_unpruned(self):
        """Pre-manifest tree: ownership unprovable — unknown files kept
        (warned), no clobber warnings for shipped files (#214)."""
        (self.specfuse / ".scaffold-manifest").unlink()
        user_rule = self.specfuse / "rules" / "legacy-own-rule.md"
        user_rule.write_bytes(b"legacy project rule\n")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            upgrade_specfuse(self.target)
        self.assertTrue(user_rule.exists(),
                        "no manifest -> cannot prove ownership -> keep")
        self.assertNotIn("locally-modified", stderr.getvalue(),
                         "no manifest -> overlay clobber warnings suppressed")

    def test_upgrade_prune_scoped_to_versioned_dirs(self):
        # features/ must never be pruned
        user_file = self.specfuse / "features" / "my-feature.md"
        user_file.write_bytes(b"feature content")
        upgrade_specfuse(self.target)
        self.assertTrue(user_file.exists())

    def test_upgrade_preserves_rules_local_files(self):
        """The rules-local/ contract: project-authored rules survive upgrade
        byte-identical — never overlaid, never pruned."""
        sentinel = b"# Project rule\n\nGrep our own rules dir before designing.\n"
        rule = self.specfuse / "rules-local" / "our-project-rule.md"
        rule.parent.mkdir(exist_ok=True)
        rule.write_bytes(sentinel)

        upgrade_specfuse(self.target)

        self.assertTrue(rule.exists(),
                        "project-authored rules-local file must survive upgrade")
        self.assertEqual(rule.read_bytes(), sentinel,
                         "project-authored rules-local file must be untouched")

    def test_upgrade_seeds_rules_local_readme_when_absent(self):
        readme = self.specfuse / "rules-local" / "README.md"
        if readme.exists():
            readme.unlink()
            readme.parent.rmdir()
        written = upgrade_specfuse(self.target)
        self.assertTrue(readme.exists())
        self.assertIn("rules-local/README.md", written)

    def test_upgrade_never_overwrites_edited_rules_local_readme(self):
        sentinel = b"project-edited readme"
        readme = self.specfuse / "rules-local" / "README.md"
        readme.parent.mkdir(exist_ok=True)
        readme.write_bytes(sentinel)
        upgrade_specfuse(self.target)
        self.assertEqual(readme.read_bytes(), sentinel,
                         "seeded README is project-owned after init — "
                         "upgrade must not overwrite it")

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
