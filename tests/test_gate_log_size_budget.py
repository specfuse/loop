"""#3499: persisted gate logs are bounded by bytes per feature, not only by
count per gate.

`GATE_LOG_KEEP` caps how many logs each gate keeps, but a generator `tests`
log runs ~138 MB, so 30 of them is ~4 GB for one feature; one operator
laptop held ~59 GB of gate logs. A byte budget across every gate's logs in
the feature prunes the oldest first, and never the log just written.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import loop


class TestGateLogSizeBudget(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.feature_dir = Path(self._tmp.name) / "feat"
        self.log_dir = self.feature_dir / "work" / "gate-logs"
        self.log_dir.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _seed(self, name, size, mtime):
        path = self.log_dir / name
        path.write_text("x" * size)
        os.utime(path, (mtime, mtime))
        return path

    def _names(self):
        return sorted(p.name for p in self.log_dir.glob("*.log"))

    def test_oldest_logs_across_gates_are_pruned_past_the_budget(self):
        self._seed("tests-20260101T000001Z.log", 400, 1000)
        self._seed("lint-20260101T000002Z.log", 400, 2000)
        self._seed("tests-20260101T000003Z.log", 400, 3000)
        with mock.patch.object(loop, "GATE_LOG_BUDGET_BYTES", 1000):
            new = loop.persist_gate_output(self.feature_dir, "lint", "y" * 400)
        self.assertIsNotNone(new)
        # 1600 bytes on disk; dropping the two oldest (one per gate) brings
        # it to 800, under the 1000-byte budget.
        self.assertEqual(self._names(), sorted(["tests-20260101T000003Z.log", new.name]))

    def test_the_log_just_written_survives_even_alone_over_budget(self):
        self._seed("tests-20260101T000001Z.log", 100, 1000)
        with mock.patch.object(loop, "GATE_LOG_BUDGET_BYTES", 1000):
            new = loop.persist_gate_output(self.feature_dir, "tests", "y" * 5000)
        self.assertEqual(self._names(), [new.name],
                         "the report names this log, so it must exist")

    def test_logs_under_budget_are_left_alone(self):
        self._seed("tests-20260101T000001Z.log", 100, 1000)
        self._seed("lint-20260101T000002Z.log", 100, 2000)
        with mock.patch.object(loop, "GATE_LOG_BUDGET_BYTES", 1000):
            new = loop.persist_gate_output(self.feature_dir, "tests", "y" * 100)
        self.assertEqual(len(self._names()), 3)
        self.assertIn(new.name, self._names())


if __name__ == "__main__":
    unittest.main()
