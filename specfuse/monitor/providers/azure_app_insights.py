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

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Iterable, Iterator, Mapping, Optional, Protocol, Sequence

from specfuse.monitor.adapters import resolve_telemetry
from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.durations import parse_duration_seconds
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


def _clean_id(value: object) -> str:
    """An operation id kept to id characters: it is echoed into reproduction
    text, and a returned value must never alter that text's shape."""
    return re.sub(r"[^A-Za-z0-9_.-]", "", str(value or ""))


def _kql_datetime(moment: datetime) -> str:
    """A KQL ``datetime()`` literal at full precision. ``moment`` comes from
    the harvester's own clock or watermark file, never from a returned row."""
    text = moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return f"datetime({text})"


def _harvest_window(since: Optional[datetime], until: Optional[datetime]) -> str:
    """The harvest-window predicate (#3480), or nothing when no window was
    given. Bounded on ``ingestion_time()`` rather than ``TimeGenerated`` so a
    row stamped before the previous run but ingested after it is read by the
    next run instead of falling between two windows."""
    if since is None or until is None:
        return ""
    return (
        f"| where ingestion_time() >= {_kql_datetime(since)} "
        f"and ingestion_time() < {_kql_datetime(until)} "
    )


# Assembly prefixes whose frames are framework, not application, code.
_FRAMEWORK_PREFIXES = ("System.", "Microsoft.")
_FRAMEWORK_FRAME_RE = "|".join(re.escape(p.rstrip(".")) for p in _FRAMEWORK_PREFIXES)

# Exception types that mean the caller went away, not that the service failed.
_CANCELLATION_TYPES = ("TaskCanceledException", "OperationCanceledException")

_SAMPLE_OPERATION_IDS = 3


def _top_frame_stages() -> str:
    """KQL stages that add ``frameMethod`` and ``frameAssembly`` to an
    ``AppExceptions`` row: the first in-app frame of ``Details[0].parsedStack``,
    framework frames dropped with ``replace_regex``."""
    framework = _FRAMEWORK_FRAME_RE
    return (
        "| extend stack = tostring(Details[0].parsedStack) "
        f"| extend appStack = replace_regex(stack, '\\{{[^{{}}]*\"assembly\":\"({framework})\\.[^{{}}]*\\}}', '') "
        "| extend frameMethod = extract('\"method\":\"([^\"]*)\"', 1, appStack), "
        "frameAssembly = extract('\"assembly\":\"([^\"]*)\"', 1, appStack) "
    )


def _error_logs_query(
    component: str, since: Optional[datetime] = None, until: Optional[datetime] = None
) -> str:
    """Built only from *component*, an operator-configured name — never from
    a telemetry query's returned rows.

    Every query here runs through ``query_workspace``, so it uses the Log
    Analytics workspace schema (``AppExceptions``, ``AppRoleName``,
    ``TimeGenerated``), not the classic App Insights names, which a workspace
    does not resolve (#3468). Columns are aliased back to the keys the
    adapters read from each row.

    One query carries the diagnostic context too (FEAT-2026-0204/T05): the
    request is a left join on ``OperationId`` (one row per operation), and the
    top in-app frame is read from ``Details[0].parsedStack`` by dropping
    framework frames with ``replace_regex`` and extracting the first frame
    left — string work per row, no ``mv-expand`` over every exception."""
    cancelled = " or ".join(f"ExceptionType endswith '{t}'" for t in _CANCELLATION_TYPES)
    request_floor = (
        f"| where TimeGenerated >= {_kql_datetime(since - timedelta(hours=1))} "
        if since is not None
        else ""
    )
    return (
        "AppExceptions "
        f"| where AppRoleName == '{component}' "
        f"{_harvest_window(since, until)}"
        f"{_top_frame_stages()}"
        "| join kind=leftouter ("
        "AppRequests "
        f"| where AppRoleName == '{component}' "
        f"{request_floor}"
        "| project OperationId = OperationId, Name = Name, ResultCode = ResultCode "
        "| summarize requestName = take_any(Name), requestResult = take_any(ResultCode) by OperationId"
        ") on OperationId "
        f"| extend clientAbort = iff(({cancelled}) and requestResult startswith '2', true, false) "
        "| project timestamp = TimeGenerated, operation_Id = OperationId, "
        "operation_ParentId = ParentId, type = ExceptionType, "
        "outerMessage = OuterMessage, instance = AppRoleInstance, "
        "loggerCategory = tostring(Properties.CategoryName), "
        "loggerTemplate = tostring(Properties.OriginalFormat), "
        "requestName, requestResult, frameMethod, frameAssembly, clientAbort"
    )


