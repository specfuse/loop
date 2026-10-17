# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3501: `specfuse upgrade` (which routes through `wire_claude`) must add the
current gitignore snippet's lines to a project that already carries an older
copy of the snippet, instead of skipping the whole snippet once its marker
line is present.
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from specfuse.loop.scaffold import read_scaffold, wire_claude

_SNIPPET = read_scaffold("gitignore.snippet").decode("utf-8")
_NEW_LINE = ".specfuse/monitor-watermarks/"


def _rules(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


class TestUpgradeAddsMissingSnippetLines(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.target = pathlib.Path(self._tmpdir.name)
        self.gitignore = self.target / ".gitignore"
        # A project initialised before the watermark line existed: its own
        # lines, then an older snippet that lacks the new line.
        self.assertIn(_NEW_LINE, _SNIPPET)
        old_snippet = "".join(
            ln for ln in _SNIPPET.splitlines(keepends=True) if ln.strip() != _NEW_LINE
        )
        self.gitignore.write_text("node_modules/\n*.log\n" + old_snippet, encoding="utf-8")

    def test_missing_snippet_line_is_added(self):
        wire_claude(self.target)
        text = self.gitignore.read_text(encoding="utf-8")
        for rule in _rules(_SNIPPET):
            with self.subTest(rule=rule):
                self.assertEqual(text.splitlines().count(rule), 1, text)

    def test_operator_lines_kept_in_order(self):
        wire_claude(self.target)
        lines = self.gitignore.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[:2], ["node_modules/", "*.log"])

    def test_second_upgrade_is_a_no_op(self):
        wire_claude(self.target)
        once = self.gitignore.read_text(encoding="utf-8")
        wire_claude(self.target)
        self.assertEqual(self.gitignore.read_text(encoding="utf-8"), once)

    def test_fresh_project_still_gets_the_whole_snippet(self):
        self.gitignore.unlink()
        wire_claude(self.target)
        self.assertEqual(self.gitignore.read_text(encoding="utf-8"), _SNIPPET)


if __name__ == "__main__":
    unittest.main()
