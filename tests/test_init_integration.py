# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""End-to-end integration tests for init_specfuse + wire_claude (FEAT-2026-0026/T06).

AC1: Full layout assertion — both init_specfuse and wire_claude in one combined call.
AC2: Refusal — second init raises ScaffoldExistsError, tree left untouched.
AC3: Idempotency — re-running wire_claude on an already-wired repo is a no-op.
AC4: .gitignore exact-snippet match; settings.json marketplace/plugin identifiers correct.
AC5: Installed-wheel resolution (skip-guarded when pyproject.toml or pip absent).
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
    ScaffoldExistsError,
    init,
    init_specfuse,
    read_scaffold,
    scaffold_version,
    wire_claude,
)

_REPO_ROOT = pathlib.Path(__file__).parent.parent

_EXPECTED_SPECFUSE_TREE = {
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
    "docs/concepts/architecture-addendum-gates-and-iterative-planning.md",
    "docs/concepts/ralph-lineage.md",
    "docs/getting-started.md",
    "docs/methodology.md",
    "docs/skills.md",
}

_GITIGNORE_SNIPPET = read_scaffold("gitignore.snippet").decode("utf-8")


def _wheel_skip_reason():
    if not (_REPO_ROOT / "pyproject.toml").exists():
        return "pyproject.toml not found at repo root"
    if importlib.util.find_spec("pip") is None:
        return "pip not importable"
    # pip wheel . fetches setuptools as a build dep; without it locally and
    # without network access the build fails. Skip rather than error.
    if importlib.util.find_spec("setuptools") is None:
        return "setuptools not installed locally — wheel build requires network access"
    return None


_WHEEL_SKIP_REASON = _wheel_skip_reason()


