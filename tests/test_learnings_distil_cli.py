#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The distillation accept step must be reachable by an operator (#3315).

FEAT-2026-0111/T03 built `propose_distilled_learnings` and
`apply_distilled_decisions` and shipped them with no caller: their only
callers were `tests/test_distilled_accept_step.py`, so the propose-and-accept
step existed and no human could run it. This module is that caller, in the
shape `learnings_query` already established for an operator-facing loop
surface.

The tests drive `main()` with argv and assert on what it prints and writes,
not on the underlying helpers — those were always callable, and a test that
called them directly would have passed throughout the defect.
"""
from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop import learnings_distil


LEARNINGS = """\
# Learnings

- [FEAT-2026-0001/G1-CLOSE] A rule that earned its place. Evidence follows and
  it is several words long so the word budget has something to measure.

- [FEAT-2026-0002/G1-CLOSE] A second rule, also with some words in it so the
  ranking has more than one candidate to order.
"""


class DistilCliIsReachableAndReadOnlyByDefault(unittest.TestCase):

    def _workspace(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / ".specfuse" / "features").mkdir(parents=True)
        (root / ".specfuse" / "LEARNINGS.md").write_text(LEARNINGS, encoding="utf-8")
        (root / ".specfuse" / "rules-local").mkdir(parents=True)
        return root

    def test_proposing_prints_entries_with_their_evidence(self):
        with TemporaryDirectory() as tmp:
            root = self._workspace(tmp)
            out = io.StringIO()
            with redirect_stdout(out):
                rc = learnings_distil.main([
                    "--learnings", str(root / ".specfuse" / "LEARNINGS.md"),
                    "--features", str(root / ".specfuse" / "features"),
                ])
            self.assertEqual(rc, 0)
            text = out.getvalue()
            self.assertIn("FEAT-2026-0001/G1-CLOSE", text)
            # the evidence a human needs to disagree with the ranking
            self.assertIn("reach", text.lower())
            self.assertIn("word", text.lower())

    def test_proposing_writes_nothing(self):
        # The negative observation FEAT-2026-0111/T03 built the step around:
        # nothing reaches the distilled file without an explicit accept.
        with TemporaryDirectory() as tmp:
            root = self._workspace(tmp)
            target = root / ".specfuse" / "rules-local" / "learnings-distilled.md"
            with redirect_stdout(io.StringIO()):
                learnings_distil.main([
                    "--learnings", str(root / ".specfuse" / "LEARNINGS.md"),
                    "--features", str(root / ".specfuse" / "features"),
                ])
            self.assertFalse(target.exists())

    def test_apply_writes_only_what_the_decisions_file_accepts(self):
        with TemporaryDirectory() as tmp:
            root = self._workspace(tmp)
            target = root / ".specfuse" / "rules-local" / "learnings-distilled.md"
            decisions = root / "decisions.json"
            decisions.write_text(json.dumps([
                {"tag": "FEAT-2026-0001/G1-CLOSE", "action": "accept",
                 "text": "A rule that earned its place."},
                {"tag": "FEAT-2026-0002/G1-CLOSE", "action": "reject"},
            ]), encoding="utf-8")

            out = io.StringIO()
            with redirect_stdout(out):
                rc = learnings_distil.main([
                    "--apply", str(decisions), "--out", str(target),
                ])
            self.assertEqual(rc, 0)
            written = target.read_text(encoding="utf-8")
            self.assertIn("A rule that earned its place.", written)
            self.assertNotIn("FEAT-2026-0002", written)

    def test_apply_with_no_accepts_leaves_the_file_untouched(self):
        with TemporaryDirectory() as tmp:
            root = self._workspace(tmp)
            target = root / ".specfuse" / "rules-local" / "learnings-distilled.md"
            target.write_text("original\n", encoding="utf-8")
            decisions = root / "decisions.json"
            decisions.write_text(json.dumps([
                {"tag": "FEAT-2026-0001/G1-CLOSE", "action": "reject"},
            ]), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                learnings_distil.main(["--apply", str(decisions), "--out", str(target)])
            self.assertEqual(target.read_text(encoding="utf-8"), "original\n")


if __name__ == "__main__":
    unittest.main()
