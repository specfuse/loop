#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The docs do not promise a `judge_editing` veto the terminal gate never gets (#3542).

`arm_eval`'s `judge_editing` class reads only the drafted *successor* gate's
units. `draft-feature` and the methodology told planners the class would veto
any feature that edits the driver, so FEAT-2026-0224 chose `auto` expecting a
halt that could not fire, and its judge-module edit reached the close with no
human checkpoint. Every copy of each surface must state the limit and none may
repeat the old promise.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SURFACES = (
    "plugins/specfuse/skills/draft-feature/SKILL.md",
    ".specfuse/skills/draft-feature/SKILL.md",
    "docs/methodology.md",
    "specfuse/loop/data/docs/methodology.md",
    "docs/concepts/autonomy-stop-classes.md",
    "specfuse/loop/data/docs/concepts/autonomy-stop-classes.md",
)

OLD_PROMISES = (
    "stop class will\nveto the arm anyway",
    "still\nvetoes any gate that edited the loop's own driver",
)


def _flat(text: str) -> str:
    return " ".join(text.split())


class JudgeEditingDocsNameTheTerminalGap(unittest.TestCase):
    def test_every_surface_names_the_gap(self):
        for rel in SURFACES:
            with self.subTest(surface=rel):
                text = (REPO / rel).read_text()
                self.assertIn("#3542", text)
                self.assertIn("review", text)

    def test_no_surface_repeats_the_old_promise(self):
        for rel in SURFACES:
            flat = _flat((REPO / rel).read_text())
            for promise in OLD_PROMISES:
                with self.subTest(surface=rel, promise=promise):
                    self.assertNotIn(_flat(promise), flat)


if __name__ == "__main__":
    unittest.main()
