#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Unit tests for attempt_outcome emission (T01) and cumulative-fold logic (T02).

FEAT-2026-0016/T03 — tests only; production code is read-only from this WU.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

DUMMY_USAGE = {
    "duration_seconds": 1.5,
    "cost_usd": 0.01,
    "input_tokens": 100,
    "output_tokens": 50,
    "cache_read_input_tokens": 10,
    "cache_creation_input_tokens": 5,
}


def _make_wu(wu_file: Path, wu_id: str = "FEAT-2026-9999/T01") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=wu_file,
        depends_on=[],
        type="implementation",
        model="sonnet",
        effort="medium",
        status="pending",
        attempts=0,
        title="Test WU",
        body=_WU_BODY,
    )


def _write_wu_file(path: Path, extra_fields: str = "") -> None:
    path.write_text(
        f"---\nid: FEAT-2026-9999/T01\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n{extra_fields}---\n\n# Test WU{_WU_BODY}"
    )


# --------------------------------------------------------------------------- #
# TestEmitAttemptOutcome                                                       #
# --------------------------------------------------------------------------- #


class TestEmitAttemptOutcome(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)
        self._wu_file = self._root / "WU-T01.md"
        _write_wu_file(self._wu_file)
        self._wu = _make_wu(self._wu_file)

    def tearDown(self):
        self._tmp.cleanup()

    def _required_top_fields(self):
        return {"event_type", "correlation_id", "timestamp"}

    def _required_payload_fields(self):
        return {
            "attempt", "outcome", "duration_seconds", "cost_usd",
            "input_tokens", "output_tokens", "cache_read_input_tokens",
            "cache_creation_input_tokens", "model", "effort",
            "failure_class", "failure_signature", "failure_excerpt",
            "files_touched", "agent_status", "agent_blocked_reason",
            "re_arm_count",
        }

    def test_emit_attempt_outcome_passed_has_all_required_fields(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "passed", DUMMY_USAGE,
            agent_status="complete",
        )
        for field in self._required_top_fields():
            self.assertIn(field, event, f"top-level field missing: {field}")
        payload = event["payload"]
        for field in self._required_payload_fields():
            self.assertIn(field, payload, f"payload field missing: {field}")

        self.assertEqual(payload["outcome"], "passed")
        self.assertEqual(payload["attempt"], 1)
        self.assertIsNone(payload["failure_class"])
        self.assertIsNone(payload["failure_signature"])
        self.assertIsNone(payload["failure_excerpt"])
        self.assertIsInstance(payload["files_touched"], list)
        self.assertEqual(payload["agent_status"], "complete")
        self.assertIsNone(payload["agent_blocked_reason"])
        self.assertIsInstance(payload["re_arm_count"], int)
        self.assertEqual(event["event_type"], "attempt_outcome")

    def test_emit_attempt_outcome_failed_carries_failure_metadata(self):
        event = loop.emit_attempt_outcome(
            self._wu, 2, "failed", DUMMY_USAGE,
            failure_class="tests",
            failure_signature="test_foo",
            failure_excerpt="FAIL: test_foo",
            files_touched=["foo.py"],
            agent_status="complete",
            agent_blocked_reason=None,
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "failed")
        self.assertEqual(payload["failure_class"], "tests")
        self.assertEqual(payload["failure_signature"], "test_foo")
        self.assertEqual(payload["failure_excerpt"], "FAIL: test_foo")
        self.assertEqual(payload["agent_status"], "complete")
        self.assertIsNone(payload["agent_blocked_reason"])

    def test_emit_attempt_outcome_blocked_carries_agent_reason(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "blocked", DUMMY_USAGE,
            agent_status="blocked",
            agent_blocked_reason="missing credential",
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "blocked")
        self.assertEqual(payload["agent_status"], "blocked")
        self.assertEqual(payload["agent_blocked_reason"], "missing credential")

    def test_emit_attempt_outcome_zero_token_skip_no_failure_class(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "zero_token_skip", DUMMY_USAGE,
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "zero_token_skip")
        self.assertIsNone(payload["failure_class"])

    def test_emit_attempt_outcome_post_pass_invariant_failed(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "post_pass_invariant_failed", DUMMY_USAGE,
            extras={"assertion": "gate must be passed"},
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "post_pass_invariant_failed")
        self.assertIn("assertion", payload)
        self.assertEqual(payload["assertion"], "gate must be passed")

    def test_emit_attempt_outcome_closing_deliverable_missing(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "closing_deliverable_missing", DUMMY_USAGE,
            extras={
                "assertion": "RETROSPECTIVE.md missing",
                "summary": "RETROSPECTIVE.md missing: file not found",
            },
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "closing_deliverable_missing")
        self.assertIn("assertion", payload)

    def test_emit_attempt_outcome_files_changed_mismatch(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "files_changed_mismatch", DUMMY_USAGE,
            extras={"unchanged_paths": ["foo.py", "bar.py"]},
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "files_changed_mismatch")
        self.assertIn("unchanged_paths", payload)
        self.assertIsInstance(payload["unchanged_paths"], list)

    def test_emit_attempt_outcome_smoke_import_failed(self):
        event = loop.emit_attempt_outcome(
            self._wu, 1, "smoke_import_failed", DUMMY_USAGE,
            extras={"summary": "ImportError: no module named foo"},
        )
        payload = event["payload"]
        self.assertEqual(payload["outcome"], "smoke_import_failed")
        self.assertIn("summary", payload)


