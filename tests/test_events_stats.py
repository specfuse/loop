#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the events.jsonl cost aggregator (issue #271).

The loop writes a rich per-attempt record and nothing read it for cost. An
afternoon of ad-hoc Python over that corpus produced four merged fixes (#266,
#268, #269, #272) — and none of it was reproducible by anyone else, including
the person who wrote it.

The properties that actually mattered in that analysis, and so are pinned here:

**Dedupe on (correlation_id, timestamp, event_type).** The same repository
appears at multiple paths — worktrees, parallel checkouts — and a naive glob
double-counts. In the workspace this was derived from, 13 paths collapsed to 9
distinct repositories. Without the dedupe every figure is inflated by an
arbitrary factor.

**Cost of PASSING attempts, separated from waste.** A floor is calibrated from
what a successful attempt costs. Mixing refused attempts into that number is
what produced the $12.00 floor #266 had to reverse.

**Diagnostics read per the documented contract.** Each outcome puts its reason
in a different field (`docs/methodology.md`, per-attempt outcome events). A
consumer that reads only `failure_class` reports complete records as empty —
three times, in the audit that led to #272.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import events_stats


def _ev(cid, ts, outcome, cost, *, etype="attempt_outcome", attempt=1, **payload):
    return json.dumps({
        "timestamp": ts,
        "correlation_id": cid,
        "event_type": etype,
        "payload": {"outcome": outcome, "cost_usd": cost, "attempt": attempt, **payload},
    })


class _Corpus(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _feature(self, repo: str, feat: str, lines: list[str]) -> None:
        d = self.root / repo / ".specfuse" / "features" / feat
        d.mkdir(parents=True, exist_ok=True)
        (d / "events.jsonl").write_text("\n".join(lines) + "\n")


class TestDedupe(_Corpus):
    def test_the_same_event_at_two_paths_is_counted_once(self):
        """Worktrees and parallel checkouts duplicate whole feature folders."""
        line = _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "passed", 3.00)
        self._feature("repo-a", "FEAT-2026-0001-x", [line])
        self._feature("repo-a-worktree", "FEAT-2026-0001-x", [line])
        stats = events_stats.collect([self.root])
        self.assertEqual(stats["totals"]["attempts"], 1)
        self.assertAlmostEqual(stats["totals"]["spend"], 3.00, places=2)

    def test_distinct_timestamps_are_kept(self):
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "failed", 1.0, attempt=1),
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:05:00Z", "passed", 2.0, attempt=2),
        ])
        self.assertEqual(events_stats.collect([self.root])["totals"]["attempts"], 2)


class TestPassingCostSeparatedFromWaste(_Corpus):
    """The distinction #266 turned on."""

    def setUp(self):
        super().setUp()
        self._feature("r", "F", [
            # one plan-next that retried: $9 wasted, $4 real
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "failed", 9.0, attempt=1),
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:05:00Z", "passed", 4.0, attempt=2),
            # one that passed first try
            _ev("FEAT-2026-0002/G1-PLAN", "2026-07-02T10:00:00Z", "passed", 2.0),
        ])
        self.stats = events_stats.collect([self.root])

    def test_cost_stats_use_passing_attempts_only(self):
        pn = self.stats["by_type"]["plan-next"]
        self.assertEqual(sorted(pn["passing_costs"]), [2.0, 4.0])
        self.assertAlmostEqual(pn["median"], 3.0, places=2)

    def test_waste_is_reported_separately(self):
        self.assertAlmostEqual(self.stats["totals"]["waste"], 9.0, places=2)
        self.assertAlmostEqual(self.stats["totals"]["spend"], 15.0, places=2)

    def test_first_try_rate_is_per_work_unit_not_per_attempt(self):
        """Two WUs, one passed first try."""
        self.assertAlmostEqual(self.stats["by_type"]["plan-next"]["first_try_rate"], 0.5, places=2)


class TestGuardAttribution(_Corpus):
    def test_waste_is_attributed_to_the_named_guard(self):
        """The ranking that drove #268: which guard costs the most."""
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z",
                "closing_deliverable_missing", 8.0,
                summary="assert_gate_review_exists: GATE-02-REVIEW.md absent or empty"),
            _ev("FEAT-2026-0002/G1-CLOSE", "2026-07-02T10:00:00Z",
                "closing_deliverable_missing", 3.0,
                summary="assert_retrospective_gate_section: no '## Gate 1'"),
            _ev("FEAT-2026-0003/G1-PLAN", "2026-07-03T10:00:00Z",
                "closing_deliverable_missing", 5.0,
                summary="assert_gate_review_exists: GATE-02-REVIEW.md absent or empty"),
        ])
        guards = events_stats.collect([self.root])["by_guard"]
        self.assertAlmostEqual(guards["assert_gate_review_exists"]["waste"], 13.0, places=2)
        self.assertEqual(guards["assert_gate_review_exists"]["fires"], 2)