def _reproduce_query(component: str, operation_ids: Sequence[str]) -> str:
    """Text for a human to paste into Log Analytics; never executed here."""
    quoted = ", ".join(f"'{i}'" for i in operation_ids)
    return (
        "AppExceptions\n"
        f"| where AppRoleName == '{component}'\n"
        f"| where OperationId in ({quoted})\n"
        "| project TimeGenerated, ExceptionType, OuterMessage, OperationId, Details"
    )


def _http_5xx_query(
    component: str, since: Optional[datetime] = None, until: Optional[datetime] = None
) -> str:
    """One query carries the diagnostic context (FEAT-2026-0204/T06). The
    exception and the dependency are each reduced to one row per
    ``OperationId`` before the left joins, so a request with several
    exceptions or dependencies still yields one row: the first exception, and
    the failed dependency, else the slowest."""
    context_floor = (
        f"| where TimeGenerated >= {_kql_datetime(since - timedelta(hours=1))} "
        if since is not None
        else ""
    )
    return (
        "AppRequests "
        f"| where AppRoleName == '{component}' and ResultCode startswith '5' "
        f"{_harvest_window(since, until)}"
        "| join kind=leftouter ("
        "AppExceptions "
        f"| where AppRoleName == '{component}' "
        f"{context_floor}"
        f"{_top_frame_stages()}"
        "| summarize arg_min(TimeGenerated, ExceptionType, OuterMessage, frameMethod, frameAssembly) "
        "by OperationId "
        "| project OperationId, exceptionType = ExceptionType, "
        "exceptionMessage = OuterMessage, frameMethod, frameAssembly"
        ") on OperationId "
        "| join kind=leftouter ("
        "AppDependencies "
        f"| where AppRoleName == '{component}' "
        f"{context_floor}"
        "| extend depRank = iff(Success == false, 1000000000, 0) + DurationMs "
        "| summarize arg_max(depRank, Target, DependencyType, ResultCode, DurationMs, Success) "
        "by OperationId "
        "| project OperationId, dependencyTarget = Target, dependencyType = DependencyType, "
        "dependencyResult = ResultCode, dependencyDurationMs = DurationMs, "
        "dependencyFailed = Success == false"
        ") on OperationId "
        "| project timestamp = TimeGenerated, operation_Id = OperationId, "
        "name = Name, resultCode = ResultCode, durationMs = DurationMs, "
        "instance = AppRoleInstance, exceptionType, exceptionMessage, "
        "frameMethod, frameAssembly, dependencyTarget, dependencyType, "
        "dependencyResult, dependencyDurationMs, dependencyFailed"
    )


def _reproduce_5xx_query(component: str, operation_ids: Sequence[str]) -> str:
    """Text for a human to paste into Log Analytics; never executed here."""
    quoted = ", ".join(f"'{i}'" for i in operation_ids)
    return (
        "AppRequests\n"
        f"| where AppRoleName == '{component}'\n"
        f"| where OperationId in ({quoted})\n"
        "| project TimeGenerated, Name, ResultCode, DurationMs, OperationId"
    )


class ErrorLogsAdapter:
    """``TelemetryAdapter`` for the ``error-logs`` check type."""

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport
        self._since = since
        self._until = until

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        query = _error_logs_query(self._component, self._since, self._until)
        rows = list(self._transport.run_query(query))
        samples: dict = {}
        for row in rows:
            ids = samples.setdefault(self._signature(row), [])
            operation_id = _clean_id(row.get("operation_Id"))
            if operation_id and operation_id not in ids and len(ids) < _SAMPLE_OPERATION_IDS:
                ids.append(operation_id)
        for row in rows:
            yield self._build_artifact(row, samples[self._signature(row)])

    @staticmethod
    def _signature(row: Mapping[str, object]) -> str:
        exception_type = str(row.get("type") or "UnknownException")
        return f"{exception_type}:{_normalize_message(str(row.get('outerMessage') or ''))}"

    def _build_artifact(
        self, row: Mapping[str, object], sample_ids: Sequence[str] = ()
    ) -> FailureArtifact:
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
            context=self._context(row, exception_type, sample_ids),
            observed_at=str(row["timestamp"]) if row.get("timestamp") else None,
            instance=str(row["instance"]) if row.get("instance") else None,
        )
        return redact_artifact(artifact)

    def _context(
        self, row: Mapping[str, object], exception_type: str, sample_ids: Sequence[str]
    ) -> Optional[dict]:
        context: dict = {}
        method = str(row.get("frameMethod") or "")
        if method:
            assembly = str(row.get("frameAssembly") or "")
            context["Where"] = f"{method} ({assembly})" if assembly else method
        route = str(row.get("requestName") or "")
        result = str(row.get("requestResult") or "")
        if route or result:
            context["Request"] = " ".join(
                part for part in (route, f"returned {result}" if result else "") if part
            )
        category = str(row.get("loggerCategory") or "")
        template = str(row.get("loggerTemplate") or "")
        if category or template:
            context["Logger"] = category + (f" (template: {template})" if template else "")
        if str(row.get("clientAbort")).lower() == "true":
            context["Likely client abort"] = (
                f"{exception_type} on a request that returned {result}: "
                "the client disconnected after the service answered."
            )
        if sample_ids:
            context["Samples"] = ", ".join(sample_ids)
            context["Reproduce"] = _reproduce_query(self._component, sample_ids)
        return context or None


