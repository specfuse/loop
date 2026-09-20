# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A setup failure stops the run instead of parking every item (#3343).

`run_agent` treats every item independently, which is right for an
item-specific failure and wrong for one whose cause is the run's environment.

Measured: the headless `/fix-bug` command did not resolve, the bug lane invoked
it 55 times, and each failure produced one `could_not_proceed` escalation
comment and one `needs-human` label. 16 minutes, 55 comments, 55 parked issues,
**one defect** — in the runner's own setup, identical every time.

The blast radius is self-inflicted and sticky: `needs-human` is in
`_HUMAN_OWNED_LABELS`, so the lane skips those issues from then on. One setup
defect removes the entire bug queue from automation until a human clears the
labels by hand.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.agent.run import (
    IDENTICAL_FAILURE_LIMIT,
    STOP_RUN_LEVEL_FAILURE,
    ActionItem,
    ActionOutcome,
    STATUS_ESCALATED,
    failure_signature,
    run_agent,
)


class _FakeClock:
    def __init__(self):
        self._now = 0.0

    def __call__(self):
        return self._now


class _AlwaysFailsTheSameWay:
    """Every item escalates with the same cause and a per-issue detail."""

    def __init__(self, count: int, *, detail_template: str):
        self._items = [
            ActionItem(item_id=f"bug-{n}", kind="bug", summary="", queue_key=None)
            for n in range(1, count + 1)
        ]
        self._template = detail_template
        self.executed: list = []

    def advertise(self, snapshot):
        return tuple(i for i in self._items if i.item_id not in self.executed)

    def execute(self, item):
        self.executed.append(item.item_id)
        number = item.item_id.split("-")[-1]
        return ActionOutcome(
            status=STATUS_ESCALATED,
            detail=self._template.format(n=number),
            escalation=None,
            escalation_waived="test double: the escalation trace is not this test's subject",
        )

    def reconcile(self, item, outcome):
        return None


def _run(provider, reports):
    with tempfile.TemporaryDirectory() as tmp:
        specfuse_dir = Path(tmp) / ".specfuse"
        specfuse_dir.mkdir()
        (specfuse_dir / "features").mkdir()
        return run_agent(
            specfuse_dir=specfuse_dir,
            repo="acme/widget",
            runner=lambda argv, check=False: type("R", (), {"returncode": 0, "stdout": "[]", "stderr": ""})(),
            providers=(provider,),
            policy_path=str(specfuse_dir / "agent-policy.yml"),
            features_root=specfuse_dir / "features",
            clock=_FakeClock(),
            reporter=reports.append,
        )


class TheSignatureIgnoresPerItemDetail(unittest.TestCase):

    def test_two_issues_failing_the_same_way_share_a_signature(self):
        a = ActionItem(item_id="bug-1916", kind="bug", summary="", queue_key=None)
        b = ActionItem(item_id="bug-1915", kind="bug", summary="", queue_key=None)
        out_a = ActionOutcome(status=STATUS_ESCALATED, detail="could_not_proceed: issue #1916: Unknown command: /fix-bug")
        out_b = ActionOutcome(status=STATUS_ESCALATED, detail="could_not_proceed: issue #1915: Unknown command: /fix-bug")
        self.assertEqual(failure_signature(a, out_a), failure_signature(b, out_b))

    def test_genuinely_different_causes_do_not_share_one(self):
        a = ActionItem(item_id="bug-1", kind="bug", summary="", queue_key=None)
        out_a = ActionOutcome(status=STATUS_ESCALATED, detail="could_not_proceed: no repro")
        out_b = ActionOutcome(status=STATUS_ESCALATED, detail="refused: feature-scoped")
        self.assertNotEqual(failure_signature(a, out_a), failure_signature(a, out_b))

    def test_the_kind_is_part_of_it(self):
        bug = ActionItem(item_id="bug-1", kind="bug", summary="", queue_key=None)
        triage = ActionItem(item_id="triage-1", kind="triage", summary="", queue_key=None)
        out = ActionOutcome(status=STATUS_ESCALATED, detail="same words")
        self.assertNotEqual(failure_signature(bug, out), failure_signature(triage, out))