# --------------------------------------------------------------------------- #
# TestParseGateFailureSignature                                                #
# --------------------------------------------------------------------------- #


class TestParseGateFailureSignature(unittest.TestCase):

    def test_tests_fail_extracts_first_failing_test_name(self):
        stdout = "### tests: FAIL\nFAIL: test_foo"
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "tests")
        self.assertEqual(sig, "test_foo")

    def test_lint_fail_extracts_first_ruff_code(self):
        stdout = "### lint: FAIL\nfile.py:5:1: E501 line too long"
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "lint")
        self.assertEqual(sig, "E501")

    def test_security_fail_extracts_first_bandit_id(self):
        stdout = (
            "### security: FAIL\n"
            "Issue: [B602:subprocess_popen_with_shell_equals_true]"
        )
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "security")
        self.assertEqual(sig, "B602")

    def test_coverage_fail_extracts_first_uncovered_file(self):
        stdout = "### coverage: FAIL\nfile.py 100 10  90%"
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "coverage")
        self.assertEqual(sig, "file.py")

    def test_unknown_gate_name_returns_other(self):
        stdout = "### custom-gate: FAIL\nsome output"
        fc, _sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "other")

    def test_no_fail_marker_returns_no_gate_marker(self):
        stdout = "all tests passed\n no failures here"
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "other")
        self.assertEqual(sig, "no_gate_marker")

    # -- #167: non-Python gate output must not collapse to a bare fence -- #

    def test_fallback_skips_bare_code_fence(self):
        # A non-Python tests gate (e.g. TypeScript) matches none of the
        # Python _SIG_PATTERNS and falls through. The first line after the
        # marker is a Markdown fence; the signature must key off the real
        # failure line beneath it, not the fence.
        stdout = (
            "### tests: FAIL\n"
            "```\n"
            "  ✕ company builds a valid config (expected 3, got 4)\n"
            "```\n"
        )
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "tests")
        self.assertNotEqual(sig, "```")
        self.assertIn("company builds a valid config", sig)

    def test_fallback_skips_whitespace_and_tilde_fence(self):
        stdout = "### tests: FAIL\n   \n~~~\n\nReal failure: assertion X\n"
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "tests")
        self.assertIn("Real failure", sig)

    def test_all_noninformative_returns_no_signature(self):
        stdout = "### tests: FAIL\n```\n   \n~~~\n"
        fc, sig = loop.parse_gate_failure_signature(stdout)
        self.assertEqual(fc, "tests")
        self.assertEqual(sig, "no_signature")

    def test_two_distinct_ts_failures_yield_distinct_signatures(self):
        # The #167 false-spin: two genuinely different failures must NOT
        # reduce to the same signature (both previously became "```").
        a = "### tests: FAIL\n```\n  ✕ builds config (expected 3, got 4)\n```\n"
        b = "### tests: FAIL\n```\n  ✕ parses tokens (unexpected EOF)\n```\n"
        _, sig_a = loop.parse_gate_failure_signature(a)
        _, sig_b = loop.parse_gate_failure_signature(b)
        self.assertNotEqual(sig_a, sig_b)


# --------------------------------------------------------------------------- #
# TestExtractFailureExcerpt                                                    #
# --------------------------------------------------------------------------- #


