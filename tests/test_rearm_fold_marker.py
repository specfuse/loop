#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Explicit fold marker replaces the cost_usd > 0 guard (FEAT-2026-0067/T01).

detect_rearm_dispatch used to infer "already folded" from cost_usd's value,
which cannot distinguish "prior cycle cost nothing" from "already folded" —
both read as cost_usd == 0. This exercises the replacement: an explicit
folded_through_re_arm marker, stamped by fold_cumulative_on_rearm in the same
write set as the accumulators.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _make_wu(wu_file: Path) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=wu_file,
        depends_on=[],
        type="implementation",
        model="sonnet",
        status="pending",
        attempts=0,
        title="T01",
        body="",
    )


class TestFoldMarker(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_wu(self, extra_yaml: str = "") -> Path:
        wu_file = self._root / "WU-T01.md"
        wu_file.write_text(
            "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
            "model: sonnet\nstatus: pending\nattempts: 0\n"
            f"{extra_yaml}---\n\n# T01{_WU_BODY}"
        )
        return wu_file

    def test_zero_cost_rearm_still_folds(self):
        """The defect: a re-armed WU whose prior cycle genuinely cost $0 must
        still be detected as owing a fold. Under the old cost_usd > 0 guard
        this returns False and the fold never runs — fails on HEAD before
        this WU, passes after."""
        wu_file = self._write_wu(
            "re_arm_count: 1\ncost_usd: 0\nfolded_through_re_arm: 0\n"
        )
        self.assertTrue(
            loop.detect_rearm_dispatch(_make_wu(wu_file)),
            "a re-arm with zero-cost prior cycle must still be folded",
        )

    def test_rearm_with_zero_cost_and_marker_behind_folds(self):
        wu_file = self._write_wu(
            "re_arm_count: 2\ncost_usd: 0\nfolded_through_re_arm: 1\n"
        )
        self.assertTrue(loop.detect_rearm_dispatch(_make_wu(wu_file)))

    def test_marker_caught_up_does_not_fold_twice(self):
        wu_file = self._write_wu(
            "re_arm_count: 2\ncost_usd: 3.5\nfolded_through_re_arm: 2\n"
        )
        self.assertFalse(loop.detect_rearm_dispatch(_make_wu(wu_file)))

    def test_first_time_dispatch_unaffected(self):
        wu_file = self._write_wu("re_arm_count: 0\ncost_usd: 5.0\n")
        self.assertFalse(loop.detect_rearm_dispatch(_make_wu(wu_file)))

        wu_file2 = self._write_wu()
        self.assertFalse(loop.detect_rearm_dispatch(_make_wu(wu_file2)))

    def test_fold_stamps_folded_through_re_arm(self):
        wu_file = self._write_wu(
            "re_arm_count: 3\ncost_usd: 2.0\ninput_tokens: 4\noutput_tokens: 6\n"
        )
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), loop.Backend())
        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(int(fm.get("folded_through_re_arm", -1)), 3)

    def test_fold_idempotent_across_all_four_accumulators(self):
        wu_file = self._write_wu(
            "re_arm_count: 1\ncost_usd: 4.25\nduration_seconds: 12.5\n"
            "input_tokens: 100\noutput_tokens: 50\n"
        )
        backend = loop.Backend()
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), backend)
        fm_once, _ = loop.read_frontmatter(wu_file)
        once = {
            k: fm_once.get(k)
            for k in (
                "cumulative_cost_usd",
                "cumulative_duration_seconds",
                "cumulative_input_tokens",
                "cumulative_output_tokens",
            )
        }

        loop.fold_cumulative_on_rearm(_make_wu(wu_file), backend)
        fm_twice, _ = loop.read_frontmatter(wu_file)
        twice = {
            k: fm_twice.get(k)
            for k in (
                "cumulative_cost_usd",
                "cumulative_duration_seconds",
                "cumulative_input_tokens",
                "cumulative_output_tokens",
            )
        }

        self.assertEqual(once, twice,
                          "two folds for one re-arm must match a single fold "
                          "across cost, duration, input and output tokens")
        self.assertEqual(once["cumulative_cost_usd"], 4.25)
        self.assertEqual(once["cumulative_duration_seconds"], 12.5)
        self.assertEqual(once["cumulative_input_tokens"], 100)
        self.assertEqual(once["cumulative_output_tokens"], 50)


if __name__ == "__main__":
    unittest.main()
