#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Stamping `folded_through_re_arm` onto pre-T01 re-armed WUs (FEAT-2026-0067/T02).

Six WUs in this repository were folded under the pre-T01 `cost_usd > 0` guard
and carry no `folded_through_re_arm` marker at all — indistinguishable, under
T01's rule, from "never folded". Two more were re-armed under a guard that
never fired, so the fold never ran; their prior spend survives only in
`re_arm_history[]`. This exercises `rearm_migration.py`'s handling of both
shapes.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

from specfuse.loop import rearm_migration as migration  # noqa: E402

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


class TestRearmMigration(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_wu(self, name: str, extra_yaml: str = "") -> Path:
        wu_file = self._root / name
        wu_file.write_text(
            "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
            "model: sonnet\nstatus: done\nattempts: 1\n"
            f"{extra_yaml}---\n\n# T01{_WU_BODY}"
        )
        return wu_file

    # -- criterion 1/2: fold-ran fixture is stamped, not re-folded ---------

    def test_fold_ran_wu_is_stamped_not_refolded(self):
        wu_file = self._write_wu(
            "WU-01.md",
            "re_arm_count: 2\ncumulative_cost_usd: 7.5\n"
            "cumulative_duration_seconds: 120.0\ncost_usd: 1.1\n",
        )
        outcome = migration.migrate_file(wu_file)
        self.assertEqual(outcome.action, "fold_ran_stamped")

        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(int(fm.get("folded_through_re_arm", -1)), 2)
        self.assertEqual(fm.get("cumulative_cost_usd"), 7.5,
                          "stamping must not re-fold cumulative_cost_usd")
        self.assertEqual(fm.get("cumulative_duration_seconds"), 120.0)

    # -- criterion 3: fold-never-ran fixture handled, fold no longer owed --

    def test_fold_never_ran_wu_migrated_and_fold_no_longer_owed(self):
        wu_file = self._write_wu(
            "WU-02.md",
            "re_arm_count: 1\ncost_usd: 0.16309\ninput_tokens: 9\n"
            "output_tokens: 1785\nre_arm_history:\n"
            "  -\n"
            "    timestamp: 2026-06-15T03:10:00+00:00\n"
            "    prior_status: blocked_human\n"
            "    prior_attempts: 0\n"
            "    prior_cost_usd: 0.16309\n"
            "    prior_duration_seconds: 42.693\n",
        )
        outcome = migration.migrate_file(wu_file)
        self.assertEqual(outcome.action, "fold_never_ran_migrated")

        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(fm.get("cumulative_cost_usd"), 0.16309)
        self.assertEqual(fm.get("cumulative_duration_seconds"), 42.693)
        self.assertEqual(int(fm.get("folded_through_re_arm", -1)), 1)

        self.assertFalse(
            loop.detect_rearm_dispatch(_make_wu(wu_file)),
            "migration's whole purpose: no fold owed after migration",
        )

    # -- criterion 4: idempotent ------------------------------------------

    def test_migration_is_idempotent(self):
        wu_file = self._write_wu(
            "WU-03.md",
            "re_arm_count: 1\ncost_usd: 5.0\nre_arm_history:\n"
            "  -\n"
            "    timestamp: 2026-06-15T03:10:00+00:00\n"
            "    prior_cost_usd: 5.0\n"
            "    prior_duration_seconds: 100.0\n",
        )
        migration.migrate_file(wu_file)
        after_first = wu_file.read_text()
        outcome_second = migration.migrate_file(wu_file)
        after_second = wu_file.read_text()

        self.assertEqual(after_first, after_second,
                          "a second pass must change nothing")
        self.assertEqual(outcome_second.action, "already_migrated")

    def test_fold_ran_migration_is_idempotent(self):
        wu_file = self._write_wu(
            "WU-03b.md", "re_arm_count: 2\ncumulative_cost_usd: 3.0\n"
        )
        migration.migrate_file(wu_file)
        after_first = wu_file.read_text()
        migration.migrate_file(wu_file)
        after_second = wu_file.read_text()
        self.assertEqual(after_first, after_second)

    # -- criterion 5: never re-armed WU is completely untouched -----------

    def test_never_rearmed_wu_untouched(self):
        wu_file = self._write_wu("WU-04.md", "cost_usd: 3.0\n")
        before = wu_file.read_text()
        outcome = migration.migrate_file(wu_file)
        after = wu_file.read_text()
        self.assertEqual(outcome.action, "not_rearmed")
        self.assertEqual(before, after)

    def test_rearm_count_zero_is_untouched(self):
        wu_file = self._write_wu("WU-05.md", "re_arm_count: 0\ncost_usd: 3.0\n")
        before = wu_file.read_text()
        migration.migrate_file(wu_file)
        after = wu_file.read_text()
        self.assertEqual(before, after)

    # -- criterion 7: frontmatter round-trips without collateral reformat --

    def test_fold_ran_round_trip_preserves_other_keys_and_body(self):
        original_extra = (
            "re_arm_count: 2\ncumulative_cost_usd: 7.5\n"
            "planned_cost_usd: 4.00\nproduces:\n  - specfuse/loop/x.py\n"
        )
        wu_file = self._write_wu("WU-06.md", original_extra)
        before_lines = wu_file.read_text().splitlines()

        migration.migrate_file(wu_file)

        after_lines = wu_file.read_text().splitlines()
        before_set = set(before_lines)
        after_set = set(after_lines)
        added = after_set - before_set
        removed = before_set - after_set

        self.assertEqual(removed, set(),
                          "no pre-existing line may be dropped or rewritten")
        self.assertEqual(
            added, {"folded_through_re_arm: 2"},
            "only the marker line may be newly added",
        )

    # -- census ---------------------------------------------------------

    def test_census_classifies_both_shapes(self):
        self._write_wu("WU-fold-ran.md", "re_arm_count: 1\ncumulative_cost_usd: 1.0\n")
        self._write_wu(
            "WU-fold-never.md",
            "re_arm_count: 1\nre_arm_history:\n  -\n    prior_cost_usd: 1.0\n",
        )
        self._write_wu("WU-never-rearmed.md", "")
        result = migration.census(self._root)
        self.assertEqual(len(result.fold_ran), 1)
        self.assertEqual(len(result.fold_never_ran), 1)

    # -- prior-cost disagreement escalation --------------------------------

    def test_prior_cost_disagreement_raises_and_writes_nothing(self):
        wu_file = self._write_wu(
            "WU-07.md",
            "re_arm_count: 1\ncost_usd: 1.0\n"
            "re_arm_history:\n"
            "  -\n"
            "    timestamp: 2026-06-15T03:10:00+00:00\n"
            "    prior_cost_usd: 99.0\n"
            "    prior_duration_seconds: 10.0\n",
        )
        events_file = self._root / "events.jsonl"
        events_file.write_text(json.dumps({
            "timestamp": "2026-06-15T01:00:00+00:00",
            "correlation_id": "FEAT-2026-9999/T01",
            "event_type": "attempt_outcome",
            "payload": {"cost_usd": 0.5},
        }) + "\n")

        before = wu_file.read_text()
        with self.assertRaises(migration.PriorCostDisagreement):
            migration.migrate_file(wu_file, events_path=events_file)
        after = wu_file.read_text()
        self.assertEqual(before, after, "a disagreement must not write anything")

    def test_prior_cost_agreement_within_tolerance_migrates(self):
        wu_file = self._write_wu(
            "WU-08.md",
            "re_arm_count: 1\ncost_usd: 1.0\n"
            "re_arm_history:\n"
            "  -\n"
            "    timestamp: 2026-06-15T03:10:00+00:00\n"
            "    prior_cost_usd: 5.01\n"
            "    prior_duration_seconds: 10.0\n",
        )
        events_file = self._root / "events.jsonl"
        with events_file.open("w") as fh:
            for cost in (1.6875993, 1.3786470, 1.9416126):
                fh.write(json.dumps({
                    "timestamp": "2026-06-15T01:00:00+00:00",
                    "correlation_id": "FEAT-2026-9999/T01",
                    "event_type": "attempt_outcome",
                    "payload": {"cost_usd": cost},
                }) + "\n")

        outcome = migration.migrate_file(wu_file, events_path=events_file)
        self.assertEqual(outcome.action, "fold_never_ran_migrated")


if __name__ == "__main__":
    unittest.main()
