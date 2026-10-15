# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0203/T04: the `http-status-regression` adapter's one query and
its share-of-requests rule, over a stub transport."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from specfuse.monitor.providers.azure_app_insights import HttpStatusRegressionAdapter

_FIRST_SEEN = datetime(2026, 10, 14, 6, 0, 0, tzinfo=timezone.utc)
_ELAPSED = _FIRST_SEEN + timedelta(hours=1, minutes=1)
_PARTIAL = _FIRST_SEEN + timedelta(minutes=30)


def _agg(after, after_total, before, before_total, version="v2", code="401"):
    return {
        "version": version,
        "code": code,
        "first_seen": _FIRST_SEEN.isoformat(),
        "after": after,
        "after_total": after_total,
        "before": before,
        "before_total": before_total,
    }


class _Transport:
    def __init__(self, rows):
        self._rows = rows
        self.queries: list[str] = []

    def run_query(self, query):
        self.queries.append(query)
        return list(self._rows)


def _run(rows, reference=_ELAPSED, codes=("401",)):
    transport = _Transport(rows)
    codes = None if codes is None else list(codes)
    adapter = HttpStatusRegressionAdapter(
        component="order-api",
        environment={"telemetry": {"provider": "azure_app_insights"}},
        transport=transport,
        deploy_signal={"kind": "app-version"},
        window_after_deploy="1h",
        codes=codes,
        reference_time=reference,
    )
    return list(adapter.fetch_failures()), transport


class RegressionRule(unittest.TestCase):
    def test_share_threshold(self):
        # 2.9x the before-share (2.0% -> 5.8%), 50+ occurrences
        out, _ = _run([_agg(after=58, after_total=1000, before=20, before_total=1000)])
        self.assertEqual(out, [], "2.9x share must not fire")
        # exactly 3.0x (0.333% -> 1.0%) with 10 occurrences
        out, _ = _run([_agg(after=10, after_total=1000, before=1, before_total=300)])
        self.assertEqual(len(out), 1)
        out, _ = _run([_agg(after=9, after_total=100, before=1, before_total=1000)])
        self.assertEqual(out, [], "5x share but only 9 occurrences")
        out, _ = _run([_agg(after=10, after_total=100, before=0, before_total=1000)])
        self.assertEqual(len(out), 1, "zero before-share fires at 10")
        out, _ = _run([_agg(after=10, after_total=100, before=0, before_total=0)])
        self.assertEqual(len(out), 1, "no prior traffic fires at 10")

    def test_traffic_ramp_is_not_a_regression(self):
        out, _ = _run([_agg(after=400, after_total=4000, before=100, before_total=1000)])
        self.assertEqual(out, [])

    def test_partial_window_is_not_evaluated(self):
        rows = [_agg(after=40, after_total=100, before=1, before_total=100)]
        out, _ = _run(rows, reference=_PARTIAL)
        self.assertEqual(out, [])
        out, _ = _run(rows, reference=_ELAPSED)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].failure_signature, "v2:401")

    def test_one_finding_per_code_per_version(self):
        rows = [
            _agg(40, 100, 1, 100, version="v2", code="401"),
            _agg(40, 100, 1, 100, version="v2", code="403"),
            _agg(40, 100, 1, 100, version="v3", code="401"),
        ]
        out, _ = _run(rows, codes=("401", "403"))
        self.assertEqual(
            sorted(a.failure_signature for a in out), ["v2:401", "v2:403", "v3:401"]
        )


class QueryShape(unittest.TestCase):
    def test_query_is_configuration_only(self):
        rows = [_agg(40, 100, 1, 100, version="9.8.7-sentinel")]
        out, transport = _run(rows, codes=("401", "403"))
        self.assertEqual(len(transport.queries), 1)
        query = transport.queries[0]
        for name in ("AppRequests", "AppRoleName", "AppVersion", "ResultCode", "TimeGenerated"):
            self.assertIn(name, query)
        for code in ("401", "403"):
            self.assertIn(code, query)
        self.assertNotIn("9.8.7-sentinel", query)
        self.assertNotIn(_FIRST_SEEN.isoformat(), query)


