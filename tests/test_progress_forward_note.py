#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The optional `forward_note` RESULT field — FEAT-2026-0106/T02.

`summary` is backward-looking by the result-contract's own definition. This
field is the other half: what the session wants the next unit to know. It is
optional on an interface that already exists (`append_progress_entry`,
`record_progress_entry`) — present it and `PROGRESS.md` gets an extra line;
omit it and the entry is byte-for-byte what T01 already wrote.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import load_loop

loop = load_loop()


class AppendProgressEntryForwardNoteTest(unittest.TestCase):

    def test_forward_note_present_adds_a_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            loop.append_progress_entry(
                fdir, "FEAT-0000/T01", "did the thing", "watch out for X",
            )
            text = (fdir / loop.PROGRESS_FILENAME).read_text()
            self.assertIn("FEAT-0000/T01", text)
            self.assertIn("did the thing", text)
            self.assertIn("watch out for X", text)

    def test_forward_note_absent_matches_t01_output_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as with_none, \
                tempfile.TemporaryDirectory() as without_arg:
            fdir_a = Path(with_none)
            fdir_b = Path(without_arg)

            loop.append_progress_entry(
                fdir_a, "FEAT-0000/T01", "did the thing", None,
            )
            loop.append_progress_entry(fdir_b, "FEAT-0000/T01", "did the thing")

            text_a = (fdir_a / loop.PROGRESS_FILENAME).read_text()
            text_b = (fdir_b / loop.PROGRESS_FILENAME).read_text()
            self.assertEqual(text_a, text_b)
            self.assertEqual(text_a, "- **FEAT-0000/T01**: did the thing\n")

    def test_forward_note_empty_string_is_treated_as_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            loop.append_progress_entry(fdir, "FEAT-0000/T01", "did the thing", "")
            text = (fdir / loop.PROGRESS_FILENAME).read_text()
            self.assertEqual(text, "- **FEAT-0000/T01**: did the thing\n")


class RecordProgressEntryForwardNoteTest(unittest.TestCase):

    def _wu(self, result_block):
        return SimpleNamespace(wu_id="FEAT-0000/T02", result_block=result_block)

    def test_forward_note_from_result_block_is_rendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = self._wu({
                "summary": "wired the field",
                "forward_note": "next unit should check the fallback path",
            })
            loop.record_progress_entry(fdir, wu, attempt=1, outcome="passed")
            text = (fdir / loop.PROGRESS_FILENAME).read_text()
            self.assertIn("wired the field", text)
            self.assertIn("next unit should check the fallback path", text)

    def test_missing_forward_note_matches_summary_only_entry(self):
        with tempfile.TemporaryDirectory() as with_field, \
                tempfile.TemporaryDirectory() as without_field:
            fdir_a = Path(with_field)
            fdir_b = Path(without_field)

            wu_a = self._wu({"summary": "wired the field"})
            wu_b = self._wu({"summary": "wired the field", "forward_note": ""})

            loop.record_progress_entry(fdir_a, wu_a, attempt=1, outcome="passed")
            loop.record_progress_entry(fdir_b, wu_b, attempt=1, outcome="passed")

            text_a = (fdir_a / loop.PROGRESS_FILENAME).read_text()
            text_b = (fdir_b / loop.PROGRESS_FILENAME).read_text()
            self.assertEqual(text_a, text_b)
            self.assertEqual(text_a, "- **FEAT-0000/T02**: wired the field\n")

    def test_malformed_result_block_still_produces_the_fallback_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = self._wu(None)
            loop.record_progress_entry(fdir, wu, attempt=1, outcome="failed")
            text = (fdir / loop.PROGRESS_FILENAME).read_text()
            self.assertEqual(text, "- **FEAT-0000/T02**: attempt 1 outcome=failed\n")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
