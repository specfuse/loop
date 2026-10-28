#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Negative and positive tests for `layout.validate` (FEAT-2026-0224/T02)."""

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import layout
from specfuse.loop.lint_roadmap import SEVERITY_ERROR, SEVERITY_WARN


def _repo(tmp, text=None):
    root = Path(tmp)
    if text is not None:
        (root / ".specfuse").mkdir()
        (root / ".specfuse" / "layout.yml").write_text(text, encoding="utf-8")
    return root


def _decisions(**fields):
    lines = ["decisions:"]
    for key, value in fields.items():
        lines.append(f'  {key}: "{value}"')
    return "\n".join(lines) + "\n"


class ValidateTest(unittest.TestCase):
    def _validate(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            root = _repo(tmp, text)
            findings = layout.validate(root)
            loaded = layout.load(root)
        self.assertIsInstance(loaded, layout.Layout)
        return findings

    def _only(self, text, severity, *needles):
        findings = self._validate(text)
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0].severity, severity)
        for needle in needles:
            self.assertIn(needle, findings[0].message)

    def test_no_file_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(layout.validate(tmp), [])

    def test_valid_entries_file_is_clean(self):
        text = _decisions(
            style="entries",
            location="docs/decisions",
            link="{location}/decisions.md#{id}",
        )
        self.assertEqual(self._validate(text), [])

    def test_rejects_absolute_location(self):
        self._only(_decisions(location="/abs"), SEVERITY_ERROR, "/abs", "absolute")

    def test_rejects_dotdot_segment(self):
        self._only(_decisions(location="docs/../x"), SEVERITY_ERROR, "..")

    def test_rejects_windows_drive_forward_slash(self):
        self._only(_decisions(location="C:/x"), SEVERITY_ERROR, "drive")

    def test_rejects_windows_drive_backslash(self):
        findings = self._validate(_decisions(location="C:\\\\x"))
        self.assertTrue(findings)
        self.assertTrue(all(f.severity == SEVERITY_ERROR for f in findings))
        self.assertTrue(any("drive" in f.message for f in findings))

    def test_rejects_backslash(self):
        self._only(_decisions(location="docs\\\\x"), SEVERITY_ERROR, "backslash")

    def test_rejects_symlink_escaping_repo(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as out:
            root = _repo(tmp, _decisions(location="docs/link"))
            (root / "docs").mkdir()
            try:
                (root / "docs" / "link").symlink_to(out, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unsupported")
            findings = layout.validate(root)
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0].severity, SEVERITY_ERROR)
        self.assertIn("outside the repo root", findings[0].message)

    def test_trailing_slash_resolves_equal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with_slash = _repo(tmp, _decisions(location="docs/decisions/"))
            self.assertEqual(layout.validate(with_slash), [])
            self.assertEqual(
                layout.load(with_slash).decisions.location,
                "docs/decisions",
            )

    def test_rejects_unknown_style(self):
        self._only(_decisions(style="wiki"), SEVERITY_ERROR, "'adr'", "'entries'")

    def test_rejects_unknown_link_placeholder(self):
        self._only(_decisions(link="{location}/{slug}"), SEVERITY_ERROR, "{slug}")

    def test_paths_block_is_warn_naming_follow_up(self):
        self._only(
            "paths:\n  specs: specs\n",
            SEVERITY_WARN,
            "`paths:` is not supported yet",
            "FEAT-2026-0224",
        )

    def test_unknown_top_level_key_is_warn(self):
        self._only("colour: blue\n", SEVERITY_WARN, "colour")


if __name__ == "__main__":
    unittest.main()
