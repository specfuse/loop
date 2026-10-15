# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Application Insights KQL adapters for the three telemetry-keyed check
types that carry no schedule (FEAT-2026-0040/T06): ``error-logs``,
``http-5xx``, and ``invariant``. The fourth telemetry-keyed type,
``heartbeat``, is T07's — it consumes T04's cron dialect and computes an
expected firing time, a different failure mode from these three.

Every adapter resolves its telemetry binding through T01's seam,
``resolve_telemetry(component, environment)`` — never by reading
``environment["telemetry"]`` directly (the recorded decision against #262).

The transport is injected at construction: each adapter takes any object
exposing ``run_query``, so every test in this module runs against a stub
with no Azure SDK on the path. ``build_app_insights_transport`` is the only
function that touches the real SDK, and it imports it lazily inside the
function body so importing this module never requires
``azure-monitor-query`` to be installed (the package has zero runtime
dependencies).

Queries are built only from configuration — the component name and, for
``invariant``, the operator-authored ``query`` string from the repository's
own ``monitoring.yml``. No value returned by a telemetry query is ever
folded back into a subsequent query; that is the direction
``security-boundaries.md`` forbids.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, Iterator, Mapping, Optional, Protocol, Sequence

from specfuse.monitor.adapters import resolve_telemetry
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.redaction import redact_artifact

# Credential construction is shared with the other Azure provider and looked up
# reflectively by the core as `build_credential` (#302).
from specfuse.monitor.providers._azure_auth import build_credential  # noqa: F401
from specfuse.monitor.schedule import most_recent_firing

_GUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)
_NUMBER_RE = re.compile(r"\b\d+\b")


def _normalize_message(text: str) -> str:
    """Strip GUIDs, timestamps, and bare numbers so two occurrences of the
    same underlying failure — differing only in operation/request IDs and
    timestamps — collapse to one signature."""
    text = _GUID_RE.sub("<guid>", text)
    text = _TIMESTAMP_RE.sub("<timestamp>", text)
    text = _NUMBER_RE.sub("<num>", text)
    return " ".join(text.split())


class AppInsightsTransport(Protocol):
    """The single operation these adapters need from a transport: run a KQL
    query and hand back the result rows."""

    def run_query(self, query: str) -> Iterable[Mapping[str, object]]:
        ...


def _error_logs_query(component: str) -> str:
    """Built only from *component*, an operator-configured name — never from
    a telemetry query's returned rows.

    Every query here runs through ``query_workspace``, so it uses the Log
    Analytics workspace schema (``AppExceptions``, ``AppRoleName``,
    ``TimeGenerated``), not the classic App Insights names, which a workspace
    does not resolve (#3468). Columns are aliased back to the keys the
    adapters read from each row."""
    return (
        "AppExceptions "
        f"| where AppRoleName == '{component}' "
        "| project timestamp = TimeGenerated, operation_Id = OperationId, "
        "operation_ParentId = ParentId, type = ExceptionType, "
        "outerMessage = OuterMessage"
    )


def _http_5xx_query(component: str) -> str:
    return (
        "AppRequests "
        f"| where AppRoleName == '{component}' and ResultCode startswith '5' "
        "| project timestamp = TimeGenerated, operation_Id = OperationId, "
        "name = Name, resultCode = ResultCode"
    )


class ErrorLogsAdapter:
    """``TelemetryAdapter`` for the ``error-logs`` check type."""

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        query = _error_logs_query(self._component)
        rows = self._transport.run_query(query)
        for row in rows:
            yield self._build_artifact(row)

    def _build_artifact(self, row: Mapping[str, object]) -> FailureArtifact:
        exception_type = str(row.get("type") or "UnknownException")
        raw_message = str(row.get("outerMessage") or "")
        failure_signature = f"{exception_type}:{_normalize_message(raw_message)}"
        artifact = FailureArtifact(
            component=self._component,
            check_type="error-logs",
            failure_class=exception_type,
            failure_signature=failure_signature,
            observed_text=raw_message,
            target_coordinates=None,
        )
        return redact_artifact(artifact)


