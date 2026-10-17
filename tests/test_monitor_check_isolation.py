# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3478: one failing check must not abort the whole `specfuse monitor run`
cycle. Each check is isolated: its error is reported in the summary, the
other checks still run and file, the environment's watermark is not advanced
(so the failed window is retried), and the run exits non-zero."""

from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import specfuse.monitor.cli as cli

_NOW = datetime(2026, 10, 16, 10, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"
_ENVIRONMENT = {
    "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
    "broker": {"provider": "azure_service_bus", "credentials": {"connection_string": "ACME_CONN"}},
}


class HttpResponseError(Exception):
    """Stands in for `azure.core.exceptions.HttpResponseError`: any provider
    SDK exception that is not a `MonitorCliError`."""


def _component(name, checks):
    return {
        "name": name,
        "type": "api",
        "runner": "local",
        "diagnose": "manual",
        "autofix": "off",
        "checks": checks,
    }


def _config():
    # order-worker: error-logs succeeds, http-5xx fails; web-api is processed
    # after the failing check and must still be checked.
    return {
        "environments": {"production": _ENVIRONMENT},
        "components": [
            _component("order-worker", [{"type": "http-5xx"}, {"type": "error-logs"}]),
            _component("web-api", [{"type": "error-logs"}]),
        ],
    }


class _Transport:
    def __init__(self, rows=None, error=None):
        self._rows = rows or []
        self._error = error

    def run_query(self, query):
        if self._error is not None:
            raise self._error
        return list(self._rows)


_ERROR_ROWS = [{"type": "NullReferenceException", "outerMessage": "boom at line 5"}]


def _failing_resolver(module, check_type, binding):
    if check_type == "http-5xx":
        return _Transport(error=HttpResponseError(
            "Failed to resolve table or column expression named 'requests'"
        ))
    return _Transport(rows=_ERROR_ROWS)


def _clean_resolver(module, check_type, binding):
    return _Transport(rows=_ERROR_ROWS if check_type == "error-logs" else [])


class _GhRecorder:
    def __init__(self):
        self.created = 0

    def __call__(self, args, check=True):
        if args[:3] == ["gh", "issue", "list"]:
            return SimpleNamespace(returncode=0, stdout="[]", stderr="")
        if args[:3] == ["gh", "issue", "create"]:
            self.created += 1
            return SimpleNamespace(
                returncode=0, stdout=f"https://github.com/{_REPO}/issues/{self.created}\n", stderr=""
            )
        if args[:3] == ["gh", "label", "create"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected gh call: {args}")


class TestOneFailingCheckIsIsolated(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.watermark_dir = Path(self._tmpdir.name)

    def _run(self, resolver, gh=None):
        out = io.StringIO()
        gh = gh or _GhRecorder()
        code = cli.run_cycle(
            _config(),
            dry_run=False,
            repo=_REPO,
            transport_resolver=resolver,
            gh_runner=gh,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        return code, out.getvalue(), gh

    def test_other_checks_still_run_and_file(self):
        _, output, gh = self._run(_failing_resolver)
        # error-logs on order-worker (same component, after the failure) and
        # on web-api (the next component) both filed.
        self.assertEqual(gh.created, 2)
        self.assertIn("production/order-worker: 1 finding(s)", output)
        self.assertIn("production/web-api: 1 finding(s)", output)
        self.assertIn("total: 2 finding(s)", output)

    def test_error_is_reported_in_the_summary(self):
        _, output, _ = self._run(_failing_resolver)
        self.assertIn(
            "production/order-worker: check http-5xx errored — HttpResponseError: "
            "Failed to resolve table or column expression named 'requests'",
            output,
        )

    def test_run_exits_non_zero(self):
        code, _, _ = self._run(_failing_resolver)
        self.assertEqual(code, 1)

    def test_watermark_is_not_advanced_for_the_environment(self):
        self._run(_failing_resolver)
        self.assertFalse((self.watermark_dir / "production.json").exists())

    def test_setup_error_inside_one_check_is_isolated_too(self):
        def resolver(module, check_type, binding):
            if check_type == "http-5xx":
                raise cli.MonitorCliError("credential env var 'ACME_API_KEY' is not set")
            return _Transport(rows=_ERROR_ROWS)

        code, output, gh = self._run(resolver)
        self.assertEqual(code, 1)
        self.assertEqual(gh.created, 2)
        self.assertIn(
            "production/order-worker: check http-5xx errored — MonitorCliError: "
            "credential env var 'ACME_API_KEY' is not set",
            output,
        )

    def test_clean_run_exits_zero_and_advances_the_watermark(self):
        code, output, gh = self._run(_clean_resolver)
        self.assertEqual(code, 0)
        self.assertEqual(gh.created, 2)
        self.assertNotIn("errored", output)
        self.assertTrue((self.watermark_dir / "production.json").exists())

    def test_run_level_errors_stay_fatal(self):
        with self.assertRaises(cli.MonitorCliError):
            cli.run_cycle(
                _config(),
                env_filter="staging",
                dry_run=True,
                transport_resolver=_clean_resolver,
                now=_NOW,
                watermark_dir=self.watermark_dir,
                out=io.StringIO(),
            )


if __name__ == "__main__":
    unittest.main()
