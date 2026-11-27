#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A re-armed unit keeps its folded cost when the new cycle ends blocked (#3552).

`fold_cumulative_on_rearm` moves the prior cycle's `cost_usd` (and duration,
tokens) into `cumulative_*` and stamps `folded_through_re_arm`. It wrote those
fields after `head_before` was taken and did not commit them, so a failed or
refused attempt's `git reset --hard head_before` erased the fold. The blocked
path then wrote the new cycle's `cost_usd` over the prior one, and the prior
cycle's spend vanished from the unit's lifetime cost.
"""

from __future__ import annotations

import io
import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
_FEATURE = "FEAT-2026-9552"


def _frontmatter(path: Path) -> dict:
    fm, _ = loop.read_frontmatter(path)
    return fm


class RearmFoldSurvivesABlockedCycle(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _run(self, sessions):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / f".specfuse/features/{_FEATURE}-fold"
            fdir.mkdir(parents=True)
            t_id = f"{_FEATURE}/T01"
            (fdir / "PLAN.md").write_text(
                f"---\nfeature_id: {_FEATURE}\ntitle: Fixture\nslug: fold\n"
                f"branch: feat/fold\nroadmap_goal: test\nstatus: active\n---\n\n"
                f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
                f"    work_units:\n      - id: {t_id}\n        file: WU-T01.md\n"
                f"        depends_on: []\n```\n")
            (fdir / "GATE-01.md").write_text(
                "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
            # Re-armed once by hand, as /unblock-wu writes it: the prior
            # cycle's $0.926254 sits in cost_usd, nothing folded yet.
            (fdir / "WU-T01.md").write_text(
                f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
                f"status: pending\nattempts: 0\nmax_attempts: 2\n"
                f"cost_usd: 0.926254\nduration_seconds: 100.0\n"
                f"input_tokens: 10\noutput_tokens: 20\nre_arm_count: 1\n"
                f"re_arm_history:\n  -\n    timestamp: 2026-10-29T00:00:00+00:00\n"
                f"    prior_status: blocked_human\n    prior_attempts: 1\n"
                f"    prior_cost_usd: 0.926254\n    prior_duration_seconds: 100.0\n"
                f"    reason: \"retry\"\n---\n\n# T01{_WU_BODY}")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-q", "-m", "scaffold"], check=True)

            calls = iter(sessions)

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # A re-plan turn before the last attempt dispatches too; it
                # is not one of the unit's attempts.
                if wu.body.startswith(loop._REPLAN_BRIEF_MARKER):
                    return "Re-planned body.\n", None
                return next(calls)(), {"input_tokens": 5, "output_tokens": 5,
                                       "cost_usd": 0.118917}

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, *a, **k: (False, "### t: FAIL\nboom"))
            with redirect_stdout(io.StringIO()):
                loop.run(None, dry_run=False)
            return _frontmatter(fdir / "WU-T01.md")

    def test_blocked_first_attempt_keeps_the_fold(self):
        fm = self._run([lambda: "```result\nstatus: blocked\n"
                                "blocked_reason: needs a human\n```\n"])
        self.assertEqual(fm.get("status"), "blocked_human")
        self.assertAlmostEqual(float(fm.get("cumulative_cost_usd") or 0),
                               0.926254, places=6)
        self.assertEqual(fm.get("folded_through_re_arm"), 1)
        self.assertAlmostEqual(float(fm.get("cost_usd") or 0), 0.118917, places=6)

    def test_failed_attempt_then_blocked_keeps_the_fold(self):
        def deliver():
            Path("src").mkdir(exist_ok=True)
            Path("src/impl.py").write_text("VALUE = 1\n")
            return "```result\nstatus: complete\n```\n"

        fm = self._run([deliver, lambda: "```result\nstatus: blocked\n"
                                         "blocked_reason: still stuck\n```\n"])
        self.assertEqual(fm.get("status"), "blocked_human")
        self.assertAlmostEqual(float(fm.get("cumulative_cost_usd") or 0),
                               0.926254, places=6)
        self.assertAlmostEqual(float(fm.get("cumulative_duration_seconds") or 0),
                               100.0, places=3)
        self.assertEqual(int(fm.get("cumulative_output_tokens") or 0), 20)
        self.assertEqual(fm.get("folded_through_re_arm"), 1)


if __name__ == "__main__":
    unittest.main()