class Http5xxAdapter:
    """``TelemetryAdapter`` for the ``http-5xx`` check type."""

    def __init__(
        self,
        *,
        component: str,
        environment: Mapping[str, object],
        transport: AppInsightsTransport,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport
        self._since = since
        self._until = until

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        query = _http_5xx_query(self._component, self._since, self._until)
        rows = list(self._transport.run_query(query))
        samples: dict = {}
        for row in rows:
            ids = samples.setdefault(self._signature(row), [])
            operation_id = _clean_id(row.get("operation_Id"))
            if operation_id and operation_id not in ids and len(ids) < _SAMPLE_OPERATION_IDS:
                ids.append(operation_id)
        for row in rows:
            yield self._build_artifact(row, samples[self._signature(row)])

    @staticmethod
    def _signature(row: Mapping[str, object]) -> str:
        route = str(row.get("name") or "unknown-route")
        status_code = str(row.get("resultCode") or "5xx")
        return f"{route}:{status_code}"

    def _build_artifact(
        self, row: Mapping[str, object], sample_ids: Sequence[str] = ()
    ) -> FailureArtifact:
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
            context=self._context(row, sample_ids),
            observed_at=str(row["timestamp"]) if row.get("timestamp") else None,
            instance=str(row["instance"]) if row.get("instance") else None,
        )
        return redact_artifact(artifact)

    def _context(
        self, row: Mapping[str, object], sample_ids: Sequence[str]
    ) -> Optional[dict]:
        context: dict = {}
        exception_type = str(row.get("exceptionType") or "")
        if exception_type:
            message = str(row.get("exceptionMessage") or "")
            context["Exception"] = f"{exception_type}: {message}" if message else exception_type
        method = str(row.get("frameMethod") or "")
        if method:
            assembly = str(row.get("frameAssembly") or "")
            context["Where"] = f"{method} ({assembly})" if assembly else method
        target = str(row.get("dependencyTarget") or "")
        if target:
            kind = str(row.get("dependencyType") or "")
            result = str(row.get("dependencyResult") or "")
            parts = [target]
            if kind:
                parts.append(f"type {kind}")
            if result:
                parts.append(f"returned {result}")
            if str(row.get("dependencyFailed")).lower() != "true":
                parts.append("slowest dependency, not failed")
            duration = _milliseconds(row.get("dependencyDurationMs"))
            if duration:
                parts.append(duration)
            context["Dependency"] = ", ".join(parts)
        duration = _milliseconds(row.get("durationMs"))
        if duration:
            context["Duration"] = duration
        if sample_ids:
            context["Samples"] = ", ".join(sample_ids)
            context["Reproduce"] = _reproduce_5xx_query(self._component, sample_ids)
        return context or None


def _milliseconds(value: object) -> str:
    try:
        return f"{float(value):.0f} ms"  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ""


# The regression rule (PLAN.md decision 2): a code fires when its share of the
# after-window's requests is at least REGRESSION_FACTOR times its share of the
# equal-length before-window and it occurs at least REGRESSION_MIN_COUNT times
# after the deployment. Documented constants in v1, not monitoring.yml fields.
REGRESSION_FACTOR = 3
REGRESSION_MIN_COUNT = 10

# The codes evaluated when `monitoring.yml` names none: forbidden, method not
# allowed, unsupported media type — the 4xx a deployment produces when it breaks
# authorization mapping, routing or content negotiation. 401 is deliberately
# opt-in: a 401 wave is as often expired client tokens as a broken deployment.
DEFAULT_REGRESSION_CODES = ("403", "405", "415")

# How many operations, and how many sample operation ids, a finding names.
_TOP_OPERATIONS = 5
_SAMPLE_OPERATIONS = 3

# How far back the one query looks for each version's first-seen time. A
# deployment is only evaluated when its before-window also lies inside it.
_REGRESSION_LOOKBACK = "7d"


