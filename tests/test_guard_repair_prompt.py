#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unit tests for compose_guard_repair_note (FEAT-2026-0103/T02).

The note a refused attempt hands to the next one must read as a repair
brief: the guard's complaint first, then that the tree is retained and
verification passed, then the mechanical remedy, then the retained diff
last — evidence, not the instruction.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

loop = load_loop()

_GUARD_CLASSES = ("guard_refusal", "files_changed_mismatch",
                   "produces_not_in_diff")

_COMPLAINTS = {
    "guard_refusal": "no files under this WU's produces: were touched",
    "files_changed_mismatch": "declared `files_changed` path shows no diff "
                               "against HEAD before this attempt",
    "produces_not_in_diff": "declared produces path(s) not in this WU's "
                            "squash diff: specfuse/loop/loop.py",
}

_DIFF = "diff --git a/foo.py b/foo.py\n+placeholder\n"


def _first_non_blank_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line
    return ""


class RetainedGuardNoteTest(unittest.TestCase):

    def test_retained_guard_note_leads_with_the_complaint(self):
        for failure_class in _GUARD_CLASSES:
            with self.subTest(failure_class=failure_class):
                complaint = _COMPLAINTS[failure_class]
                note = loop.compose_guard_repair_note(
                    failure_class, complaint, _DIFF, True)

                first_line = _first_non_blank_line(note)
                self.assertIn(complaint.splitlines()[0], first_line)

                diff_idx = note.index("Retained diff")
                pre_diff = note[:diff_idx]
                self.assertIn("STILL PRESENT", pre_diff)
                self.assertIn("PASSED", pre_diff)

                hint = loop._RETRY_CLASS_HINT[failure_class]
                self.assertIn(hint, pre_diff)

                self.assertLess(
                    note.index(hint), diff_idx,
                    "remedy sentence must precede the Retained diff line")
                self.assertTrue(note.rstrip().endswith("```"))

    def test_unretained_guard_note_is_unchanged(self):
        for failure_class in _GUARD_CLASSES:
            with self.subTest(failure_class=failure_class):
                complaint = _COMPLAINTS[failure_class]
                note = loop.compose_guard_repair_note(
                    failure_class, complaint, None, False)

                self.assertNotIn("STILL PRESENT", note)
                self.assertNotIn("Retained diff", note)
                self.assertNotIn("```diff", note)

                hint = loop._RETRY_CLASS_HINT[failure_class]
                self.assertIn(hint, note)


if __name__ == "__main__":
    unittest.main()
