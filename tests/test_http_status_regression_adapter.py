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
    adapter = HttpStatusRegressionAdapter(
        component="order-api",
        environment={"telemetry": {"provider": "azure_app_insights"}},
        transport=transport,
        deploy_signal={"kind": "app-version"},
        window_after_deploy="1h",
        codes=list(codes),
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


if __name__ == "__main__":
    unittest.main()
