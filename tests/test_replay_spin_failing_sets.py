# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`replay_with_failing_sets` re-judges historical spin escalations.

FEAT-2026-0116/T02 changed `detect_spinning_signature_repeat` to compare
failing-test sets (when both attempts named recognisable per-test ids)
ahead of the old `(failure_class, failure_signature)` comparison. This
answers, for escalations already recorded in `events.jsonl` before that
change shipped, whether the new rule would still have fired.

Old events carry no `failing_tests` field (bootstrap gap) and the full gate
log is gone, so the only surviving evidence is the 500-char
`failure_excerpt` persisted at emission time. This re-derives a failing set
from that excerpt with today's `extract_failing_tests` and says explicitly
that the excerpt is all that is left to re-derive from.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import replay_spin


def _write_events(tmp: Path, rows: list) -> Path:
    """An events.jsonl of `attempt_outcome` rows followed by one escalation.

    *rows* is a list of (attempt, failure_class, failure_signature,
    failure_excerpt) tuples for consecutive failed attempts on one work
    unit; the escalation event always follows the last row.
    """
    feat = tmp / "FEAT-2026-8888-example"
    feat.mkdir(parents=True)
    lines = []
    for attempt, fc, fs, excerpt in rows:
        lines.append(json.dumps({
            "event_type": "attempt_outcome",
            "correlation_id": "FEAT-2026-8888/T04",
            "payload": {"attempt": attempt, "outcome": "failed",
                        "failure_class": fc, "failure_signature": fs,
                        "failure_excerpt": excerpt},
        }))
    lines.append(json.dumps({
        "event_type": "human_escalation",
        "correlation_id": "FEAT-2026-8888/T04",
        "payload": {"reason": "spinning_signature_repeat",
                    "failure_class": rows[-1][1],
                    "failure_signature": rows[-1][2],
                    "attempts": rows[-1][0]},
    }))
    (feat / "events.jsonl").write_text("\n".join(lines) + "\n")
    return feat / "events.jsonl"


class TestReplayWithFailingSets(unittest.TestCase):
    def test_differing_failing_tests_would_not_fire(self):
        with tempfile.TemporaryDirectory() as tmp:
            events_path = _write_events(Path(tmp), [
                (1, "tests", "generic maven failure", "FAIL: test_a"),
                (2, "tests", "generic maven failure", "FAIL: test_b"),
            ])
            out = replay_spin.replay_with_failing_sets([events_path])

        escalations = out["features"]["FEAT-2026-8888-example"]
        self.assertEqual(len(escalations), 1)
        self.assertTrue(escalations[0]["fired_historically"])
        self.assertEqual(escalations[0]["would_fire"], False)

    def test_same_failing_tests_would_fire(self):
        with tempfile.TemporaryDirectory() as tmp:
            events_path = _write_events(Path(tmp), [
                (1, "tests", "generic maven failure", "FAIL: test_a"),
                (2, "tests", "generic maven failure", "FAIL: test_a"),
            ])
            out = replay_spin.replay_with_failing_sets([events_path])

        escalations = out["features"]["FEAT-2026-8888-example"]
        self.assertEqual(escalations[0]["would_fire"], True)

    def test_the_report_says_the_full_log_is_gone(self):
        with tempfile.TemporaryDirectory() as tmp:
            events_path = _write_events(Path(tmp), [
                (1, "tests", "x", "FAIL: test_a"),
                (2, "tests", "x", "FAIL: test_a"),
            ])
            out = replay_spin.replay_with_failing_sets([events_path])

        self.assertIn("failure_excerpt", out["note"])
        report = replay_spin.format_failing_sets_report(out)
        self.assertIn("failure_excerpt", report)

    def test_no_recognisable_ids_is_not_classified_as_would_fire(self):
        with tempfile.TemporaryDirectory() as tmp:
            events_path = _write_events(Path(tmp), [
                (1, "tests", "x", "some unrecognised chatter"),
                (2, "tests", "x", "more unrecognised chatter"),
            ])
            out = replay_spin.replay_with_failing_sets([events_path])

        escalations = out["features"]["FEAT-2026-8888-example"]
        self.assertIsNone(escalations[0]["would_fire"])
        self.assertFalse(escalations[0]["classified"])


if __name__ == "__main__":
    unittest.main()
