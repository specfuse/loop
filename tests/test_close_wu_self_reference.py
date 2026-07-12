#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Issue #145 — a close WU's own failed attempt must not arm the
failure-class-breakdown guard against that same close WU.

`assert_failure_class_breakdown_when_failures_present` requires a
`### Failure-class breakdown` subsection in RETROSPECTIVE.md once non-passing
attempts exist in the gate. It counted ALL non-passing attempts — including the
close WU's OWN. Since the close WU is the one that authors the RETROSPECTIVE the
guard inspects, its malformed first attempt retroactively added a required
subsection to its own output, and the between-attempt `reset --hard` wiped the
partial each retry → spin → blocked_human on otherwise-done features.

Fix #3: exclude the close WU's own attempts (correlation_id == its wu_id) from
the failure set that arms the guard against it. Substantive-WU failures still
require the breakdown. Fix #2: when the guard does fire, its message names the
required subsection and embeds the exact expected table (it flows into the retry
prompt via failure_note), so the agent doesn't rediscover the moved bar.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

CLOSE_ID = "FEAT-2026-0099/G1-CLOSE"
SUBSTANTIVE_ID = "FEAT-2026-0099/G1-T01"


def _close_wu(wu_file: Path) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=CLOSE_ID, file=wu_file, depends_on=[], type="close",
        model="opus", effort="high", status="pending", attempts=1,
        title="Close gate 1", body="body",
    )


def _attempt_event(correlation_id: str, outcome: str = "failed",
                   failure_class: str = "other", sig: str = "verdict_malformed") -> str:
    return json.dumps({
        "event_type": "attempt_outcome",
        "correlation_id": correlation_id,
        "timestamp": "2026-07-12T00:00:00Z",
        "payload": {"outcome": outcome, "failure_class": failure_class,
                    "failure_signature": sig},
    })


class TestCloseSelfReference(unittest.TestCase):
    def _feature_dir(self, tmp: str, events: list[str], retro: str = "# Retro\n") -> Path:
        d = Path(tmp)
        (d / "events.jsonl").write_text("\n".join(events) + "\n")
        (d / "RETROSPECTIVE.md").write_text(retro)
        return d

    def test_close_own_failure_does_not_arm_guard(self):
        # Only the close WU's OWN attempts are non-passing (the observed run).
        with tempfile.TemporaryDirectory() as tmp:
            d = self._feature_dir(tmp, [_attempt_event(CLOSE_ID)])
            wu = _close_wu(d / "WU.md")
            ok, msg = loop.assert_failure_class_breakdown_when_failures_present(
                wu, d, Path(tmp), "HEAD~1")
        self.assertTrue(ok, f"close's own failure must not require the breakdown: {msg}")

    def test_substantive_failure_still_requires_breakdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._feature_dir(
                tmp, [_attempt_event(SUBSTANTIVE_ID), _attempt_event(CLOSE_ID)])
            wu = _close_wu(d / "WU.md")
            ok, msg = loop.assert_failure_class_breakdown_when_failures_present(
                wu, d, Path(tmp), "HEAD~1")
        self.assertFalse(ok, "a substantive-WU failure still requires the breakdown")
        # Fix #2 — message is actionable and embeds the exact table to include.
        self.assertIn("### Failure-class breakdown", msg)
        self.assertIn("| failure_class |", msg)

    def test_breakdown_table_excludes_close_own_attempts(self):
        # Two substantive failures + one close-own failure; the rendered table
        # the guard offers must count only the two substantive ones.
        with tempfile.TemporaryDirectory() as tmp:
            d = self._feature_dir(
                tmp,
                [_attempt_event(SUBSTANTIVE_ID), _attempt_event(SUBSTANTIVE_ID),
                 _attempt_event(CLOSE_ID)])
            table = loop.summarize_attempt_failure_classes(
                d, gate_n=1, exclude_correlation_id=CLOSE_ID)
        self.assertIn("**total** | **2**", table)

    def test_summarize_all_self_returns_sentinel(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._feature_dir(tmp, [_attempt_event(CLOSE_ID)])
            table = loop.summarize_attempt_failure_classes(
                d, gate_n=1, exclude_correlation_id=CLOSE_ID)
        self.assertEqual(table, loop._NO_FAILURES_SENTINEL)

    def test_breakdown_present_passes(self):
        retro = "# Retro\n\n### Failure-class breakdown\n\n| x | 1 | y |\n"
        with tempfile.TemporaryDirectory() as tmp:
            d = self._feature_dir(tmp, [_attempt_event(SUBSTANTIVE_ID)], retro=retro)
            wu = _close_wu(d / "WU.md")
            ok, _ = loop.assert_failure_class_breakdown_when_failures_present(
                wu, d, Path(tmp), "HEAD~1")
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
