#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unit tests for specfuse.loop.layout (FEAT-2026-0224/T01)."""

import re
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import layout
from tests.test_layout_end_to_end import run_layout


def _write(repo, text):
    (Path(repo) / ".specfuse").mkdir(exist_ok=True)
    (Path(repo) / ".specfuse" / "layout.yml").write_text(text)


class LoadDefaults(unittest.TestCase):
    def test_file_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = layout.load(tmp).decisions
        self.assertEqual((d.style, d.location, d.link), ("adr", "docs/adr", "{path}"))

    def test_no_decisions_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "other: 1\n")
            d = layout.load(tmp).decisions
        self.assertEqual((d.style, d.location, d.link), ("adr", "docs/adr", "{path}"))

    def test_entries_defaults_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "decisions:\n  style: entries\n")
            d = layout.load(tmp).decisions
        self.assertEqual(d.style, "entries")
        self.assertEqual(d.location, "docs/decisions")
        self.assertEqual(d.link, "{location}/decisions.md#{id}")

    def test_explicit_values_win(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, 'decisions:\n  style: entries\n  location: x/y\n  link: "{id}"\n')
            d = layout.load(tmp).decisions
        self.assertEqual((d.location, d.link), ("x/y", "{id}"))


class GetKey(unittest.TestCase):
    def test_unknown_key_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(KeyError):
                layout.get(layout.load(tmp), "decisions.nope")

    def test_unknown_key_cli_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_layout(tmp, "get", "decisions.nope")
        self.assertEqual(r.returncode, 2)
        for k in ("decisions.style", "decisions.location", "decisions.link"):
            self.assertIn(k, r.stderr)

    def test_repo_flag(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
            _write(tmp, "decisions:\n  style: entries\n")
            r = run_layout(other, "--repo", tmp, "get", "decisions.style")
        self.assertEqual(r.stdout.strip(), "entries")


class NoDriverImport(unittest.TestCase):
    def test_no_loop_import(self):
        src = Path(layout.__file__).read_text()
        self.assertIsNone(re.search(r"specfuse\.loop\.loop|from \.loop|import loop", src))


if __name__ == "__main__":
    unittest.main()
