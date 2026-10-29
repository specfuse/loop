#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The docs describe the terminal judge-editing stop (FEAT-2026-0246/T04).

#3544 told planners `review` was the only checkpoint for a judge edit in the
terminal gate. `review` adds no terminal checkpoint; the terminal stop does, at
every autonomy level, cleared by `judge_edit_acknowledged` plus `/unblock-wu`.
Every copy of each surface must name the stop and none may keep the old advice.
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

OLD_ADVICE = (
    "the only checkpoint the change gets",
    "Choose `review` for such a feature",
    "should run under `review`",
    "does **not** cover the terminal gate",
    "Does not cover the terminal gate",
    "stop class will\nveto the arm anyway",
    "still\nvetoes any gate that edited the loop's own driver",
)


def _flat(text: str) -> str:
    return " ".join(text.split())


class JudgeEditingDocsNameTheTerminalStop(unittest.TestCase):
    def test_every_surface_names_the_stop(self):
        for rel in SURFACES:
            with self.subTest(surface=rel):
                flat = _flat((REPO / rel).read_text())
                self.assertIn("judge_edit_acknowledged", flat)
                self.assertIn("/unblock-wu", flat)
                self.assertIn("before the close", flat)

    def test_no_surface_recommends_review_for_the_terminal_gate(self):
        for rel in SURFACES:
            flat = _flat((REPO / rel).read_text())
            for old in OLD_ADVICE:
                with self.subTest(surface=rel, old=old):
                    self.assertNotIn(_flat(old), flat)

    def test_copies_are_identical(self):
        for a, b in zip(SURFACES[::2], SURFACES[1::2], strict=True):
            with self.subTest(pair=a):
                self.assertEqual((REPO / a).read_bytes(), (REPO / b).read_bytes())


if __name__ == "__main__":
    unittest.main()
