#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.notify_escalation."""

from __future__ import annotations

import tempfile
import unittest
from unittest import mock

from specfuse.loop.escalation import CATEGORY_LABELS, NEEDS_HUMAN_LABEL
from specfuse.loop.notify_escalation import notify_new_escalation

_BASE_POLICY = """\
version: 1
queue: []
rules:
  bugs:
    preempt: true
    min_severity: low
    automerge: "off"
  features:
    gate_review: human
    wip_limit: 1
  triage:
    auto: false
budgets:
  max_tokens_per_run: 2000000
  max_open_prs: 3
  max_items_per_day: 10
escalation:
  webhook_env: {webhook_env}
  provider: {provider}
  assignee: ""
  quiet_hours: ""
  sla_hours: 24
"""


def _write_policy(webhook_env: str = '""', provider: str = "none") -> str:
    text = _BASE_POLICY.format(webhook_env=webhook_env, provider=provider)
    fd = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    fd.write(text)
    fd.close()
    return fd.name


class TestNotifyNewEscalation(unittest.TestCase):
    def test_posts_one_liner_and_link(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_ESC_TEST_URL", provider="discord")
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        with mock.patch.dict(
            "os.environ",
            {"SPECFUSE_NOTIFY_ESC_TEST_URL": "https://example.invalid/hook"},
        ):
            result = notify_new_escalation(
                "FEAT-2026-0047/T02",
                repo="acme-widget/acme-widget",
                issue_number="42",
                category="blocked-wu",
                summary="notifier missing a config key",
                policy_path=path,
                poster=poster,
            )

        self.assertTrue(result)
        self.assertEqual(len(calls), 1)
        _url, payload = calls[0]
        message = payload["content"]
        self.assertIn("https://github.com/acme-widget/acme-widget/issues/42", message)
        self.assertIn("blocked-wu", message)
        self.assertIn("notifier missing a config key", message)

    def test_message_has_no_extra_newline(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_ESC_TEST_URL", provider="discord")
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        with mock.patch.dict(
            "os.environ",
            {"SPECFUSE_NOTIFY_ESC_TEST_URL": "https://example.invalid/hook"},
        ):
            notify_new_escalation(
                "FEAT-2026-0047/T02",
                repo="acme-widget/acme-widget",
                issue_number="42",
                category="blocked-wu",
                summary="multi-line\nsummary body\nwith detail",
                policy_path=path,
                poster=poster,
            )

        message = calls[0][1]["content"]
        self.assertNotIn("\n", message)

    def test_imports_are_same_objects_as_escalation_module(self):
        from specfuse.loop import escalation

        self.assertIs(CATEGORY_LABELS, escalation.CATEGORY_LABELS)
        self.assertIs(NEEDS_HUMAN_LABEL, escalation.NEEDS_HUMAN_LABEL)

    def test_unknown_category_rejected_before_posting(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_ESC_TEST_URL", provider="discord")
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        with mock.patch.dict(
            "os.environ",
            {"SPECFUSE_NOTIFY_ESC_TEST_URL": "https://example.invalid/hook"},
        ):
            with self.assertRaises(ValueError):
                notify_new_escalation(
                    "FEAT-2026-0047/T02",
                    repo="acme-widget/acme-widget",
                    issue_number="42",
                    category="not-a-real-category",
                    summary="anything",
                    policy_path=path,
                    poster=poster,
                )
        self.assertEqual(calls, [])

    def test_no_webhook_configured_returns_false_and_no_call(self):
        path = _write_policy(webhook_env='""')
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        result = notify_new_escalation(
            "FEAT-2026-0047/T02",
            repo="acme-widget/acme-widget",
            issue_number="42",
            category="blocked-wu",
            summary="anything",
            policy_path=path,
            poster=poster,
        )
        self.assertFalse(result)
        self.assertEqual(calls, [])

    def test_poster_raising_returns_false_not_raise(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_ESC_TEST_URL", provider="discord")

        def poster(url, payload):
            raise RuntimeError("boom")

        with mock.patch.dict(
            "os.environ",
            {"SPECFUSE_NOTIFY_ESC_TEST_URL": "https://example.invalid/hook"},
        ):
            result = notify_new_escalation(
                "FEAT-2026-0047/T02",
                repo="acme-widget/acme-widget",
                issue_number="42",
                category="blocked-wu",
                summary="anything",
                policy_path=path,
                poster=poster,
            )
        self.assertFalse(result)

    def test_redaction_applied_to_summary(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_ESC_TEST_URL", provider="discord")
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        secret = "password=hunter2secret"
        with mock.patch.dict(
            "os.environ",
            {"SPECFUSE_NOTIFY_ESC_TEST_URL": "https://example.invalid/hook"},
        ):
            notify_new_escalation(
                "FEAT-2026-0047/T02",
                repo="acme-widget/acme-widget",
                issue_number="42",
                category="blocked-wu",
                summary=f"leaked {secret}",
                policy_path=path,
                poster=poster,
            )
        message = calls[0][1]["content"]
        self.assertNotIn("hunter2secret", message)


if __name__ == "__main__":
    unittest.main()