class DefaultCodes(unittest.TestCase):
    """An omitted `codes` falls back to 403, 405 and 415. 401 is opt-in: a
    401 wave is as often expired client tokens as a broken deployment."""

    def test_omitted_codes_queries_the_default_set(self):
        _, transport = _run([], codes=None)
        query = transport.queries[0]
        self.assertTrue(
            query.rstrip().endswith("| where code in ('403', '405', '415')"), query
        )
        self.assertNotIn("'401'", query)

    def test_default_set_filters_returned_rows(self):
        rows = [
            _agg(40, 100, 1, 100, code="401"),
            _agg(40, 100, 1, 100, code="403"),
        ]
        out, _ = _run(rows, codes=None)
        self.assertEqual([a.failure_signature for a in out], ["v2:403"])

    def test_configured_codes_replace_the_default(self):
        _, transport = _run([], codes=("401",))
        self.assertTrue(transport.queries[0].rstrip().endswith("| where code in ('401')"))


def _diagnosable(**extra):
    row = _agg(after=57, after_total=1200, before=2, before_total=500, code="403")
    row.update(extra)
    return row


_ENDPOINTS = [
    {"name": "POST /api/orders", "after": 9, "before": 1},
    {"name": "GET /api/orders/{id}", "after": 41, "before": 0},
]


class FindingIsDiagnosable(unittest.TestCase):
    """The filed issue says where the code came from, by how much it moved,
    and how to look at it — not only that it moved."""

    def _text(self, **extra):
        out, _ = _run([_diagnosable(**extra)], codes=("403",))
        self.assertEqual(len(out), 1)
        return out[0]

    def test_query_returns_operations_and_samples(self):
        _, transport = _run([], codes=("403",))
        query = transport.queries[0]
        for name in ("Name", "OperationId", "endpoints", "samples"):
            self.assertIn(name, query)

    def test_observed_text_names_top_operations_by_after_count(self):
        text = self._text(endpoints=_ENDPOINTS).observed_text
        first = text.index("GET /api/orders/{id}: 41 after, 0 before")
        second = text.index("POST /api/orders: 9 after, 1 before")
        self.assertLess(first, second)

    def test_dynamic_columns_may_arrive_as_json_text(self):
        import json

        text = self._text(
            endpoints=json.dumps(_ENDPOINTS), samples=json.dumps(["op-a", "op-b"])
        ).observed_text
        self.assertIn("GET /api/orders/{id}: 41 after, 0 before", text)
        self.assertIn("op-a, op-b", text)

    def test_observed_text_states_both_shares_and_first_seen(self):
        text = self._text().observed_text
        self.assertIn("0.40%", text)  # 2 of 500 before
        self.assertIn("4.75%", text)  # 57 of 1200 after
        self.assertIn("57 of 1200", text)
        self.assertIn("2 of 500", text)
        self.assertIn("2026-10-14T06:00:00Z", text)

    def test_observed_text_lists_sample_operation_ids(self):
        text = self._text(samples=["op-1", "op-2", "op-3"]).observed_text
        self.assertIn("op-1, op-2, op-3", text)

    def test_observed_text_carries_an_investigation_query(self):
        text = self._text().observed_text
        self.assertIn("AppRequests", text)
        self.assertIn("AppRoleName == 'order-api'", text)
        self.assertIn("ResultCode == '403'", text)
        self.assertIn("datetime(2026-10-14T05:00:00Z) .. datetime(2026-10-14T07:00:00Z)", text)

    def test_missing_diagnostics_still_render(self):
        text = self._text().observed_text
        self.assertIn("403", text)
        self.assertNotIn("Top operations", text)

    def test_diagnostics_do_not_change_the_fingerprint(self):
        plain = self._text()
        rich = self._text(endpoints=_ENDPOINTS, samples=["op-1"])
        self.assertEqual(plain.failure_signature, rich.failure_signature)
        self.assertEqual(plain.failure_class, rich.failure_class)

    def test_operation_names_are_redacted(self):
        # Assembled at runtime so the repo's own leak scan does not read the
        # fixture as a committed credential.
        name = "GET /cb?" + "tok" + "en=" + "abcdef123456"
        text = self._text(
            endpoints=[{"name": name, "after": 12, "before": 0}]
        ).observed_text
        self.assertNotIn("abcdef123456", text)


if __name__ == "__main__":
    unittest.main()