def _http_status_regression_query(
    component: str, window_seconds: int, codes: Sequence[object]
) -> str:
    """One query, built only from operator configuration (the component, the
    configured ``codes``, ``window_after_deploy`` and a fixed lookback) —
    never from returned rows or the watermark. Each version's first-seen time
    is found, deployments whose after-window has fully elapsed are kept, and
    per (version, code) the after- and before-window counts come back with
    each window's total request count, the code's top operations by
    after-window count, and a few after-window operation ids. The ratio
    arithmetic is the adapter's.
    """
    window = f"{int(window_seconds)}s"
    code_list = ", ".join(f"'{c}'" for c in codes)
    scope = (
        f"AppRequests | where AppRoleName == '{component}' "
        f"and TimeGenerated > ago({_REGRESSION_LOOKBACK}) "
        "and isnotempty(AppVersion)"
    )
    return (
        f"{scope} "
        "| summarize first_seen = min(TimeGenerated) by AppVersion "
        f"| where first_seen + {window} <= now() "
        f"and first_seen - {window} >= ago({_REGRESSION_LOOKBACK}) "
        "| project AppVersion, first_seen, k = 1 "
        f"| join kind=inner ({scope} "
        "| project TimeGenerated, ResultCode, Name, OperationId, k = 1) on k "
        f"| where TimeGenerated >= first_seen - {window} "
        f"and TimeGenerated < first_seen + {window} "
        "| summarize after = countif(TimeGenerated >= first_seen), "
        "before = countif(TimeGenerated < first_seen), "
        "sample = take_anyif(OperationId, TimeGenerated >= first_seen) "
        "by AppVersion, first_seen, ResultCode, Name "
        "| sort by AppVersion asc, ResultCode asc, after desc "
        "| extend rn = row_number(1, prev(AppVersion) != AppVersion "
        "or prev(ResultCode) != ResultCode) "
        "| summarize after = sum(after), before = sum(before), "
        "endpoints = make_list_if(pack('name', Name, 'after', after, "
        f"'before', before), rn <= {_TOP_OPERATIONS}), "
        f"samples = make_list_if(sample, rn <= {_SAMPLE_OPERATIONS} "
        "and isnotempty(sample)) "
        "by AppVersion, first_seen, ResultCode "
        "| summarize per_code = make_list(pack('code', ResultCode, "
        "'after', after, 'before', before, 'endpoints', endpoints, "
        "'samples', samples)), "
        "after_total = sum(after), before_total = sum(before) "
        "by AppVersion, first_seen "
        "| mv-expand per_code "
        "| project version = AppVersion, first_seen, "
        "code = tostring(per_code.code), after = tolong(per_code.after), "
        "before = tolong(per_code.before), endpoints = per_code.endpoints, "
        "samples = per_code.samples, after_total, before_total "
        f"| where code in ({code_list})"
    )


