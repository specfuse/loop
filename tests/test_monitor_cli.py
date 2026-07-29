# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for `specfuse.monitor.cli` — the `specfuse-monitor run` CLI
(FEAT-2026-0040/T10)."""

from __future__ import annotations

import io
import re
import subprocess
import sys
import tempfile
import types
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import specfuse.monitor.cli as cli
from specfuse.monitor.adapters import resolve_telemetry
from specfuse.monitor.fingerprint import fingerprint_artifact

_NOW = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)
_REPO = "acme-widget/repo"

_ENVIRONMENT = {
    "telemetry": {"provider": "azure_app_insights", "credentials": {"api_key": "ACME_API_KEY"}},
    "broker": {"provider": "azure_service_bus", "credentials": {"connection_string": "ACME_CONN"}},
}


def _component(name, checks):
    return {
        "name": name,
        "type": "queue-consumer",
        "runner": "local",
        "diagnose": "manual",
        "autofix": "off",
        "checks": checks,
    }


def _config(checks, *, environment=None, component_name="order-worker"):
    return {
        "environments": {"production": environment or _ENVIRONMENT},
        "components": [_component(component_name, checks)],
    }


# ---------------------------------------------------------------------------
# stub transports satisfying the real providers' Protocols (T05/T06/T07/T08)
# ---------------------------------------------------------------------------


@dataclass
class _StubMessage:
    dead_letter_reason: str = "MaxDeliveryCountExceeded"
    dead_letter_error_description: str = "boom"
    message_id: str = "m1"
    sequence_number: int = 1


class _StubDlqTransport:
    def __init__(self, messages):
        self._messages = messages

    def peek_dead_letter_messages(self, *, subscription, max_message_count):
        return list(self._messages.get(subscription, []))


class _StubQueueStalledTransport:
    def __init__(self, active_counts=None, oldest=None):
        self._active = active_counts or {}
        self._oldest = oldest or {}

    def get_active_message_count(self, *, subscription):
        return self._active.get(subscription, 0)

    def get_oldest_message_enqueued_time(self, *, subscription):
        return self._oldest.get(subscription)


class _StubAppInsightsTransport:
    def __init__(self, rows):
        self._rows = rows

    def run_query(self, query):
        return list(self._rows)


_ROWS_BY_CHECK_TYPE = {
    "error-logs": [{"type": "NullReferenceException", "outerMessage": "boom at line 5"}],
    "http-5xx": [{"name": "/orders", "resultCode": "503"}],
    "invariant": [{"order_id": "abc-123"}],
    "heartbeat": [],
}


def _stub_resolver(module, check_type, binding):
    if check_type == "dlq":
        return _StubDlqTransport({
            "orders-sub": [_StubMessage()],
            "inventory-sub": [_StubMessage(dead_letter_error_description="a different failure")],
        })
    if check_type == "queue-stalled":
        return _StubQueueStalledTransport(
            active_counts={"stalled-sub": 5},
            oldest={"stalled-sub": _NOW - timedelta(hours=1)},
        )
    return _StubAppInsightsTransport(_ROWS_BY_CHECK_TYPE[check_type])


_ALL_SIX_CHECKS = [
    {"type": "dlq", "targets": [
        {"subscription": "orders-sub", "function": "ProcessOrder"},
        {"subscription": "inventory-sub", "function": "SyncInventory"},
    ]},
    {"type": "queue-stalled", "targets": [
        {"subscription": "stalled-sub", "function": "ProcessOrder", "stall_after": "15m"},
        {"subscription": "quiet-sub", "function": "ProcessOrder"},
    ]},
    {"type": "error-logs"},
    {"type": "http-5xx"},
    {"type": "invariant", "query": "select 1", "fingerprint_by": "order_id"},
    {"type": "heartbeat", "targets": [
        {"name": "nightly", "cron": "0 2 * * *", "dialect": "standard-5", "timezone": "Etc/UTC"},
    ]},
]


def _register_fake_module(test_case, name, **attrs):
    module = types.ModuleType(f"specfuse.monitor.providers.{name}")
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module.__name__] = module
    test_case.addCleanup(sys.modules.pop, module.__name__, None)
    return module


class _CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.watermark_dir = Path(self._tmpdir.name)


# ---------------------------------------------------------------------------
# criteria 1 & 3 — enumeration follows the 0069 axis
# ---------------------------------------------------------------------------


class TestRunCycle(_CliTestCase):
    def test_two_targets_on_one_component_yield_two_findings(self):
        check = {"type": "dlq", "targets": [
            {"subscription": "orders-sub", "function": "ProcessOrder"},
            {"subscription": "inventory-sub", "function": "SyncInventory"},
        ]}
        artifacts, skipped = cli._process_check(
            check=check,
            component=_component("order-worker", [check]),
            environment=_ENVIRONMENT,
            transport_resolver=_stub_resolver,
            now=_NOW,
        )
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(skipped, [])
        fingerprints = {fingerprint_artifact(a) for a in artifacts}
        self.assertEqual(len(fingerprints), 2)

    def test_targetless_check_enumerates_the_component(self):
        check = {"type": "invariant", "query": "select 1", "fingerprint_by": "order_id"}
        artifacts, _ = cli._process_check(
            check=check,
            component=_component("order-worker", [check]),
            environment=_ENVIRONMENT,
            transport_resolver=_stub_resolver,
            now=_NOW,
        )
        self.assertEqual(len(artifacts), 1)
        self.assertIsNone(artifacts[0].target_coordinates)


# ---------------------------------------------------------------------------
# criterion 4 — all six check types dispatch to a real, shipped adapter
# ---------------------------------------------------------------------------


class TestAllCheckTypesDispatch(_CliTestCase):
    def test_all_six_check_types_reach_their_adapter(self):
        config = _config(_ALL_SIX_CHECKS)
        out = io.StringIO()
        code = cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=_stub_resolver,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        self.assertEqual(code, 0)
        output = out.getvalue()
        for check_type in ("dlq", "queue-stalled", "error-logs", "http-5xx", "invariant", "heartbeat"):
            self.assertIn(f"check_type={check_type}", output)

    def test_check_type_with_no_registered_adapter_is_a_clear_error(self):
        class DlqAdapter:
            def __init__(self, *, component, transport, targets):
                pass

            def fetch_failures(self):
                return []

        _register_fake_module(self, "fixture_partial_broker", DlqAdapter=DlqAdapter)
        environment = {
            "telemetry": _ENVIRONMENT["telemetry"],
            "broker": {"provider": "fixture_partial_broker"},
        }
        check = {"type": "queue-stalled", "targets": [{"subscription": "s", "function": "f", "stall_after": "5m"}]}
        with self.assertRaises(cli.MonitorCliError) as ctx:
            cli._process_check(
                check=check,
                component=_component("order-worker", [check]),
                environment=environment,
                transport_resolver=_stub_resolver,
                now=_NOW,
            )
        self.assertIn("queue-stalled", str(ctx.exception))


# ---------------------------------------------------------------------------
# criterion 5 — provider dispatch is registry-driven and opaque
# ---------------------------------------------------------------------------


class TestProviderRegistry(_CliTestCase):
    def test_unknown_provider_names_the_string_and_registered_keys(self):
        environment = {
            "telemetry": {"provider": "totally-unknown-vendor"},
            "broker": _ENVIRONMENT["broker"],
        }
        check = {"type": "error-logs"}
        with self.assertRaises(cli.MonitorCliError) as ctx:
            cli._process_check(
                check=check,
                component=_component("order-worker", [check]),
                environment=environment,
                transport_resolver=_stub_resolver,
                now=_NOW,
            )
        message = str(ctx.exception)
        self.assertIn("totally-unknown-vendor", message)
        self.assertIn("azure_app_insights", message)
        self.assertIn("azure_service_bus", message)

    def test_no_provider_identifier_reaches_the_core(self):
        pattern = re.compile(r"azure|appinsights|servicebus|kusto", re.IGNORECASE)
        for path in (
            "specfuse/monitor/cli.py",
            "specfuse/monitor/artifact.py",
            "specfuse/monitor/adapters.py",
            "specfuse/monitor/fingerprint.py",
            "specfuse/monitor/redaction.py",
            "specfuse/monitor/schedule.py",
            "specfuse/monitor/issues.py",
        ):
            source = Path(path).read_text(encoding="utf-8")
            self.assertIsNone(
                pattern.search(source), f"{path} contains a provider identifier"
            )


# ---------------------------------------------------------------------------
# criterion 6 — the seam is used, not bypassed
# ---------------------------------------------------------------------------


class TestTelemetrySeam(_CliTestCase):
    def test_resolve_telemetry_called_with_the_component_name(self):
        config = _config([
            {"type": "error-logs"},
            {"type": "http-5xx"},
            {"type": "invariant", "query": "select 1", "fingerprint_by": "order_id"},
            {"type": "heartbeat", "targets": [
                {"name": "nightly", "cron": "0 2 * * *", "dialect": "standard-5", "timezone": "Etc/UTC"},
            ]},
        ])
        out = io.StringIO()
        with mock.patch("specfuse.monitor.cli.resolve_telemetry", wraps=resolve_telemetry) as spy:
            cli.run_cycle(
                config,
                dry_run=True,
                transport_resolver=_stub_resolver,
                now=_NOW,
                watermark_dir=self.watermark_dir,
                out=out,
            )
        self.assertEqual(spy.call_count, 4)
        for call in spy.call_args_list:
            self.assertEqual(call.args[0], "order-worker")

    def test_source_never_reaches_into_telemetry_directly(self):
        source = Path("specfuse/monitor/cli.py").read_text(encoding="utf-8")
        pattern = re.compile(r'environment\["telemetry"\]|environment\.get\("telemetry"\)')
        self.assertIsNone(pattern.search(source))


# ---------------------------------------------------------------------------
# criterion 7 — selectors select
# ---------------------------------------------------------------------------


class TestSelectors(_CliTestCase):
    def test_unknown_component_names_available_values(self):
        config = _config([{"type": "error-logs"}])
        with self.assertRaises(cli.MonitorCliError) as ctx:
            cli.run_cycle(
                config,
                component_filter="does-not-exist",
                dry_run=True,
                transport_resolver=_stub_resolver,
                now=_NOW,
                watermark_dir=self.watermark_dir,
            )
        message = str(ctx.exception)
        self.assertIn("does-not-exist", message)
        self.assertIn("order-worker", message)

    def test_unknown_env_names_available_values(self):
        config = _config([{"type": "error-logs"}])
        with self.assertRaises(cli.MonitorCliError) as ctx:
            cli.run_cycle(
                config,
                env_filter="nope",
                dry_run=True,
                transport_resolver=_stub_resolver,
                now=_NOW,
                watermark_dir=self.watermark_dir,
            )
        message = str(ctx.exception)
        self.assertIn("nope", message)
        self.assertIn("production", message)

    def test_component_selector_restricts_the_run(self):
        config = {
            "environments": {"production": _ENVIRONMENT},
            "components": [
                _component("order-worker", [{"type": "error-logs"}]),
                _component("web-api", [{"type": "error-logs"}]),
            ],
        }
        out = io.StringIO()
        cli.run_cycle(
            config,
            component_filter="web-api",
            dry_run=True,
            transport_resolver=_stub_resolver,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        output = out.getvalue()
        self.assertIn("web-api", output)
        self.assertNotIn("order-worker", output)


# ---------------------------------------------------------------------------
# criterion 8 — dry-run touches nothing, proven by an empty recorded call set
# ---------------------------------------------------------------------------


class TestDryRunTouchesNothing(_CliTestCase):
    def test_dry_run_records_zero_gh_calls_and_leaves_the_watermark_untouched(self):
        config = _config([{"type": "dlq", "targets": [{"subscription": "orders-sub", "function": "ProcessOrder"}]}])
        watermark_path = self.watermark_dir / "production.json"
        watermark_path.parent.mkdir(parents=True, exist_ok=True)
        original_bytes = b'{"since": "2026-07-28T00:00:00+00:00"}'
        watermark_path.write_bytes(original_bytes)

        def _must_not_be_called(args, check=True):
            raise AssertionError(f"gh must not be invoked under --dry-run, got {args}")

        recorder = cli._CallRecorder(_must_not_be_called)
        out = io.StringIO()
        cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=_stub_resolver,
            gh_runner=recorder,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        self.assertEqual(recorder.calls, [])
        self.assertEqual(watermark_path.read_bytes(), original_bytes)


# ---------------------------------------------------------------------------
# criterion 9 — watermarks degrade, never fail
# ---------------------------------------------------------------------------


class TestWatermarkFallback(_CliTestCase):
    def test_missing_watermark_falls_back_to_the_lookback_window(self):
        since, reason = cli._read_watermark(
            self.watermark_dir / "missing.json", lookback=cli.DEFAULT_LOOKBACK, now=_NOW
        )
        self.assertEqual(reason, "missing")
        self.assertEqual(since, _NOW - cli.DEFAULT_LOOKBACK)

    def test_corrupt_watermark_falls_back_to_the_lookback_window(self):
        path = self.watermark_dir / "corrupt.json"
        path.write_text("{not valid json", encoding="utf-8")
        since, reason = cli._read_watermark(path, lookback=cli.DEFAULT_LOOKBACK, now=_NOW)
        self.assertEqual(reason, "corrupt")
        self.assertEqual(since, _NOW - cli.DEFAULT_LOOKBACK)

    def test_unreadable_watermark_falls_back_to_the_lookback_window(self):
        path = self.watermark_dir / "unreadable.json"
        path.write_text('{"since": "2026-01-01T00:00:00+00:00"}', encoding="utf-8")
        with mock.patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            since, reason = cli._read_watermark(path, lookback=cli.DEFAULT_LOOKBACK, now=_NOW)
        self.assertEqual(reason, "unreadable")
        self.assertEqual(since, _NOW - cli.DEFAULT_LOOKBACK)

    def test_run_completes_and_names_the_fallback_in_the_summary(self):
        config = _config([{"type": "error-logs"}])
        out = io.StringIO()
        code = cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=_stub_resolver,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        self.assertEqual(code, 0)
        self.assertIn("watermark fallback (missing)", out.getvalue())


# ---------------------------------------------------------------------------
# criterion 10 — the run summary is the operator's evidence
# ---------------------------------------------------------------------------


class TestRunSummary(_CliTestCase):
    def test_created_count_and_skip_reasons_reach_the_summary(self):
        config = _config([
            {"type": "dlq", "targets": [{"subscription": "orders-sub", "function": "ProcessOrder"}]},
            {"type": "queue-stalled", "targets": [
                {"subscription": "stalled-sub", "function": "ProcessOrder", "stall_after": "15m"},
                {"subscription": "quiet-sub", "function": "ProcessOrder"},
            ]},
        ])

        def runner(args, check=True):
            if args[:3] == ["gh", "issue", "list"]:
                return SimpleNamespace(returncode=0, stdout="[]", stderr="")
            if args[:3] == ["gh", "issue", "create"]:
                return SimpleNamespace(
                    returncode=0, stdout=f"https://github.com/{_REPO}/issues/1\n", stderr=""
                )
            raise AssertionError(f"unexpected gh call: {args}")

        out = io.StringIO()
        cli.run_cycle(
            config,
            dry_run=False,
            repo=_REPO,
            transport_resolver=_stub_resolver,
            gh_runner=runner,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        output = out.getvalue()
        self.assertIn("created 2, updated 0, throttled 0", output)
        self.assertIn("skipped quiet-sub/ProcessOrder", output)
        self.assertIn("no stall_after configured", output)

    def test_dry_run_reports_would_be_filed(self):
        config = _config([{"type": "dlq", "targets": [{"subscription": "orders-sub", "function": "ProcessOrder"}]}])
        out = io.StringIO()
        cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=_stub_resolver,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        self.assertIn("would be filed", out.getvalue())


# ---------------------------------------------------------------------------
# criterion 11 — redaction survives the CLI
# ---------------------------------------------------------------------------


class TestRedactionSurvivesTheCli(_CliTestCase):
    def test_planted_secret_never_appears_in_dry_run_output(self):
        secret = "zzsynthetic8f2c9a4-not-a-real-credential"
        planted = f"connection_string=redis://user:{secret}@cache.internal:6379/0"

        def resolver(module, check_type, binding):
            return _StubDlqTransport({
                "orders-sub": [_StubMessage(dead_letter_error_description=planted)],
            })

        config = _config([{"type": "dlq", "targets": [{"subscription": "orders-sub", "function": "ProcessOrder"}]}])
        out = io.StringIO()
        cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=resolver,
            now=_NOW,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        output = out.getvalue()
        self.assertNotIn(secret, output)
        self.assertIn("<redacted:", output)


# ---------------------------------------------------------------------------
# criterion 2 — zero-runtime-dependency import; the CLI entry point
# ---------------------------------------------------------------------------


class TestImportAndEntryPoint(unittest.TestCase):
    def test_import_exits_zero_with_no_cloud_sdk(self):
        result = subprocess.run(
            [sys.executable, "-c", "from specfuse.monitor.cli import main"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pyproject_declares_the_entry_point(self):
        text = Path("pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('specfuse-monitor = "specfuse.monitor.cli:main"', text)

    def test_main_without_run_prints_help_and_exits_nonzero(self):
        code = cli.main([])
        self.assertEqual(code, 2)

    def test_build_parser_accepts_run_flags(self):
        parser = cli.build_parser()
        args = parser.parse_args(["run", "--component", "web-api", "--env", "production", "--dry-run"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.component, "web-api")
        self.assertEqual(args.env, "production")
        self.assertTrue(args.dry_run)


# ---------------------------------------------------------------------------
# issue-lifecycle classification — updated / throttled, not just created
# ---------------------------------------------------------------------------


class TestIssueClassification(_CliTestCase):
    def test_repeat_sighting_outside_throttle_window_is_classified_updated(self):
        config = _config([{"type": "dlq", "targets": [{"subscription": "orders-sub", "function": "ProcessOrder"}]}])
        existing_body = (
            "<!-- specfuse:finding fingerprint=deadbeef -->\n"
            "<!-- specfuse:finding-meta occurrences=1 last_seen=0.0 -->\nold body"
        )

        def runner(args, check=True):
            if args[:3] == ["gh", "issue", "list"]:
                return SimpleNamespace(
                    returncode=0,
                    stdout=f'[{{"number": 7, "body": {existing_body!r}, "title": "x"}}]'.replace("'", '"'),
                    stderr="",
                )
            if args[:3] == ["gh", "issue", "edit"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            raise AssertionError(f"unexpected gh call: {args}")

        # `find_finding_issue` re-checks the marker client-side, so drive it
        # through a fake fingerprint match instead of guessing the real one.
        with mock.patch("specfuse.monitor.cli.fingerprint_artifact", return_value="deadbeef"):
            out = io.StringIO()
            cli.run_cycle(
                config,
                dry_run=False,
                repo=_REPO,
                transport_resolver=_stub_resolver,
                gh_runner=runner,
                now=_NOW,
                watermark_dir=self.watermark_dir,
                out=out,
            )
        self.assertIn("created 0, updated 1, throttled 0", out.getvalue())

    def test_repeat_sighting_inside_throttle_window_is_classified_throttled(self):
        config = _config([{"type": "dlq", "targets": [{"subscription": "orders-sub", "function": "ProcessOrder"}]}])
        recent = _NOW.timestamp() - 10
        existing_body = (
            "<!-- specfuse:finding fingerprint=deadbeef -->\n"
            f"<!-- specfuse:finding-meta occurrences=1 last_seen={recent} -->\nold body"
        )

        def runner(args, check=True):
            if args[:3] == ["gh", "issue", "list"]:
                return SimpleNamespace(
                    returncode=0,
                    stdout=f'[{{"number": 7, "body": {existing_body!r}, "title": "x"}}]'.replace("'", '"'),
                    stderr="",
                )
            raise AssertionError(f"unexpected gh call: {args}")

        with mock.patch("specfuse.monitor.cli.fingerprint_artifact", return_value="deadbeef"):
            out = io.StringIO()
            cli.run_cycle(
                config,
                dry_run=False,
                repo=_REPO,
                transport_resolver=_stub_resolver,
                gh_runner=runner,
                now=_NOW,
                watermark_dir=self.watermark_dir,
                out=out,
            )
        self.assertIn("created 0, updated 0, throttled 1", out.getvalue())


# ---------------------------------------------------------------------------
# the default (real) transport resolver and its reflective helpers
# ---------------------------------------------------------------------------


class TestDefaultTransportResolver(unittest.TestCase):
    def test_find_transport_factory_resolves_by_token_match(self):
        import specfuse.monitor.providers.azure_service_bus as service_bus

        factory = cli._find_transport_factory(service_bus, "queue-stalled")
        self.assertIs(factory, service_bus.build_azure_queue_stalled_transport)

    def test_find_transport_factory_resolves_by_elimination(self):
        import specfuse.monitor.providers.azure_service_bus as service_bus

        factory = cli._find_transport_factory(service_bus, "dlq")
        self.assertIs(factory, service_bus.build_azure_transport)

    def test_find_transport_factory_serves_every_telemetry_check_type(self):
        import specfuse.monitor.providers.azure_app_insights as app_insights

        for check_type in ("error-logs", "http-5xx", "invariant", "heartbeat"):
            factory = cli._find_transport_factory(app_insights, check_type)
            self.assertIs(factory, app_insights.build_app_insights_transport)

    def test_find_transport_factory_raises_when_module_has_none(self):
        module = types.ModuleType("specfuse.monitor.providers.fixture_no_transport")
        with self.assertRaises(cli.MonitorCliError):
            cli._find_transport_factory(module, "dlq")

    def test_call_filtered_raises_on_missing_required_argument(self):
        def needs_two(*, a, b):
            return (a, b)

        with self.assertRaises(cli.MonitorCliError):
            cli._call_filtered(needs_two, a=1)

    def test_call_filtered_passes_through_var_keyword(self):
        def sink(**kwargs):
            return kwargs

        result = cli._call_filtered(sink, a=1, b=2)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_default_transport_resolver_reports_missing_credentials_clearly(self):
        import specfuse.monitor.providers.azure_app_insights as app_insights

        with self.assertRaises(cli.MonitorCliError):
            cli._default_transport_resolver(app_insights, "error-logs", {"provider": "azure_app_insights"})


# ---------------------------------------------------------------------------
# config loading
# ---------------------------------------------------------------------------


class TestLoadMonitoringConfig(_CliTestCase):
    def test_missing_file_is_a_clear_error(self):
        with self.assertRaises(cli.MonitorCliError):
            cli.load_monitoring_config(self.watermark_dir / "does-not-exist.yml")

    def test_invalid_config_is_a_clear_error(self):
        path = self.watermark_dir / "monitoring.yml"
        path.write_text("environments: {}\n", encoding="utf-8")
        with self.assertRaises(cli.MonitorCliError):
            cli.load_monitoring_config(path)

    def test_valid_config_parses(self):
        path = self.watermark_dir / "monitoring.yml"
        path.write_text(
            "environments:\n"
            "  production:\n"
            "    telemetry:\n"
            "      provider: azure_app_insights\n"
            "    broker:\n"
            "      provider: azure_service_bus\n"
            "components:\n"
            "  - name: order-worker\n"
            "    type: queue-consumer\n"
            "    runner: local\n"
            "    diagnose: manual\n"
            "    autofix: \"off\"\n"
            "    checks:\n"
            "      - type: error-logs\n",
            encoding="utf-8",
        )
        config = cli.load_monitoring_config(path)
        self.assertIn("production", config["environments"])


# ---------------------------------------------------------------------------
# repo resolution and main()
# ---------------------------------------------------------------------------


class TestResolveRepoAndMain(_CliTestCase):
    def test_resolve_repo_parses_origin_url(self):
        completed = SimpleNamespace(stdout="git@github.com:acme-widget/repo.git\n", returncode=0)
        with mock.patch("specfuse.monitor.cli.subprocess.run", return_value=completed):
            self.assertEqual(cli._resolve_repo(), "acme-widget/repo")

    def test_resolve_repo_raises_when_unresolvable(self):
        completed = SimpleNamespace(stdout="", returncode=1)
        with mock.patch("specfuse.monitor.cli.subprocess.run", return_value=completed):
            with self.assertRaises(cli.MonitorCliError):
                cli._resolve_repo()

    def test_main_reports_monitor_cli_error_on_stderr(self):
        with mock.patch("specfuse.monitor.cli.load_monitoring_config", side_effect=cli.MonitorCliError("boom")):
            code = cli.main(["run", "--dry-run"])
        self.assertEqual(code, 1)

    def test_main_runs_a_real_dry_run_cycle(self):
        config = _config([{"type": "error-logs"}])
        with mock.patch("specfuse.monitor.cli.load_monitoring_config", return_value=config), mock.patch(
            "specfuse.monitor.cli.run_cycle", return_value=0
        ) as run_cycle_spy:
            code = cli.main(["run", "--dry-run", "--component", "order-worker", "--env", "production"])
        self.assertEqual(code, 0)
        run_cycle_spy.assert_called_once()
        _, kwargs = run_cycle_spy.call_args
        self.assertEqual(kwargs["component_filter"], "order-worker")
        self.assertEqual(kwargs["env_filter"], "production")
        self.assertTrue(kwargs["dry_run"])
        self.assertIsNone(kwargs["repo"])

    def test_main_resolves_repo_for_a_real_non_dry_run(self):
        config = _config([{"type": "error-logs"}])
        with mock.patch("specfuse.monitor.cli.load_monitoring_config", return_value=config), mock.patch(
            "specfuse.monitor.cli.run_cycle", return_value=0
        ) as run_cycle_spy, mock.patch("specfuse.monitor.cli._resolve_repo", return_value=_REPO):
            code = cli.main(["run"])
        self.assertEqual(code, 0)
        _, kwargs = run_cycle_spy.call_args
        self.assertEqual(kwargs["repo"], _REPO)


if __name__ == "__main__":
    unittest.main()
