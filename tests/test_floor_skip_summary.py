# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A bug held back by the severity floor is not told to "re-run" (#3521).

A 2026-10-18 run's summary said `1 newly triaged as bug, not dispatched —
re-run to fix them: #2833`. #2833 carried only `severity:minor`, which does not
clear `min_severity: medium` (read as absent on that repository, as `low`
under the default aliases), so a re-run would not dispatch it either. The summary
now names the floor as the reason, the way `BugsProvider.advertise` reports a
skip, and keeps "re-run" for bugs a re-run would actually reach.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import _format_summary, run_agent
from tests.test_agent_snapshot_refresh import (
    _BugsDouble,
    _FakeClock,
    _IssueListRunner,
    _TriageDouble,
)

_POLICY = """\
version: 1
queue: []
rules:
  bugs:
    min_severity: medium
"""


def _run(runner, providers, *, reports, max_items):
    with tempfile.TemporaryDirectory() as tmp:
        specfuse_dir = Path(tmp) / ".specfuse"
        specfuse_dir.mkdir()
        features_root = specfuse_dir / "features"
        features_root.mkdir()
        policy = specfuse_dir / "agent-policy.yml"
        policy.write_text(_POLICY)
        return run_agent(
            specfuse_dir=specfuse_dir,
            repo="acme/widget",
            runner=runner,
            providers=providers,
            policy_path=str(policy),
            features_root=features_root,
            clock=_FakeClock(),
            max_items=max_items,
            reporter=reports.append,
        )


class FloorSkippedBugIsNotToldToReRun(unittest.TestCase):
    def _summary(self, labels):
        runner = _IssueListRunner([
            {"number": 2833, "title": "minor glitch", "labels": labels,
             "body": "no marker"},
        ])
        reports = []
        summary = _run(runner, (_BugsDouble(), _TriageDouble(runner)),
                       reports=reports, max_items=1)
        return summary, reports

    def test_below_floor_bug_names_the_floor_not_a_re_run(self):
        summary, reports = self._summary([{"name": "severity:minor"}])

        text = _format_summary(summary)
        self.assertEqual(summary.newly_triaged_bugs_undispatched, ())
        self.assertNotIn("re-run to fix them", text)
        self.assertIn("#2833", text)
        self.assertIn("below the medium floor", text)
        self.assertFalse(any("re-run to fix them" in line for line in reports))
        self.assertTrue(any("#2833" in line and "floor" in line for line in reports),
                        f"the run must name the floor as it finishes, got {reports!r}")

    def test_bug_that_clears_the_floor_is_still_told_to_re_run(self):
        summary, _reports = self._summary([{"name": "severity:high"}])

        self.assertEqual(summary.newly_triaged_bugs_undispatched, (2833,))
        self.assertIn("re-run to fix them: #2833", _format_summary(summary))


if __name__ == "__main__":
    unittest.main()
