#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for judge.py (FEAT-2026-0100/T01).

Pure functions only — an evidence-bundle builder over a fixture feature dir, a
prompt renderer, and a RESULT parser. No dispatch, no driver state; the close
path that calls these is T02's.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.judge import (
    JUDGE_MAX_EVIDENCE_CHARS,
    JUDGE_VERDICT_VALUES,
    build_judge_bundle,
    parse_judge_result,
    render_judge_prompt,
    strip_forbidden_sections,
)

GATE_MD = """\
---
gate: 1
status: open
---

# Gate 1 — a fixture gate

## Definition of done

- The judge reads the gate's definition of done and nothing the close wrote
  about its own performance.
- A terminal close is followed by a judge dispatch in the same driver run.

## Arming discipline

- This heading must terminate the definition-of-done slice.

## Reflection notes

<Written by the human at review time.>
"""

CRITERIA_MD = """\
### T01#1

- **criterion:** the bundle carries the gate's definition of done
- **oracle:** `python3 -m unittest tests.test_judge_module -v`
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `93a6438e48b42bbb1d8e0ce6a1ef0c5ebb8376df`
- **attempt:** `1`

### T02#4

- **criterion:** the close's own prose never reaches the judge
- **oracle:** `python3 -m unittest tests.test_judge_close_path -v`
- **kind:** `broad`
- **state:** `unverified`
- **attempt:** `1`
"""

RETRO_MD = """\
# Retrospective — FEAT-9999-0001

## Gate 1

## Measurements

| measurement | value |
| --- | --- |
| lint ERROR count over every feature folder | 0 |
| judged closes before this feature | 0 |

## Verdict

verdict: met — I checked every criterion myself and each one holds.

## Retrospective

The work went smoothly and I am confident the gate is done.
"""

DIFF_TEXT = """\
diff --git a/specfuse/loop/judge.py b/specfuse/loop/judge.py
--- /dev/null
+++ b/specfuse/loop/judge.py
@@ -0,0 +1,3 @@
+def build_judge_bundle(feature_dir, gate_number, *, diff_text, measurements=None):
+    return JudgeBundle(...)
"""


def _feature_dir(tmp: str, *, criteria: bool = True) -> Path:
    d = Path(tmp)
    (d / "GATE-01.md").write_text(GATE_MD)
    (d / "RETROSPECTIVE.md").write_text(RETRO_MD)
    if criteria:
        (d / "GATE-01-CRITERIA.md").write_text(CRITERIA_MD)
    return d