class TheBreakerStopsTheRun(unittest.TestCase):

    def test_identical_failures_stop_the_run_at_the_limit(self):
        provider = _AlwaysFailsTheSameWay(
            55, detail_template="could_not_proceed: issue #{n}: Unknown command: /fix-bug"
        )
        reports: list = []

        summary = _run(provider, reports)

        self.assertEqual(len(provider.executed), IDENTICAL_FAILURE_LIMIT)
        self.assertEqual(summary.stop_reason, STOP_RUN_LEVEL_FAILURE)
        self.assertNotEqual(len(provider.executed), 55)

    def test_the_run_escalates_once_naming_the_shared_cause(self):
        provider = _AlwaysFailsTheSameWay(
            55, detail_template="could_not_proceed: issue #{n}: Unknown command: /fix-bug"
        )
        reports: list = []

        summary = _run(provider, reports)

        run_level = [e for e in summary.escalations if e.item_id.startswith("run:")]
        self.assertEqual(len(run_level), 1)
        self.assertIn("Unknown command", run_level[0].reason)
        self.assertIn(str(IDENTICAL_FAILURE_LIMIT), run_level[0].reason)

    def test_differing_causes_never_trip_it(self):
        # NOTE the fixture: causes differing only by a NUMBER share a
        # signature by design — that is what lets "issue #1916" and
        # "issue #1915" count as one cause. A test of genuinely different
        # causes has to differ in words, and the first draft of this one did
        # not, which the breaker correctly caught by tripping.
        words = ["no repro", "gh auth failed", "feature scoped", "gate red",
                 "timed out", "dirty tree"]

        class _Varied(_AlwaysFailsTheSameWay):
            def execute(self, item):
                self.executed.append(item.item_id)
                return ActionOutcome(
                    status=STATUS_ESCALATED,
                    detail=f"could_not_proceed: {words[len(self.executed) - 1]}",
                    escalation_waived="test double",
                )

        provider = _Varied(6, detail_template="unused")
        reports: list = []

        summary = _run(provider, reports)

        self.assertEqual(len(provider.executed), 6)
        self.assertNotEqual(summary.stop_reason, STOP_RUN_LEVEL_FAILURE)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class TheTemplateStopsAssertingARefusal(unittest.TestCase):
    """#3343 part 3: `classify_outcome` fails closed to `could_not_proceed`
    for output naming no outcome, which correctly covers both "the skill
    refused" and "the session never started" — but the escalation template
    presented the first as established fact.

    All 55 comments in the measured run said `/fix-bug`'s own refusal stopped
    it and recommended promoting to a feature. The skill never ran. An
    operator following that advice would have promoted 55 bugs to features on
    the strength of a missing command.
    """

    def test_a_named_outcome_is_distinguishable_from_a_failed_closed_one(self):
        from specfuse.monitor.autofix_invoke import classify_outcome, outcome_was_named

        named = "status: could_not_proceed\nsummary: no repro in the issue"
        self.assertEqual(classify_outcome(named), "could_not_proceed")
        self.assertTrue(outcome_was_named(named))

        unnamed = "Unknown command: /fix-bug"
        self.assertEqual(classify_outcome(unnamed), "could_not_proceed")
        self.assertFalse(outcome_was_named(unnamed))

        self.assertFalse(outcome_was_named(""))
        self.assertFalse(outcome_was_named("status: refused and also completed"))

    def test_the_payload_points_at_setup_when_no_outcome_was_named(self):
        from specfuse.agent.providers.bugs import _fix_bug_stopped_payload

        established = _fix_bug_stopped_payload(
            1916, "could_not_proceed", "no repro", outcome_named=True
        )
        self.assertIn("refusal or precondition check", established.why_not_auto)

        unestablished = _fix_bug_stopped_payload(
            1916, "could_not_proceed", "Unknown command: /fix-bug", outcome_named=False
        )
        self.assertNotIn("refusal or precondition check", unestablished.why_not_auto)
        self.assertIn("no outcome", unestablished.why_not_auto.lower())
        self.assertNotIn(
            "promoting rather than forcing", unestablished.recommendation,
            "the promote-to-feature advice must not appear when the skill "
            "never ran — that is what would have promoted 55 bugs",
        )
