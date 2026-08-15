#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A close WU must not name the one lessons destination `auto` forbids (#2173).

Under `autonomy_default: auto`, `close-i` (`assert_learnings_staged_under_auto`)
forbids a closing WU from appending to `.specfuse/LEARNINGS.md`; lessons stage
to `LEARNINGS-pending.md` instead. Nothing at authoring, lint, or arming time
flagged a WU that told the session to do the forbidden thing, so a session
following its own acceptance criteria literally is refused by the guard.

**This check is not what would have prevented #2173's headline $40.27.** That
spin was the stale-build hazard (#1040, fixed dispatcher-side in #2186), and
the issue's author retracted the original diagnosis with reflog evidence: every
refused attempt had in fact staged correctly. What survives the retraction is
the narrower defect this check owns — a work unit that *describes* a forbidden
destination is wrong whether or not any session has yet been misled by it.

WARN, never ERROR, matching `check_closing_guard_literals`'s rationale. Measured
on this repo: 9 of 14 historical `auto` closing WUs name `LEARNINGS.md` without
naming the staging file. All 14 are `done` and therefore skipped as sealed
history, so the live tree is clean — but a prose match on a body is not a strong
enough signal to fail a build over.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.lint_plan import check_closing_learnings_destination

_WU = """---
id: FEAT-2026-9402/{wid}
type: {wtype}
status: {status}
---

# Gate 1 {wtype} — close the gate

{body}
"""


class _Harness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _wu(self, body: str, *, wtype: str = "close", status: str = "pending",
            wid: str = "G1-CLOSE") -> list:
        (self.dir / "WU.md").write_text(
            _WU.format(wid=wid, wtype=wtype, status=status, body=body)
        )
        return [{"work_units": [{"file": "WU.md"}]}]

    def _run(self, gates, autonomy: str = "auto") -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_closing_learnings_destination(
                self.dir, {"autonomy_default": autonomy}, gates
            )
        return buf.getvalue()


class TestFiresOnTheForbiddenDestination(_Harness):
    def test_auto_close_naming_only_learnings_warns(self):
        """The worked example: FEAT-2026-0080/G1-CLOSE's criterion 5."""
        out = self._run(self._wu(
            "Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`, or "
            "the close states explicitly that nothing generalizes and why."
        ))
        self.assertIn("WARN", out)
        self.assertIn("LEARNINGS-pending.md", out)
        self.assertIn("assert_learnings_staged_under_auto", out)

    def test_close_intermediate_is_covered_too(self):
        out = self._run(self._wu(
            "Lessons go to `.specfuse/LEARNINGS.md`.", wtype="close-intermediate",
            wid="G1-CLOSE-INTERMEDIATE",
        ))
        self.assertIn("WARN", out)


class TestDoesNotFire(_Harness):
    def test_naming_the_staging_file_too_is_correct(self):
        """The fix an author applies: name where lessons actually go. A body
        that names both is describing the routing, not a forbidden write."""
        out = self._run(self._wu(
            "Do NOT append to `.specfuse/LEARNINGS.md` under auto — stage "
            "generalizable lessons to `LEARNINGS-pending.md` instead."
        ))
        self.assertEqual(out, "")

    def test_a_review_feature_may_name_learnings_directly(self):
        """Under `review`/`supervised` the direct append is the correct
        instruction, so the same body must not warn."""
        out = self._run(
            self._wu("Lessons are promoted to `.specfuse/LEARNINGS.md`."),
            autonomy="review",
        )
        self.assertEqual(out, "")

    def test_a_body_naming_neither_is_another_check_s_business(self):
        out = self._run(self._wu("Write RETROSPECTIVE.md and record the verdict."))
        self.assertEqual(out, "")

    def test_done_work_units_are_sealed_history(self):
        """Backfilling instructions onto a WU that already ran is pointless —
        the same exemption `check_closing_guard_literals` makes."""
        out = self._run(self._wu(
            "Lessons are promoted to `.specfuse/LEARNINGS.md`.", status="done"
        ))
        self.assertEqual(out, "")

    def test_implementation_work_units_are_not_closing_work_units(self):
        out = self._run(self._wu(
            "Lessons are promoted to `.specfuse/LEARNINGS.md`.",
            wtype="implementation", wid="T01",
        ))
        self.assertEqual(out, "")

    def test_the_learnings_archive_is_not_the_learnings_file(self):
        """`LEARNINGS-archive.md` is a different surface; naming it is not a
        claim about where a close writes lessons."""
        out = self._run(self._wu(
            "Retired entries live in `.specfuse/LEARNINGS-archive.md`."
        ))
        self.assertEqual(out, "")


class TestExitCodeUnchanged(_Harness):
    def test_the_check_returns_nothing_and_raises_nothing(self):
        """Advisory: findings print, the caller's error list is untouched."""
        self.assertIsNone(
            check_closing_learnings_destination(
                self.dir,
                {"autonomy_default": "auto"},
                self._wu("Lessons go to `.specfuse/LEARNINGS.md`."),
            )
        )

    def test_a_missing_work_unit_file_is_skipped_not_an_error(self):
        out = self._run([{"work_units": [{"file": "absent.md"}]}])
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
