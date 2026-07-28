# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the App Insights KQL adapters (FEAT-2026-0040/T06)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import dataclass, field
from unittest import mock

from specfuse.monitor.adapters import TelemetryAdapter
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers import azure_app_insights as aai
from specfuse.monitor.providers.azure_app_insights import (
    ErrorLogsAdapter,
    Http5xxAdapter,
    InvariantAdapter,
)

_ENVIRONMENT = {"telemetry": {"provider": "app-insights"}}


@dataclass
class StubTransport:
    """Records every query it was asked to run (criterion 9) and returns a
    canned row set keyed by call order."""

    rows_by_call: list
    queries: list = field(default_factory=list)

    def run_query(self, query):
        self.queries.append(query)
        index = len(self.queries) - 1
        return list(self.rows_by_call[index])


class TestTelemetryAdapters(unittest.TestCase):
    def test_resolve_telemetry_is_called_with_the_component(self):
        transport = StubTransport(rows_by_call=[[]])
        with mock.patch.object(
            aai, "resolve_telemetry", wraps=aai.resolve_telemetry
        ) as spy:
            ErrorLogsAdapter(
                component="checkout-api", environment=_ENVIRONMENT, transport=transport
            )
            spy.assert_called_once_with("checkout-api", _ENVIRONMENT)

        transport = StubTransport(rows_by_call=[[]])
        with mock.patch.object(
            aai, "resolve_telemetry", wraps=aai.resolve_telemetry
        ) as spy:
            Http5xxAdapter(
                component="checkout-api", environment=_ENVIRONMENT, transport=transport
            )
            spy.assert_called_once_with("checkout-api", _ENVIRONMENT)

        transport = StubTransport(rows_by_call=[[]])
        with mock.patch.object(
            aai, "resolve_telemetry", wraps=aai.resolve_telemetry
        ) as spy:
            InvariantAdapter(
                component="checkout-api",
                environment=_ENVIRONMENT,
                transport=transport,
                query="orders | where total < 0",
                fingerprint_by="order_id",
            )
            spy.assert_called_once_with("checkout-api", _ENVIRONMENT)

    def test_adapters_satisfy_telemetry_adapter_protocol(self):
        for adapter in (
            ErrorLogsAdapter(
                component="c", environment=_ENVIRONMENT, transport=StubTransport([[]])
            ),
            Http5xxAdapter(
                component="c", environment=_ENVIRONMENT, transport=StubTransport([[]])
            ),
            InvariantAdapter(
                component="c",
                environment=_ENVIRONMENT,
                transport=StubTransport([[]]),
                query="q",
                fingerprint_by="k",
            ),
        ):
            self.assertTrue(hasattr(adapter, "fetch_failures"))
            self.assertTrue(callable(adapter.fetch_failures))
            self.assertTrue(callable(TelemetryAdapter.fetch_failures))
            artifacts = list(adapter.fetch_failures())
            self.assertEqual(artifacts, [])

    def test_azure_sdk_is_not_importable_at_module_scope(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import specfuse.monitor.providers.azure_app_insights",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_targetless_artifacts_have_no_target_coordinates(self):
        rows = [{"type": "System.Exception", "outerMessage": "boom", "timestamp": "t"}]
        adapter = ErrorLogsAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)
        self.assertIsNone(artifacts[0].target_coordinates)

    def test_from_target_raises_for_all_three_targetless_check_types(self):
        for check_type in ("error-logs", "http-5xx", "invariant"):
            with self.assertRaises(ValueError):
                FailureArtifact.from_target(
                    component="c",
                    check_type=check_type,
                    target={"subscription": "s", "function": "f"},
                    failure_class="x",
                    failure_signature="y",
                    observed_text="z",
                )

    def test_invariant_fingerprint_by_column_drives_signature_and_cardinality(self):
        rows = [
            {"order_id": "ord-1", "total": -5},
            {"order_id": "ord-2", "total": -10},
            {"order_id": "ord-1", "total": -5},
        ]
        adapter = InvariantAdapter(
            component="checkout-api",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
            query="orders | where total < 0",
            fingerprint_by="order_id",
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 3)
        self.assertEqual(artifacts[0].failure_signature, "ord-1")
        self.assertEqual(artifacts[1].failure_signature, "ord-2")
        digests = {fingerprint_artifact(a) for a in artifacts}
        self.assertEqual(len(digests), 2)

    def test_error_logs_signature_stable_across_occurrence_ids(self):
        rows = [
            {
                "type": "System.TimeoutException",
                "outerMessage": "call timed out",
                "timestamp": "2026-01-01T00:00:00Z",
                "operation_Id": "11111111-1111-1111-1111-111111111111",
            },
            {
                "type": "System.TimeoutException",
                "outerMessage": "call timed out",
                "timestamp": "2026-01-02T00:00:00Z",
                "operation_Id": "22222222-2222-2222-2222-222222222222",
            },
        ]
        adapter = ErrorLogsAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(artifacts[0].failure_signature, artifacts[1].failure_signature)

    def test_error_logs_different_exception_types_yield_different_signatures(self):
        rows = [
            {"type": "System.TimeoutException", "outerMessage": "boom"},
            {"type": "System.ArgumentNullException", "outerMessage": "boom"},
        ]
        adapter = ErrorLogsAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertNotEqual(artifacts[0].failure_signature, artifacts[1].failure_signature)

    def test_http_5xx_signature_stable_across_occurrence_ids(self):
        rows = [
            {"name": "GET /orders", "resultCode": "500", "operation_Id": "aaa"},
            {"name": "GET /orders", "resultCode": "500", "operation_Id": "bbb"},
        ]
        adapter = Http5xxAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(artifacts[0].failure_signature, artifacts[1].failure_signature)

    def test_http_5xx_different_routes_yield_different_signatures(self):
        rows = [
            {"name": "GET /orders", "resultCode": "500"},
            {"name": "POST /checkout", "resultCode": "500"},
        ]
        adapter = Http5xxAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertNotEqual(artifacts[0].failure_signature, artifacts[1].failure_signature)

    def test_planted_secret_is_redacted_at_the_boundary(self):
        planted_secret = "ai-fixture-example-token-not-a-real-credential-000111"
        rows = [
            {
                "type": "System.Exception",
                "outerMessage": f"auth failed, token={planted_secret}",
            }
        ]
        adapter = ErrorLogsAdapter(
            component="c",
            environment=_ENVIRONMENT,
            transport=StubTransport(rows_by_call=[rows]),
        )
        artifacts = list(adapter.fetch_failures())
        self.assertEqual(len(artifacts), 1)
        observed_text = artifacts[0].observed_text
        self.assertNotIn(planted_secret, observed_text)
        self.assertIn("<redacted:", observed_text)

    def test_no_query_is_built_from_observed_data(self):
        query_shaped_text = "requests | where cloud_RoleName == 'evil-injected'"
        rows = [{"type": "System.Exception", "outerMessage": query_shaped_text}]
        transport = StubTransport(rows_by_call=[rows, []])
        adapter = ErrorLogsAdapter(
            component="checkout-api", environment=_ENVIRONMENT, transport=transport
        )
        list(adapter.fetch_failures())
        self.assertEqual(len(transport.queries), 1)
        expected_query = aai._error_logs_query("checkout-api")
        self.assertEqual(transport.queries[0], expected_query)
        for recorded_query in transport.queries:
            self.assertNotIn(query_shaped_text, recorded_query)


if __name__ == "__main__":
    unittest.main()