class TestDiagnosticContract(_Corpus):
    """Reads the reason per the documented per-outcome field (#272).

    A consumer that checks only `failure_class` reports complete records as
    empty. That error was made three times before the contract was written down.
    """

    def test_blocked_reason_is_found_in_agent_blocked_reason(self):
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/T01", "2026-07-01T10:00:00Z", "blocked", 2.0,
                agent_blocked_reason="spec ambiguity in AC3"),
        ])
        s = events_stats.collect([self.root])
        self.assertEqual(s["undiagnosed"], 0)

    def test_unchanged_paths_counts_as_a_diagnostic(self):
        """Pre-0.3.23 files_changed_mismatch carries only this field."""
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/T01", "2026-07-01T10:00:00Z",
                "files_changed_mismatch", 1.0, unchanged_paths=["src/a.py"]),
        ])
        self.assertEqual(events_stats.collect([self.root])["undiagnosed"], 0)

    def test_zero_token_skip_is_not_counted_as_undiagnosed(self):
        """Nothing ran, so there is nothing to describe."""
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/T01", "2026-07-01T10:00:00Z", "zero_token_skip", 0.0),
        ])
        self.assertEqual(events_stats.collect([self.root])["undiagnosed"], 0)

    def test_a_genuinely_mute_failure_is_counted(self):
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/T01", "2026-07-01T10:00:00Z", "failed", 1.0),
        ])
        self.assertEqual(events_stats.collect([self.root])["undiagnosed"], 1)


class TestRobustness(_Corpus):
    def test_malformed_lines_are_skipped_not_fatal(self):
        d = self.root / "r" / ".specfuse" / "features" / "F"
        d.mkdir(parents=True)
        (d / "events.jsonl").write_text(
            "not json\n"
            + _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "passed", 1.0) + "\n"
            + "\n{ broken\n"
        )
        self.assertEqual(events_stats.collect([self.root])["totals"]["attempts"], 1)

    def test_no_corpus_returns_empty_rather_than_raising(self):
        stats = events_stats.collect([self.root])
        self.assertEqual(stats["totals"]["attempts"], 0)
        self.assertEqual(stats["by_type"], {})

    def test_a_root_two_levels_above_the_repo_still_finds_it(self):
        """Pointing at a home directory rather than a workspace is the obvious
        mistake, and returning 0 silently reads as 'no waste' rather than
        'wrong path'. Both common depths are supported."""
        self._feature("workspace/repo", "F", [
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "passed", 1.0),
        ])
        self.assertEqual(events_stats.collect([self.root])["totals"]["attempts"], 1)

    def test_empty_corpus_exits_nonzero_rather_than_printing_a_clean_report(self):
        import contextlib
        import io
        import sys
        buf = io.StringIO()
        argv = sys.argv
        sys.argv = ["events_stats.py", "--roots", str(self.root)]
        try:
            with contextlib.redirect_stdout(buf):
                rc = events_stats.main()
        finally:
            sys.argv = argv
        self.assertEqual(rc, 1, "an empty corpus must not exit 0 with a clean report")
        self.assertIn("no events.jsonl found", buf.getvalue())

    def test_non_closing_wus_are_bucketed_as_implementation(self):
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/T01", "2026-07-01T10:00:00Z", "passed", 1.0),
        ])
        self.assertIn("implementation", events_stats.collect([self.root])["by_type"])


class TestRendering(_Corpus):
    def test_json_output_round_trips(self):
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "passed", 1.0),
        ])
        stats = events_stats.collect([self.root])
        self.assertEqual(json.loads(json.dumps(stats))["totals"]["attempts"], 1)

    def test_report_names_the_dedupe_so_a_reader_can_trust_the_n(self):
        self._feature("r", "F", [
            _ev("FEAT-2026-0001/G1-PLAN", "2026-07-01T10:00:00Z", "passed", 1.0),
        ])
        text = events_stats.render(events_stats.collect([self.root]))
        self.assertIn("repositor", text.lower())


if __name__ == "__main__":
    unittest.main()
