# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

import json
import pathlib
import shutil
import tempfile
import unittest

from specfuse.loop.scaffold import migrate_legacy


def _make_target() -> tuple[pathlib.Path, str]:
    tmpdir = tempfile.mkdtemp()
    target = pathlib.Path(tmpdir)
    (target / ".specfuse" / "scripts").mkdir(parents=True, exist_ok=True)
    (target / ".specfuse" / "skills").mkdir(parents=True, exist_ok=True)
    return target, tmpdir


def _write_verification_yml(specfuse_dir: pathlib.Path, content: str) -> None:
    (specfuse_dir / "verification.yml").write_text(content, encoding="utf-8")


def _write_settings_json(target: pathlib.Path, data: dict) -> None:
    claude_dir = target / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "settings.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


class TestMigrateLegacy(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.specfuse_dir = self.target / ".specfuse"
        self.scripts_dir = self.specfuse_dir / "scripts"
        self.skills_dir = self.specfuse_dir / "skills"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write_yml(self, content: str) -> None:
        _write_verification_yml(self.specfuse_dir, content)

    def _write_settings(self, data: dict) -> None:
        _write_settings_json(self.target, data)

    # ------------------------------------------------------------------
    # AC1: red test — script referenced in verification.yml survives
    # ------------------------------------------------------------------

    def test_keeps_live_shims(self):
        (self.scripts_dir / "lint_plan.py").write_bytes(b"# live shim")
        (self.scripts_dir / "dead_script.py").write_bytes(b"# legacy")
        self._write_yml(
            "plannext:\n"
            "  - name: plan-lint\n"
            "    command: \"python3 .specfuse/scripts/lint_plan.py {feature_dir}\"\n"
        )

        result = migrate_legacy(self.target)

        self.assertIn("scripts/dead_script.py", result)
        self.assertNotIn("scripts/lint_plan.py", result)
        self.assertTrue((self.scripts_dir / "lint_plan.py").exists())
        self.assertFalse((self.scripts_dir / "dead_script.py").exists())

    # ------------------------------------------------------------------
    # AC2/AC3: prune legacy, keep referenced
    # ------------------------------------------------------------------

    def test_prunes_unreferenced_script(self):
        (self.scripts_dir / "old_bootstrap.sh").write_bytes(b"#!/bin/sh")
        self._write_yml(
            "code:\n"
            "  - name: tests\n"
            "    command: \"python3 -m unittest\"\n"
        )

        result = migrate_legacy(self.target)

        self.assertIn("scripts/old_bootstrap.sh", result)
        self.assertFalse((self.scripts_dir / "old_bootstrap.sh").exists())

    def test_keeps_script_referenced_in_settings_allow(self):
        (self.scripts_dir / "loop.py").write_bytes(b"# loop shim")
        (self.scripts_dir / "dead.py").write_bytes(b"# dead")
        self._write_yml(
            "code:\n"
            "  - name: tests\n"
            "    command: \"python3 -m unittest\"\n"
        )
        self._write_settings({
            "permissions": {
                "allow": ["Bash(python3 .specfuse/scripts/loop.py:*)"]
            }
        })

        result = migrate_legacy(self.target)

        self.assertNotIn("scripts/loop.py", result)
        self.assertIn("scripts/dead.py", result)
        self.assertTrue((self.scripts_dir / "loop.py").exists())
        self.assertFalse((self.scripts_dir / "dead.py").exists())

    def test_keeps_script_referenced_in_both_sources(self):
        (self.scripts_dir / "lint_plan.py").write_bytes(b"# shim")
        self._write_yml(
            "plannext:\n"
            "  - name: lint\n"
            "    command: \"python3 .specfuse/scripts/lint_plan.py {feature_dir}\"\n"
        )
        self._write_settings({
            "permissions": {
                "allow": ["Bash(python3 .specfuse/scripts/lint_plan.py:*)"]
            }
        })

        result = migrate_legacy(self.target)

        self.assertEqual(result, [])
        self.assertTrue((self.scripts_dir / "lint_plan.py").exists())

    def test_prunes_skills_freely(self):
        (self.skills_dir / "some-skill.md").write_bytes(b"# old skill")
        (self.skills_dir / "other.md").write_bytes(b"# other")
        self._write_yml(
            "code:\n"
            "  - name: tests\n"
            "    command: \"python3 -m unittest\"\n"
        )

        result = migrate_legacy(self.target)

        self.assertIn("skills/some-skill.md", result)
        self.assertIn("skills/other.md", result)
        self.assertFalse((self.skills_dir / "some-skill.md").exists())

    # ------------------------------------------------------------------
    # AC3: unparseable verification.yml refuses with no deletions
    # ------------------------------------------------------------------

    def test_unparseable_verification_yml_refuses_and_leaves_files(self):
        (self.scripts_dir / "dead_script.py").write_bytes(b"# legacy")
        # single-quoted strings are rejected by _miniyaml
        (self.specfuse_dir / "verification.yml").write_bytes(
            b"code:\n  - name: t\n    command: 'single-quoted'\n"
        )

        with self.assertRaises(Exception):
            migrate_legacy(self.target)

        self.assertTrue((self.scripts_dir / "dead_script.py").exists())

    def test_unparseable_settings_json_refuses_and_leaves_files(self):
        (self.scripts_dir / "dead_script.py").write_bytes(b"# legacy")
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )
        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "settings.json").write_bytes(b"{broken json")

        with self.assertRaises(Exception):
            migrate_legacy(self.target)

        self.assertTrue((self.scripts_dir / "dead_script.py").exists())

    # ------------------------------------------------------------------
    # AC4: dry_run deletes nothing
    # ------------------------------------------------------------------

    def test_dry_run_deletes_nothing(self):
        (self.scripts_dir / "old_script.py").write_bytes(b"# legacy")
        (self.skills_dir / "old_skill.md").write_bytes(b"# old skill")
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )

        result_dry = migrate_legacy(self.target, dry_run=True)

        self.assertIn("scripts/old_script.py", result_dry)
        self.assertIn("skills/old_skill.md", result_dry)
        self.assertTrue((self.scripts_dir / "old_script.py").exists())
        self.assertTrue((self.skills_dir / "old_skill.md").exists())

    def test_dry_run_returns_same_list_as_real_run(self):
        (self.scripts_dir / "old_script.py").write_bytes(b"# legacy")
        (self.skills_dir / "old_skill.md").write_bytes(b"# old skill")
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )

        dry_result = migrate_legacy(self.target, dry_run=True)
        real_result = migrate_legacy(self.target)

        self.assertEqual(dry_result, real_result)

    # ------------------------------------------------------------------
    # AC5: idempotent + absent dirs no-op
    # ------------------------------------------------------------------

    def test_idempotent_second_run_returns_empty(self):
        (self.scripts_dir / "dead_script.py").write_bytes(b"# legacy")
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )

        first = migrate_legacy(self.target)
        self.assertIn("scripts/dead_script.py", first)

        second = migrate_legacy(self.target)
        self.assertEqual(second, [])

    def test_absent_scripts_dir_no_op(self):
        shutil.rmtree(self.scripts_dir)
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )

        result = migrate_legacy(self.target)

        self.assertEqual(result, [])

    def test_absent_skills_dir_no_op(self):
        shutil.rmtree(self.skills_dir)
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )

        result = migrate_legacy(self.target)

        self.assertEqual(result, [])

    def test_absent_both_dirs_no_op(self):
        shutil.rmtree(self.scripts_dir)
        shutil.rmtree(self.skills_dir)

        result = migrate_legacy(self.target)

        self.assertEqual(result, [])

    def test_absent_verification_yml_no_error(self):
        (self.scripts_dir / "old.py").write_bytes(b"# legacy")
        # No verification.yml written

        result = migrate_legacy(self.target)

        self.assertIn("scripts/old.py", result)

    def test_result_is_sorted(self):
        for name in ["z_script.py", "a_script.py", "m_script.py"]:
            (self.scripts_dir / name).write_bytes(b"# legacy")
        self._write_yml(
            "code:\n  - name: tests\n    command: \"python3 -m unittest\"\n"
        )

        result = migrate_legacy(self.target)

        self.assertEqual(result, sorted(result))


if __name__ == "__main__":
    unittest.main()
