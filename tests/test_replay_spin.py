#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`replay_spin` re-derives a past escalation's signatures with today's parser.

The tool answers "would the driver have caught this?" from artifacts already
on disk, which is the cheap counterpart to re-running an escalation at full
price. Its load-bearing behaviours:

- recorded (what the driver stored at run time) and replayed (what this
  checkout's parser produces from the attempt note) are reported side by
  side, because the whole point is that they can disagree;
- a recorded `('other','no_gate_marker')` whose replay names a real
  signature is flagged, since `detect_spinning_signature_repeat` ignores
  that sentinel and the early halt could not have fired while a gate
  produced it (#2557);
- the halt is located at the FIRST attempt whose signature repeats, and only
  spend *after* that point counts as avoidable — the attempt that trips the
  detector is already paid for.

`parse_fn`/`spin_fn` are injected so these assert the replay logic rather
than re-asserting the parser's behaviour, which `test_hyphenated_gate_name`
already owns.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import replay_spin


def _feature(tmp: Path, rows: list, notes: dict | None = None) -> Path:
    """A feature folder with an events.jsonl and optional attempt notes."""
    feat = tmp / "FEAT-2026-9999-example"
    (feat / "work" / "FEAT-2026-9999_T04").mkdir(parents=True)
    lines = []
    for attempt, outcome, cost, fc, fs in rows:
        lines.append(json.dumps({
            "event_type": "attempt_outcome",
            "correlation_id": "FEAT-2026-9999/T04",
            "payload": {"attempt": attempt, "outcome": outcome,
                        "cost_usd": cost, "failure_class": fc,
                        "failure_signature": fs},
        }))
    (feat / "events.jsonl").write_text("\n".join(lines) + "\n")
    for attempt, text in (notes or {}).items():
        (feat / "work" / "FEAT-2026-9999_T04"
         / f"attempt-{attempt}.md").write_text(text)
    return feat


def _repeating_parse(note: str):
    return ("tests", note.strip())


def _real_spin(current, prior):
    from specfuse.loop.loop import detect_spinning_signature_repeat
    return detect_spinning_signature_repeat(current, prior)


class TestReadingRecordedAttempts(unittest.TestCase):
    def test_passing_attempts_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), [
                (1, "failed", 1.0, "tests", "test_a"),
                (2, "passed", 2.0, None, None),
            ])
            rows = replay_spin.read_recorded_attempts(feat)

        self.assertEqual([r["attempt"] for r in rows], [1])

    def test_a_missing_event_log_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "no-events"
            empty.mkdir()

            self.assertEqual(replay_spin.read_recorded_attempts(empty), [])

    def test_a_truncated_tail_does_not_lose_earlier_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), [(1, "failed", 1.0, "tests", "test_a")])
            with (feat / "events.jsonl").open("a") as fh:
                fh.write('{"event_type": "attempt_outcome", "payl')

            rows = replay_spin.read_recorded_attempts(feat)

        self.assertEqual(len(rows), 1)

    def test_the_work_unit_filter_selects_by_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), [(1, "failed", 1.0, "tests", "test_a")])

            self.assertEqual(len(replay_spin.read_recorded_attempts(feat, "T04")), 1)
            self.assertEqual(replay_spin.read_recorded_attempts(feat, "T99"), [])


