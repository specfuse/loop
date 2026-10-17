# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0204 gate 1 oracle: per-check diagnostic context (PLAN.md
"Diagnostic context"). Each class is skipped with its owning unit; the owner
removes the skip and makes it pass."""

from __future__ import annotations

import io
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli
import specfuse.monitor.providers.azure_app_insights as aai
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.issues import _render_body
from tests.test_app_insights_query_schema_check import schema_violations


_NOW = datetime(2026, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"
_CANCEL = "System.Threading.Tasks.TaskCanceledException"
_ROWS = [
    {
        "timestamp": "2026-10-17T00:10:00Z", "operation_Id": "op-1", "type": _CANCEL,
        "outerMessage": "A task was canceled.", "instance": "web-api-0",
        "frameMethod": "Acme.Orders.OrderService.Handle", "frameAssembly": "Acme.Orders",
        "requestName": "GET /orders", "requestResult": "200",
        "loggerCategory": "Acme.Orders.OrderService",
        "loggerTemplate": "Order {OrderId} failed", "clientAbort": True,
    },
    {
        "timestamp": "2026-10-17T00:40:00Z", "operation_Id": "op-2", "type": _CANCEL,
        "outerMessage": "A task was canceled.", "instance": "web-api-1",
        "frameMethod": "Acme.Orders.OrderService.Handle", "frameAssembly": "Acme.Orders",
        "requestName": "GET /orders", "requestResult": "200",
        "loggerCategory": "Acme.Orders.OrderService",
        "loggerTemplate": "Order {OrderId} failed", "clientAbort": True,
    },
]


def _config():
    return {
        "environments": {
            "production": {
                "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
            },
        },
        "components": [{
            "name": "web-api", "type": "api", "runner": "local",
            "diagnose": "manual", "autofix": "off",
            "checks": [{"type": "error-logs"}],
        }],
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows
        self.queries = []

    def run_query(self, query):
        self.queries.append(query)
        return list(self._rows)


def _drive(rows):
    calls = []

    def gh(args, check=True):
        calls.append(list(args))
        if args[:3] == ["gh", "issue", "create"]:
            return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/900\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    transport = _Transport(rows)
    with tempfile.TemporaryDirectory() as tmp:
        cli.run_cycle(
            _config(), dry_run=False, repo=_REPO,
            transport_resolver=lambda module, check_type, binding: transport,
            gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=io.StringIO(),
        )
    creates = [c for c in calls if c[:3] == ["gh", "issue", "create"]]
    return calls, creates, transport


def _field(create, flag):
    return create[create.index(flag) + 1]


class EveryFinding(unittest.TestCase):
    def test_readable_title_labels_and_run_summary(self):
        calls, creates, _ = _drive(_ROWS)
        self.assertEqual(len(creates), 1, calls)
        create = creates[0]
        title, body = _field(create, "--title"), _field(create, "--body")
        self.assertNotIn("[monitor:", title)
        self.assertEqual(title, f"web-api: {_CANCEL} in Acme.Orders.OrderService")
        labels = [create[i + 1] for i, arg in enumerate(create) if arg == "--label"]
        self.assertIn("component:web-api", labels)
        self.assertIn("check:error-logs", labels)
        self.assertIn("**Seen this run:** 2, first 2026-10-17T00:10:00Z, last 2026-10-17T00:40:00Z (UTC)", body)
        self.assertIn("**Instances:** web-api-0, web-api-1", body)

    def test_each_label_is_created_once_before_first_use(self):
        calls, _, _ = _drive(_ROWS)
        label_calls = [c for c in calls if c[:3] == ["gh", "label", "create"]]
        self.assertEqual(
            sorted(c[3] for c in label_calls), ["check:error-logs", "component:web-api"]
        )
        for c in label_calls:
            self.assertIn("--force", c)
            self.assertLess(calls.index(c), calls.index(next(x for x in calls if x[:3] == ["gh", "issue", "create"])))

    def test_fingerprint_unchanged_by_context(self):
        base = FailureArtifact(
            component="web-api", check_type="error-logs", failure_class="X",
            failure_signature="X:m", observed_text="m",
        )
        other = replace(base, context={"Where": "A.B"}, observed_at="2026-10-17T00:00:00Z", instance="i-0")
        self.assertEqual(fingerprint_artifact(base), fingerprint_artifact(other))

    def test_secret_in_context_value_is_redacted_in_body(self):
        artifact = FailureArtifact(
            component="web-api", check_type="error-logs", failure_class="X",
            failure_signature="X:m", observed_text="m",
            context={"Logger": "password=hunter2hunter2 in template"},
        )
        body = _render_body("f" * 64, artifact, occurrences=1, last_seen=1.0)
        self.assertNotIn("hunter2hunter2", body)
        self.assertIn("<redacted:", body)

    def test_multiline_context_is_fenced(self):
        artifact = FailureArtifact(
            component="web-api", check_type="error-logs", failure_class="X",
            failure_signature="X:m", observed_text="m", context={"Reproduce": "a\nb"},
        )
        body = _render_body("f" * 64, artifact, occurrences=1, last_seen=1.0)
        self.assertIn("**Reproduce:**\n```\na\nb\n```", body)


class ErrorLogsContext(unittest.TestCase):
    def test_sections_present(self):
        _, creates, transport = _drive(_ROWS)
        body = _field(creates[0], "--body")
        for needle in (
            "**Where:** Acme.Orders.OrderService.Handle (Acme.Orders)",
            "**Request:** GET /orders returned 200",
            "**Logger:** Acme.Orders.OrderService (template: Order {OrderId} failed)",
            "**Likely client abort:**",
            "**Samples:** op-1, op-2",
            "**Reproduce:**",
            "| where OperationId in ('op-1', 'op-2')",
        ):
            self.assertIn(needle, body)
        self.assertEqual(len(transport.queries), 1)

    def test_reproduce_is_text_only_and_ids_are_cleaned(self):
        rows = [dict(_ROWS[0], operation_Id="op-1') | take 5 //")]
        _, creates, transport = _drive(rows)
        body = _field(creates[0], "--body")
        self.assertIn("OperationId in ('op-1take5')", body)
        self.assertEqual(len(transport.queries), 1)

    def test_query_has_no_schema_violations(self):
        self.assertEqual(schema_violations(aai._error_logs_query("web-api")), [])


_ROW_5XX = {
    "timestamp": "2026-10-17T00:20:00Z", "operation_Id": "op-9", "name": "POST /tokens",
    "resultCode": "500", "durationMs": 1234.0, "instance": "web-api-0",
    "exceptionType": "Acme.Auth.ManagementApiException",
    "exceptionMessage": "Management API call failed.",
    "frameMethod": "Acme.Auth.TokenService.Exchange", "frameAssembly": "Acme.Auth",
    "dependencyTarget": "acme.example.com", "dependencyType": "Http",
    "dependencyResult": "401", "dependencyDurationMs": 210.0, "dependencyFailed": True,
}


def _config_5xx():
    config = _config()
    config["components"][0]["checks"] = [{"type": "http-5xx"}]
    return config


def _drive_5xx(rows):
    calls = []

    def gh(args, check=True):
        calls.append(list(args))
        if args[:3] == ["gh", "issue", "create"]:
            return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/901\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    transport = _Transport(rows)
    with tempfile.TemporaryDirectory() as tmp:
        cli.run_cycle(
            _config_5xx(), dry_run=False, repo=_REPO,
            transport_resolver=lambda module, check_type, binding: transport,
            gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=io.StringIO(),
        )
    creates = [c for c in calls if c[:3] == ["gh", "issue", "create"]]
    return creates, transport


class Http5xxContext(unittest.TestCase):
    def test_sections_present(self):
        creates, transport = _drive_5xx([_ROW_5XX])
        self.assertEqual(len(creates), 1)
        body = _field(creates[0], "--body")
        for needle in (
            "**Exception:** Acme.Auth.ManagementApiException: Management API call failed.",
            "**Where:** Acme.Auth.TokenService.Exchange (Acme.Auth)",
            "**Dependency:** acme.example.com, type Http, returned 401, 210 ms",
            "**Duration:** 1234 ms",
            "**Samples:** op-9",
            "**Reproduce:**",
            "| where OperationId in ('op-9')",
        ):
            self.assertIn(needle, body)
        self.assertEqual(len(transport.queries), 1)

    def test_no_exception_and_no_dependency_still_files_without_those_sections(self):
        row = {
            "timestamp": "2026-10-17T00:20:00Z", "operation_Id": "op-9",
            "name": "POST /tokens", "resultCode": "500", "durationMs": 50.0,
        }
        creates, _ = _drive_5xx([row])
        self.assertEqual(len(creates), 1)
        body = _field(creates[0], "--body")
        for absent in ("**Exception:**", "**Where:**", "**Dependency:**"):
            self.assertNotIn(absent, body)
        self.assertIn("**Duration:** 50 ms", body)

    def test_query_has_no_schema_violations(self):
        self.assertEqual(schema_violations(aai._http_5xx_query("web-api")), [])

    def test_query_reduces_joined_tables_to_one_row_per_operation(self):
        query = aai._http_5xx_query("web-api")
        self.assertEqual(query.count("by OperationId "), 2)
        self.assertIn("arg_max(depRank", query)


def _drive_dlq_messages(messages):
    calls = []

    def gh(args, check=True):
        calls.append(list(args))
        if args[:3] == ["gh", "issue", "create"]:
            return SimpleNamespace(returncode=0, stdout=f"https://github.com/{_REPO}/issues/902\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")

    class Transport:
        def peek_dead_letter_messages(self, *, subscription, max_message_count):
            return list(messages)

    config = _config()
    config["environments"]["production"]["broker"] = {
        "provider": "azure_service_bus", "credentials": {"connection_string": "ACME_CONN"},
        "fully_qualified_namespace": "acme.servicebus.example.com", "topic_name": "orders-topic",
    }
    config["components"][0]["checks"] = [{
        "type": "dlq", "targets": [{"subscription": "orders", "function": "OrderHandler"}],
    }]
    with tempfile.TemporaryDirectory() as tmp:
        cli.run_cycle(
            config, dry_run=False, repo=_REPO,
            transport_resolver=lambda module, check_type, binding: Transport(),
            gh_runner=gh, now=_NOW, watermark_dir=Path(tmp), out=io.StringIO(),
        )
    return [c for c in calls if c[:3] == ["gh", "issue", "create"]]


class DlqContext(unittest.TestCase):
    def test_sections_present(self):
        message = SimpleNamespace(
            message_id="m-1016", sequence_number=77, subject="RestaurantUpdated",
            enqueued_time_utc=datetime(2026, 10, 16, 23, 0, 0, tzinfo=timezone.utc),
            delivery_count=10, dead_letter_reason="", dead_letter_error_description="",
            application_properties={
                b"Exception.Message": b"Sequence contains no elements",
                b"Exception.StackTrace": b"\n".join(b"   at Acme.Frame%d()" % n for n in range(30)),
            },
            body=b'{"restaurantId": "SECRET-R", "companyId": "SECRET-C", "after": {"x": 1}}',
        )
        creates = _drive_dlq_messages([message])
        self.assertEqual(len(creates), 1)
        title, body = _field(creates[0], "--title"), _field(creates[0], "--body")
        self.assertEqual(title, "web-api: Unknown in OrderHandler")
        for needle in (
            "**Message:**", "id: m-1016", "sequence number: 77", "subject: RestaurantUpdated",
            "enqueued (UTC): 2026-10-16T23:00:00Z", "delivery count: 10",
            "Sequence contains no elements", "at Acme.Frame0()",
            "**Body shape:** top-level keys: restaurantId, companyId, after",
            "**Peek it:**", "namespace: acme.servicebus.example.com", "topic: orders-topic",
            "subscription: orders", "sub-queue: $DeadLetterQueue",
        ):
            self.assertIn(needle, body)
        self.assertNotIn("at Acme.Frame10()", body)
        self.assertNotIn("**Dead-letter:**", body)
        for value in ("SECRET-R", "SECRET-C"):
            self.assertNotIn(value, body)

    def test_bare_message_still_files(self):
        message = SimpleNamespace(
            message_id="m-1", sequence_number=1, dead_letter_reason="MaxDeliveryCountExceeded",
            dead_letter_error_description="System.Exception: boom", body=b"not json",
        )
        creates = _drive_dlq_messages([message])
        self.assertEqual(len(creates), 1)
        body = _field(creates[0], "--body")
        for absent in ("**Exception:**", "**Body shape:**"):
            self.assertNotIn(absent, body)
        self.assertIn("**Dead-letter:**", body)
        self.assertIn("**Peek it:**", body)


@unittest.skip("owned by FEAT-2026-0204/T08")
class HeartbeatContext(unittest.TestCase):
    SECTIONS = ("Schedule", "Last execution", "Earliest heartbeat", "Telemetry in silent gap")

    def test_sections_present(self):
        self.fail("T08")


@unittest.skip("owned by FEAT-2026-0204/T08")
class QueueStalledContext(unittest.TestCase):
    SECTIONS = ("Oldest active message age", "Last completed message", "Depth")

    def test_sections_present(self):
        self.fail("T08")


if __name__ == "__main__":
    unittest.main()