class TestInitFullLayout(unittest.TestCase):
    """AC1: Full combined layout after init() = init_specfuse + wire_claude."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        self.written = init(self.target)
        self.sf = self.target / ".specfuse"
        self.claude = self.target / ".claude"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_specfuse_tree_complete(self):
        self.assertEqual(set(self.written), _EXPECTED_SPECFUSE_TREE)

    def test_templates_dir_present(self):
        self.assertTrue((self.sf / "templates").is_dir())

    def test_rules_dir_present(self):
        self.assertTrue((self.sf / "rules").is_dir())

    def test_version_equals_scaffold_version(self):
        v = (self.sf / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(v, scaffold_version())

    def test_templates_byte_faithful(self):
        for rel in (
            "templates/GATE.template.md",
            "templates/PLAN.template.md",
            "templates/WU.template.md",
        ):
            self.assertTrue((self.sf / rel).exists(), f"{rel} not written")
            self.assertEqual(
                (self.sf / rel).read_bytes(),
                read_scaffold(rel),
                f"{rel} differs from seed",
            )

    def test_rules_byte_faithful(self):
        for rel in (
            "rules/correlation-ids.md",
            "rules/never-touch.md",
            "rules/result-contract.md",
            "rules/security-boundaries.md",
        ):
            self.assertTrue((self.sf / rel).exists(), f"{rel} not written")
            self.assertEqual(
                (self.sf / rel).read_bytes(),
                read_scaffold(rel),
                f"{rel} differs from seed",
            )

    def test_roadmap_seeded_from_template(self):
        self.assertEqual(
            (self.sf / "roadmap.md").read_bytes(),
            read_scaffold("roadmap.template.md"),
        )

    def test_learnings_seeded_from_template(self):
        self.assertEqual(
            (self.sf / "LEARNINGS.md").read_bytes(),
            read_scaffold("LEARNINGS.template.md"),
        )

    def test_verification_yml_seeded_from_example(self):
        self.assertEqual(
            (self.sf / "verification.yml").read_bytes(),
            read_scaffold("verification.yml.example"),
        )

    def test_features_dir_present(self):
        self.assertTrue((self.sf / "features").is_dir())

    def test_claude_md_rules_block(self):
        text = (self.claude / "CLAUDE.md").read_text(encoding="utf-8")
        for rule in (
            "result-contract.md",
            "correlation-ids.md",
            "never-touch.md",
            "security-boundaries.md",
        ):
            self.assertIn(f"@.specfuse/rules/{rule}", text)

    def test_settings_allowlist(self):
        data = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))
        allow = data["permissions"]["allow"]
        self.assertIn("Bash(specfuse-loop:*)", allow)
        self.assertIn("Bash(specfuse-lint:*)", allow)

    def test_settings_marketplace(self):
        data = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))
        mkt = data["extraKnownMarketplaces"]["specfuse"]
        self.assertEqual(mkt["source"]["source"], "github")
        self.assertEqual(mkt["source"]["repo"], "specfuse/specfuse")

    def test_settings_plugin(self):
        data = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))
        self.assertTrue(data["enabledPlugins"]["specfuse@specfuse"])

    def test_gitignore_written(self):
        self.assertTrue((self.target / ".gitignore").exists())

    def test_gitignore_runtime_artifact_lines(self):
        text = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".specfuse/.loop.lock", text)
        self.assertIn(".specfuse/.scratch-*", text)
        self.assertIn(".specfuse/scripts/__pycache__/", text)

    def test_written_list_is_sorted(self):
        self.assertEqual(self.written, sorted(self.written))


class TestInitRefusal(unittest.TestCase):
    """AC2: Second init_specfuse raises ScaffoldExistsError; existing tree untouched."""

    def test_second_init_raises_scaffold_exists_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            init(target)
            sf = target / ".specfuse"

            before = {
                str(p.relative_to(sf)): p.read_bytes()
                for p in sf.rglob("*")
                if p.is_file()
            }

            with self.assertRaises(ScaffoldExistsError):
                init_specfuse(target)

            after = {
                str(p.relative_to(sf)): p.read_bytes()
                for p in sf.rglob("*")
                if p.is_file()
            }

            self.assertEqual(before, after, "tree mutated after refusal")

    def test_refusal_message_names_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".specfuse").mkdir()
            with self.assertRaises(ScaffoldExistsError) as ctx:
                init_specfuse(target)
            self.assertIn("specfuse upgrade", str(ctx.exception))


class TestWireClaudeIdempotency(unittest.TestCase):
    """AC3: Re-running wire_claude on an already-wired repo is a no-op."""

    def test_gitignore_no_duplicate_sentinel(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            wire_claude(target)
            text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(text.count(".specfuse/.loop.lock"), 1)

    def test_gitignore_no_duplicate_scratch_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            wire_claude(target)
            text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(text.count(".specfuse/.scratch-*"), 1)

    def test_settings_json_stable_on_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            first = (target / ".claude" / "settings.json").read_text(encoding="utf-8")
            wire_claude(target)
            second = (target / ".claude" / "settings.json").read_text(encoding="utf-8")
            self.assertEqual(first, second)

    def test_claude_md_no_duplicate_rules_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            wire_claude(target)
            text = (target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertEqual(text.count("@.specfuse/rules/result-contract.md"), 1)


class TestGitignoreAndPluginConfig(unittest.TestCase):
    """AC4: .gitignore contains exactly the snippet; settings.json identifiers correct."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        wire_claude(self.target)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_gitignore_equals_snippet_exactly(self):
        text = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(text, _GITIGNORE_SNIPPET)

    def test_settings_json_valid(self):
        raw = (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        self.assertIsInstance(data, dict)

    def test_settings_marketplace_repo_identifier(self):
        data = json.loads(
            (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            data["extraKnownMarketplaces"]["specfuse"]["source"]["repo"],
            "specfuse/specfuse",
        )

    def test_settings_plugin_identifier(self):
        data = json.loads(
            (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        self.assertIn("specfuse@specfuse", data["enabledPlugins"])
        self.assertTrue(data["enabledPlugins"]["specfuse@specfuse"])


class TestInstalledWheelResolution(unittest.TestCase):
    """AC5: init() resolves package data from an installed wheel, not the source tree.

    Skip-guarded when pyproject.toml is absent or pip is unavailable.
    """

    @unittest.skipIf(
        _WHEEL_SKIP_REASON is not None,
        _WHEEL_SKIP_REASON or "build toolchain unavailable",
    )
    def test_init_from_installed_wheel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            wheel_dir = tmp / "dist"
            wheel_dir.mkdir()
            venv_dir = tmp / "venv"
            target_dir = tmp / "target_repo"
            target_dir.mkdir()

            # Build wheel from source tree
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

            # Create clean venv (no access to source tree packages)
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
            )

            if sys.platform == "win32":
                venv_python = venv_dir / "Scripts" / "python.exe"
            else:
                venv_python = venv_dir / "bin" / "python"

            # Install wheel into venv
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--quiet", str(wheel_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Run init() from the venv — proves write path uses package data from wheel
            script = textwrap.dedent(f"""
                import json, pathlib
                from specfuse.loop.scaffold import init, scaffold_version
                target = pathlib.Path({str(target_dir)!r})
                written = init(target)
                result = {{
                    "written": written,
                    "version": scaffold_version(),
                    "claude_md": (target / ".claude" / "CLAUDE.md").read_text(),
                    "settings": (target / ".claude" / "settings.json").read_text(),
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
                f"init from installed wheel failed:\n{proc.stdout}\n{proc.stderr}",
            )

            result = json.loads(proc.stdout.strip())

            self.assertTrue(result["ok"], ".specfuse/ not created from wheel")
            self.assertIn("VERSION", result["written"])
            self.assertEqual(result["version"], scaffold_version())
            self.assertIn("@.specfuse/rules/result-contract.md", result["claude_md"])
            self.assertIn("specfuse@specfuse", result["settings"])
            self.assertIn(".specfuse/.loop.lock", result["gitignore"])


if __name__ == "__main__":
    unittest.main()