class TestTheHaltIsLocated(unittest.TestCase):
    def test_a_repeated_signature_halts_at_the_second_occurrence(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(
                Path(tmp),
                [(1, "failed", 1.0, "tests", "test_a"),
                 (2, "failed", 2.0, "tests", "test_a"),
                 (3, "failed", 4.0, "tests", "test_a")],
                notes={1: "test_a", 2: "test_a", 3: "test_a"})
            out = replay_spin.replay(feat, "T04", _repeating_parse, _real_spin)

        self.assertEqual(out["halt_at"], 2)
        # Attempt 2 trips the detector and is already paid for; only attempt
        # 3's spend was avoidable.
        self.assertAlmostEqual(out["avoidable_usd"], 4.0)
        self.assertAlmostEqual(out["spent_usd"], 7.0)

    def test_differing_signatures_never_halt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(
                Path(tmp),
                [(1, "failed", 1.0, "tests", "test_a"),
                 (2, "failed", 2.0, "tests", "test_b")],
                notes={1: "test_a", 2: "test_b"})
            out = replay_spin.replay(feat, "T04", _repeating_parse, _real_spin)

        self.assertIsNone(out["halt_at"])
        self.assertEqual(out["avoidable_usd"], 0.0)

    def test_missing_notes_leave_the_replay_unknown_rather_than_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp), [(1, "failed", 1.0, "tests", "test_a")])
            out = replay_spin.replay(feat, "T04", _repeating_parse, _real_spin)

        self.assertTrue(out["rows"][0]["note_missing"])
        self.assertIsNone(out["rows"][0]["replayed"])
        self.assertIsNone(out["halt_at"])


class TestRecoveredSignaturesAreFlagged(unittest.TestCase):
    def test_a_sentinel_that_replays_to_a_real_signature_is_flagged(self):
        # The #2557 shape: recorded as the no-marker sentinel, re-parsed
        # today into a nameable failure.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(
                Path(tmp),
                [(1, "failed", 2.19, "other", "no_gate_marker")],
                notes={1: "not ok 1 vendor records a baseline"})
            out = replay_spin.replay(feat, "T04", _repeating_parse, _real_spin)

        self.assertTrue(out["rows"][0]["recovered"])
        self.assertIn("OLD PARSER COULD NOT NAME THIS",
                      replay_spin.format_report(out, "x", 3))

    def test_a_sentinel_with_no_note_is_not_claimed_as_recovered(self):
        # Nothing was re-parsed, so nothing is known either way. Claiming a
        # recovery here would invent evidence.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp),
                            [(1, "failed", 2.19, "other", "no_gate_marker")])
            out = replay_spin.replay(feat, "T04", _repeating_parse, _real_spin)

        self.assertFalse(out["rows"][0]["recovered"])

    def test_a_sentinel_that_still_replays_to_the_sentinel_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _feature(Path(tmp),
                            [(1, "failed", 1.0, "other", "no_gate_marker")],
                            notes={1: "chatter"})
            out = replay_spin.replay(
                feat, "T04", lambda _n: replay_spin.NO_MARKER, _real_spin)

        self.assertFalse(out["rows"][0]["recovered"])


class TestTheReportNamesItsOwnDriver(unittest.TestCase):
    def test_the_driver_source_is_printed_first(self):
        # Replaying against an installed build while believing you replayed
        # against the checkout is #2642's defect; the report must make the
        # resolved source visible rather than leave it inferred.
        report = replay_spin.format_report(
            {"rows": [], "halt_at": None, "spent_usd": 0.0,
             "avoidable_usd": 0.0},
            "/somewhere/specfuse/loop/loop.py", 3)

        self.assertTrue(report.startswith("driver source: "))
        self.assertIn("/somewhere/specfuse/loop/loop.py", report)

    def test_an_empty_result_says_so_rather_than_printing_a_clean_run(self):
        report = replay_spin.format_report(
            {"rows": [], "halt_at": None, "spent_usd": 0.0,
             "avoidable_usd": 0.0}, "x", 3)

        self.assertIn("no non-passing attempt_outcome rows found", report)


class TestTheModuleIsClassified(unittest.TestCase):
    def test_replay_spin_is_registered_as_a_non_judge_module(self):
        # Every module under specfuse/loop/ must be classified in writing;
        # this one grants no verdict.
        from specfuse.loop import arm_eval

        self.assertIn("replay_spin.py", arm_eval.NON_JUDGE_MODULES)


if __name__ == "__main__":
    unittest.main()
