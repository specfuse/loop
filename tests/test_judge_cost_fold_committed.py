#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A judged close commits its judge cost, rather than leaving it in the tree (#3296).

After a `close` unit passes, the driver folds the judge session's spend into the
close's cumulative usage and writes it to the WU frontmatter. That write lands
AFTER the squash commit, and nothing committed it: `_fire_and_verify_terminal_flips`
commits only `flip_paths` (the gate file, the roadmap row, `PLAN.md`), and the
only `commit_bookkeeping` following the fold sits on the `not_met` /
`revert_terminal_surfaces` path. So a `met` close finished with the write still
in the working tree.

Observed on FEAT-2026-0110/G1-CLOSE (2026-09-10): `cost_usd` 5.359607 ->
5.582307, `input_tokens` 100 -> 108, `output_tokens` 40501 -> 41745 — exactly the
`judged` event's `judge_cost_usd: 0.2227` and `usage` of 8/1244.

`events.jsonl` carries the folded number, so `wu_lifetime_cost_usd`'s primary
source stays correct. What breaks is the committed record: the driver ends with a
dirty tree (which `/wrap-feature` refuses to push from), and the committed
frontmatter under-reports the close by exactly the judge's spend — making the
separate judge session FEAT-2026-0100 built for attributable cost look free.

The fold happens BEFORE the verdict branch, so the commit must not be attached to
either verdict.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop

loop = load_loop()


class _Backend:
    """Records frontmatter writes without touching disk."""

    def __init__(self):
        self.written: dict[str, object] = {}

    def set_wu(self, wu, key, value):
        self.written[key] = value


def _judged(cost: float = 0.2227, inp: int = 8, out: int = 1244) -> dict:
    return {
        "gate": 1,
        "close_verdict": "met",
        "judge_verdict": "met",
        "verdict": "met",
        "lowered": False,
        "usage": {
            "cost_usd": cost,
            "input_tokens": inp,
            "output_tokens": out,
        },
    }


class TestJudgeCostFoldIsCommitted(unittest.TestCase):

    def setUp(self):
        self.wu = loop.WorkUnit(
            wu_id="FEAT-2026-9999/G1-CLOSE",
            file=Path("/tmp/does-not-matter/WU-90-gate-1-close.md"),
            depends_on=[], type="close", model="opus", status="in_progress",
            attempts=1, title="Close", body="",
        )

    def test_the_fold_commits_the_wu_file(self):
        backend = _Backend()
        attempt_usage = {"cost_usd": 5.359607, "input_tokens": 100,
                         "output_tokens": 40501}
        cum_usage = dict(attempt_usage)

        with mock.patch.object(loop, "commit_bookkeeping") as commit:
            loop.record_judge_cost_fold(
                backend, self.wu, attempt_usage, cum_usage,
                _judged(), "FEAT-2026-9999")

        self.assertTrue(
            commit.called,
            "the judge's cost fold is written to the WU frontmatter after the "
            "squash commit — if nothing commits it, the driver finishes with a "
            "dirty tree and the committed record under-reports the close by "
            "exactly the judge's spend (#3296)")
        paths = commit.call_args[0][0]
        self.assertIn(
            self.wu.file, list(paths),
            "the commit must carry the close WU's own file — that is where "
            "write_cost_to_wu put the folded number")

    def test_the_fold_still_lands_in_the_frontmatter(self):
        """The commit must not displace the write it exists to persist."""
        backend = _Backend()
        attempt_usage = {"cost_usd": 5.359607, "input_tokens": 100,
                         "output_tokens": 40501}
        cum_usage = dict(attempt_usage)

        with mock.patch.object(loop, "commit_bookkeeping"):
            loop.record_judge_cost_fold(
                backend, self.wu, attempt_usage, cum_usage,
                _judged(), "FEAT-2026-9999")

        self.assertAlmostEqual(backend.written["cost_usd"], 5.582307, places=6)
        self.assertEqual(backend.written["input_tokens"], 108)
        self.assertEqual(backend.written["output_tokens"], 41745)

    def test_both_usage_dicts_are_folded(self):
        """attempt_usage feeds the attempt_outcome event; cum_usage feeds the
        frontmatter. Folding only one is how the two came to disagree."""
        backend = _Backend()
        attempt_usage = {"cost_usd": 1.0, "input_tokens": 10, "output_tokens": 20}
        cum_usage = {"cost_usd": 2.0, "input_tokens": 30, "output_tokens": 40}

        with mock.patch.object(loop, "commit_bookkeeping"):
            loop.record_judge_cost_fold(
                backend, self.wu, attempt_usage, cum_usage,
                _judged(cost=0.5, inp=1, out=2), "FEAT-2026-9999")

        self.assertAlmostEqual(attempt_usage["cost_usd"], 1.5, places=6)
        self.assertAlmostEqual(cum_usage["cost_usd"], 2.5, places=6)

    def test_a_judge_with_no_usage_envelope_commits_nothing(self):
        """A plain-text or skipped judge has no spend to record, so there is no
        write to persist and no empty commit to make."""
        backend = _Backend()
        attempt_usage = {"cost_usd": 5.0, "input_tokens": 1, "output_tokens": 2}
        cum_usage = dict(attempt_usage)

        with mock.patch.object(loop, "commit_bookkeeping") as commit:
            loop.record_judge_cost_fold(
                backend, self.wu, attempt_usage, cum_usage,
                {"verdict": "met"}, "FEAT-2026-9999")

        self.assertFalse(commit.called)
        self.assertEqual(backend.written, {})
        self.assertAlmostEqual(attempt_usage["cost_usd"], 5.0, places=6)

    def test_the_judge_cost_is_stamped_on_the_payload(self):
        """`judge_cost_usd` is what the `judged` event reports, and it is
        rounded at the same precision the frontmatter uses."""
        backend = _Backend()
        payload = _judged(cost=0.22269999)
        with mock.patch.object(loop, "commit_bookkeeping"):
            loop.record_judge_cost_fold(
                backend, self.wu, {"cost_usd": 0.0}, {"cost_usd": 0.0},
                payload, "FEAT-2026-9999")
        self.assertEqual(payload["judge_cost_usd"], 0.2227)


if __name__ == "__main__":
    unittest.main()