def _dynamic_list(value: object) -> list:
    """A ``dynamic`` column arrives parsed or as JSON text, depending on the
    client; anything else reads as empty rather than failing the finding."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return list(value) if isinstance(value, (list, tuple)) else []


def _share(count: int, total: int) -> str:
    return f"{100 * count / total:.2f}%" if total > 0 else "n/a (no requests)"


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _kql_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _as_utc(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _count(value: object) -> Optional[int]:
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class HttpStatusRegressionAdapter:
    """``TelemetryAdapter`` for the ``http-status-regression`` check type.

    One finding per (status code, deployment version) whose after-window has
    fully elapsed at ``reference_time`` and whose share of requests regressed
    by ``REGRESSION_FACTOR`` with at least ``REGRESSION_MIN_COUNT`` after-window
    occurrences. The version is part of ``failure_signature`` so the finding
    is filed once per deployment.
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
        reference_time: Optional[datetime] = None,
    ) -> None:
        self._component = component
        self._telemetry = resolve_telemetry(component, environment)
        self._transport = transport
        self._deploy_signal = deploy_signal
        self._window_after_deploy = window_after_deploy
        self._codes = [str(c) for c in codes] if codes else list(DEFAULT_REGRESSION_CODES)
        self._reference_time = reference_time

    def fetch_failures(self) -> Iterator[FailureArtifact]:
        window_seconds = parse_duration_seconds(
            self._window_after_deploy, "window_after_deploy"  # type: ignore[arg-type]
        )
        reference = _as_utc(self._reference_time) or datetime.now(timezone.utc)
        query = _http_status_regression_query(self._component, window_seconds, self._codes)
        seen: set = set()
        for row in self._transport.run_query(query):
            code = str(row.get("code") or "")
            version = str(row.get("version") or "unknown-version")
            if code not in self._codes:
                continue
            first_seen = _as_utc(row.get("first_seen"))
            counts = [
                _count(row.get(key))
                for key in ("after", "before", "after_total", "before_total")
            ]
            if first_seen is None or None in counts:
                continue
            if first_seen + timedelta(seconds=window_seconds) > reference:
                continue
            after, before, after_total, before_total = counts  # type: ignore[misc]
            if (code, version) in seen or not _regressed(
                after, before, after_total, before_total
            ):
                continue
            seen.add((code, version))
            yield self._build_artifact(
                code, version, first_seen, window_seconds,
                after, before, after_total, before_total,
                _dynamic_list(row.get("endpoints")), _dynamic_list(row.get("samples")),
            )

    def _build_artifact(
        self,
        code: str,
        version: str,
        first_seen: datetime,
        window_seconds: int,
        after: int,
        before: int,
        after_total: int,
        before_total: int,
        endpoints: list,
        samples: list,
    ) -> FailureArtifact:
        window = self._window_after_deploy
        lines = [
            f"{code} rose after deployment {version} "
            f"(first seen {_iso(first_seen)}).",
            f"Share of requests: {_share(before, before_total)} in the {window} "
            f"before ({before} of {before_total}), {_share(after, after_total)} "
            f"in the {window} after ({after} of {after_total}). Fires at "
            f"{REGRESSION_FACTOR}x the before-share with at least "
            f"{REGRESSION_MIN_COUNT} occurrences after.",
        ]
        operations = sorted(
            (e for e in endpoints if isinstance(e, Mapping)),
            key=lambda e: _count(e.get("after")) or 0,
            reverse=True,
        )[:_TOP_OPERATIONS]
        if operations:
            lines += ["", f"Top operations returning {code}:"]
            lines += [
                f"  {e.get('name') or '(unnamed)'}: {_count(e.get('after')) or 0} "
                f"after, {_count(e.get('before')) or 0} before"
                for e in operations
            ]
        sample_ids = [str(s) for s in samples if s][:_SAMPLE_OPERATIONS]
        if sample_ids:
            lines += ["", f"Sample operation ids after the deployment: {', '.join(sample_ids)}"]
        span = timedelta(seconds=window_seconds)
        lines += [
            "",
            "Investigate in Log Analytics:",
            "AppRequests",
            f"| where AppRoleName == '{_kql_literal(self._component)}' "
            f"and ResultCode == '{_kql_literal(code)}'",
            f"| where TimeGenerated between (datetime({_iso(first_seen - span)}) "
            f".. datetime({_iso(first_seen + span)}))",
            "| summarize count() by AppVersion, Name, bin(TimeGenerated, 5m)",
        ]
        artifact = FailureArtifact(
            component=self._component,
            check_type="http-status-regression",
            failure_class=code,
            failure_signature=f"{version}:{code}",
            observed_text="\n".join(lines),
            target_coordinates=None,
        )
        return redact_artifact(artifact)


def _regressed(after: int, before: int, after_total: int, before_total: int) -> bool:
    """``after/after_total >= FACTOR * before/before_total``, in integers; a
    before-window with no requests, or none of the code, has a share of 0."""
    if after_total <= 0 or after < REGRESSION_MIN_COUNT:
        return False
    if before_total <= 0 or before <= 0:
        return True
    return after * before_total >= REGRESSION_FACTOR * before * after_total


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
    heartbeat targets (T04's `acme-functions-host` shape). Also carries each
    schedule's earliest heartbeat, whose minimum across rows is the
    component's earliest heartbeat — the instant before which no firing is
    evaluated (FEAT-2026-0204/T04)."""
    return (
        "AppEvents "
        f"| where AppRoleName == '{component}' "
        f"and Name == '{HEARTBEAT_EVENT_NAME}' "
        "| summarize last_heartbeat = max(TimeGenerated), "
        "first_heartbeat = min(TimeGenerated) by "
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
        earliest: Optional[datetime] = None
        for row in rows:
            name = row.get("name")
            observed = _parse_heartbeat_timestamp(row.get("last_heartbeat"))
            first = _parse_heartbeat_timestamp(row.get("first_heartbeat")) or observed
            if first is not None and (earliest is None or first < earliest):
                earliest = first
            if name and observed is not None:
                last_seen[str(name)] = observed

        if earliest is None:
            # No liveness signal at all: "never deployed" and "silent" are
            # indistinguishable, so every target stays pending.
            return

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
            if expected < earliest:
                # Pending first firing: emission began after this firing.
                continue
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