class TestExtractFailureExcerpt(unittest.TestCase):

    def test_extracts_error_lines_when_present(self):
        stdout = "normal line\nError: foo\nanother line"
        excerpt = loop.extract_failure_excerpt(stdout)
        self.assertIn("Error: foo", excerpt)

    def test_truncates_to_max_chars(self):
        stdout = "Error: " + "x" * 10000
        excerpt = loop.extract_failure_excerpt(stdout, max_chars=500)
        self.assertLessEqual(len(excerpt.encode("utf-8")), 500)

    def test_falls_back_to_last_lines_when_no_error_pattern(self):
        stdout = "line one\nline two\nline three"
        excerpt = loop.extract_failure_excerpt(stdout)
        # No FAIL/Error/Exception/Traceback → falls back to all stdout
        self.assertIn("line three", excerpt)

    def test_handles_utf8_safe_boundary(self):
        # Build a string with multi-byte chars that would be truncated
        # mid-codepoint if we naively sliced bytes.
        multibyte = "Error: " + "日本語テスト" * 100
        try:
            excerpt = loop.extract_failure_excerpt(multibyte, max_chars=500)
        except UnicodeDecodeError as e:
            self.fail(f"UnicodeDecodeError raised: {e}")
        self.assertIsInstance(excerpt, str)


# --------------------------------------------------------------------------- #
# TestCumulativeFoldOnRearm                                                    #
# --------------------------------------------------------------------------- #


def _write_wu_with_costs(path: Path, **fields) -> None:
    """Write a WU file with given frontmatter fields."""
    lines = ["---", "id: FEAT-2026-9999/T01", "type: implementation",
             "model: sonnet", "status: pending", "attempts: 0"]
    for k, v in fields.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("# Test WU" + _WU_BODY)
    path.write_text("\n".join(lines))


def _read_fm(path: Path) -> dict:
    fm, _ = loop.read_frontmatter(path)
    return fm


