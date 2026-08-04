# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the autofix predicate (FEAT-2026-0042/T01)."""

from __future__ import annotations

import subprocess
import unittest

from specfuse.monitor.autofix import (
    CONFIDENCE_THRESHOLD,
    DECLINE,
    FIRE,
    REASON_ALREADY_ATTEMPTED,
    REASON_DAILY_CAP_REACHED,
    REASON_DIAL_OFF,
    REASON_ELIGIBLE,
    REASON_FIX_SCOPE_OUT_OF_COMPETENCE,
    REASON_LOW_CONFIDENCE,
    REASON_UNREADABLE_INPUT,
    ROUTE_TO_HUMAN,
    decide,
)
from specfuse.monitor.diagnosis import Diagnosis, render

_COMPONENT = "order-worker"
_FINGERPRINT = "fp-1234"


def _diagnosis_body(confidence: float, fix_scope: str) -> str:
    return render(
        Diagnosis(
            root_cause="root",
            evidence="evidence",
            candidate_fix="fix",
            confidence=confidence,
            fix_scope=fix_scope,
        )
    )


def _config(dial):
    return {_COMPONENT: {"autofix": dial}}


class _StubStateReader:
    def __init__(self, *, has_prior_attempt=False, daily_cap_reached=False):
        self._has_prior_attempt = has_prior_attempt
        self._daily_cap_reached = daily_cap_reached

    def has_prior_attempt(self, fingerprint):
        return self._has_prior_attempt

    def daily_cap_reached(self):
        return self._daily_cap_reached


class _RaisingHasPriorAttemptReader:
    def has_prior_attempt(self, fingerprint):
        raise RuntimeError("state store unreachable")

    def daily_cap_reached(self):
        raise AssertionError("should not be reached")


class _RaisingDailyCapReader:
    def has_prior_attempt(self, fingerprint):
        return False

    def daily_cap_reached(self):
        raise RuntimeError("state store unreachable")


class TestAutofixPredicate(unittest.TestCase):
    def test_dial_off_declines_regardless_of_confidence(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("off"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_DIAL_OFF)

    def test_large_fix_scope_routes_to_human(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="large"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, ROUTE_TO_HUMAN)
        self.assertEqual(decision.reason, REASON_FIX_SCOPE_OUT_OF_COMPETENCE)

    def test_external_fix_scope_routes_to_human(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="external"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, ROUTE_TO_HUMAN)
        self.assertEqual(decision.reason, REASON_FIX_SCOPE_OUT_OF_COMPETENCE)

    def test_large_and_external_are_route_to_human_not_decline(self):
        for scope in ("large", "external"):
            decision = decide(
                diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope=scope),
                monitoring_config=_config("on"),
                component=_COMPONENT,
                fingerprint=_FINGERPRINT,
                state_reader=_StubStateReader(),
            )
            self.assertEqual(decision.decision, ROUTE_TO_HUMAN, msg=scope)
            self.assertNotEqual(decision.decision, DECLINE, msg=scope)

    def test_low_confidence_routes_to_human(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(
                confidence=CONFIDENCE_THRESHOLD - 0.01, fix_scope="small"
            ),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, ROUTE_TO_HUMAN)
        self.assertEqual(decision.reason, REASON_LOW_CONFIDENCE)

    def test_prior_attempt_declines(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(has_prior_attempt=True),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_ALREADY_ATTEMPTED)

    def test_daily_cap_reached_declines(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(daily_cap_reached=True),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_DAILY_CAP_REACHED)

    def test_eligible_diagnosis_fires(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, FIRE)
        self.assertEqual(decision.reason, REASON_ELIGIBLE)

    def test_unparseable_diagnosis_declines(self):
        decision = decide(
            diagnosis_body="not a diagnosis comment at all",
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_UNREADABLE_INPUT)

    def test_malformed_diagnosis_marker_declines(self):
        decision = decide(
            diagnosis_body="<!-- specfuse:diagnosis confidence=oops -->",
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_UNREADABLE_INPUT)

    def test_component_absent_from_config_declines(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config={"some-other-component": {"autofix": "on"}},
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_UNREADABLE_INPUT)

    def test_malformed_dial_value_declines(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("enabled"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_StubStateReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_UNREADABLE_INPUT)

    def test_state_reader_raising_on_prior_attempt_declines(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_RaisingHasPriorAttemptReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_UNREADABLE_INPUT)

    def test_state_reader_raising_on_daily_cap_declines(self):
        decision = decide(
            diagnosis_body=_diagnosis_body(confidence=1.0, fix_scope="small"),
            monitoring_config=_config("on"),
            component=_COMPONENT,
            fingerprint=_FINGERPRINT,
            state_reader=_RaisingDailyCapReader(),
        )
        self.assertEqual(decision.decision, DECLINE)
        self.assertEqual(decision.reason, REASON_UNREADABLE_INPUT)

    def test_confidence_threshold_is_module_constant_no_config_read(self):
        self.assertIsInstance(CONFIDENCE_THRESHOLD, float)
        result = subprocess.run(
            [
                "grep",
                "-n",
                r"open(\|Path(\|yaml\|load",
                "specfuse/monitor/autofix.py",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, msg=f"unexpected match: {result.stdout!r}")
        self.assertEqual(result.stdout, "")

    def test_no_subprocess_network_or_gh_call(self):
        result = subprocess.run(
            [
                "grep",
                "-n",
                r"^from \|^import \|subprocess\|requests\|urllib\|gh ",
                "specfuse/monitor/autofix.py",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        allowed_prefixes = (
            "from __future__ import annotations",
            "from dataclasses import dataclass",
            "from typing import Any, Mapping, Protocol",
            "from specfuse.monitor.diagnosis import Diagnosis, DiagnosisParseError, parse",
        )
        for line in result.stdout.splitlines():
            _, _, content = line.partition(":")
            _, _, statement = content.partition(":")
            self.assertTrue(
                statement.strip().startswith(allowed_prefixes)
                or statement.strip() == "",
                msg=f"unexpected import/call line: {line!r}",
            )


if __name__ == "__main__":
    unittest.main()
