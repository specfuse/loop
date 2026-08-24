#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0064/T03: release wiring for CHANGELOG.md.

Covers the WU's acceptance criteria: a stamped section refuses a later
append (1-2), stamping requires the umbrella version and writes it alongside
the driver version and date (3), a stamp leaves a fresh empty `Unreleased`
above the one just frozen (4), `bump_version.py` stamps in the same run that
sets the four version sources (5), the tag convention and version-source
list are configuration with this repo's values as defaults (6), and
stamping refuses to double-stamp the same version (7).
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.changelog import (
    append_entry,
    parse_changelog,
    split_version_field,
    stamp_release,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_bump_version():
    path = REPO_ROOT / "scripts" / "bump_version.py"
    spec = importlib.util.spec_from_file_location("bump_version_t03", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


bump_version = _load_bump_version()


def _unreleased_text():
    return (
        "## [Unreleased]\n"
        "\n"
        "### Added\n"
        "\n"
        "- a thing landed (FEAT-2026-0099/T01)\n"
    )


class TestChangelogReleaseWiring(unittest.TestCase):
    # -- criteria 1/2: a stamped section refuses a later append --

    def test_stamped_section_refuses_a_later_append(self):
        text = _unreleased_text()
        stamped = stamp_release(
            text, version="1.2.3", date="2026-08-04", umbrella_version="1.4.0",
        )
        with self.assertRaises(ValueError) as ctx:
            append_entry(
                stamped,
                entry_class="fixed",
                summary="a late append",
                trace="FEAT-2026-0100/T01",
                section="1.2.3+umbrella.1.4.0",
            )
        message = str(ctx.exception)
        self.assertIn("Unreleased", message)
        self.assertIn("only", message.lower())

        # The default target ("Unreleased") still works after a stamp.
        appended = append_entry(
            stamped,
            entry_class="fixed",
            summary="a well-aimed append",
            trace="FEAT-2026-0100/T01",
        )
        result = parse_changelog(appended)
        self.assertEqual(result.findings, [])
        unreleased = result.unreleased()
        self.assertEqual(len(unreleased.entries), 1)
        self.assertEqual(unreleased.entries[0].summary, "a well-aimed append")

    # -- criterion 3: version + date + umbrella version, and umbrella required --

    def test_stamp_writes_version_date_and_umbrella_version(self):
        stamped = stamp_release(
            _unreleased_text(),
            version="1.2.3",
            date="2026-08-04",
            umbrella_version="1.4.0",
        )
        result = parse_changelog(stamped)
        released = [s for s in result.sections if not s.is_unreleased]
        self.assertEqual(len(released), 1)
        section = released[0]
        version, umbrella = split_version_field(section.version)
        self.assertEqual(version, "1.2.3")
        self.assertEqual(umbrella, "1.4.0")
        self.assertEqual(section.date, "2026-08-04")

    def test_stamp_without_umbrella_version_is_refused(self):
        with self.assertRaises(ValueError) as ctx:
            stamp_release(
                _unreleased_text(), version="1.2.3", date="2026-08-04",
                umbrella_version="",
            )
        self.assertIn("umbrella_version", str(ctx.exception))

        with self.assertRaises(ValueError):
            stamp_release(
                _unreleased_text(), version="1.2.3", date="2026-08-04",
                umbrella_version=None,
            )

    # -- criterion 4: a fresh empty Unreleased is left above the stamp --

    def test_stamp_leaves_fresh_empty_unreleased_above(self):
        stamped = stamp_release(
            _unreleased_text(),
            version="1.2.3",
            date="2026-08-04",
            umbrella_version="1.4.0",
        )
        result = parse_changelog(stamped)
        self.assertEqual(len(result.sections), 2)
        fresh, released = result.sections
        self.assertTrue(fresh.is_unreleased)
        self.assertEqual(fresh.entries, [])
        self.assertFalse(released.is_unreleased)
        self.assertEqual(len(released.entries), 1)

        # The fresh section has a home for the next append with no manual setup.
        appended = append_entry(
            stamped, entry_class="added", summary="next thing",
            trace="FEAT-2026-0101/T01",
        )
        result2 = parse_changelog(appended)
        self.assertEqual(result2.findings, [])
        self.assertEqual(len(result2.unreleased().entries), 1)

    def test_append_twice_to_the_same_class_heading_keeps_both_entries(self):
        text = _unreleased_text()  # already has one "### Added" entry
        appended = append_entry(
            text, entry_class="added", summary="a second addition",
            trace="FEAT-2026-0102/T01",
        )
        result = parse_changelog(appended)
        self.assertEqual(result.findings, [])
        summaries = [e.summary for e in result.unreleased().entries]
        self.assertEqual(
            summaries, ["a thing landed", "a second addition"])

    # -- criterion 7: stamping is idempotent-refusing, not idempotent --
    #
    # A second stamp of the SAME version raises rather than silently
    # double-stamping: a release script that double-stamps corrupts the
    # document it exists to protect, and idempotent-silent would hide that
    # the caller re-ran a release by mistake.

    def test_second_stamp_of_the_same_version_is_refused(self):
        stamped = stamp_release(
            _unreleased_text(),
            version="1.2.3",
            date="2026-08-04",
            umbrella_version="1.4.0",
        )
        with self.assertRaises(ValueError) as ctx:
            stamp_release(
                stamped, version="1.2.3", date="2026-08-05",
                umbrella_version="1.4.1",
            )
        self.assertIn("1.2.3", str(ctx.exception))

        # A different version still stamps cleanly.
        stamped_again = stamp_release(
            stamped, version="1.3.0", date="2026-08-05",
            umbrella_version="1.4.1",
        )
        result = parse_changelog(stamped_again)
        released_versions = {
            split_version_field(s.version)[0]
            for s in result.sections if not s.is_unreleased
        }
        self.assertEqual(released_versions, {"1.2.3", "1.3.0"})


class TestBumpVersionReleaseWiring(unittest.TestCase):
    """Criterion 5: bump_version.py stamps as part of the same run that sets
    the four version sources."""

    def _make_tree(self, root: Path, version: str) -> None:
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "specfuse-loop"\nversion = "{version}"\n',
            encoding="utf-8",
        )
        loop_dir = root / "specfuse" / "loop"
        (loop_dir / "data").mkdir(parents=True)
        (loop_dir / "loop.py").write_text(
            f'DRIVER_VERSION = "{version}"\nMIN_SCAFFOLD_VERSION = "0.2.0"\n',
            encoding="utf-8",
        )
        (root / ".specfuse").mkdir()
        (root / ".specfuse" / "VERSION").write_text(version + "\n", encoding="utf-8")
        (loop_dir / "data" / "VERSION").write_text(version + "\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text(_unreleased_text(), encoding="utf-8")

    def test_release_sets_four_sources_and_stamps_changelog_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_tree(root, "0.2.0")
            changed = bump_version.release(
                root, "0.9.0", "1.4.0", date="2026-08-04",
            )
            self.assertEqual(
                set(changed),
                {"pyproject.toml", "specfuse/loop/loop.py",
                 ".specfuse/VERSION", "specfuse/loop/data/VERSION",
                 "CHANGELOG.md"},
            )
            self.assertIn('version = "0.9.0"', (root / "pyproject.toml").read_text())
            self.assertEqual(
                (root / ".specfuse/VERSION").read_text().strip(), "0.9.0")

            changelog_text = (root / "CHANGELOG.md").read_text()
            result = parse_changelog(changelog_text)
            released = [s for s in result.sections if not s.is_unreleased]
            self.assertEqual(len(released), 1)
            version, umbrella = split_version_field(released[0].version)
            self.assertEqual(version, "0.9.0")
            self.assertEqual(umbrella, "1.4.0")

    def test_release_without_umbrella_version_touches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_tree(root, "0.2.0")
            before = (root / "pyproject.toml").read_text()
            with self.assertRaises(ValueError):
                bump_version.release(root, "0.9.0", "")
            self.assertEqual((root / "pyproject.toml").read_text(), before)
            self.assertEqual(
                (root / "CHANGELOG.md").read_text(), _unreleased_text())

    def test_main_validates_the_umbrella_version_before_writing(self):
        """Superseded by #2757: the flag is optional, the value is checked.

        This pinned "`main` refuses without `--umbrella-version`". The flag was
        required so a release could not document half of itself — a rationale
        that expired with umbrella 0.11.0, when components became hard
        dependencies and the driver started reaching users regardless. What the
        requirement never did was check the value, so two published headings
        name umbrella versions that were never released.

        The guarantee is kept and strengthened: `main` still refuses to write a
        coordinate it cannot stand behind. It just refuses on *falsity* now
        rather than on absence, and resolves the value itself when omitted.

        `fetch` is injected — resolution does network I/O, and this test drove
        `main()` straight into PyPI before the seam existed.
        """
        released = ("0.11.0", "0.12.0", "0.12.1")

        def fetch():
            return released

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_tree(root, "0.2.0")
            real_root = bump_version._REPO_ROOT
            try:
                bump_version._REPO_ROOT = root
                # A version that was never released is refused, and nothing
                # is written -- this is the #2757 defect.
                before = (root / "pyproject.toml").read_text()
                self.assertEqual(
                    bump_version.main(
                        ["0.9.0", "--umbrella-version", "1.4.0"], fetch=fetch),
                    2,
                )
                self.assertEqual((root / "pyproject.toml").read_text(), before)

                # Omitted resolves to the latest release and succeeds.
                self.assertEqual(bump_version.main(["0.9.0"], fetch=fetch), 0)
            finally:
                bump_version._REPO_ROOT = real_root

            changelog_text = (root / "CHANGELOG.md").read_text()
            self.assertIn("umbrella.0.12.1", changelog_text)
            result = parse_changelog(changelog_text)
            released_sections = [s for s in result.sections if not s.is_unreleased]
            self.assertEqual(len(released_sections), 1)

    def test_main_still_accepts_an_explicit_released_version(self):
        """Pinning stays possible — a release cut against an older umbrella
        deliberately is a real case, and only fiction is refused."""
        def fetch():
            return ("0.11.0", "0.12.0", "0.12.1")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_tree(root, "0.2.0")
            real_root = bump_version._REPO_ROOT
            try:
                bump_version._REPO_ROOT = root
                self.assertEqual(
                    bump_version.main(
                        ["0.9.0", "--umbrella-version", "0.11.0"], fetch=fetch),
                    0,
                )
            finally:
                bump_version._REPO_ROOT = real_root

            self.assertIn(
                "umbrella.0.11.0", (root / "CHANGELOG.md").read_text())


class TestReleaseWiringPortability(unittest.TestCase):
    """Criterion 6: tag convention and version-source list are configuration,
    with this repo's values as the default, and a target project's own
    values are honoured."""

    def test_default_config_matches_this_repos_values(self):
        config = bump_version.load_release_config(REPO_ROOT)
        self.assertEqual(config.tag_prefix, "v")
        self.assertEqual(
            [s["path"] for s in config.version_sources],
            ["pyproject.toml", "specfuse/loop/loop.py",
             ".specfuse/VERSION", "specfuse/loop/data/VERSION"],
        )

    def test_this_repo_ships_release_yml_matching_the_defaults(self):
        config_path = REPO_ROOT / ".specfuse" / "release.yml"
        self.assertTrue(config_path.is_file())
        config = bump_version.load_release_config(REPO_ROOT)
        self.assertEqual(config, bump_version.ReleaseConfig())

    def test_a_target_projects_config_is_honoured(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specfuse").mkdir()
            (root / ".specfuse" / "release.yml").write_text(
                "tag_prefix: release-\n"
                "\n"
                "version_sources:\n"
                "  - path: VERSION\n"
                "    kind: plain_version_file\n",
                encoding="utf-8",
            )
            (root / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            config = bump_version.load_release_config(root)
            self.assertEqual(config.tag_prefix, "release-")
            self.assertEqual(
                [s["path"] for s in config.version_sources], ["VERSION"])

            changed = bump_version.set_version(root, "0.2.0", config)
            self.assertEqual(changed, ["VERSION"])
            self.assertEqual((root / "VERSION").read_text().strip(), "0.2.0")

            # Confirms the assertion is on the config path, not a hardcoded
            # "v*" tag convention: a target project's non-"v" prefix survives
            # the round trip untouched.
            self.assertNotEqual(config.tag_prefix, "v")


class TestStampParseRoundTrip(unittest.TestCase):
    """The document a stamp produces must satisfy the parser that reads it.

    Regression: `stamp_release` opens a fresh empty `Unreleased` above the
    frozen section (criterion 4 — the next append needs a home nobody creates
    by hand), and the parser flagged every empty section as `has no entries`.
    The two shipped in the same feature and disagreed, so cutting any release
    produced a CHANGELOG that failed its own parse test.
    """

    STAMPED = (
        "## [Unreleased]\n\n"
        "### Added\n\n"
        "- a thing (FEAT-2026-0064/T01)\n"
    )

    def test_stamped_document_parses_clean(self):
        stamped = stamp_release(
            self.STAMPED, version="0.9.0", date="2026-08-04",
            umbrella_version="0.9.0",
        )
        result = parse_changelog(stamped)
        self.assertEqual(result.findings, [], f"stamped output rejected: {result.findings}")

    def test_fresh_unreleased_is_empty_and_appendable(self):
        stamped = stamp_release(
            self.STAMPED, version="0.9.0", date="2026-08-04",
            umbrella_version="0.9.0",
        )
        self.assertEqual(parse_changelog(stamped).unreleased().entries, [])
        appended = append_entry(
            stamped, entry_class="fixed", summary="a later fix", trace="#999",
        )
        result = parse_changelog(appended)
        self.assertEqual(result.findings, [])
        self.assertEqual([e.trace for e in result.unreleased().entries], ["#999"])

    def test_empty_released_section_is_still_a_finding(self):
        """The exemption is scoped to `Unreleased`, not to emptiness at large."""
        result = parse_changelog(
            "## [Unreleased]\n\n"
            "### Added\n\n"
            "- a thing (FEAT-2026-0064/T01)\n\n"
            "## [0.8.0] - 2026-01-01\n"
        )
        self.assertTrue(
            any("no entries" in f for f in result.findings),
            "an empty released section must still be reported",
        )


if __name__ == "__main__":
    unittest.main()