class Http5xxAdapter:
    """``TelemetryAdapter`` for the ``http-5xx`` check type."""

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        query = _http_5xx_query(self._component)
        rows = self._transport.run_query(query)
        for row in rows:
            yield self._build_artifact(row)

    def _build_artifact(self, row: Mapping[str, object]) -> FailureArtifact:
        route = str(row.get("name") or "unknown-route")
        status_code = str(row.get("resultCode") or "5xx")
        failure_signature = f"{route}:{status_code}"
        observed_text = f"{route} returned {status_code}"
        artifact = FailureArtifact(
            component=self._component,
            check_type="http-5xx",
            failure_class=status_code,
            failure_signature=failure_signature,
            observed_text=observed_text,
            target_coordinates=None,
        )
        return redact_artifact(artifact)


def _http_status_regression_query(
    component: str, deploy_signal: object, window_after_deploy: object, codes: Sequence[object]
) -> str:
    """Placeholder (T04 owns the real query). Built only from operator
    configuration — never from returned rows or the watermark."""
    code_list = ", ".join(f"'{c}'" for c in codes)
    return (
        "AppRequests "
        f"| where AppRoleName == '{component}' and ResultCode in ({code_list}) "
        f"// deploy_signal={deploy_signal} window_after_deploy={window_after_deploy} "
        "| project timestamp = TimeGenerated, version = AppVersion, "
        "resultCode = ResultCode"
    )


class HttpStatusRegressionAdapter:
    """``TelemetryAdapter`` for the ``http-status-regression`` check type.

    Skeleton rule: a row fires when its ``after`` count exceeds its ``before``
    count. One finding per (status code, deployment version); the version is
    part of ``failure_signature`` so the finding is filed once per deployment.
    """

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
        deploy_signal: object = None,
        window_after_deploy: object = None,
        codes: Optional[Sequence[object]] = None,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport
        self._deploy_signal = deploy_signal
        self._window_after_deploy = window_after_deploy
        self._codes = [str(c) for c in (codes or [])]

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        query = _http_status_regression_query(
            self._component, self._deploy_signal, self._window_after_deploy, self._codes
        )
        rows = self._transport.run_query(query)
        seen: set = set()
        for row in rows:
            code = str(row.get("code") or "")
            version = str(row.get("version") or "unknown-version")
            if self._codes and code not in self._codes:
                continue
            try:
                regressed = float(row.get("after") or 0) > float(row.get("before") or 0)
            except (TypeError, ValueError):
                continue
            if not regressed or (code, version) in seen:
                continue
            seen.add((code, version))
            yield self._build_artifact(code, version)

    def _build_artifact(self, code: str, version: str) -> FailureArtifact:
        artifact = FailureArtifact(
            component=self._component,
            check_type="http-status-regression",
            failure_class=code,
            failure_signature=f"{version}:{code}",
            observed_text=f"{code} rose after deployment {version}",
            target_coordinates=None,
        )
        return redact_artifact(artifact)


class InvariantAdapter:
    """``TelemetryAdapter`` for the ``invariant`` check type.

    ``failure_signature`` is the violating row's value in the
    ``fingerprint_by`` column — never the query text, the row index, or a
    hash of the whole row (FEAT-2026-0040/T06 criterion 6). ``query`` is the
    operator-authored, opaque KQL string from ``monitoring.yml``, executed
    as written.
    """

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
        query: str,
        fingerprint_by: str,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport
        self._query = query
        self._fingerprint_by = fingerprint_by

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        rows = self._transport.run_query(self._query)
        for row in rows:
            yield self._build_artifact(row)

    def _build_artifact(self, row: Mapping[str, object]) -> FailureArtifact:
        signature = str(row[self._fingerprint_by])
        artifact = FailureArtifact(
            component=self._component,
            check_type="invariant",
            failure_class="invariant",
            failure_signature=signature,
            observed_text=str(dict(row)),
            target_coordinates=None,
        )
        return redact_artifact(artifact)


# The heartbeat emission contract (#3470): a component signals one firing of a
# schedule by emitting one custom event with this name, under its own role name,
# carrying the schedule's name in this property. Documented for target
# applications in `.specfuse/rules/design-for-diagnosis.md`;
# tests/test_heartbeat_emission_contract.py holds the two in step.
HEARTBEAT_EVENT_NAME = "ScheduleHeartbeat"
HEARTBEAT_SCHEDULE_PROPERTY = "scheduleName"


