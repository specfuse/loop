# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The triage lane does not triage the agent's own escalations (#2384).

`specfuse-agent` filed four `drafting-needed` escalations and then spent four
more items of the same run triaging the four issues it had just written —
8 items attempted, 0 units of work. Escalations carry `needs-human` plus one
of `escalation.CATEGORY_LABELS`, written by `escalation.py` itself, so they
are categorised by construction; re-deriving a category for an agent-authored
template adds nothing.

That it adds nothing is measurable: four near-identical generated bodies came
out three `triage:feature` and one `triage:question`. Same input shape,
different answer — the classifier was reading a template, not a report.

`BugsProvider` already learned this, and its own comment records the same
failure from the other side: "every escalation the agent filed was itself
triaged `bug` and became a candidate on the next run -- the lane trying to
'fix' its own 'PR was declined by the merge guardrails' report." This is that
rule applied to the lane that does the labelling.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from specfuse.agent.providers import triage as triage_provider
from specfuse.agent.providers.triage import TriageProvider
from specfuse.loop.escalation import CATEGORY_LABELS, NEEDS_HUMAN_LABEL


def _snapshot(auto=False):
    return SimpleNamespace(
        triage_auto=auto,
        queue=(),
        bug_automerge=False,
        bug_lane_limits={},
        issues=(),
        issues_error=None,
        prs=(),
        prs_error=None,
        features=(),
    )


def _row(number, *labels, title="an issue", structured=False):
    return {
        "number": number,
        "title": title,
        "body": "",
        "labels": [{"name": name} for name in labels],
        "needs_repair": False,
        "already_structured": structured,
    }


class _Rows:
    """Stands in for `list_untriaged`, which is where the provider's input
    comes from — the filter under test belongs to the provider, not the
    reader (whose docstring is explicit that its flags are 'a flag, not an
    exclusion')."""

    def __init__(self, rows):
        self._rows = rows
        self.calls = 0

    def __call__(self, runner, repo, *args, **kwargs):
        self.calls += 1
        return list(self._rows)


class TriageSkipsAgentEscalationsTests(unittest.TestCase):
    def setUp(self):
        self._real = triage_provider.list_untriaged

    def tearDown(self):
        triage_provider.list_untriaged = self._real

    def _advertise(self, rows):
        triage_provider.list_untriaged = _Rows(rows)
        provider = TriageProvider(repo="acme-widget/example")
        return provider.advertise(_snapshot())

    def test_every_category_label_is_skipped(self):
        """One subtest per member of CATEGORY_LABELS, so a category added
        later fails here rather than silently becoming triageable."""
        for label in sorted(CATEGORY_LABELS):
            with self.subTest(label=label):
                items = self._advertise([_row(10, NEEDS_HUMAN_LABEL, label)])
                self.assertEqual(items, [])

    def test_a_category_label_alone_is_enough(self):
        """The label is written by escalation.py and by nothing else, so it
        identifies an agent-authored issue on its own — an operator who has
        released `needs-human` has not made the body worth classifying."""
        items = self._advertise([_row(11, "drafting-needed")])
        self.assertEqual(items, [])

    def test_an_ordinary_untriaged_issue_is_still_advertised(self):
        """The lane's actual job must be untouched."""
        items = self._advertise([_row(12, "bug", title="crash on startup")])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].summary, "crash on startup")

    def test_an_issue_with_no_labels_is_still_advertised(self):
        items = self._advertise([_row(13)])
        self.assertEqual(len(items), 1)

    def test_already_structured_is_still_skipped(self):
        """No regression on the filter that was already there."""
        items = self._advertise([_row(14, structured=True)])
        self.assertEqual(items, [])

    def test_the_four_observed_escalations_produce_no_items(self):
        """The run that produced #2384: issues 2380-2383, each carrying
        `needs-human` + `drafting-needed`, every one of them triaged."""
        rows = [
            _row(n, NEEDS_HUMAN_LABEL, "drafting-needed")
            for n in (2380, 2381, 2382, 2383)
        ]
        self.assertEqual(self._advertise(rows), [])

    def test_a_mixed_batch_keeps_only_the_real_work(self):
        rows = [
            _row(2380, NEEDS_HUMAN_LABEL, "drafting-needed"),
            _row(99, "bug", title="a real report"),
            _row(2381, NEEDS_HUMAN_LABEL, "gate-review"),
        ]
        items = self._advertise(rows)
        self.assertEqual([i.summary for i in items], ["a real report"])


if __name__ == "__main__":
    unittest.main()