class TestBundle(unittest.TestCase):

    def test_bundle_contains_dod_criteria_diff_and_measurements_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            bundle = build_judge_bundle(
                d, 1, diff_text=DIFF_TEXT, measurements=RETRO_MD
            )
            prompt = render_judge_prompt(bundle)

        # 1. the gate's definition of done, sliced at the next heading
        self.assertIn("The judge reads the gate's definition of done", prompt)
        self.assertNotIn("This heading must terminate", prompt)
        # 2. the criteria artifact's entries
        self.assertIn("T01#1", prompt)
        self.assertIn("T02#4", prompt)
        self.assertIn("tests.test_judge_close_path", prompt)
        # 3. the diff the caller captured
        self.assertIn("+def build_judge_bundle", prompt)
        # 4. the close's Measurements section
        self.assertIn("lint ERROR count over every feature folder", prompt)

        # ... and nothing the close wrote about its own verdict.
        self.assertNotIn("## Verdict", prompt)
        self.assertNotIn("## Retrospective", prompt)
        self.assertNotIn("I checked every criterion myself", prompt)
        self.assertNotIn("I am confident", prompt)

    def test_missing_criteria_artifact_is_an_empty_list_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp, criteria=False)
            bundle = build_judge_bundle(
                d, 1, diff_text=DIFF_TEXT, measurements=RETRO_MD
            )
            self.assertEqual(bundle.criteria, [])
            # and the renderer still produces a usable prompt
            prompt = render_judge_prompt(bundle)
            self.assertIn("+def build_judge_bundle", prompt)

    def test_missing_gate_file_yields_empty_dod_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            bundle = build_judge_bundle(d, 3, diff_text="", measurements="")
            self.assertEqual(bundle.definition_of_done, "")
            self.assertEqual(bundle.criteria, [])
            self.assertEqual(bundle.gate_number, 3)

    def test_measurements_defaults_to_the_feature_retrospective(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            bundle = build_judge_bundle(d, 1, diff_text=DIFF_TEXT)
            self.assertIn("judged closes before this feature", bundle.measurements)
            self.assertNotIn("I am confident", bundle.measurements)

    def test_already_sliced_measurements_text_is_kept_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            bundle = build_judge_bundle(
                d, 1, diff_text="", measurements="| coverage | 94% |"
            )
            self.assertIn("| coverage | 94% |", bundle.measurements)

    def test_close_prose_inside_the_diff_is_redacted(self):
        diff = (
            "diff --git a/RETROSPECTIVE.md b/RETROSPECTIVE.md\n"
            "@@ -0,0 +1,4 @@\n"
            "+## Verdict\n"
            "+\n"
            "+verdict: met — everything holds.\n"
            "diff --git a/specfuse/loop/judge.py b/specfuse/loop/judge.py\n"
            "+def render_judge_prompt(bundle):\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            bundle = build_judge_bundle(d, 1, diff_text=diff, measurements="")
            prompt = render_judge_prompt(bundle)
        self.assertNotIn("## Verdict", prompt)
        self.assertNotIn("everything holds", prompt)
        # the code half of the same diff survives the redaction
        self.assertIn("+def render_judge_prompt", prompt)

    def test_measurements_section_with_child_headings_is_captured_whole(self):
        retro = (
            "# Retrospective — FEAT-9999-0001\n"
            "\n"
            "## Measurements\n"
            "\n"
            "| measurement | value |\n"
            "| --- | --- |\n"
            "| lint ERROR count | 0 |\n"
            "\n"
            "### Failure-class breakdown\n"
            "\n"
            "| class | count |\n"
            "| --- | --- |\n"
            "| timeout | 2 |\n"
            "\n"
            "## Retrospective\n"
            "\n"
            "The work went smoothly.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            bundle = build_judge_bundle(d, 1, diff_text="", measurements=retro)
        self.assertIn("lint ERROR count", bundle.measurements)
        self.assertIn("### Failure-class breakdown", bundle.measurements)
        self.assertIn("timeout", bundle.measurements)
        self.assertNotIn("## Retrospective", bundle.measurements)
        self.assertNotIn("The work went smoothly", bundle.measurements)

    def test_oversized_diff_is_truncated_to_the_failure_note_cap(self):
        big = "\n".join(f"+line {i}" for i in range(4000))
        self.assertGreater(len(big), JUDGE_MAX_EVIDENCE_CHARS)
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            bundle = build_judge_bundle(d, 1, diff_text=big, measurements="")
        self.assertLessEqual(len(bundle.diff_text), JUDGE_MAX_EVIDENCE_CHARS + 200)
        self.assertIn("chars elided", bundle.diff_text)
        self.assertIn("+line 0", bundle.diff_text)
        self.assertIn("+line 3999", bundle.diff_text)


class TestRedaction(unittest.TestCase):

    def test_redaction_stops_at_the_next_ordinary_heading(self):
        text = (
            "## Measurements\n"
            "\n"
            "| coverage | 94% |\n"
            "\n"
            "## Verdict and rationale\n"
            "\n"
            "verdict: met — I am satisfied.\n"
            "\n"
            "## Cost analysis\n"
            "\n"
            "| planned | actual |\n"
        )
        stripped = strip_forbidden_sections(text)
        self.assertIn("| coverage | 94% |", stripped)
        self.assertIn("## Cost analysis", stripped)
        self.assertIn("| planned | actual |", stripped)
        self.assertNotIn("## Verdict", stripped)
        self.assertNotIn("I am satisfied", stripped)

    def test_text_with_nothing_to_redact_is_unchanged(self):
        text = "## Measurements\n\n| coverage | 94% |\n"
        self.assertEqual(strip_forbidden_sections(text), text)

    def test_forbidden_section_with_subheadings_is_fully_stripped(self):
        text = (
            "## Verdict\n"
            "\n"
            "verdict: met — I am satisfied.\n"
            "\n"
            "### Why I am confident\n"
            "\n"
            "I checked every criterion myself.\n"
            "\n"
            "## Retrospective\n"
            "\n"
            "### What went well\n"
            "\n"
            "This close went smoothly.\n"
            "\n"
            "### What I would change\n"
            "\n"
            "Nothing, honestly.\n"
            "\n"
            "## Cost analysis\n"
            "\n"
            "| planned | actual |\n"
        )
        stripped = strip_forbidden_sections(text)
        for line in (
            "verdict: met",
            "I am satisfied",
            "Why I am confident",
            "checked every criterion",
            "What went well",
            "went smoothly",
            "What I would change",
            "Nothing, honestly",
        ):
            self.assertNotIn(line, stripped)
        self.assertIn("## Cost analysis", stripped)
        self.assertIn("| planned | actual |", stripped)

    def test_forbidden_section_in_diff_hunk_form_is_fully_stripped(self):
        text = (
            "+## Verdict\n"
            "+\n"
            "+verdict: met — I am satisfied.\n"
            "+\n"
            "+### Why I am confident\n"
            "+\n"
            "+I checked every criterion myself.\n"
            "+\n"
            "+## Retrospective\n"
            "+\n"
            "+### What went well\n"
            "+\n"
            "+This close went smoothly.\n"
            "+\n"
            "+### What I would change\n"
            "+\n"
            "+Nothing, honestly.\n"
            "+\n"
            "+## Cost analysis\n"
            "+\n"
            "+| planned | actual |\n"
        )
        stripped = strip_forbidden_sections(text)
        for line in (
            "verdict: met",
            "I am satisfied",
            "Why I am confident",
            "checked every criterion",
            "What went well",
            "went smoothly",
            "What I would change",
            "Nothing, honestly",
        ):
            self.assertNotIn(line, stripped)
        self.assertIn("## Cost analysis", stripped)
        self.assertIn("| planned | actual |", stripped)


class TestPrompt(unittest.TestCase):

    def test_prompt_states_the_job_and_the_finding_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp)
            prompt = render_judge_prompt(
                build_judge_bundle(d, 1, diff_text=DIFF_TEXT, measurements=RETRO_MD)
            )
        self.assertIn("met", prompt)
        self.assertIn("not_met", prompt)
        self.assertIn("### <criterion>", prompt)
        self.assertIn("```result", prompt)
        # it forbids opening the close's own prose without naming the banned strings
        self.assertIn("RETROSPECTIVE.md", prompt)


class TestParse(unittest.TestCase):

    def test_parse_met_and_not_met_with_findings(self):
        met = "Ran both oracles.\n\n```result\nverdict: met\n```\n"
        result = parse_judge_result(met)
        self.assertEqual(result.verdict, "met")
        self.assertEqual(result.findings, [])
        self.assertIsNone(result.reason)
        self.assertIn("verdict: met", result.raw)

        finding_one = (
            "### T01#1\n"
            "\n"
            "The oracle does not pass on the squashed tree.\n"
            "\n"
            "- command: `python3 -m unittest tests.test_judge_module -v`\n"
            "- exit: 1"
        )
        finding_two = (
            "### T02#4\n"
            "\n"
            "Coverage is below the declared threshold.\n"
            "\n"
            "- command: `coverage report --fail-under=90`\n"
            "- exit: 2"
        )
        not_met = (
            "I re-ran both oracles named by the criteria.\n"
            "\n"
            "```result\n"
            "verdict: not_met\n"
            "\n"
            f"{finding_one}\n"
            "\n"
            f"{finding_two}\n"
            "```\n"
        )
        result = parse_judge_result(not_met)
        self.assertEqual(result.verdict, "not_met")
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.findings[0].criterion, "T01#1")
        self.assertEqual(result.findings[1].criterion, "T02#4")
        self.assertEqual(result.findings[0].text, finding_one)
        self.assertEqual(result.findings[1].text, finding_two)
        self.assertIsNone(result.reason)

    def test_unparseable_output_yields_none_with_reason(self):
        for label, text in (
            ("empty", ""),
            ("whitespace only", "   \n\n"),
            ("unrecognized verdict", "```result\nverdict: partially_met\n```"),
            ("no block", "The gate looks fine to me, verdict: met, shipping it."),
            ("no verdict field", "```result\nstatus: complete\n```"),
        ):
            with self.subTest(label=label):
                result = parse_judge_result(text)
                self.assertIsNone(result.verdict)
                self.assertEqual(result.findings, [])
                self.assertTrue(result.reason)
                self.assertNotIn("\n", result.reason)

    def test_unrecognized_verdict_reason_names_the_value(self):
        result = parse_judge_result("```result\nverdict: partially_met\n```")
        self.assertIn("partially_met", result.reason)

    def test_last_result_block_wins(self):
        text = (
            "```result\nverdict: met\n```\n"
            "on reflection:\n"
            "```result\nverdict: not_met\n```\n"
        )
        self.assertEqual(parse_judge_result(text).verdict, "not_met")

    def test_verdict_value_tolerates_backticks_and_quotes(self):
        for raw in ("`met`", '"met"', "'met'", "met  "):
            with self.subTest(raw=raw):
                result = parse_judge_result(f"```result\nverdict: {raw}\n```")
                self.assertEqual(result.verdict, "met")

    def test_raw_is_truncated_and_reason_is_a_single_line_scalar(self):
        noisy = "x" * (JUDGE_MAX_EVIDENCE_CHARS * 2)
        result = parse_judge_result(noisy)
        self.assertLessEqual(len(result.raw), JUDGE_MAX_EVIDENCE_CHARS + 200)
        self.assertIsNone(result.verdict)
        self.assertNotIn("\n", result.reason)

    def test_verdict_values(self):
        self.assertEqual(JUDGE_VERDICT_VALUES, frozenset({"met", "not_met"}))


if __name__ == "__main__":
    unittest.main()
