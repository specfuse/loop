# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Backfill reconciles a human-applied severity instead of re-deciding it (#3360).

A backfill candidate is selected on its *marker*: already triaged, no
`severity=` field. Nothing looked at whether the issue already carried a
`severity:*` **label**. So an issue a person had labelled was still a candidate,
got a fresh classification, and had a second severity label written beside the
human's -- with `read_severity_label` then returning whichever it recognised
first. The agent silently overriding a person at the floor is the one outcome
FEAT-2026-0113 recorded that it must not ship into.

This was masked when the follow-up was written: the measured repository declares
`severity:critical`/`major`/`minor`, only `critical` was in the vocabulary, so
the rubric had one entry and the classifier failed closed on everything else.
**#3355 removed the mask** by shipping the default alias table -- that scheme now
yields a three-entry rubric (`critical`, `high`, `low`), so those issues are
classifiable and the collision is live rather than latent.

The fix reconciles rather than skips: the marker is written FROM the label, so
the issue stops being stranded *and* the person's judgement is what gets
recorded. No classification session is spent on it, and no label is written,
because the label is already there and is the source.

Two cases refuse to guess. Labels that resolve to more than one distinct value
are the operator's own ambiguity, and a `severity:*` label nobody can read is a
person's judgement in words this repo has no mapping for -- classifying either
would put a second, readable label beside one a human chose.
"""

from __future__ import annotations

import unittest

from specfuse.loop.agent_policy import DEFAULT_SEVERITY_ALIASES
from specfuse.loop.triage import (
    SEVERITY_CLASSIFY,
    SEVERITY_RECONCILE,
    SEVERITY_SKIP,
    severity_decision,
)


def _labels(*names):
    return [{"name": n} for n in names]


class SeverityDecision(unittest.TestCase):

    def test_no_severity_label_is_classified_as_before(self):
        action, value, _reason = severity_decision(_labels("bug", "triage:bug"))

        self.assertEqual(action, SEVERITY_CLASSIFY)
        self.assertIsNone(value)

    def test_no_labels_at_all_is_classified(self):
        self.assertEqual(severity_decision([])[0], SEVERITY_CLASSIFY)
        self.assertEqual(severity_decision(None)[0], SEVERITY_CLASSIFY)

    def test_an_in_vocabulary_label_is_reconciled_from(self):
        action, value, _reason = severity_decision(_labels("bug", "severity:high"))

        self.assertEqual(action, SEVERITY_RECONCILE)
        self.assertEqual(value, "high")

    def test_an_aliased_label_is_reconciled_to_its_vocabulary_value(self):
        # The live case: a person applied `severity:minor`; the marker must
        # record `low`, which is what that label means under the alias table.
        action, value, _reason = severity_decision(
            _labels("severity:minor"), aliases=DEFAULT_SEVERITY_ALIASES)

        self.assertEqual(action, SEVERITY_RECONCILE)
        self.assertEqual(value, "low")

    def test_two_labels_meaning_different_severities_refuse_to_guess(self):
        action, value, reason = severity_decision(
            _labels("severity:high", "severity:low"))

        self.assertEqual(action, SEVERITY_SKIP)
        self.assertIsNone(value)
        self.assertIn("more than one", reason)

    def test_two_labels_meaning_the_same_severity_still_reconcile(self):
        # `severity:high` and `severity:major` both mean high. That is not
        # ambiguity about the answer, so it is not a reason to strand the issue.
        action, value, _reason = severity_decision(
            _labels("severity:high", "severity:major"),
            aliases=DEFAULT_SEVERITY_ALIASES)

        self.assertEqual(action, SEVERITY_RECONCILE)
        self.assertEqual(value, "high")

    def test_an_unreadable_severity_label_is_skipped_not_classified(self):
        # A person labelled this something this repo has no mapping for.
        # Classifying would add a readable label beside a human's unreadable
        # one, which is the collision in a different spelling.
        action, value, reason = severity_decision(_labels("severity:p0"))

        self.assertEqual(action, SEVERITY_SKIP)
        self.assertIsNone(value)
        self.assertIn("severity:p0", reason)

    def test_an_unreadable_label_becomes_reconcilable_once_aliased(self):
        action, value, _reason = severity_decision(
            _labels("severity:p0"), aliases={"p0": "critical"})

        self.assertEqual(action, SEVERITY_RECONCILE)
        self.assertEqual(value, "critical")

    def test_the_vocabulary_wins_over_an_alias_pointing_elsewhere(self):
        # read_severity_label's rule, preserved here: an alias makes an unknown
        # word readable, it never redefines `severity:high`.
        action, value, _reason = severity_decision(
            _labels("severity:high"), aliases={"high": "low"})

        self.assertEqual(action, SEVERITY_RECONCILE)
        self.assertEqual(value, "high")


class TheRunReportDistinguishesTheSources(unittest.TestCase):
    """#3360's re-run condition is read off a dry run's own output: a majority
    classified, and zero rows the run would contradict. Both are unreadable if
    a reconciled row prints identically to a classified one and a deliberate
    refusal prints as "no usable classification"."""

    def _render(self, rows) -> str:
        import io
        from contextlib import redirect_stdout

        from specfuse.agent import severity_backfill

        buf = io.StringIO()
        with redirect_stdout(buf):
            severity_backfill._print_run_report(
                {"reason": None, "rows": rows, "rubric": {}, "candidates": []})
        return buf.getvalue()

    def test_a_reconciled_row_says_the_severity_came_from_the_label(self):
        out = self._render([{
            "number": 1902, "classified": True, "severity": "low",
            "severity_source": "label",
        }])

        self.assertIn("1902", out)
        self.assertIn("low", out)
        self.assertIn("label", out)

    def test_a_classified_row_is_not_labelled_as_reconciled(self):
        out = self._render([{
            "number": 42, "classified": True, "severity": "high",
            "severity_source": "classifier",
        }])

        self.assertIn("severity=high", out)
        self.assertNotIn("from its own label", out)

    def test_a_refusal_prints_its_reason_not_a_classification_failure(self):
        out = self._render([{
            "number": 7, "classified": False, "severity": None,
            "severity_source": "label",
            "skipped_reason": "labels resolve to more than one severity",
        }])

        self.assertIn("more than one", out)
        self.assertNotIn("no usable classification", out)

    def test_a_real_classification_failure_still_says_so(self):
        out = self._render([{
            "number": 9, "classified": False, "severity": None,
            "severity_source": "classifier",
        }])

        self.assertIn("no usable classification", out)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
