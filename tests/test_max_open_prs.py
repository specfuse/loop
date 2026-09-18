# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`budgets.max_open_prs` gates the lanes that open pull requests (#3340).

The key was required by the schema, proposed from evidence by
`policy_proposals`, and reported on by `policy_review` -- and read by nothing
that could act on it. A policy declaring `max_open_prs: 5` alongside
`automerge: "on"` described a ceiling that did not exist.

Two lanes open a pull request: `KIND_BUG` and `KIND_FINDING_AUTOFIX`, both of
which dispatch a headless `/specfuse:fix-bug`. `KIND_FEATURE` does not -- the
driver runs gates and `/wrap-feature` opens the PR interactively -- so it is
deliberately not gated here.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from specfuse.agent.run import (
    ActionItem,
    ActionOutcome,
    PR_OPENING_KINDS,
    STATUS_COMPLETED,
    run_agent,
)
from specfuse.loop.agent_policy import resolve_max_open_prs

_POLICY = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "off"
  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 100000
  max_open_prs: {cap}
  max_items_per_day: 10
escalation:
  provider: none
  webhook_env: ""
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
  silence_hours: 24
"""


class _FakeClock:
    def __init__(self):
        self._now = 0.0

    def __call__(self):
        return self._now


class _PRListRunner:
    """A `gh` runner whose open-PR listing is mutable mid-run."""

    def __init__(self, open_prs: int, issues=()):
        self.open_prs = open_prs
        self.issues = list(issues)

    def __call__(self, argv, check=False):
        import json as _json

        argv = list(argv)
        if argv[:3] == ["gh", "pr", "list"]:
            rows = [
                {"number": n, "title": f"pr {n}", "labels": [], "body": ""}
                for n in range(1, self.open_prs + 1)
            ]
            return SimpleNamespace(returncode=0, stdout=_json.dumps(rows), stderr="")
        if argv[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(returncode=0, stdout=_json.dumps(self.issues), stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")


class _KindProvider:
    """Advertises one item of a given kind until it is executed."""

    def __init__(self, kind, item_id):
        self._item = ActionItem(item_id=item_id, kind=kind, summary="", queue_key=None)
        self._done = False
        self.executed = []

    def advertise(self, snapshot):
        return () if self._done else (self._item,)

    def execute(self, item):
        self._done = True
        self.executed.append(item.item_id)
        return ActionOutcome(status=STATUS_COMPLETED, detail="ok")

    def reconcile(self, item, outcome):
        return None


def _run(runner, providers, policy_body, reports):
    with tempfile.TemporaryDirectory() as tmp:
        specfuse_dir = Path(tmp) / ".specfuse"
        specfuse_dir.mkdir()
        (specfuse_dir / "features").mkdir()
        policy = specfuse_dir / "agent-policy.yml"
        policy.write_text(policy_body, encoding="utf-8")
        return run_agent(
            specfuse_dir=specfuse_dir,
            repo="acme/widget",
            runner=runner,
            providers=providers,
            policy_path=str(policy),
            features_root=specfuse_dir / "features",
            clock=_FakeClock(),
            reporter=reports.append,
        )


class ResolvingTheCap(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write(self, cap: str) -> str:
        path = Path(self._tmp.name) / "agent-policy.yml"
        path.write_text(_POLICY.format(cap=cap), encoding="utf-8")
        return str(path)

    def test_a_declared_cap_resolves(self):
        self.assertEqual(resolve_max_open_prs(self._write("5")), 5)

    def test_a_missing_file_is_unbounded(self):
        self.assertIsNone(resolve_max_open_prs("/nonexistent/agent-policy.yml"))

    def test_a_zero_or_negative_cap_is_unbounded_not_a_total_stop(self):
        # Same defensive shape as `resolve_max_tokens`: a cap of 0 would stop
        # every lane forever, which is never what a malformed value means.
        self.assertIsNone(resolve_max_open_prs(self._write("0")))
        self.assertIsNone(resolve_max_open_prs(self._write("-1")))


class TheCapGatesPROpeningLanes(unittest.TestCase):

    def test_the_gated_kinds_are_the_two_that_open_a_pull_request(self):
        self.assertEqual(PR_OPENING_KINDS, frozenset({"bug", "finding-autofix"}))

    def test_a_bug_item_is_not_dispatched_at_the_cap(self):
        runner = _PRListRunner(open_prs=5)
        bugs = _KindProvider("bug", "bug-7")
        reports = []

        summary = _run(runner, (bugs,), _POLICY.format(cap="5"), reports)

        self.assertEqual(bugs.executed, [])
        self.assertEqual(summary.items_attempted, 0)
        self.assertTrue(
            any("max_open_prs" in line and "5" in line for line in reports),
            f"the suppression must be reported with its number, got {reports!r}",
        )

    def test_below_the_cap_the_item_is_dispatched(self):
        runner = _PRListRunner(open_prs=2)
        bugs = _KindProvider("bug", "bug-7")
        reports = []

        _run(runner, (bugs,), _POLICY.format(cap="5"), reports)

        self.assertEqual(bugs.executed, ["bug-7"])

    def test_a_non_pr_opening_kind_still_runs_at_the_cap(self):
        runner = _PRListRunner(open_prs=9)
        triage = _KindProvider("triage", "triage-7")
        reports = []

        _run(runner, (triage,), _POLICY.format(cap="5"), reports)

        self.assertEqual(
            triage.executed, ["triage-7"],
            "the cap is about opening pull requests; triage opens none",
        )

    def test_an_unreadable_pr_listing_does_not_suppress(self):
        # `snapshot.prs` is empty with `prs_error` set when the listing fails.
        # Counting that as zero open PRs is the right read: the cap must not
        # fire on a number the run could not actually measure.
        class _FailingPRs(_PRListRunner):
            def __call__(self, argv, check=False):
                if list(argv)[:3] == ["gh", "pr", "list"]:
                    return SimpleNamespace(returncode=1, stdout="", stderr="gh: boom")
                return super().__call__(argv, check=check)

        bugs = _KindProvider("bug", "bug-7")
        reports = []
        _run(_FailingPRs(open_prs=99), (bugs,), _POLICY.format(cap="1"), reports)

        self.assertEqual(bugs.executed, ["bug-7"])


class TheSnapshotRefreshMovesTheCap(unittest.TestCase):

    def test_a_pr_opened_mid_run_counts_against_the_cap(self):
        """#3338's refresh is what makes this a live ceiling rather than a
        once-at-startup read: the second bug item sees the PR the first one
        opened."""
        runner = _PRListRunner(open_prs=1)

        class _OpensAPR(_KindProvider):
            def execute(self, item):
                runner.open_prs += 1
                return super().execute(item)

        first = _OpensAPR("bug", "bug-7")
        second = _KindProvider("bug", "bug-8")
        reports = []

        _run(runner, (first, second), _POLICY.format(cap="2"), reports)

        self.assertEqual(first.executed, ["bug-7"])
        self.assertEqual(
            second.executed, [],
            "the cap was reached by the PR the first item opened",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
