# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0041/T01: the diagnosis comment contract."""

from __future__ import annotations

import unittest

from specfuse.monitor.diagnosis import (
    Diagnosis,
    DiagnosisParseError,
    FIX_SCOPES,
    parse,
    render,
)

_CONN_STRING_SECRET = "postgres://svc_user:Sup3rSecret!Pass@db.internal:5432/orders"
_BEARER_SECRET_A = "Bearer abcDEF123456789token"
_BEARER_SECRET_B = "Bearer zyxWVU987654321other"


class TestDiagnosis(unittest.TestCase):
    def _make(self, fix_scope: str) -> Diagnosis:
        return Diagnosis(
            root_cause="the worker retried a poisoned message without a backoff",
            evidence="dlq depth climbed from 0 to 40 over five minutes",
            candidate_fix="add exponential backoff to the retry loop",
            confidence=0.75,
            fix_scope=fix_scope,
        )

    def test_render_parse_roundtrip_preserves_fix_scope(self):
        for fix_scope in FIX_SCOPES:
            diagnosis = self._make(fix_scope)
            with self.subTest(fix_scope=fix_scope):
                self.assertEqual(parse(render(diagnosis)), diagnosis)

    def test_illegal_fix_scope_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            Diagnosis(
                root_cause="r",
                evidence="e",
                candidate_fix="c",
                confidence=0.5,
                fix_scope="huge",
            )

    def test_illegal_confidence_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            Diagnosis(
                root_cause="r",
                evidence="e",
                candidate_fix="c",
                confidence=1.5,
                fix_scope="small",
            )

    def test_secret_shaped_prose_is_redacted_on_render(self):
        diagnosis = Diagnosis(
            root_cause=f"connection failed against {_CONN_STRING_SECRET}",
            evidence=f"auth header carried {_BEARER_SECRET_A}",
            candidate_fix="rotate the credential",
            confidence=0.4,
            fix_scope="external",
        )

        body = render(diagnosis)

        self.assertIn("<redacted:", body)
        self.assertNotIn(_CONN_STRING_SECRET, body)
        self.assertNotIn(_BEARER_SECRET_A, body)

    def test_same_secret_redacts_to_same_token_different_to_different(self):
        diagnosis = Diagnosis(
            root_cause=f"seen twice: {_BEARER_SECRET_A} and again {_BEARER_SECRET_A}",
            evidence=f"distinct secret here: {_BEARER_SECRET_B}",
            candidate_fix="rotate the credential",
            confidence=0.4,
            fix_scope="external",
        )

        body = render(diagnosis)

        root_cause_section = body.split("**Evidence:**")[0]
        tokens = [
            part for part in root_cause_section.replace("\n", " ").split()
            if part.startswith("<redacted:")
        ]
        self.assertEqual(len(tokens), 2, root_cause_section)
        self.assertEqual(tokens[0], tokens[1])
        self.assertNotIn(tokens[0], body.split("**Evidence:**")[1])

    def test_parse_returns_none_on_body_with_no_marker(self):
        self.assertIsNone(parse("just some prose with no marker at all"))

    def test_parse_raises_named_error_on_malformed_marker(self):
        body = "<!-- specfuse:diagnosis confidence=notanumber fix_scope=small -->"
        with self.assertRaises(DiagnosisParseError):
            parse(body)

    def test_parse_raises_named_error_on_unterminated_marker(self):
        body = "<!-- specfuse:diagnosis confidence=0.5 fix_scope=small"
        with self.assertRaises(DiagnosisParseError):
            parse(body)


if __name__ == "__main__":
    unittest.main()
