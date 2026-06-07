"""Tests for truncate_failure_note() — FEAT-2026-0007/T05."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".specfuse", "scripts"))
from loop import truncate_failure_note


class TestTruncateFailureNote(unittest.TestCase):

    def test_under_limit_unchanged(self):
        note = "line one\nline two\nline three"
        self.assertEqual(truncate_failure_note(note), note)

    def test_over_line_limit_preserves_first_and_last(self):
        lines = [f"line {i}" for i in range(300)]
        note = "\n".join(lines)
        result = truncate_failure_note(note, max_lines=200, max_chars=999_999)
        self.assertIn(lines[0], result)
        self.assertIn(lines[-1], result)
        self.assertIn("elided", result)
        self.assertNotIn("```", result)

    def test_over_char_limit_marker_reports_counts(self):
        line = "x" * 100
        note = "\n".join([line] * 100)
        result = truncate_failure_note(note, max_lines=999, max_chars=500)
        self.assertIn("elided", result)
        self.assertRegex(result, r"\.\.\. \[\d+ lines / \d+ chars elided\] \.\.\.")
        self.assertNotIn("```", result)


if __name__ == "__main__":
    unittest.main()
