# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for severity on the triage classification path (FEAT-2026-0113/T05).

`build_invocation` folds the repository's severity rubric into the single
per-issue classification prompt -- no second session -- and `classify_severity`
reads the session's answer back, failing closed on anything short of a
rubric-matched, high-confidence severity.
"""

from __future__ import annotations

import inspect
import unittest

from specfuse.agent.triage_invoke import build_invocation, classify_result, classify_severity

_ARGS = dict(
    issue_number=42,
    title="Something broke",
    body="It does not work when I click the button.",
    repo="acme-widget/example",
)

_RUBRIC = {
    "low": "Minor impact; cosmetic.",
    "high": "Major impact; broken with no workaround.",
}


class SeverityPrompt(unittest.TestCase):
    def test_prompt_unchanged_when_rubric_is_empty(self):
        _argv, baseline_prompt = build_invocation(**_ARGS)
        _argv, empty_rubric_prompt = build_invocation(**_ARGS, rubric={})
        _argv, no_rubric_prompt = build_invocation(**_ARGS, rubric=None)

        self.assertEqual(baseline_prompt, empty_rubric_prompt)
        self.assertEqual(baseline_prompt, no_rubric_prompt)

    def test_prompt_names_each_severity_value_beside_its_definition(self):
        _argv, prompt = build_invocation(**_ARGS, rubric=_RUBRIC)

        for value, description in _RUBRIC.items():
            self.assertIn(f"{value}: {description}", prompt)

        self.assertIn(
            "<!-- specfuse:triage category=<category> confidence=<high|low> "
            "severity=<value> -->",
            prompt,
        )

    def test_module_holds_no_copy_of_the_shipped_default_rubric(self):
        import specfuse.agent.triage_invoke as module

        source = inspect.getsource(module)
        self.assertNotIn("SEVERITY_VALUES", source)
        self.assertNotIn("DEFAULT_SEVERITY_RUBRIC", source)


class ClassifyResultUnchanged(unittest.TestCase):
    def test_two_field_marker_still_returns_category_and_confidence(self):
        self.assertEqual(
            classify_result("<!-- specfuse:triage category=bug confidence=high -->"),
            ("bug", "high"),
        )

    def test_three_field_marker_still_returns_only_category_and_confidence(self):
        self.assertEqual(
            classify_result(
                "<!-- specfuse:triage category=bug confidence=high severity=high -->"
            ),
            ("bug", "high"),
        )

    def test_empty_output_returns_none(self):
        self.assertIsNone(classify_result(""))


class ClassifySeverityFailsClosed(unittest.TestCase):
    def test_returns_rubric_matched_severity_at_high_confidence(self):
        marker = "<!-- specfuse:triage category=bug confidence=high severity=high -->"
        self.assertEqual(classify_severity(marker, _RUBRIC), "high")

    def test_absent_severity_field_yields_none(self):
        marker = "<!-- specfuse:triage category=bug confidence=high -->"
        self.assertIsNone(classify_severity(marker, _RUBRIC))

    def test_empty_severity_value_yields_none(self):
        marker = "<!-- specfuse:triage category=bug confidence=high severity= -->"
        self.assertIsNone(classify_severity(marker, _RUBRIC))

    def test_severity_outside_rubric_yields_none(self):
        marker = "<!-- specfuse:triage category=bug confidence=high severity=critical -->"
        self.assertIsNone(classify_severity(marker, _RUBRIC))

    def test_non_high_confidence_yields_none_even_with_matching_severity(self):
        marker = "<!-- specfuse:triage category=bug confidence=low severity=high -->"
        self.assertIsNone(classify_severity(marker, _RUBRIC))

    def test_empty_output_yields_none(self):
        self.assertIsNone(classify_severity("", _RUBRIC))


if __name__ == "__main__":
    unittest.main()
