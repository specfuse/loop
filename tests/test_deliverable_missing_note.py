#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Diagnostic attempt note on a deliverable-presence refusal — issue #1412.

The reported symptom was a 0-byte `work/<WU>/attempt-N.md`. That part does not
reproduce: the note carried 43 bytes with no trailing newline, and the issue's
evidence was `wc -l`, which counts newlines. The defect underneath it is real —
the note held only `assert_declared_deliverables`' one-line summary, which is
the same string the retry prompt already prints, so nothing in the artifact set
said *which* declared path was missing relative to what the attempt actually
wrote. Three attempts of a real run reached the same wall and none of them left
that behind.

Covers the composed note, the trailing-newline guarantee in the single writer,
and the end-to-end shape a real refusal leaves on disk.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace
from tests.test_deliverable_presence_gate import write_minimal_feature

loop = load_loop()


def _make_wu(produces: list, wu_id: str = "FEAT-2026-9999/T02") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path("WU-T02.md"),
        depends_on=[],
        type="implementation",
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title="deliverable WU",
        body="",
        produces=produces,
    )


class _RestoresCwd(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)


# --------------------------------------------------------------------------- #
# The composed note                                                           #
# --------------------------------------------------------------------------- #


class TestFormatDeliverableMissingNote(_RestoresCwd):

    def test_marks_each_declared_path_present_or_absent(self):
        """The decisive item: a partial bundle must say which of the declared
        paths landed and which did not."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("SECURITY.md").write_text("present\n")
            wu = _make_wu(["SECURITY.md", "CODE_OF_CONDUCT.md"])
            note = loop.format_deliverable_missing_note(
                wu,
                "declared deliverable absent: CODE_OF_CONDUCT.md",
                ["SECURITY.md"],
                attempt=1,
            )
            self.assertIn("SECURITY.md", note)
            self.assertIn("CODE_OF_CONDUCT.md", note)
            self.assertRegex(note, r"CODE_OF_CONDUCT\.md.*(?i:absent)")
            self.assertRegex(note, r"SECURITY\.md.*(?i:present)")

    def test_carries_the_guard_summary(self):
        with integration_workspace() as root:
            os.chdir(root)
            note = loop.format_deliverable_missing_note(
                _make_wu(["A.md"]), "declared deliverable absent: A.md", [], attempt=2,
            )
            self.assertIn("declared deliverable absent: A.md", note)

    def test_names_the_files_the_attempt_touched(self):
        with integration_workspace() as root:
            os.chdir(root)
            note = loop.format_deliverable_missing_note(
                _make_wu(["A.md"]),
                "declared deliverable absent: A.md",
                ["src/other.py"],
                attempt=1,
            )
            self.assertIn("src/other.py", note)

    def test_states_explicitly_when_nothing_was_touched(self):
        """An empty touched list is evidence, not an absence of it — the third
        attempt of the reported run touched nothing at all."""
        with integration_workspace() as root:
            os.chdir(root)
            note = loop.format_deliverable_missing_note(
                _make_wu(["A.md"]), "declared deliverable absent: A.md", [], attempt=3,
            )
            self.assertRegex(note, r"(?i:none)")

    def test_names_the_attempt(self):
        with integration_workspace() as root:
            os.chdir(root)
            note = loop.format_deliverable_missing_note(
                _make_wu(["A.md"]), "declared deliverable absent: A.md", [], attempt=2,
            )
            self.assertIn("2", note)

    def test_ends_with_a_newline(self):
        with integration_workspace() as root:
            os.chdir(root)
            note = loop.format_deliverable_missing_note(
                _make_wu(["A.md"]), "declared deliverable absent: A.md", [], attempt=1,
            )
            self.assertTrue(note.endswith("\n"))

    def test_empty_produces_still_renders(self):
        """Defensive: the gate cannot fire with empty produces:, but the
        formatter must not raise if it is ever called that way."""
        with integration_workspace() as root:
            os.chdir(root)
            note = loop.format_deliverable_missing_note(
                _make_wu([]), "declared deliverable absent: A.md", [], attempt=1,
            )
            self.assertTrue(note.endswith("\n"))


# --------------------------------------------------------------------------- #
# The single writer's trailing-newline guarantee                              #
# --------------------------------------------------------------------------- #


class TestPersistAttemptNotesNewline(unittest.TestCase):
    """`wc -l` reporting 0 on a non-empty note is what made #1412 read as a
    0-byte file. Every note the driver writes ends with a newline."""

    def test_adds_a_missing_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            loop.persist_attempt_notes(work, "FEAT-9999/T01", [(1, "no newline here")])
            written = (work / "FEAT-9999_T01" / "attempt-1.md").read_text()
            self.assertTrue(written.endswith("\n"))
            self.assertIn("no newline here", written)

    def test_does_not_double_an_existing_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            loop.persist_attempt_notes(work, "FEAT-9999/T01", [(1, "ends already\n")])
            written = (work / "FEAT-9999_T01" / "attempt-1.md").read_text()
            self.assertEqual(written, "ends already\n")

    def test_empty_evidence_stays_empty(self):
        """Nothing to say writes nothing — a newline-only file would be a
        false signal that evidence exists."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            loop.persist_attempt_notes(work, "FEAT-9999/T01", [(1, "")])
            written = (work / "FEAT-9999_T01" / "attempt-1.md").read_text()
            self.assertEqual(written, "")


# --------------------------------------------------------------------------- #
# End to end — what a real refusal leaves on disk                             #
# --------------------------------------------------------------------------- #


class TestNoteOnDiskAfterRefusal(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _notes(self, root: Path, slug: str) -> list:
        work = root / f".specfuse/features/{slug}/work"
        return sorted(work.rglob("attempt-*.md"))

    def test_partial_bundle_note_distinguishes_present_from_absent(self):
        """The reported run's decisive gap: the agent wrote one of two declared
        files every time, and nothing said which one was missing."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(
                root, "FEAT-2026-0022", "partial-bundle", "feat/partial-bundle",
                [("FEAT-2026-0022/T02", "implementation", "pending",
                  ["SECURITY.md", "CODE_OF_CONDUCT.md"])],
            )

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T02"):
                    Path("SECURITY.md").write_text("written\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - SECURITY.md\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            loop.run(None, dry_run=False)

            notes = self._notes(root, "FEAT-2026-0022-partial-bundle")
            self.assertTrue(notes, "a refused attempt must leave a note")
            body = notes[0].read_text()
            self.assertIn("CODE_OF_CONDUCT.md", body)
            self.assertIn("SECURITY.md", body)
            self.assertRegex(body, r"CODE_OF_CONDUCT\.md.*(?i:absent)")

    def test_note_is_not_zero_lines(self):
        """#1412's own evidence was `wc -l` reading 0. Every note the driver
        leaves must count at least one line."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(
                root, "FEAT-2026-0022", "deliv-absent", "feat/deliv-absent",
                [("FEAT-2026-0022/T02", "implementation", "pending",
                  ["DELIVERABLE.md"])],
            )
            self._patch("dispatch", lambda wu, fn, ct=True:
                        "```result\nstatus: complete\n```\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            loop.run(None, dry_run=False)

            notes = self._notes(root, "FEAT-2026-0022-deliv-absent")
            self.assertTrue(notes)
            for note in notes:
                raw = note.read_text()
                self.assertTrue(raw.strip(), f"{note.name} is empty")
                self.assertGreaterEqual(
                    raw.count("\n"), 1, f"{note.name} counts 0 lines under wc -l",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
