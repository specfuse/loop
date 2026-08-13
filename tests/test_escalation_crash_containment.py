# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Reporting a failure must not destroy the run that is reporting it (#2170).

Observed 2026-08-12, end to end:

1. `specfuse run` raised `FeatureBranchError` — the feature branch had
   diverged from `main`. A correct, well-worded refusal.
2. `FeatureProvider` built an escalation whose `issue_summary` was **the whole
   Python traceback**.
3. `emit_escalation` passed that verbatim as `--title`, so `gh issue create`
   got a multi-line ~2000-character title and rejected it.
4. `check=True` turned the rejection into `CalledProcessError`, which raised
   out of `emit_escalation`, out of `_record_escalation`, out of `run_agent`,
   and out of the process.

The run died with a traceback while trying to report a failure it had already
correctly diagnosed. Three independent defects, each pinned below: an
unbounded title, a fatal `check=True`, and an unguarded call site — the last
being a gap in #2005, which guarded `advertise` and `reconcile` but not this.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from specfuse.agent.run import (
    KIND_FEATURE,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    run_agent,
)
from specfuse.loop.escalation import (
    CREATED_NUMBER_UNKNOWN,
    emit_escalation,
    issue_title,
)

_TRACEBACK = '''FEAT-2026-0080's driver invocation failed: File "/x/bin/specfuse", line 10, in <module>
    sys.exit(main())
             ~~~~^^
  File "/x/loop.py", line 1754, in ensure_feature_branch
    raise FeatureBranchError(
specfuse.loop.loop.FeatureBranchError: branch 'feat/FEAT-2026-0080-answer-escalation' has diverged from 'main' — it carries commits 'main' does not.'''


class TestTheTitleIsUsable(unittest.TestCase):
    def test_a_traceback_becomes_one_short_line(self):
        title = issue_title("feature-FEAT-2026-0080-g1", _TRACEBACK)

        self.assertEqual(title.count("\n"), 0)
        self.assertLessEqual(len(title), 180)

    def test_it_keeps_the_first_meaningful_line(self):
        title = issue_title("cid", _TRACEBACK)

        self.assertIn("driver invocation failed", title)

    def test_the_correlation_id_survives_truncation(self):
        title = issue_title("feature-FEAT-2026-0080-g1", "x" * 5000)

        self.assertTrue(title.startswith("[feature-FEAT-2026-0080-g1]"))

    def test_an_empty_summary_still_yields_a_title(self):
        self.assertEqual(issue_title("cid", ""), "[cid] escalation")
        self.assertEqual(issue_title("cid", "\n\n  \n"), "[cid] escalation")


class TestAFailedCreateDoesNotRaise(unittest.TestCase):
    def _emit(self, runner):
        return emit_escalation(
            "cid",
            category="blocked-wu",
            repo="o/r",
            done_so_far="a",
            issue_summary="b",
            decision_needed="c",
            why_not_auto="d",
            options=[("x", "p", "c"), ("y", "p", "c")],
            recommendation="e",
            runner=runner,
        )

    def test_a_rejected_create_returns_empty_rather_than_raising(self):
        def rejecting(argv, check=False):
            if argv[:3] == ["gh", "issue", "create"]:
                return SimpleNamespace(returncode=1, stdout="", stderr="title too long")
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        self.assertEqual(self._emit(rejecting), "")

    def test_a_raising_runner_returns_empty_rather_than_propagating(self):
        def exploding(argv, check=False):
            if argv[:3] == ["gh", "issue", "create"]:
                raise subprocess.CalledProcessError(1, argv)
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        self.assertEqual(self._emit(exploding), "")

    def test_created_but_unparseable_is_not_reported_as_failure(self):
        """"Created, number unknown" must not read as "not created".

        Reporting it as a failure sends the operator looking for an issue
        that exists.
        """

        def quiet_success(argv, check=False):
            if argv[:3] == ["gh", "issue", "create"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        self.assertEqual(self._emit(quiet_success), CREATED_NUMBER_UNKNOWN)


class _FeatureProviderThatEscalates:
    """One feature item whose escalation carries a traceback, as the real one does."""

    def __init__(self):
        self._served = False

    def advertise(self, snapshot):
        if self._served:
            return ()
        return (ActionItem(item_id="feature-x-g1", kind=KIND_FEATURE, queue_key="x"),)

    def execute(self, item):
        self._served = True
        return ActionOutcome(
            status=STATUS_ESCALATED,
            detail="driver failed",
            escalation=EscalationPayload(
                done_so_far="ran the driver",
                issue_summary=_TRACEBACK,
                decision_needed="investigate",
                why_not_auto="the driver exited non-zero",
                options=[("Investigate", "p", "c"), ("Leave it", "p", "c")],
                recommendation="investigate",
            ),
        )

    def reconcile(self, item, outcome):
        return None


class TestTheRunSurvivesAFailedEscalation(unittest.TestCase):
    def _run(self, runner, lines):
        with tempfile.TemporaryDirectory() as tmp:
            specfuse_dir = Path(tmp)
            (specfuse_dir / "features").mkdir()
            (specfuse_dir / "agent-policy.yml").write_text("queue:\n  - x\n")
            return run_agent(
                specfuse_dir=specfuse_dir,
                repo="o/r",
                runner=runner,
                providers=(_FeatureProviderThatEscalates(),),
                policy_path=str(specfuse_dir / "agent-policy.yml"),
                features_root=specfuse_dir / "features",
                reporter=lines.append,
            )

    def test_a_raising_escalation_does_not_end_the_run(self):
        """The gap #2005 left: advertise and reconcile were guarded, this was not."""

        def exploding(argv, check=False):
            if argv[:3] == ["gh", "issue", "create"]:
                raise subprocess.CalledProcessError(1, argv, stderr="title too long")
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        lines = []
        summary = self._run(exploding, lines)

        self.assertEqual(summary.stop_reason, "drained")
        self.assertEqual(summary.items_escalated, 1)

    def test_the_item_is_still_recorded_as_escalated(self):
        def exploding(argv, check=False):
            if argv[:3] == ["gh", "issue", "create"]:
                raise subprocess.CalledProcessError(1, argv)
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        lines = []
        summary = self._run(exploding, lines)

        entry = summary.escalations[0]
        self.assertEqual(entry.item_id, "feature-x-g1")
        self.assertIn("driver failed", entry.reason)

    def test_the_lost_github_trace_is_stated_not_implied(self):
        def rejecting(argv, check=False):
            if argv[:3] == ["gh", "issue", "create"]:
                return SimpleNamespace(returncode=1, stdout="", stderr="too long")
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")

        lines = []
        summary = self._run(rejecting, lines)

        self.assertIn("could NOT be filed", summary.escalations[0].reason)


if __name__ == "__main__":
    unittest.main()
