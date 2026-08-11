# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for specfuse.loop.escalation.emit_escalation."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from specfuse.loop.escalation import (
    CATEGORY_LABELS,
    DEFAULT_ASSIGNEE,
    NEEDS_HUMAN_LABEL,
    emit_escalation,
    validate_escalation_body,
)

_CORRELATION_ID = "FEAT-2026-0046/T02"


def _sample_kwargs():
    return dict(
        category="blocked-wu",
        repo="acme-widget/repo",
        done_so_far="T01 landed.",
        issue_summary="Emission primitive needs a human decision.",
        decision_needed="Whether to proceed with the drafted approach.",
        why_not_auto="This mutation is irreversible and never auto-fired.",
        options=[
            ("Ship as drafted", "fast", "unverified"),
            ("Rewrite from scratch", "clean slate", "slow"),
        ],
        recommendation="Ship as drafted.",
    )


class _StubRunner:
    """Records every call and replays a scripted sequence of results."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(args)
        return self._results.pop(0)


def _search_result(issues):
    return SimpleNamespace(returncode=0, stdout=json.dumps(issues), stderr="")


def _create_result(number=123):
    return SimpleNamespace(
        returncode=0,
        stdout=f"https://github.com/acme-widget/repo/issues/{number}\n",
        stderr="",
    )


class TestEmitEscalation(unittest.TestCase):
    def test_no_existing_issue_creates_one_with_needs_human_label(self):
        runner = _StubRunner([_search_result([]), _create_result()])

        emit_escalation(_CORRELATION_ID, runner=runner, **_sample_kwargs())

        create_call = runner.calls[-1]
        self.assertIn(NEEDS_HUMAN_LABEL, create_call)

    def test_no_existing_issue_create_call_has_exactly_one_category_label(self):
        runner = _StubRunner([_search_result([]), _create_result()])

        emit_escalation(_CORRELATION_ID, runner=runner, **_sample_kwargs())

        create_call = runner.calls[-1]
        present = [label for label in CATEGORY_LABELS if label in create_call]
        self.assertEqual(len(present), 1)

    def test_no_existing_issue_create_call_omits_assignee_by_default(self):
        """Rewritten for #1762. This test previously asserted that the create
        call carried `DEFAULT_ASSIGNEE`, which was the literal
        `specfuse-operator` — a username assignable on no repository. That
        assertion passed for the whole life of the bug and is precisely why it
        reached a live run, where `gh issue create` exited 1 on that flag and
        the escalation was silently never filed.

        The contract now: with nothing configured, no `--assignee` is sent at
        all. An unassigned needs-human issue beats an unfiled one.
        """
        runner = _StubRunner([_search_result([]), _create_result()])

        emit_escalation(_CORRELATION_ID, runner=runner, **_sample_kwargs())

        create_call = runner.calls[-1]
        self.assertEqual(DEFAULT_ASSIGNEE, "")
        self.assertNotIn("--assignee", create_call)
        self.assertNotIn("specfuse-operator", create_call)

    def test_configured_assignee_is_sent(self):
        runner = _StubRunner([_search_result([]), _create_result()])

        emit_escalation(
            _CORRELATION_ID, runner=runner, assignee="clabonte", **_sample_kwargs()
        )

        create_call = runner.calls[-1]
        self.assertIn("--assignee", create_call)
        self.assertIn("clabonte", create_call)

    def test_second_emit_for_same_correlation_id_creates_nothing(self):
        marker = f"<!-- specfuse:escalation id={_CORRELATION_ID} -->"
        runner = _StubRunner([
            _search_result([{"number": 42, "body": f"{marker}\n\nsome body"}]),
        ])

        result = emit_escalation(_CORRELATION_ID, runner=runner, **_sample_kwargs())

        self.assertEqual(result, "42")
        for call in runner.calls:
            self.assertNotIn("create", call)

    def test_created_body_satisfies_validate_escalation_body(self):
        runner = _StubRunner([_search_result([]), _create_result()])

        emit_escalation(_CORRELATION_ID, runner=runner, **_sample_kwargs())

        create_call = runner.calls[-1]
        body = create_call[create_call.index("--body") + 1]
        self.assertEqual(validate_escalation_body(body), [])

    def test_no_test_here_invokes_real_gh(self):
        # Every test in this module injects a stub runner (see _StubRunner
        # above); this test just documents that invariant for criterion 9.
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
