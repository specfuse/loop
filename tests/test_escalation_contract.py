# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Contract tests for specfuse.loop.escalation."""

from __future__ import annotations

import unittest

from specfuse.loop.escalation import (
    CATEGORY_LABELS,
    NEEDS_HUMAN_LABEL,
    render_escalation_body,
    validate_escalation_body,
)

_PART_HEADINGS = (
    "What has been done so far",
    "What this issue is about",
    "What decision is needed, and why",
    "Why it did not, or could not, close automatically",
    "Options, each with pros and cons",
    "A recommendation",
)


def _sample_kwargs():
    return dict(
        category="blocked-wu",
        done_so_far="T01 landed, T02 half-finished.",
        issue_summary="The escalation body shape is not machine-checkable yet.",
        decision_needed="Whether the six-part shape is correct.",
        why_not_auto="No validator existed to confirm conformance.",
        options=[
            ("Ship as drafted", "fast", "unverified"),
            ("Rewrite from scratch", "clean slate", "slow"),
        ],
        recommendation="Ship as drafted, it matches the rule.",
    )


class TestLabelVocabulary(unittest.TestCase):
    def test_needs_human_label_value(self):
        self.assertEqual(NEEDS_HUMAN_LABEL, "needs-human")

    def test_category_labels_exact_membership(self):
        self.assertEqual(
            CATEGORY_LABELS,
            frozenset(
                {
                    "gate-review",
                    "blocked-wu",
                    "triage-question",
                    "drafting-needed",
                    "merge-approval",
                }
            ),
        )
        self.assertIsInstance(CATEGORY_LABELS, frozenset)


class TestRenderEscalationBody(unittest.TestCase):
    def test_contains_all_six_part_headings(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        for heading in _PART_HEADINGS:
            self.assertIn(heading, body)

    def test_contains_numbered_answers_section(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        self.assertIn("reply", body.lower())
        self.assertIn("1.", body)
        self.assertIn("2.", body)

    def test_contains_correlation_marker(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        self.assertIn("<!-- specfuse:escalation id=FEAT-2026-0046/T01 -->", body)

    def test_rejects_unknown_category(self):
        kwargs = _sample_kwargs()
        kwargs["category"] = "not-a-real-category"
        with self.assertRaises(ValueError):
            render_escalation_body("FEAT-2026-0046/T01", **kwargs)


class TestEscalationBodyValidator(unittest.TestCase):
    def test_accepts_body_from_renderer(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        self.assertEqual(validate_escalation_body(body), [])

    def test_rejects_body_missing_a_required_part(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        heading = "## What decision is needed, and why"
        start = body.index(heading)
        next_heading = body.index("\n## ", start + 1)
        mutilated = body[:start] + body[next_heading + 1 :]

        findings = validate_escalation_body(mutilated)

        self.assertTrue(findings)
        self.assertTrue(
            any("What decision is needed, and why" in f for f in findings)
        )

    def test_rejects_body_missing_each_of_the_six_parts_individually(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        for heading in _PART_HEADINGS:
            marker = f"## {heading}"
            start = body.index(marker)
            end = body.find("\n## ", start + 1)
            if end == -1:
                end = len(body)
            mutilated = body[:start] + body[end + 1 :]

            findings = validate_escalation_body(mutilated)

            self.assertTrue(findings, f"expected a finding when {heading!r} is removed")
            self.assertTrue(
                any(heading in f for f in findings),
                f"expected a finding naming {heading!r}, got {findings}",
            )

    def test_rejects_body_missing_correlation_marker(self):
        body = render_escalation_body("FEAT-2026-0046/T01", **_sample_kwargs())
        without_marker = body.replace(
            "<!-- specfuse:escalation id=FEAT-2026-0046/T01 -->\n\n", ""
        )

        findings = validate_escalation_body(without_marker)

        self.assertTrue(any("correlation marker" in f for f in findings))


if __name__ == "__main__":
    unittest.main()