class TestCumulativeFoldOnRearm(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _backend(self):
        return loop.Backend()

    def test_first_dispatch_no_fold(self):
        wu_file = self._root / "WU-T01.md"
        _write_wu_with_costs(wu_file)  # no re_arm_count, no cost_usd
        wu = _make_wu(wu_file)

        result = loop.detect_rearm_dispatch(wu)
        self.assertFalse(result, "first dispatch (no re_arm_count) must not be re-arm")

    def test_first_dispatch_zero_rearm_count_no_fold(self):
        wu_file = self._root / "WU-T01.md"
        _write_wu_with_costs(wu_file, re_arm_count=0, cost_usd=5.0)
        wu = _make_wu(wu_file)

        result = loop.detect_rearm_dispatch(wu)
        self.assertFalse(result, "re_arm_count=0 must not trigger fold")

    def test_rearm_dispatch_folds_prior_cycle(self):
        wu_file = self._root / "WU-T01.md"
        _write_wu_with_costs(
            wu_file,
            re_arm_count=1,
            cost_usd=5.0,
            input_tokens=100,
            output_tokens=50,
            cumulative_cost_usd=0,
            cumulative_input_tokens=0,
            cumulative_output_tokens=0,
        )
        wu = _make_wu(wu_file)
        backend = self._backend()

        loop.fold_cumulative_on_rearm(wu, backend)

        fm = _read_fm(wu_file)
        self.assertEqual(float(fm.get("cumulative_cost_usd", 0)), 5.0)
        self.assertEqual(float(fm.get("cost_usd", 999)), 0.0)
        self.assertEqual(int(fm.get("cumulative_input_tokens", 0)), 100)
        self.assertEqual(int(fm.get("input_tokens", 999)), 0)
        self.assertEqual(int(fm.get("cumulative_output_tokens", 0)), 50)
        self.assertEqual(int(fm.get("output_tokens", 999)), 0)

    def test_rearm_dispatch_preserves_cumulative_from_earlier_rearms(self):
        wu_file = self._root / "WU-T01.md"
        _write_wu_with_costs(
            wu_file,
            re_arm_count=2,
            cost_usd=3.0,
            input_tokens=30,
            output_tokens=20,
            cumulative_cost_usd=5.0,
            cumulative_input_tokens=80,
            cumulative_output_tokens=40,
        )
        wu = _make_wu(wu_file)
        backend = self._backend()

        loop.fold_cumulative_on_rearm(wu, backend)

        fm = _read_fm(wu_file)
        self.assertAlmostEqual(float(fm.get("cumulative_cost_usd", 0)), 8.0, places=5)
        self.assertEqual(float(fm.get("cost_usd", 999)), 0.0)
        self.assertEqual(int(fm.get("cumulative_input_tokens", 0)), 110)
        self.assertEqual(int(fm.get("cumulative_output_tokens", 0)), 60)

    def test_missing_fields_default_zero(self):
        wu_file = self._root / "WU-T01.md"
        # No cumulative_* fields at all; prior cycle has cost
        _write_wu_with_costs(wu_file, re_arm_count=1, cost_usd=2.5,
                             input_tokens=10, output_tokens=5)
        wu = _make_wu(wu_file)
        backend = self._backend()

        try:
            loop.fold_cumulative_on_rearm(wu, backend)
        except KeyError as e:
            self.fail(f"KeyError raised on missing cumulative_ fields: {e}")

        fm = _read_fm(wu_file)
        self.assertAlmostEqual(float(fm.get("cumulative_cost_usd", 0)), 2.5, places=5)

    def test_re_arm_dispatched_event_emitted(self):
        # Verify build_event produces the right shape for re_arm_dispatched.
        wu_file = self._root / "WU-T01.md"
        _write_wu_with_costs(wu_file, re_arm_count=1, cost_usd=2.0)
        wu = _make_wu(wu_file)

        event = loop.build_event("re_arm_dispatched", wu.wu_id, {
            "re_arm_count": 1,
            "reason": "operator re-armed after credential fix",
        })

        self.assertEqual(event["event_type"], "re_arm_dispatched")
        self.assertEqual(event["correlation_id"], wu.wu_id)
        self.assertIn("timestamp", event)
        payload = event["payload"]
        self.assertIn("re_arm_count", payload)
        self.assertEqual(payload["re_arm_count"], 1)
        self.assertIn("reason", payload)


# --------------------------------------------------------------------------- #
# TestDetectSpinningSignatureRepeat                                            #
# --------------------------------------------------------------------------- #


class TestDetectSpinningSignatureRepeat(unittest.TestCase):

    def test_detect_spinning_signature_repeat_true_on_match(self):
        result = loop.detect_spinning_signature_repeat(
            ("tests", "test_foo"), ("tests", "test_foo"),
        )
        self.assertTrue(result)

    def test_detect_spinning_signature_repeat_false_on_none_prior(self):
        result = loop.detect_spinning_signature_repeat(
            ("tests", "test_foo"), None,
        )
        self.assertFalse(result)

    def test_detect_spinning_signature_repeat_false_on_null_element(self):
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                (None, "test_foo"), ("tests", "test_foo"),
            )
        )
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", None), ("tests", "test_foo"),
            )
        )

    def test_detect_spinning_signature_repeat_false_on_no_gate_marker_current(self):
        result = loop.detect_spinning_signature_repeat(
            ("other", "no_gate_marker"), ("tests", "test_foo"),
        )
        self.assertFalse(result)

    def test_detect_spinning_signature_repeat_false_on_no_gate_marker_prior(self):
        result = loop.detect_spinning_signature_repeat(
            ("tests", "test_foo"), ("other", "no_gate_marker"),
        )
        self.assertFalse(result)

    # -- #167: non-informative signatures must not trip the spin detector -- #

    def test_false_on_bare_fence_signature(self):
        # The exact #167 shape: both attempts reduced to "```". Even though
        # current == prior, a bare fence carries no failure-distinguishing
        # content and must not escalate.
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", "```"), ("tests", "```"),
            )
        )

    def test_false_on_whitespace_signature(self):
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", "   "), ("tests", "   "),
            )
        )

    def test_false_on_pure_ansi_signature(self):
        ansi = "\x1b[31m\x1b[0m"
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", ansi), ("tests", ansi),
            )
        )

    def test_false_on_no_signature_sentinel(self):
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", "no_signature"), ("tests", "no_signature"),
            )
        )

    def test_still_true_on_real_repeated_signature(self):
        # Guard against over-correction: a genuine repeat still escalates.
        self.assertTrue(
            loop.detect_spinning_signature_repeat(
                ("tests", "builds config (expected 3, got 4)"),
                ("tests", "builds config (expected 3, got 4)"),
            )
        )


# --------------------------------------------------------------------------- #
# TestSummarizeAttemptFailureClasses                                           #
# --------------------------------------------------------------------------- #


