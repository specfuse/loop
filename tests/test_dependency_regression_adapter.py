# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3577: the `dependency-regression` adapter's one query over
`AppDependencies` and its failure-rate rule, over a stub transport."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.providers.azure_app_insights import DependencyRegressionAdapter

_FIRST_SEEN = datetime(2026, 11, 10, 6, 0, 0, tzinfo=timezone.utc)
_ELAPSED = _FIRST_SEEN + timedelta(hours=1, minutes=1)
_PARTIAL = _FIRST_SEEN + timedelta(minutes=30)
_TARGET = "acme-widget-sql | orders"


def _agg(after, after_total, before, before_total, version="v2", dep_type="SQL",
         target=_TARGET, codes=None, samples=None):
    return {
        "version": version,
        "first_seen": _FIRST_SEEN.isoformat(),
        "dependency_type": dep_type,
        "target": target,
        "after": after,
        "after_total": after_total,
        "before": before,
        "before_total": before_total,
        "codes": codes if codes is not None else [
            {"code": "207", "after": after, "before": before}
        ],
        "samples": samples or [],
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows
        self.queries: list[str] = []

    def run_query(self, query):
        self.queries.append(query)
        return list(self._rows)


def _run(rows, reference=_ELAPSED, dependency_types=None, min_failures=None):
    transport = _Transport(rows)
    adapter = DependencyRegressionAdapter(
        component="order-api",
        environment={"telemetry": {"provider": "azure_app_insights"}},
        transport=transport,
        deploy_signal={"kind": "app-version"},
        window_after_deploy="1h",
        dependency_types=dependency_types,
        min_failures=min_failures,
        reference_time=reference,
    )
    return list(adapter.fetch_failures()), transport


class RegressionRule(unittest.TestCase):
    def test_min_failures_floor(self):
        out, _ = _run([_agg(after=5, after_total=100, before=0, before_total=100)])
        self.assertEqual(len(out), 1, "default floor is 5")
        out, _ = _run([_agg(after=4, after_total=100, before=0, before_total=100)])
        self.assertEqual(out, [], "4 failures is under the default floor")
        out, _ = _run([_agg(after=2, after_total=100, before=0, before_total=100)],
                      min_failures=2)
        self.assertEqual(len(out), 1, "a configured floor replaces the default")

    def test_failure_rate_must_triple(self):
        out, _ = _run([_agg(after=30, after_total=1000, before=10, before_total=1000)])
        self.assertEqual(len(out), 1, "exactly 3x the before-rate fires")
        out, _ = _run([_agg(after=29, after_total=1000, before=10, before_total=1000)])
        self.assertEqual(out, [], "2.9x the before-rate does not")

    def test_new_or_previously_clean_target_fires_on_the_floor_alone(self):
        out, _ = _run([_agg(after=5, after_total=5, before=0, before_total=0)])
        self.assertEqual(len(out), 1, "a target first called after the deployment")
        out, _ = _run([_agg(after=5, after_total=900, before=0, before_total=1000)])
        self.assertEqual(len(out), 1, "a target that never failed before")

    def test_traffic_ramp_is_not_a_regression(self):
        out, _ = _run([_agg(after=40, after_total=4000, before=10, before_total=1000)])
        self.assertEqual(out, [])

    def test_partial_window_is_not_evaluated(self):
        rows = [_agg(after=40, after_total=100, before=0, before_total=100)]
        self.assertEqual(_run(rows, reference=_PARTIAL)[0], [])
        self.assertEqual(len(_run(rows, reference=_ELAPSED)[0]), 1)

    def test_malformed_rows_are_skipped(self):
        row = _agg(after=40, after_total=100, before=0, before_total=100)
        row["first_seen"] = "not-a-time"
        self.assertEqual(_run([row])[0], [])
        row = _agg(after=40, after_total=100, before=0, before_total=100)
        row["after"] = None
        self.assertEqual(_run([row])[0], [])


class Identity(unittest.TestCase):
    def test_signature_is_version_type_target_and_top_code(self):
        codes = [
            {"code": "207", "after": 3, "before": 0},
            {"code": "-2", "after": 9, "before": 0},
            {"code": "4060", "after": 9, "before": 0},
        ]
        out, _ = _run([_agg(21, 100, 0, 100, codes=codes)])
        self.assertEqual(len(out), 1)
        # ties on count break on the code's text, so the choice is stable
        self.assertEqual(out[0].failure_signature, f"v2:SQL:{_TARGET}:-2")
        self.assertEqual(out[0].failure_class, "SQL")
        self.assertEqual(out[0].check_type, "dependency-regression")
        self.assertIsNone(out[0].target_coordinates)

    def test_failure_with_no_result_code_has_a_stable_placeholder(self):
        out, _ = _run([_agg(10, 100, 0, 100, codes=[{"code": "", "after": 10, "before": 0}])])
        self.assertEqual(out[0].failure_signature, f"v2:SQL:{_TARGET}:none")
        out, _ = _run([_agg(10, 100, 0, 100, codes=[])])
        self.assertEqual(out[0].failure_signature, f"v2:SQL:{_TARGET}:none")

    def test_fingerprint_includes_the_deployment(self):
        first, _ = _run([_agg(10, 100, 0, 100)])
        again, _ = _run([_agg(10, 100, 0, 100)])
        later, _ = _run([_agg(10, 100, 0, 100, version="v3")])
        self.assertEqual(fingerprint_artifact(first[0]), fingerprint_artifact(again[0]))
        self.assertNotEqual(fingerprint_artifact(first[0]), fingerprint_artifact(later[0]))

    def test_one_finding_per_type_and_target_per_version(self):
        rows = [
            _agg(10, 100, 0, 100, version="v2", target="acme-widget-sql | orders"),
            _agg(10, 100, 0, 100, version="v2", target="acme-widget-sql | billing"),
            _agg(10, 100, 0, 100, version="v2", dep_type="HTTP", target="acme-widget.example.com"),
            _agg(10, 100, 0, 100, version="v3", target="acme-widget-sql | orders"),
            _agg(10, 100, 0, 100, version="v3", target="acme-widget-sql | orders"),
        ]
        out, _ = _run(rows)
        self.assertEqual(
            sorted(a.failure_signature for a in out),
            [
                "v2:HTTP:acme-widget.example.com:207",
                "v2:SQL:acme-widget-sql | billing:207",
                "v2:SQL:acme-widget-sql | orders:207",
                "v3:SQL:acme-widget-sql | orders:207",
            ],
        )


class DependencyTypes(unittest.TestCase):
    def test_omitted_types_evaluate_every_type(self):
        rows = [_agg(10, 100, 0, 100, dep_type="SQL"),
                _agg(10, 100, 0, 100, dep_type="Azure blob", target="acme-widget-blob")]
        out, transport = _run(rows)
        self.assertEqual(len(out), 2)
        self.assertNotIn("DependencyType in", transport.queries[0])

    def test_configured_types_filter_query_and_rows_case_insensitively(self):
        rows = [_agg(10, 100, 0, 100, dep_type="SQL"),
                _agg(10, 100, 0, 100, dep_type="HTTP", target="acme-widget.example.com")]
        out, transport = _run(rows, dependency_types=["sql"])
        self.assertEqual([a.failure_class for a in out], ["SQL"])
        self.assertIn("DependencyType in~ ('sql')", transport.queries[0])


class QueryShape(unittest.TestCase):
    def test_query_is_configuration_only(self):
        rows = [_agg(10, 100, 0, 100, version="9.8.7-sentinel", target="sentinel-target")]
        out, transport = _run(rows, dependency_types=["SQL"], min_failures=7)
        self.assertEqual(len(transport.queries), 1)
        query = transport.queries[0]
        self.assertTrue(query.startswith("AppDependencies "), query)
        for name in ("AppRoleName == 'order-api'", "AppVersion", "Success", "Target",
                     "DependencyType", "ResultCode", "3600s", ">= 7"):
            self.assertIn(name, query)
        for value in ("9.8.7-sentinel", "sentinel-target", _FIRST_SEEN.isoformat()):
            self.assertNotIn(value, query)

    def test_window_must_parse(self):
        transport = _Transport([])
        adapter = DependencyRegressionAdapter(
            component="order-api",
            environment={"telemetry": {"provider": "azure_app_insights"}},
            transport=transport,
            window_after_deploy="1 hour",
        )
        with self.assertRaises(ValueError):
            list(adapter.fetch_failures())


class FindingIsDiagnosable(unittest.TestCase):
    def _finding(self, **extra):
        codes = [
            {"code": "207", "after": 30, "before": 1},
            {"code": "-2", "after": 12, "before": 0},
        ]
        row = _agg(after=42, after_total=1400, before=1, before_total=1000,
                   codes=codes, samples=["op-aaa", "op-bbb", "op-ccc", "op-ddd"])
        row.update(extra)
        out, _ = _run([row])
        self.assertEqual(len(out), 1)
        return out[0].observed_text

    def test_observed_text_states_rates_codes_samples_and_query(self):
        text = self._finding()
        self.assertIn("SQL calls to acme-widget-sql | orders", text)
        self.assertIn("deployment v2", text)
        self.assertIn("2026-11-10T06:00:00Z", text)
        self.assertIn("0.10% in the 1h before (1 of 1000)", text)
        self.assertIn("3.00% in the 1h after (42 of 1400)", text)
        self.assertIn("3x the before-rate with at least 5 failed calls", text)
        self.assertLess(text.index("  207: 30 after, 1 before"),
                        text.index("  -2: 12 after, 0 before"))
        self.assertIn("op-aaa, op-bbb, op-ccc", text)
        self.assertNotIn("op-ddd", text)
        self.assertIn("AppDependencies", text)
        self.assertIn("Target == 'acme-widget-sql | orders'", text)
        self.assertIn("datetime(2026-11-10T05:00:00Z) .. datetime(2026-11-10T07:00:00Z)", text)

    def test_dynamic_columns_may_arrive_as_json_text(self):
        text = self._finding(
            codes=json.dumps([{"code": "-2", "after": 42, "before": 1}]),
            samples=json.dumps(["op-json"]),
        )
        self.assertIn("  -2: 42 after, 1 before", text)
        self.assertIn("op-json", text)

    def test_no_prior_calls_reads_as_such(self):
        out, _ = _run([_agg(5, 5, 0, 0)])
        self.assertIn("n/a (no calls)", out[0].observed_text)

    def test_secret_shaped_target_text_is_redacted_in_the_body(self):
        target = "postgres://svc:hunter2pass@acme-widget-db/orders"
        out, _ = _run([_agg(10, 100, 0, 100, target=target)])
        self.assertNotIn("hunter2pass", out[0].observed_text)
        # the signature is redacted too, deterministically, so dedupe holds
        self.assertNotIn("hunter2pass", out[0].failure_signature)
        again, _ = _run([_agg(10, 100, 0, 100, target=target)])
        self.assertEqual(out[0].failure_signature, again[0].failure_signature)


if __name__ == "__main__":
    unittest.main()
