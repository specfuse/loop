# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""Tests for wire_claude / init wiring (FEAT-2026-0026/T05).

AC1: test_wiring_is_merge_safe is the red test — it fails on HEAD before
wire_claude exists (ImportError / missing symbol) and passes after.
AC6: test_wiring_writes_all_surfaces paired with it.
"""

import json
import pathlib
import tempfile
import unittest


class TestWiringCore(unittest.TestCase):
    """AC1, AC2, AC3, AC4, AC5, AC6 — core red test and all-surfaces check."""

    def test_wiring_is_merge_safe(self):
        """Red test: import fails if wire_claude absent; passes when idempotent."""
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)

            wire_claude(target)
            wire_claude(target)  # second call must be a no-op

            # .gitignore: sentinel line appears exactly once
            gitignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(gitignore_text.count(".specfuse/.loop.lock"), 1)

            # CLAUDE.md: sentinel rule import appears exactly once
            claude_md_text = (target / ".claude" / "CLAUDE.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                claude_md_text.count("@.specfuse/rules/result-contract.md"), 1
            )

            # settings.json: allow entries appear exactly once
            data = json.loads(
                (target / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            allow = data["permissions"]["allow"]
            self.assertEqual(allow.count("Bash(specfuse:*)"), 1)

    def test_wiring_writes_all_surfaces(self):
        """AC2, AC4, AC5: all surfaces written with correct content; no symlinks."""
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)

            # --- .gitignore ---
            gitignore_text = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".specfuse/.loop.lock", gitignore_text)
            self.assertIn(".specfuse/.scratch-*", gitignore_text)
            self.assertIn(".specfuse/scripts/__pycache__/", gitignore_text)

            # --- .claude/CLAUDE.md ---
            claude_md = (target / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            for rule in (
                "result-contract.md",
                "correlation-ids.md",
                "never-touch.md",
                "security-boundaries.md",
            ):
                self.assertIn(f"@.specfuse/rules/{rule}", claude_md)

            # --- .claude/settings.json — valid JSON ---
            raw = (target / ".claude" / "settings.json").read_text(encoding="utf-8")
            data = json.loads(raw)  # must not raise

            # Bash allowlist (pip-native commands, AC2)
            allow = data["permissions"]["allow"]
            self.assertIn("Bash(specfuse:*)", allow)

            # Marketplace identifier (AC4)
            self.assertIn("specfuse", data["extraKnownMarketplaces"])
            mkt = data["extraKnownMarketplaces"]["specfuse"]
            self.assertEqual(mkt["source"]["source"], "github")
            self.assertEqual(mkt["source"]["repo"], "specfuse/specfuse")

            # Plugin identifier (AC4)
            self.assertIn("specfuse@specfuse", data["enabledPlugins"])
            self.assertTrue(data["enabledPlugins"]["specfuse@specfuse"])

            # No symlinks under .claude/ (AC5)
            claude_dir = target / ".claude"
            for path in claude_dir.rglob("*"):
                self.assertFalse(
                    path.is_symlink(), f"unexpected symlink: {path}"
                )


class TestWiringMergeSafeExistingContent(unittest.TestCase):
    """AC3: merge-safe when user content already exists on each surface."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_existing_gitignore_user_lines_preserved(self):
        from specfuse.loop.scaffold import wire_claude

        gitignore = self.target / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n", encoding="utf-8")
        wire_claude(self.target)
        text = gitignore.read_text(encoding="utf-8")
        self.assertIn("*.pyc", text)
        self.assertIn("__pycache__/", text)
        self.assertIn(".specfuse/.loop.lock", text)

    def test_existing_gitignore_no_duplicate_when_sentinel_present(self):
        from specfuse.loop.scaffold import wire_claude

        gitignore = self.target / ".gitignore"
        gitignore.write_text(
            "*.pyc\n.specfuse/.loop.lock\n.specfuse/.scratch-*\n", encoding="utf-8"
        )
        original = gitignore.read_text(encoding="utf-8")
        wire_claude(self.target)
        after = gitignore.read_text(encoding="utf-8")
        self.assertEqual(original, after)

    def test_existing_claude_md_user_content_preserved(self):
        from specfuse.loop.scaffold import wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("# My project\nSome user notes.\n", encoding="utf-8")
        wire_claude(self.target)
        text = claude_md.read_text(encoding="utf-8")
        self.assertIn("My project", text)
        self.assertIn("Some user notes.", text)
        self.assertIn("@.specfuse/rules/result-contract.md", text)

    def test_existing_claude_md_no_duplicate_when_sentinel_present(self):
        """The sentinel suppresses re-appending the block, not the backfill.

        A project whose CLAUDE.md predates a rule must still gain that rule's
        import — otherwise the scaffold ships a binding rule the project never
        loads. So the guarantee here is *no duplication and no clobbering*:
        the user's own content survives, the block is not appended a second
        time, and every import appears exactly once.
        """
        from specfuse.loop.scaffold import _RULES_BLOCK, wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text(
            "# Project\n@.specfuse/rules/result-contract.md\n", encoding="utf-8"
        )
        wire_claude(self.target)
        after = claude_md.read_text(encoding="utf-8")

        self.assertIn("# Project", after)
        self.assertNotIn(
            "## Specfuse binding rules", after,
            "the block header was appended even though the sentinel was present",
        )
        for line in _RULES_BLOCK.splitlines():
            if line.startswith("@.specfuse/rules/"):
                with self.subTest(rule=line):
                    self.assertEqual(after.count(line), 1)

    def test_existing_claude_md_wiring_is_idempotent(self):
        from specfuse.loop.scaffold import wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text(
            "# Project\n@.specfuse/rules/result-contract.md\n", encoding="utf-8"
        )
        wire_claude(self.target)
        once = claude_md.read_text(encoding="utf-8")
        wire_claude(self.target)
        self.assertEqual(once, claude_md.read_text(encoding="utf-8"))

    def test_existing_settings_json_user_keys_preserved(self):
        from specfuse.loop.scaffold import wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        settings = claude_dir / "settings.json"
        settings.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
        wire_claude(self.target)
        data = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "dark")
        self.assertIn("Bash(specfuse:*)", data["permissions"]["allow"])

    def test_existing_settings_json_allow_entries_not_duplicated(self):
        from specfuse.loop.scaffold import wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        settings = claude_dir / "settings.json"
        settings.write_text(
            json.dumps(
                {"permissions": {"allow": ["Bash(specfuse:*)"]}}
            ),
            encoding="utf-8",
        )
        wire_claude(self.target)
        data = json.loads(settings.read_text(encoding="utf-8"))
        allow = data["permissions"]["allow"]
        self.assertEqual(allow.count("Bash(specfuse:*)"), 1)

    def test_existing_settings_json_legacy_flat_allow_entries_preserved(self):
        """A repo wired before the subcommand migration keeps its old entries.

        `Bash(specfuse-loop:*)` / `Bash(specfuse-lint:*)` still authorise the
        deprecated flat aliases, which keep working until 1.0.0. The merge is
        additive, so upgrading such a repo gains `Bash(specfuse:*)` without
        revoking anything it already had.
        """
        from specfuse.loop.scaffold import wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        settings = claude_dir / "settings.json"
        settings.write_text(
            json.dumps(
                {"permissions": {"allow": ["Bash(specfuse-loop:*)", "Bash(specfuse-lint:*)"]}}
            ),
            encoding="utf-8",
        )
        wire_claude(self.target)
        allow = json.loads(settings.read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertIn("Bash(specfuse-loop:*)", allow)
        self.assertIn("Bash(specfuse-lint:*)", allow)
        self.assertIn("Bash(specfuse:*)", allow)

    def test_existing_settings_json_user_allow_entries_preserved(self):
        from specfuse.loop.scaffold import wire_claude

        claude_dir = self.target / ".claude"
        claude_dir.mkdir(parents=True)
        settings = claude_dir / "settings.json"
        settings.write_text(
            json.dumps({"permissions": {"allow": ["Bash(npm:*)"]}}),
            encoding="utf-8",
        )
        wire_claude(self.target)
        data = json.loads(settings.read_text(encoding="utf-8"))
        allow = data["permissions"]["allow"]
        self.assertIn("Bash(npm:*)", allow)
        self.assertIn("Bash(specfuse:*)", allow)


class TestWiringNewFiles(unittest.TestCase):
    """AC2: correct content when no files exist yet."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.target = pathlib.Path(self._tmpdir.name)
        from specfuse.loop.scaffold import wire_claude

        wire_claude(self.target)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_gitignore_created(self):
        self.assertTrue((self.target / ".gitignore").exists())

    def test_claude_md_created(self):
        self.assertTrue((self.target / ".claude" / "CLAUDE.md").exists())

    def test_settings_json_created(self):
        self.assertTrue((self.target / ".claude" / "settings.json").exists())

    def test_settings_json_is_valid_json(self):
        raw = (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        data = json.loads(raw)
        self.assertIsInstance(data, dict)

    def test_settings_json_marketplace_shape(self):
        data = json.loads(
            (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        mkt = data["extraKnownMarketplaces"]["specfuse"]
        self.assertEqual(
            mkt,
            {"source": {"source": "github", "repo": "specfuse/specfuse"}},
        )

    def test_settings_json_plugin_enabled(self):
        data = json.loads(
            (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        self.assertTrue(data["enabledPlugins"]["specfuse@specfuse"])

    def test_gitignore_no_trailing_blank_before_snippet(self):
        # When .gitignore didn't exist, snippet is written verbatim (no leading newline)
        text = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertFalse(text.startswith("\n"))


class TestWiringGitignoreExistingNoNewline(unittest.TestCase):
    """Edge case: existing .gitignore with no trailing newline."""

    def test_appended_snippet_starts_on_own_line(self):
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            gitignore = target / ".gitignore"
            gitignore.write_text("*.pyc", encoding="utf-8")  # no trailing \n
            wire_claude(target)
            text = gitignore.read_text(encoding="utf-8")
            self.assertIn("\n.specfuse/.loop.lock", text)


class TestInitOrchestrator(unittest.TestCase):
    """AC7: init() = init_specfuse() + wire_claude()."""

    def test_init_writes_specfuse_and_claude(self):
        from specfuse.loop.scaffold import init

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            written = init(target)

            # init_specfuse side
            self.assertIn("VERSION", written)
            self.assertTrue((target / ".specfuse").is_dir())

            # wire_claude side
            self.assertTrue((target / ".claude" / "CLAUDE.md").exists())
            self.assertTrue((target / ".claude" / "settings.json").exists())
            self.assertIn(
                ".specfuse/.loop.lock",
                (target / ".gitignore").read_text(encoding="utf-8"),
            )

    def test_init_returns_sorted_specfuse_relpaths(self):
        from specfuse.loop.scaffold import init

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            written = init(target)
            self.assertEqual(written, sorted(written))
            self.assertIn("VERSION", written)

    def test_init_forwards_ci_check(self):
        """ci_check is accepted without error (wired in a later WU)."""
        from specfuse.loop.scaffold import init

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            written = init(target, ci_check="python3 -m pytest")
            self.assertIn("VERSION", written)

    def test_init_combined_settings_valid_json(self):
        from specfuse.loop.scaffold import init

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            init(target)
            data = json.loads(
                (target / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            self.assertIn("specfuse@specfuse", data["enabledPlugins"])


if __name__ == "__main__":
    unittest.main()


class TestChangelogSeed(unittest.TestCase):
    """#575 — init must leave a CHANGELOG.md that close-k can satisfy.

    `close-k` fails a close whose §3 enumeration names a real change unless
    `CHANGELOG.md`'s Unreleased gained an entry. `specfuse init` never created
    the file, so a fresh downstream project's first feature with any
    consumer-visible change failed at its terminal close on a file the
    scaffold owed it.
    """

    def test_wire_claude_seeds_changelog(self):
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            self.assertTrue(
                (target / "CHANGELOG.md").exists(),
                "wire_claude left no CHANGELOG.md for close-k to read",
            )

    def test_seeded_changelog_parses_clean_and_has_unreleased(self):
        """The seed is a contract: it ships into every downstream project."""
        from specfuse.loop.changelog import parse_changelog
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            result = parse_changelog(
                (target / "CHANGELOG.md").read_text(encoding="utf-8")
            )
            self.assertEqual(result.findings, [], f"seed rejected: {result.findings}")
            self.assertIsNotNone(result.unreleased(), "seed has no Unreleased section")

    def test_seeded_changelog_accepts_an_append(self):
        """A close must be able to append to the seed without editing it first."""
        from specfuse.loop.changelog import append_entry, parse_changelog
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            wire_claude(target)
            path = target / "CHANGELOG.md"
            path.write_text(
                append_entry(
                    path.read_text(encoding="utf-8"),
                    entry_class="added", summary="a thing", trace="FEAT-2026-0001",
                ),
                encoding="utf-8",
            )
            result = parse_changelog(path.read_text(encoding="utf-8"))
            self.assertEqual(result.findings, [])
            self.assertEqual(
                [e.trace for e in result.unreleased().entries], ["FEAT-2026-0001"]
            )

    def test_existing_changelog_is_never_overwritten(self):
        """Upgrade routes through wire_claude too; a project's own file wins."""
        from specfuse.loop.scaffold import wire_claude

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            own = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- mine (#1)\n"
            (target / "CHANGELOG.md").write_text(own, encoding="utf-8")
            wire_claude(target)
            wire_claude(target)
            self.assertEqual(
                (target / "CHANGELOG.md").read_text(encoding="utf-8"), own
            )

    def test_init_end_to_end_leaves_a_changelog(self):
        """The failure in #575 was reported against `init`, so assert on `init`."""
        from specfuse.loop.scaffold import init

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            init(target, no_labels=True)
            self.assertTrue((target / "CHANGELOG.md").exists())