def _make_attempt_outcome_event(
    wu_id: str,
    outcome: str,
    failure_class: str | None = None,
    failure_signature: str | None = None,
) -> dict:
    return {
        "event_type": "attempt_outcome",
        "correlation_id": wu_id,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "source": "driver",
        "source_version": "test",
        "payload": {
            "attempt": 1,
            "outcome": outcome,
            "failure_class": failure_class,
            "failure_signature": failure_signature,
        },
    }


def _write_events(path: Path, events: list) -> None:
    import json as _json
    with path.open("w") as fh:
        for evt in events:
            fh.write(_json.dumps(evt) + "\n")


class TestSummarizeAttemptFailureClasses(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)
        self._events_path = self._root / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_summarize_failure_classes_empty_when_all_passed(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "passed"),
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T02", "passed"),
        ])
        result = loop.summarize_attempt_failure_classes(self._root)
        self.assertEqual(result, loop._NO_FAILURES_SENTINEL)

    def test_summarize_failure_classes_groups_by_class(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_foo_bar"),
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_foo_bar"),
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_baz"),
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T02", "failed", "lint", "E501"),
        ])
        result = loop.summarize_attempt_failure_classes(self._root)
        self.assertIn("### Failure-class breakdown", result)
        self.assertIn("| tests | 3 | test_foo_bar |", result)
        self.assertIn("| lint | 1 | E501 |", result)
        self.assertIn("| **total** | **4** | — |", result)
        # tests row must appear before lint row (count desc)
        self.assertLess(result.index("| tests |"), result.index("| lint |"))

    def test_summarize_failure_classes_filters_by_gate(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_a"),
            _make_attempt_outcome_event("FEAT-2026-9999/G2-T01", "failed", "lint", "E501"),
        ])
        result = loop.summarize_attempt_failure_classes(self._root, gate_n=2)
        self.assertNotIn("tests", result)
        self.assertIn("| lint | 1 | E501 |", result)

    def test_summarize_failure_classes_no_events_file_returns_sentinel(self):
        result = loop.summarize_attempt_failure_classes(self._root)
        self.assertEqual(result, loop._NO_FAILURES_SENTINEL)


# --------------------------------------------------------------------------- #
# TestAssertFailureClassBreakdownWhenFailuresPresent                           #
# --------------------------------------------------------------------------- #


def _make_close_wu(wu_file: Path, wu_id: str = "FEAT-2026-9999/G1-CLOSE") -> "loop.WorkUnit":
    wu_file.write_text(
        f"---\nid: {wu_id}\ntype: close\nmodel: sonnet\nstatus: pending\nattempts: 0\n"
        f"verdict: met\n---\n\n# Close WU\n"
    )
    return loop.WorkUnit(
        wu_id=wu_id,
        file=wu_file,
        depends_on=[],
        type="close",
        model="sonnet",
        effort="medium",
        status="pending",
        attempts=0,
        title="Close WU",
        body="",
        verdict="met",
    )


class TestAssertFailureClassBreakdownWhenFailuresPresent(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)
        self._wu_file = self._root / "G1-CLOSE.md"
        self._wu = _make_close_wu(self._wu_file)
        self._retro = self._root / "RETROSPECTIVE.md"
        self._events_path = self._root / "events.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_guard_passes_when_no_failures(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "passed"),
        ])
        self._retro.write_text("## Cost analysis\n\nsome content\n")
        ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
            self._wu, self._root, self._root, "HEAD",
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_guard_fails_when_failures_present_but_heading_absent(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_foo"),
        ])
        self._retro.write_text("## Cost analysis\n\nsome content\n")
        ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
            self._wu, self._root, self._root, "HEAD",
        )
        self.assertFalse(ok)
        self.assertIn("assert_failure_class_breakdown_when_failures_present", reason)
        self.assertIn("1", reason)
        self.assertIn("### Failure-class breakdown", reason)

    def test_guard_passes_when_failures_present_and_heading_present(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_foo"),
        ])
        self._retro.write_text(
            "## Cost analysis\n\nsome content\n\n### Failure-class breakdown\n\n| ... |\n"
        )
        ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
            self._wu, self._root, self._root, "HEAD",
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_guard_passes_when_retro_absent(self):
        _write_events(self._events_path, [
            _make_attempt_outcome_event("FEAT-2026-9999/G1-T01", "failed", "tests", "test_foo"),
        ])
        # No RETROSPECTIVE.md written
        ok, reason = loop.assert_failure_class_breakdown_when_failures_present(
            self._wu, self._root, self._root, "HEAD",
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
