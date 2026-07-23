# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""End-to-end integration tests for upgrade_specfuse (FEAT-2026-0026/T09).

Uses a real init() to lay the baseline — so .claude wiring is already in place —
then mutates the tree, runs upgrade_specfuse, and asserts the post-state.

AC1: Versioned refresh — versioned files byte-faithful to seed; VERSION stamped.
AC2: User-authored untouched — sentinel content in LEARNINGS.md, verification.yml,
     roadmap.md, and a features/ file is byte-unchanged after upgrade.
AC3: Prune removed-versioned — stray rules/obsolete.md gone after upgrade;
     scripts/ and skills/ dirs left intact.
AC4: Never-downgrade — newer VERSION raises ScaffoldDowngradeError; tree untouched.
AC5: .claude refreshed + idempotent — wiring present after upgrade; second upgrade
     produces no duplicate gitignore lines and leaves settings.json stable.
AC6: Installed-wheel resolution (skip-guarded when build toolchain is absent).
"""

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

from specfuse.loop.scaffold import (
    ScaffoldDowngradeError,
    init,
    read_scaffold,
    scaffold_version,
    upgrade_specfuse,
)

_REPO_ROOT = pathlib.Path(__file__).parent.parent

# Versioned relpaths that upgrade_specfuse overlays verbatim into .specfuse/<relpath>
_VERSIONED_OVERLAY = {
    "templates/GATE.template.md",
    "templates/PLAN.template.md",
    "templates/WU.template.md",
    "rules/correlation-ids.md",
    "rules/never-touch.md",
    "rules/result-contract.md",
    "rules/security-boundaries.md",
    "VERSION",
    "verification.yml.example",
}


def _wheel_skip_reason():
    if not (_REPO_ROOT / "pyproject.toml").exists():
        return "pyproject.toml not found at repo root"
    if importlib.util.find_spec("pip") is None:
        return "pip not importable"
    if importlib.util.find_spec("setuptools") is None:
        return "setuptools not installed locally — wheel build requires network access"
    return None


_WHEEL_SKIP_REASON = _wheel_skip_reason()


class TestUpgradeVersionedRefresh(unittest.TestCase):
    """AC1: Versioned files restored to seed bytes; VERSION stamped after upgrade."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.sf = self.target / ".specfuse"
        init(self.target)
        # Stamp an older VERSION so the downgrade guard passes cleanly
        (self.sf / "VERSION").write_text("0.0.1\n", encoding="utf-8")

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_mutated_versioned_file_restored(self):
        victim = self.sf / "rules" / "result-contract.md"
        victim.write_bytes(b"# stale content written by test\n")
        upgrade_specfuse(self.target)
        self.assertEqual(victim.read_bytes(), read_scaffold("rules/result-contract.md"))

    def test_all_versioned_files_byte_faithful_after_upgrade(self):
        upgrade_specfuse(self.target)
        for relpath in _VERSIONED_OVERLAY:
            dest = self.sf / relpath
            self.assertTrue(dest.exists(), f"{relpath} missing after upgrade")
            self.assertEqual(
                dest.read_bytes(),
                read_scaffold(relpath),
                f"{relpath} differs from seed after upgrade",
            )

    def test_version_equals_scaffold_version_after_upgrade(self):
        upgrade_specfuse(self.target)
        v = (self.sf / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(v, scaffold_version())

    def test_upgrade_returns_sorted_list(self):
        written = upgrade_specfuse(self.target)
        self.assertEqual(written, sorted(written))


class TestUpgradeUserAuthoredUntouched(unittest.TestCase):
    """AC2: User-authored files are byte-unchanged after upgrade."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.sf = self.target / ".specfuse"
        init(self.target)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _plant(self, relpath: str, content: bytes) -> pathlib.Path:
        dest = self.sf / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        return dest

    def test_learnings_md_untouched(self):
        sentinel = b"# sentinel LEARNINGS - must survive upgrade\n"
        p = self._plant("LEARNINGS.md", sentinel)
        upgrade_specfuse(self.target)
        self.assertEqual(p.read_bytes(), sentinel)

    def test_verification_yml_untouched(self):
        sentinel = b"# sentinel verification.yml - must survive upgrade\n"
        p = self._plant("verification.yml", sentinel)
        upgrade_specfuse(self.target)
        self.assertEqual(p.read_bytes(), sentinel)

    def test_roadmap_md_untouched(self):
        sentinel = b"# sentinel roadmap.md - must survive upgrade\n"
        p = self._plant("roadmap.md", sentinel)
        upgrade_specfuse(self.target)
        self.assertEqual(p.read_bytes(), sentinel)

    def test_feature_file_untouched(self):
        sentinel = b"# sentinel feature file - must survive upgrade\n"
        p = self._plant("features/MY-FEATURE/PLAN.md", sentinel)
        upgrade_specfuse(self.target)
        self.assertEqual(p.read_bytes(), sentinel)


class TestUpgradePruneAndPreserve(unittest.TestCase):
    """AC3: Stray versioned files pruned; non-versioned dirs left intact."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.sf = self.target / ".specfuse"
        init(self.target)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_stray_rules_file_pruned(self):
        """Manifest-owned rules file the seed no longer ships is pruned;
        an unmanaged file would be kept (#214, covered in
        test_scaffold_upgrade)."""
        import json as _json
        stray = self.sf / "rules" / "obsolete.md"
        stray.write_bytes(b"# no longer shipped by seed\n")
        manifest = self.sf / ".scaffold-manifest"
        entries = _json.loads(manifest.read_text())
        entries["rules/obsolete.md"] = "0" * 64
        manifest.write_text(_json.dumps(entries))
        upgrade_specfuse(self.target)
        self.assertFalse(stray.exists(), "stray versioned file must be pruned")

    def test_scripts_dir_left_intact(self):
        scripts_dir = self.sf / "scripts"
        scripts_dir.mkdir()
        sentinel = scripts_dir / "my-script.sh"
        sentinel.write_bytes(b"#!/bin/sh\necho hello\n")
        upgrade_specfuse(self.target)
        self.assertTrue(sentinel.exists(), "scripts/ must survive upgrade")

    def test_skills_dir_left_intact(self):
        skills_dir = self.sf / "skills"
        skills_dir.mkdir()
        sentinel = skills_dir / "my-skill.md"
        sentinel.write_bytes(b"# my skill\n")
        upgrade_specfuse(self.target)
        self.assertTrue(sentinel.exists(), "skills/ must survive upgrade")


class TestUpgradeNeverDowngrade(unittest.TestCase):
    """AC4: Newer VERSION in target raises ScaffoldDowngradeError; tree untouched."""

    def test_raises_downgrade_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            init(target)
            (target / ".specfuse" / "VERSION").write_text("99.99.99\n", encoding="utf-8")
            with self.assertRaises(ScaffoldDowngradeError):
                upgrade_specfuse(target)

    def test_tree_untouched_on_downgrade_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            init(target)
            sf = target / ".specfuse"
            sf.joinpath("VERSION").write_text("99.99.99\n", encoding="utf-8")
            victim = sf / "rules" / "result-contract.md"
            stale = b"# stale - upgrade must not restore this\n"
            victim.write_bytes(stale)

            try:
                upgrade_specfuse(target)
            except ScaffoldDowngradeError:
                pass

            self.assertEqual(victim.read_bytes(), stale, "versioned file was modified despite downgrade refusal")
            self.assertEqual(
                (sf / "VERSION").read_text(encoding="utf-8").strip(),
                "99.99.99",
                "VERSION was modified despite downgrade refusal",
            )


class TestUpgradeClaudeRefreshedIdempotent(unittest.TestCase):
    """AC5: .claude wiring present after upgrade; second upgrade is a no-op."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.sf = self.target / ".specfuse"
        init(self.target)
        (self.sf / "VERSION").write_text("0.0.1\n", encoding="utf-8")

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_claude_md_rules_block_present_after_upgrade(self):
        upgrade_specfuse(self.target)
        text = (self.target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        for rule in (
            "result-contract.md",
            "correlation-ids.md",
            "never-touch.md",
            "security-boundaries.md",
        ):
            self.assertIn(f"@.specfuse/rules/{rule}", text)

    def test_settings_allowlist_present_after_upgrade(self):
        upgrade_specfuse(self.target)
        data = json.loads(
            (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        allow = data["permissions"]["allow"]
        self.assertIn("Bash(specfuse-loop:*)", allow)
        self.assertIn("Bash(specfuse-lint:*)", allow)

    def test_gitignore_runtime_lines_present_after_upgrade(self):
        upgrade_specfuse(self.target)
        text = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".specfuse/.loop.lock", text)
        self.assertIn(".specfuse/.scratch-*", text)

    def test_gitignore_no_duplicate_lines_on_second_upgrade(self):
        upgrade_specfuse(self.target)
        upgrade_specfuse(self.target)
        text = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(text.count(".specfuse/.loop.lock"), 1)
        self.assertEqual(text.count(".specfuse/.scratch-*"), 1)

    def test_settings_json_stable_on_second_upgrade(self):
        upgrade_specfuse(self.target)
        first = (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        upgrade_specfuse(self.target)
        second = (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        self.assertEqual(first, second)

    def test_claude_md_no_duplicate_rules_block_on_second_upgrade(self):
        upgrade_specfuse(self.target)
        upgrade_specfuse(self.target)
        text = (self.target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("@.specfuse/rules/result-contract.md"), 1)


class TestUpgradeInstalledWheelResolution(unittest.TestCase):
    """AC6: upgrade() resolves package data from an installed wheel, not the source tree.

    Skip-guarded when pyproject.toml is absent or pip/setuptools is unavailable.
    """

    @unittest.skipIf(
        _WHEEL_SKIP_REASON is not None,
        _WHEEL_SKIP_REASON or "build toolchain unavailable",
    )
    def test_upgrade_from_installed_wheel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            wheel_dir = tmp / "dist"
            wheel_dir.mkdir()
            venv_dir = tmp / "venv"
            target_dir = tmp / "target_repo"
            target_dir.mkdir()

            build_result = subprocess.run(
                [
                    sys.executable, "-m", "pip", "wheel", ".",
                    "--no-deps", "--wheel-dir", str(wheel_dir), "--quiet",
                ],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                build_result.returncode, 0,
                f"wheel build failed:\n{build_result.stdout}\n{build_result.stderr}",
            )

            wheels = list(wheel_dir.glob("*.whl"))
            self.assertEqual(len(wheels), 1, f"expected 1 wheel, got {wheels}")
            wheel_path = wheels[0]

            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
            )

            if sys.platform == "win32":
                venv_python = venv_dir / "Scripts" / "python.exe"
            else:
                venv_python = venv_dir / "bin" / "python"

            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--quiet", str(wheel_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            # init, mutate a versioned file, stamp older VERSION, then upgrade
            script = textwrap.dedent(f"""
                import json, pathlib
                from specfuse.loop.scaffold import (
                    init, upgrade_specfuse, scaffold_version, read_scaffold
                )
                target = pathlib.Path({str(target_dir)!r})
                sf = target / ".specfuse"

                init(target)
                (sf / "VERSION").write_text("0.0.1\\n", encoding="utf-8")
                victim = sf / "rules" / "result-contract.md"
                victim.write_bytes(b"# stale\\n")

                written = upgrade_specfuse(target)

                result = {{
                    "written": written,
                    "version": (sf / "VERSION").read_text(encoding="utf-8").strip(),
                    "scaffold_version": scaffold_version(),
                    "versioned_restored": victim.read_bytes() != b"# stale\\n",
                    "learnings_exists": (sf / "LEARNINGS.md").exists(),
                    "claude_md": (target / ".claude" / "CLAUDE.md").read_text(),
                    "gitignore": (target / ".gitignore").read_text(),
                    "ok": (target / ".specfuse").is_dir(),
                }}
                print(json.dumps(result))
            """).strip()

            proc = subprocess.run(
                [str(venv_python), "-c", script],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                proc.returncode, 0,
                f"upgrade from installed wheel failed:\n{proc.stdout}\n{proc.stderr}",
            )

            result = json.loads(proc.stdout.strip())

            self.assertTrue(result["ok"], ".specfuse/ not present after wheel upgrade")
            self.assertEqual(
                result["version"],
                result["scaffold_version"],
                "VERSION not stamped to scaffold_version after wheel upgrade",
            )
            self.assertTrue(
                result["versioned_restored"],
                "versioned file not restored from wheel seed",
            )
            self.assertTrue(result["learnings_exists"], "LEARNINGS.md missing after upgrade")
            self.assertIn("@.specfuse/rules/result-contract.md", result["claude_md"])
            self.assertIn(".specfuse/.loop.lock", result["gitignore"])


if __name__ == "__main__":
    unittest.main()
