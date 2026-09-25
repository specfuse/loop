#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The `judged` event says where the judge's findings went (#3406).

The issue reported that a judge lowering a terminal verdict "persists no
findings". It does persist them: `write_judge_followups` writes each finding
verbatim into `FOLLOW-UPS.md` and `commit_bookkeeping` commits it. Verified in
the reporting repository's own history — `chore(loop): FEAT-2026-0168/G1-CLOSE
judge lowered verdict to not_met` contains "Filed by the judge for gate 1. Each
entry is the judge's own words."

What is missing is the pointer. The `judged` event records `findings: 1` and
`reason: null`, and names nothing. The reporter looked in `events.jsonl`, in
`<feature>/work/`, and for a repository-level judge artifact — the three places
the event gave them no reason to leave — and concluded the text was nowhere.
They then priced a third close at ~$12 to re-derive a finding that was sitting
in a committed file.

So the event becomes self-describing: it names the file the findings were
written to and the criteria they were raised against, and its `reason` stops
being `null` on the one path where something specific was found.

The finding TEXT deliberately stays out of the event. It is already recorded
verbatim in one place; copying it into a second invites the two to disagree,
and `write_judge_followups` exists precisely so the judge's words are not
reformatted by the driver.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from tests._loop_loader import load_loop

loop = load_loop()


class _Finding:
    def __init__(self, criterion, text):
        self.criterion = criterion
        self.text = text


class TheLoweredEventNamesTheRecord(unittest.TestCase):

    def _payload_for(self, findings):
        """Drive judge_close's lowered branch with the file writes stubbed."""
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        feature_dir = Path(tmp.name)
        (feature_dir / "PLAN.md").write_text("---\nfeature_id: FEAT-2026-9999\n---\n")
        wu_file = feature_dir / "WU-90-close.md"
        wu_file.write_text("---\nid: FEAT-2026-9999/G1-CLOSE\nverdict: met\n---\n")
        wu = SimpleNamespace(
            file=wu_file, wu_id="FEAT-2026-9999/G1-CLOSE", verdict="met")

        result = SimpleNamespace(verdict="not_met", findings=findings, reason=None)

        with mock.patch.object(loop, "_gate_identity",
                               return_value=(1, feature_dir / "GATE-01.md")), \
             mock.patch.object(loop, "_judge_disabled", return_value=False), \
             mock.patch.object(loop, "resolve_gate_start_sha",
                               return_value=("abc123", "gate frontmatter")), \
             mock.patch.object(loop, "capture_gate_diff", return_value="diff"), \
             mock.patch.object(loop, "build_judge_bundle", return_value={}), \
             mock.patch.object(loop, "render_judge_prompt", return_value="prompt"), \
             mock.patch.object(loop, "parse_judge_result", return_value=result), \
             mock.patch.object(loop, "write_frontmatter_field"), \
             mock.patch.object(loop, "commit_bookkeeping"):
            return loop.judge_close(
                wu, feature_dir, feature_dir,
                runner=lambda prompt, timeout=None: ("raw", {}),
            )

    def test_it_names_the_file_the_findings_were_written_to(self):
        payload = self._payload_for([_Finding("T11#3", "### T11#3\n\nThe thing.")])

        self.assertTrue(payload["lowered"])
        self.assertIn("FOLLOW-UPS.md", payload.get("findings_path", ""))

    def test_it_names_the_criteria(self):
        payload = self._payload_for([
            _Finding("T11#3", "### T11#3\n\nOne."),
            _Finding("T06#2", "### T06#2\n\nTwo."),
        ])

        self.assertEqual(["T11#3", "T06#2"], payload.get("finding_criteria"))
        self.assertEqual(2, payload["findings"])

    def test_the_reason_is_no_longer_null_when_something_was_found(self):
        payload = self._payload_for([_Finding("T11#3", "### T11#3\n\nThe thing.")])

        self.assertIsNotNone(
            payload["reason"],
            "`findings: 1` with `reason: null` is what sent a reader looking "
            "in three places that do not hold the text (#3406)",
        )
        self.assertIn("FOLLOW-UPS.md", payload["reason"])
        self.assertIn("T11#3", payload["reason"])

    def test_the_finding_text_is_not_copied_into_the_event(self):
        # One verbatim record, not two that can disagree.
        payload = self._payload_for([
            _Finding("T11#3", "### T11#3\n\nA sentence only in the file.")])

        self.assertNotIn("A sentence only in the file", repr(payload))


class ThePathsThatFoundNothingAreUnchanged(unittest.TestCase):

    def test_a_disabled_judge_still_explains_itself(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        feature_dir = Path(tmp.name)
        (feature_dir / "PLAN.md").write_text(
            "---\nfeature_id: FEAT-2026-9999\njudge_disabled: true\n---\n")
        wu_file = feature_dir / "WU-90-close.md"
        wu_file.write_text("---\nid: X/G1-CLOSE\nverdict: met\n---\n")
        wu = SimpleNamespace(file=wu_file, wu_id="X/G1-CLOSE", verdict="met")

        with mock.patch.object(loop, "_gate_identity",
                               return_value=(1, feature_dir / "GATE-01.md")):
            payload = loop.judge_close(wu, feature_dir, feature_dir)

        self.assertFalse(payload["lowered"])
        self.assertEqual(0, payload["findings"])
        self.assertIsNotNone(payload["reason"])
        self.assertNotIn("findings_path", payload)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
