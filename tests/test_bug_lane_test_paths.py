#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# #1418: the test-evidence guardrail hardcoded `tests/`, so on a repository whose
# tests live in `spec/`, `src/**/__tests__/`, or beside sources as `*_test.go`, no
# diff could ever satisfy it and the bug lane silently never merged. It failed
# CLOSED — nothing unsafe shipped — but the feature was inert in a way that reads
# as "the dial is on and nothing qualifies" rather than as a misconfiguration, and
# no oracle in this repository could observe it, because this repository has the
# layout the prefix assumed.
#
# The guardrail stays STRUCTURAL: it asks whether the diff touches a declared test
# path, never whether the test is a good test. A semantic judgement would be a
# model-authored *approval*, which FEAT-2026-0053's organizing principle forbids.

import tempfile
import unittest

from specfuse.loop.agent_policy import (
    DEFAULT_TEST_PATHS,
    bug_lane_limits,
    validate_agent_policy,
)
from specfuse.loop.bug_lane import REASON_ELIGIBLE, REASON_NO_TEST_EVIDENCE, evaluate_merge_guardrails

_POLICY = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "off"
{test_paths}  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: ""
  provider: none
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
  silence_hours: 24
"""


def _write(test_paths_block: str = "") -> str:
    fd = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8")
    fd.write(_POLICY.format(test_paths=test_paths_block))
    fd.close()
    return fd.name


class _AlwaysUnderCap:
    def merges_last_24h(self, *_a, **_k):
        return 0


def _decide(changed, test_paths):
    return evaluate_merge_guardrails(
        changed_files=changed,
        ci_conclusion="success",
        diff_lines=10,
        max_diff_lines=150,
        provenance={"kind": "triaged_issue", "ref": "#1"},
        max_merges_per_day=3,
        test_paths=test_paths,
        state_reader=_AlwaysUnderCap(),
    )


class TestTestPathsResolution(unittest.TestCase):
    def test_default_preserves_the_previous_hardcoded_behaviour(self):
        self.assertEqual(DEFAULT_TEST_PATHS, ("tests/",))

    def test_absent_key_falls_back_to_the_default(self):
        self.assertEqual(bug_lane_limits(_write())["test_paths"], list(DEFAULT_TEST_PATHS))

    def test_declared_paths_are_read(self):
        block = "    test_paths:\n      - spec/\n      - src/__tests__/\n"
        self.assertEqual(
            bug_lane_limits(_write(block))["test_paths"], ["spec/", "src/__tests__/"]
        )

    def test_missing_policy_file_falls_back_to_the_default(self):
        self.assertEqual(
            bug_lane_limits("/nonexistent/agent-policy.yml")["test_paths"],
            list(DEFAULT_TEST_PATHS),
        )


class TestTestPathsValidation(unittest.TestCase):
    """A malformed declaration must be an ERROR, not a silent fallback.

    `bug_lane_limits` falls back to the default on a bad value, so without
    validation an operator's declared layout would be dropped with no signal —
    the same silent inertness the hardcoded prefix caused.
    """

    def _errors(self, block):
        return [f for f in validate_agent_policy(_write(block)) if f.startswith("ERROR: ")]

    def test_valid_list_is_accepted(self):
        self.assertEqual(self._errors("    test_paths:\n      - spec/\n"), [])

    def test_empty_list_is_rejected(self):
        # Would refuse every merge — a misconfiguration, not a way to disable it.
        self.assertEqual(len(self._errors("    test_paths: []\n")), 1)

    def test_bare_string_is_rejected(self):
        # `test_paths: spec/` is the likely typo; as a string it would iterate
        # per-character if anything downstream trusted it.
        self.assertEqual(len(self._errors("    test_paths: spec/\n")), 1)

    def test_list_with_an_empty_entry_is_rejected(self):
        self.assertEqual(len(self._errors('    test_paths:\n      - ""\n')), 1)

    def test_absent_key_is_not_an_error(self):
        self.assertEqual(self._errors(""), [])


class TestGuardrailHonoursTestPaths(unittest.TestCase):
    def test_default_layout_still_passes(self):
        # The regression guard: this repository's own layout must be unaffected.
        self.assertEqual(
            # NOT a specfuse/loop/ path: that is in JUDGE_PATHS and would decline for a
            # different reason, masking what this test is about.
            _decide(["tests/test_x.py", "docs/x.md"], ["tests/"]).reason,
            REASON_ELIGIBLE,
        )

    def test_alternative_layout_passes_when_declared(self):
        # The defect: this diff could never satisfy the old hardcoded prefix.
        self.assertEqual(
            _decide(["spec/x_spec.rb", "lib/x.rb"], ["spec/"]).reason, REASON_ELIGIBLE
        )

    def test_go_style_suffix_layout_passes_when_declared(self):
        # Tests beside sources — no directory prefix at all.
        self.assertEqual(
            _decide(["pkg/x_test.go", "pkg/x.go"], ["pkg/"]).reason, REASON_ELIGIBLE
        )

    def test_diff_outside_every_declared_path_still_declines(self):
        # The guardrail must not become permissive: a diff with no test evidence
        # under any declared path is still refused.
        self.assertEqual(
            _decide(["lib/x.rb"], ["spec/"]).reason, REASON_NO_TEST_EVIDENCE
        )

    def test_any_declared_path_matching_is_enough(self):
        self.assertEqual(
            _decide(["src/__tests__/x.js", "src/x.js"], ["spec/", "src/__tests__/"]).reason,
            REASON_ELIGIBLE,
        )

    def test_empty_test_paths_declines_rather_than_permits(self):
        # Fail closed: declaring no test paths must not mean "no evidence needed".
        # The permissive reading would silently disable the guardrail entirely,
        # which is the opposite of the defect being fixed.
        self.assertEqual(_decide(["tests/test_x.py"], []).reason, REASON_NO_TEST_EVIDENCE)

    def test_unreadable_test_paths_fails_closed(self):
        for bad in (None, "tests/", 42):
            with self.subTest(value=bad):
                self.assertFalse(_decide(["tests/test_x.py"], bad).eligible)


if __name__ == "__main__":
    unittest.main()