def _heartbeat_query(component: str) -> str:
    """Built only from *component*, an operator-configured name — never from
    a telemetry query's returned rows. Groups the component's heartbeat
    signal by schedule name, since one component may carry several
    heartbeat targets (T04's `acme-functions-host` shape)."""
    return (
        "AppEvents "
        f"| where AppRoleName == '{component}' "
        f"and Name == '{HEARTBEAT_EVENT_NAME}' "
        "| summarize last_heartbeat = max(TimeGenerated) by "
        f"name = tostring(Properties.{HEARTBEAT_SCHEDULE_PROPERTY})"
    )


def _parse_heartbeat_timestamp(value: object) -> Optional[datetime]:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


class HeartbeatAdapter:
    """``TelemetryAdapter`` for the ``heartbeat`` check type
    (FEAT-2026-0040/T07).

    Unlike the three adapters above, a silent schedule is not a row a query
    returns — it is the *absence* of one. This adapter computes, per
    configured target, the most recent time its declared cron expression
    under its declared dialect (``specfuse.monitor.schedule``, reading T04's
    dialect rather than inferring it) was expected to fire, and compares
    that against the target's last observed heartbeat row. A target that
    reported in at or after its most recent expected firing yields nothing;
    only a target that has gone silent yields a `FailureArtifact`, built
    through `FailureArtifact.from_target` so its `name` round-trips into
    `target_coordinates` and keeps distinct silent schedules on one
    component individually fingerprinted (T02).
    """

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
        targets: Sequence[Mapping[str, str]],
        reference_time: datetime,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport
        self._targets = targets
        self._reference_time = reference_time

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        query = _heartbeat_query(self._component)
        rows = self._transport.run_query(query)
        last_seen: dict[str, datetime] = {}
        for row in rows:
            name = row.get("name")
            observed = _parse_heartbeat_timestamp(row.get("last_heartbeat"))
            if name and observed is not None:
                last_seen[str(name)] = observed

        for target in self._targets:
            name = target["name"]
            cron = target.get("cron")
            dialect = target.get("dialect")
            if not cron or not dialect:
                # A cron-less heartbeat target is valid per T04; there is
                # nothing to evaluate a firing expectation against.
                continue
            timezone_name = target.get("timezone", "Etc/UTC")
            expected = most_recent_firing(
                cron, dialect, timezone_name, self._reference_time
            )
            observed = last_seen.get(name)
            if observed is not None and observed >= expected:
                continue
            yield self._build_artifact(name, expected, observed)

    def _build_artifact(
        self, name: str, expected: datetime, observed: Optional[datetime]
    ) -> FailureArtifact:
        observed_text = (
            f"schedule '{name}' expected to fire at or before "
            f"{expected.isoformat()}, last observed heartbeat "
            f"{observed.isoformat() if observed is not None else 'never'}"
        )
        artifact = FailureArtifact.from_target(
            component=self._component,
            check_type="heartbeat",
            target={"name": name},
            failure_class="silent-schedule",
            failure_signature=f"heartbeat:{name}",
            observed_text=observed_text,
        )
        return redact_artifact(artifact)


def build_app_insights_transport(
    *, workspace_id: str, credential: object
) -> AppInsightsTransport:
    """Build a transport backed by the real Azure Monitor Query SDK.

    Imported lazily so `azure-monitor-query` is never required to import
    this module — only to call this factory.
    """
    from azure.monitor.query import LogsQueryClient

    class _AzureAppInsightsTransport:
        def run_query(self, query: str) -> Iterable[Mapping[str, object]]:
            client = LogsQueryClient(credential)
            response = client.query_workspace(
                workspace_id=workspace_id, query=query, timespan=None
            )
            tables = getattr(response, "tables", None) or []
            rows: list[Mapping[str, object]] = []
            for table in tables:
                columns = list(getattr(table, "columns", []))
                for row in getattr(table, "rows", []):
                    rows.append(dict(zip(columns, row, strict=False)))
            return rows

    return _AzureAppInsightsTransport()
