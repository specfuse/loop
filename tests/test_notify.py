#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for specfuse.loop.notify."""

from __future__ import annotations

import logging
import tempfile
import unittest
from datetime import time
from unittest import mock

from specfuse.loop.notify import (
    discord_payload,
    post_notification,
    resolve_webhook_url,
    slack_payload,
    teams_payload,
)

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
  quiet_hours: {quiet_hours}
  sla_hours: 24
"""


def _write_policy(webhook_env: str = '""', provider: str = "none",
                   quiet_hours: str = '""') -> str:
    text = _BASE_POLICY.format(
        webhook_env=webhook_env, provider=provider, quiet_hours=quiet_hours
    )
    fd = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    fd.write(text)
    fd.close()
    return fd.name


class TestResolveWebhookUrl(unittest.TestCase):
    def test_missing_policy_file_is_none(self):
        self.assertIsNone(resolve_webhook_url("/nonexistent/agent-policy.yml"))

    def test_empty_webhook_env_key_is_none(self):
        path = _write_policy(webhook_env='""')
        self.assertIsNone(resolve_webhook_url(path))

    def test_absent_env_var_is_none(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_UNSET")
        with mock.patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("SPECFUSE_NOTIFY_TEST_UNSET", None)
            self.assertIsNone(resolve_webhook_url(path))

    def test_set_env_var_resolves_to_its_value(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL")
        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            self.assertEqual(
                resolve_webhook_url(path), "https://example.invalid/hook"
            )


class TestPayloadAdapters(unittest.TestCase):
    def test_discord_payload_shape(self):
        self.assertEqual(discord_payload("hello"), {"content": "hello"})

    def test_slack_payload_shape(self):
        self.assertEqual(slack_payload("hello"), {"text": "hello"})

    def test_teams_payload_shape(self):
        payload = teams_payload("hello")
        self.assertEqual(payload["@type"], "MessageCard")
        self.assertEqual(payload["text"], "hello")

    def test_unknown_provider_yields_no_payload_and_no_post(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL", provider="pagerduty")
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification("hi", policy_path=path, poster=poster)
        self.assertFalse(result)
        self.assertEqual(calls, [])

    def test_redaction_applied_before_entering_payload(self):
        secret = "password=hunter2secret"
        for builder in (discord_payload, slack_payload, teams_payload):
            payload = builder(f"leaked {secret}")
            self.assertNotIn("hunter2secret", str(payload))


class TestPostNotification(unittest.TestCase):
    def test_no_webhook_configured_is_noop(self):
        path = _write_policy(webhook_env='""')
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        result = post_notification("hello", policy_path=path, poster=poster)
        self.assertFalse(result)
        self.assertEqual(calls, [])

    def test_successful_post_returns_true(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL", provider="discord")

        def poster(url, payload):
            return 204

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification("hello", policy_path=path, poster=poster)
        self.assertTrue(result)

    def test_poster_raising_is_never_fatal(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL", provider="discord")

        def poster(url, payload):
            raise RuntimeError("boom")

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification("hello", policy_path=path, poster=poster)
        self.assertFalse(result)

    def test_poster_timeout_is_never_fatal(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL", provider="discord")

        def poster(url, payload):
            raise TimeoutError("timed out")

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification("hello", policy_path=path, poster=poster)
        self.assertFalse(result)

    def test_poster_non_2xx_status_is_never_fatal(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL", provider="discord")

        def poster(url, payload):
            return 500

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification("hello", policy_path=path, poster=poster)
        self.assertFalse(result)

    def test_quiet_hours_suppress_post_and_nothing_else(self):
        path = _write_policy(
            webhook_env="SPECFUSE_NOTIFY_TEST_URL",
            provider="discord",
            quiet_hours="22:00-06:00",
        )
        calls = []

        def poster(url, payload):
            calls.append((url, payload))
            return 200

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification(
                "hello", policy_path=path, poster=poster, now=time(23, 0)
            )
        self.assertFalse(result)
        self.assertEqual(calls, [])

    def test_outside_quiet_hours_posts_normally(self):
        path = _write_policy(
            webhook_env="SPECFUSE_NOTIFY_TEST_URL",
            provider="discord",
            quiet_hours="22:00-06:00",
        )

        def poster(url, payload):
            return 200

        with mock.patch.dict(
            "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": "https://example.invalid/hook"}
        ):
            result = post_notification(
                "hello", policy_path=path, poster=poster, now=time(12, 0)
            )
        self.assertTrue(result)

    def test_url_never_leaves_process_on_poster_exception(self):
        path = _write_policy(webhook_env="SPECFUSE_NOTIFY_TEST_URL", provider="discord")
        secret_url = "https://example.invalid/hook/super-secret-path"

        def poster(url, payload):
            raise RuntimeError("poster exploded")

        logger = logging.getLogger("specfuse.loop.notify")
        buf = []

        class _Handler(logging.Handler):
            def emit(self, record):
                buf.append(self.format(record))

        handler = _Handler()
        logger.addHandler(handler)
        try:
            with mock.patch.dict(
                "os.environ", {"SPECFUSE_NOTIFY_TEST_URL": secret_url}
            ):
                try:
                    post_notification("hello", policy_path=path, poster=poster)
                except Exception as exc:  # pragma: no cover - must not happen
                    self.assertNotIn(secret_url, str(exc))
                    raise
        finally:
            logger.removeHandler(handler)

        self.assertTrue(all(secret_url not in line for line in buf))

    def test_no_network_call_under_default_no_op_path(self):
        path = _write_policy(webhook_env='""')
        with mock.patch("urllib.request.urlopen") as urlopen:
            result = post_notification("hello", policy_path=path)
        self.assertFalse(result)
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
