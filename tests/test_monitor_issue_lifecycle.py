# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.monitor.issues, the fingerprint-keyed issue lifecycle."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

import specfuse.loop.escalation as escalation
import specfuse.monitor.issues as issues
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.issues import (
    DEFAULT_QUIET_AFTER_RUNS,
    FINDING_LABEL,
    TruncatedListingError,
    annotate_if_quiet,
    find_finding_issue,
    record_finding,
)

_ISSUES_SOURCE = Path("specfuse/monitor/issues.py").read_text(encoding="utf-8")

_REPO = "acme-widget/repo"


def _artifact(**overrides):
    fields = dict(
        component="orders-worker",
        check_type="dlq",
        failure_class="poison-message",
        failure_signature="orders.created.dlq",
        observed_text="dead-lettered after 5 attempts",
        target_coordinates={"subscription": "orders-created", "function": "OnOrderCreated"},
    )
    fields.update(overrides)
    return FailureArtifact(**fields)


class _StubRunner:
    """Records every call and replays a scripted sequence of results."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return self._results.pop(0)


def _list_result(issues_json):
    return SimpleNamespace(returncode=0, stdout=json.dumps(issues_json), stderr="")


def _create_result(number=101):
    return SimpleNamespace(
        returncode=0,
        stdout=f"https://github.com/{_REPO}/issues/{number}\n",
        stderr="",
    )


def _ok_result():
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def _row(fingerprint, *, number=101, occurrences=1, last_seen=1000.0, extra_marker=""):
    body = (
        f"<!-- specfuse:finding fingerprint={fingerprint} -->\n"
        f"<!-- specfuse:finding-meta occurrences={occurrences} last_seen={last_seen} -->\n"
        f"{extra_marker}\nsome finding body"
    )
    return {"number": number, "body": body, "title": f"[monitor:{fingerprint[:12]}] x"}


class TestFindingLifecycle(unittest.TestCase):
    # --- criterion 3: reuse asserted, not claimed ---

    def test_reuses_extract_issue_number_and_default_runner_from_escalation(self):
        self.assertIs(issues._extract_issue_number, escalation._extract_issue_number)
        self.assertIs(issues._default_runner, escalation._default_runner)

    def test_no_reimplementation_of_issue_number_parse(self):
        defined = re.findall(r"^def (\w+)", _ISSUES_SOURCE, flags=re.MULTILINE)
        self.assertNotIn("_extract_issue_number", defined)

    # --- criterion 4: finder does not pass the marker to --search ---

    def test_source_never_passes_search_flag(self):
        self.assertNotIn('"--search"', _ISSUES_SOURCE)
        self.assertNotIn("'--search'", _ISSUES_SOURCE)

    def test_list_call_uses_label_and_json_fields_not_search(self):
        runner = _StubRunner([_list_result([])])

        find_finding_issue(runner, _REPO, "fp-1")

        list_call = runner.calls[0]
        self.assertIn("--label", list_call)
        self.assertIn(FINDING_LABEL, list_call)
        self.assertIn("--json", list_call)
        self.assertIn("number,body,title", list_call)
        self.assertNotIn("--search", list_call)

    # --- criterion 5: marker-in-body re-check is load-bearing ---

    def test_finder_returns_only_the_row_whose_body_carries_the_marker(self):
        fp = "fp-target"
        matching = _row(fp, number=55)
        non_matching = _row("fp-other", number=56)
        runner = _StubRunner([_list_result([non_matching, matching])])

        found = find_finding_issue(runner, _REPO, fp)

        self.assertEqual(found["number"], 55)

    def test_finder_reports_not_found_when_no_row_carries_the_marker(self):
        rows = [_row("fp-a", number=1), _row("fp-b", number=2)]
        runner = _StubRunner([_list_result(rows)])

        found = find_finding_issue(runner, _REPO, "fp-absent")

        self.assertIsNone(found)

    def test_create_path_runs_when_finder_reports_not_found(self):
        rows = [_row("fp-a", number=1)]
        runner = _StubRunner([_list_result(rows), _create_result(number=200)])

        number = record_finding("fp-new", _artifact(), _REPO, runner=runner, now=1000.0)

        self.assertEqual(number, "200")
        self.assertIn("create", runner.calls[-1])

    # --- criterion 6: a truncated page is never reported as not-found ---

    def test_full_page_with_no_match_raises_rather_than_reports_not_found(self):
        limit = 3
        rows = [_row(f"fp-{i}", number=i) for i in range(limit)]
        runner = _StubRunner([_list_result(rows)])

        with self.assertRaises(TruncatedListingError):
            find_finding_issue(runner, _REPO, "fp-missing", limit=limit)

    def test_page_under_limit_with_no_match_does_not_raise(self):
        limit = 5
        rows = [_row(f"fp-{i}", number=i) for i in range(limit - 1)]
        runner = _StubRunner([_list_result(rows)])

        found = find_finding_issue(runner, _REPO, "fp-missing", limit=limit)

        self.assertIsNone(found)

    # --- criteria 1 & 7: idempotence, the property this unit exists for ---

    def test_second_sighting_of_one_fingerprint_creates_no_second_issue(self):
        artifact = _artifact()
        fp = fingerprint_artifact(artifact)

        first_runner = _StubRunner([_list_result([]), _create_result(number=300)])
        first_number = record_finding(fp, artifact, _REPO, runner=first_runner, now=1000.0)

        created_row = _row(fp, number=300, occurrences=1, last_seen=1000.0)
        second_runner = _StubRunner([_list_result([created_row])])
        second_number = record_finding(fp, artifact, _REPO, runner=second_runner, now=1000.0)

        self.assertEqual(first_number, "300")
        self.assertEqual(second_number, "300")
        create_calls = [c for c in first_runner.calls + second_runner.calls if "create" in c]
        self.assertEqual(len(create_calls), 1)

    # --- criterion 8: distinct fingerprints do not collapse ---

    def test_distinct_target_coordinates_produce_two_distinct_fingerprints_and_two_creates(self):
        artifact_a = _artifact(target_coordinates={"subscription": "orders-created", "function": "OnOrderCreated"})
        artifact_b = _artifact(target_coordinates={"subscription": "orders-cancelled", "function": "OnOrderCreated"})
        fp_a = fingerprint_artifact(artifact_a)
        fp_b = fingerprint_artifact(artifact_b)
        self.assertNotEqual(fp_a, fp_b)

        runner_a = _StubRunner([_list_result([]), _create_result(number=1)])
        runner_b = _StubRunner([_list_result([]), _create_result(number=2)])

        record_finding(fp_a, artifact_a, _REPO, runner=runner_a, now=1000.0)
        record_finding(fp_b, artifact_b, _REPO, runner=runner_b, now=1000.0)

        self.assertTrue(any("create" in c for c in runner_a.calls))
        self.assertTrue(any("create" in c for c in runner_b.calls))

    # --- criterion 9: occurrence count under throttle, nothing closes ---

    def test_repeat_sighting_outside_throttle_updates_occurrence_record(self):
        fp = "fp-repeat"
        existing_row = _row(fp, number=42, occurrences=1, last_seen=1000.0)
        runner = _StubRunner([_list_result([existing_row]), _ok_result()])

        number = record_finding(
            fp, _artifact(), _REPO, runner=runner, now=1000.0 + issues.DEFAULT_THROTTLE_SECONDS + 1
        )

        self.assertEqual(number, "42")
        edit_calls = [c for c in runner.calls if "edit" in c]
        self.assertEqual(len(edit_calls), 1)
        body_index = edit_calls[0].index("--body") + 1
        self.assertIn("occurrences=2", edit_calls[0][body_index])

    def test_repeat_sighting_inside_throttle_produces_no_update_call(self):
        fp = "fp-throttled"
        existing_row = _row(fp, number=43, occurrences=1, last_seen=1000.0)
        runner = _StubRunner([_list_result([existing_row])])

        number = record_finding(fp, _artifact(), _REPO, runner=runner, now=1000.0 + 60)

        self.assertEqual(number, "43")
        self.assertEqual(len(runner.calls), 1)  # only the list call

    def test_no_close_calls_across_new_repeat_throttled_and_quiet_paths(self):
        all_calls = []

        new_runner = _StubRunner([_list_result([]), _create_result(number=500)])
        record_finding("fp-close-check", _artifact(), _REPO, runner=new_runner, now=1000.0)
        all_calls += new_runner.calls

        row = _row("fp-close-check", number=500, occurrences=1, last_seen=1000.0)
        repeat_runner = _StubRunner([_list_result([row]), _ok_result()])
        record_finding(
            "fp-close-check", _artifact(), _REPO, runner=repeat_runner,
            now=1000.0 + issues.DEFAULT_THROTTLE_SECONDS + 1,
        )
        all_calls += repeat_runner.calls

        throttled_runner = _StubRunner([_list_result([row])])
        record_finding("fp-close-check", _artifact(), _REPO, runner=throttled_runner, now=1000.0 + 1)
        all_calls += throttled_runner.calls

        quiet_runner = _StubRunner([_list_result([row]), _ok_result(), _ok_result()])
        annotate_if_quiet("fp-close-check", _REPO, DEFAULT_QUIET_AFTER_RUNS, runner=quiet_runner)
        all_calls += quiet_runner.calls

        for call in all_calls:
            self.assertNotIn("close", call)
            joined = " ".join(call).lower()
            self.assertNotIn("closed", joined)
            self.assertNotIn("state:closed", joined)

    # --- criterion 10: quiet annotation annotates and stops ---

    def test_quiet_annotation_fires_once_and_names_candidate_for_close(self):
        fp = "fp-quiet"
        row = _row(fp, number=77, occurrences=3, last_seen=1000.0)
        runner = _StubRunner([_list_result([row]), _ok_result(), _ok_result()])

        number = annotate_if_quiet(fp, _REPO, DEFAULT_QUIET_AFTER_RUNS, runner=runner)

        self.assertEqual(number, "77")
        comment_calls = [c for c in runner.calls if "comment" in c]
        self.assertEqual(len(comment_calls), 1)
        body_index = comment_calls[0].index("--body") + 1
        self.assertIn("candidate for close", comment_calls[0][body_index])

    def test_quiet_annotation_below_threshold_does_not_fire(self):
        runner = _StubRunner([])

        result = annotate_if_quiet("fp-not-quiet-yet", _REPO, DEFAULT_QUIET_AFTER_RUNS - 1, runner=runner)

        self.assertIsNone(result)
        self.assertEqual(runner.calls, [])

    def test_quiet_annotation_does_not_repeat_once_already_annotated(self):
        fp = "fp-quiet-repeat"
        already_annotated_row = _row(fp, number=88, occurrences=3, last_seen=1000.0, extra_marker=issues._QUIET_MARKER)
        runner = _StubRunner([_list_result([already_annotated_row])])

        number = annotate_if_quiet(fp, _REPO, DEFAULT_QUIET_AFTER_RUNS, runner=runner)

        self.assertEqual(number, "88")
        comment_calls = [c for c in runner.calls if "comment" in c]
        self.assertEqual(len(comment_calls), 0)

    def test_quiet_after_runs_is_a_named_parameter_not_a_constant_literal(self):
        fp = "fp-custom-n"
        row = _row(fp, number=99, occurrences=1, last_seen=1000.0)
        runner = _StubRunner([_list_result([row]), _ok_result(), _ok_result()])

        number = annotate_if_quiet(fp, _REPO, 2, quiet_after_runs=2, runner=runner)

        self.assertEqual(number, "99")

    # --- criterion 11: redaction at egress ---

    def test_issue_body_redacts_planted_secret_in_observed_text(self):
        # Deliberately carries NO vendor-recognisable prefix. The previous value
        # was Stripe-shaped ("sk_test_51..."), and gitleaks matches that shape
        # rather than a denylist, so the repo's own leak-scan gate failed on the
        # committed tree — blocking the NEXT work unit, which had not touched this
        # file. `redact_artifact` matches on the `api_key=` key-value pattern, not
        # on the token's shape, so realism here buys nothing and costs a red gate.
        # Do not "improve" this back into something that looks like a real key.
        secret = "NotARealCredential0123456789abcdef"
        artifact = _artifact(observed_text=f"upstream call failed: api_key={secret}")
        runner = _StubRunner([_list_result([]), _create_result(number=900)])

        record_finding("fp-secret", artifact, _REPO, runner=runner, now=1000.0)

        create_call = runner.calls[-1]
        body_index = create_call.index("--body") + 1
        body = create_call[body_index]
        self.assertNotIn(secret, body)
        self.assertIn("<redacted:", body)


if __name__ == "__main__":
    unittest.main()
