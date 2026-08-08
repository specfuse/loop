# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""``specfuse monitor run`` — one polling cycle, end to end
(FEAT-2026-0040/T10).

Reads ``.specfuse/monitoring.yml``, enumerates every check and target,
dispatches each to its provider adapter, fingerprints and redacts what comes
back, and hands the findings to the issue lifecycle in
``specfuse.monitor.issues`` — or, under ``--dry-run``, prints them and
touches nothing (see the flag-scope table in the work unit).

**The provider registry is reflective, not a hardcoded table.** A
``telemetry.provider`` / ``broker.provider`` string names, by convention, a
module under ``specfuse.monitor.providers`` (hyphens become underscores) —
resolved with ``importlib.import_module`` at dispatch time, never imported
by name here. Inside that module, the adapter class for a given check type
is found by matching the check type's PascalCase form against class names
ending in ``Adapter`` (unambiguous for every check type the schema defines
today). This keeps the opaque-string contract real: adding a provider is
dropping a new module under ``providers/``, with no change to this file, to
``lint_monitoring.py``, or to the schema — and it keeps no provider
identifier reachable from this module's own source text.

Transports are injected. Adapter construction touches nothing (the
protocols this package defines take a transport at construction and do no
I/O until ``fetch_failures()``), so building one is safe under
``--dry-run``. A default, best-effort transport resolver discovers a
provider module's transport-building callable the same reflective way and
calls it with whatever an environment binding's own fields supply —
correctness of that real-world wiring is outside what this work unit can
prove in-loop (no cloud SDK is installed here and never will be; see the
work unit's deferred criterion D-10). Tests inject their own resolver.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import pkgutil
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from specfuse.loop import _miniyaml
from specfuse.loop.escalation import _default_runner
from specfuse.loop.lint_monitoring import CHECK_TYPES, RUNNER_VALUES, validate_monitoring
from specfuse.monitor.adapters import resolve_telemetry
from specfuse.monitor.fingerprint import fingerprint_artifact
from specfuse.monitor.issues import record_finding

__all__ = ("main", "run_cycle", "load_monitoring_config", "MonitorCliError")

DEFAULT_CONFIG_PATH = Path(".specfuse/monitoring.yml")
DEFAULT_WATERMARK_DIR = Path(".specfuse/monitor-watermarks")
DEFAULT_LOOKBACK = timedelta(hours=24)

_PROVIDERS_PACKAGE = "specfuse.monitor.providers"

# Which axis a check type dispatches on. Not a provider registry — a fixed
# fact about the schema's own two adapter protocols (T01), used only to
# disambiguate a provider module's transport-factory candidates from one
# another (see `_find_transport_factory`).
_BROKER_CHECK_TYPES = frozenset({"dlq", "queue-stalled"})
_TELEMETRY_CHECK_TYPES = frozenset(CHECK_TYPES) - _BROKER_CHECK_TYPES


class MonitorCliError(RuntimeError):
    """A clear, user-facing config/selector/dispatch error."""


# ---------------------------------------------------------------------------
# provider registry — opaque config strings resolved to lazily-imported
# modules; the module names live in the config, never as literals here.
# ---------------------------------------------------------------------------


def _available_providers() -> list:
    package = importlib.import_module(_PROVIDERS_PACKAGE)
    return sorted(
        name
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__)
        if not is_pkg and not name.startswith("_")
    )


def _load_provider_module(provider: str):
    module_name = provider.replace("-", "_")
    full_name = f"{_PROVIDERS_PACKAGE}.{module_name}"
    try:
        return importlib.import_module(full_name)
    except ImportError as exc:
        raise MonitorCliError(
            f"unknown provider {provider!r} (looked for module {full_name!r}); "
            f"registered providers: {_available_providers()}"
        ) from exc


def _pascal(check_type: str) -> str:
    """"dlq" -> "Dlq", "http-5xx" -> "Http5xx", "queue-stalled" -> "QueueStalled"."""
    return "".join(part[:1].upper() + part[1:].lower() for part in check_type.split("-") if part)


def _find_adapter_class(module, check_type: str):
    marker = _pascal(check_type)
    matches = [
        obj
        for name, obj in vars(module).items()
        if isinstance(obj, type)
        and name.endswith("Adapter")
        and marker in name
        and hasattr(obj, "fetch_failures")
    ]
    if len(matches) != 1:
        raise MonitorCliError(
            f"no adapter registered for check type {check_type!r} in provider "
            f"module {module.__name__!r} (found {len(matches)} candidate(s))"
        )
    return matches[0]


def _sibling_check_types(check_type: str) -> frozenset:
    group = _BROKER_CHECK_TYPES if check_type in _BROKER_CHECK_TYPES else _TELEMETRY_CHECK_TYPES
    return group - {check_type}


def _find_transport_factory(module, check_type: str):
    def _normalize(name: str) -> str:
        return name.lower().replace("_", "")

    candidates = [
        (name, obj)
        for name, obj in vars(module).items()
        if callable(obj)
        and not isinstance(obj, type)
        and name.lower().startswith("build")
        and "transport" in name.lower()
    ]
    if not candidates:
        raise MonitorCliError(
            f"no transport factory found in provider module {module.__name__!r}"
        )

    marker = _normalize(_pascal(check_type))
    token_matches = [obj for name, obj in candidates if marker in _normalize(name)]
    if len(token_matches) == 1:
        return token_matches[0]

    sibling_markers = {_normalize(_pascal(ct)) for ct in _sibling_check_types(check_type)}
    generic = [
        obj
        for name, obj in candidates
        if not any(sib and sib in _normalize(name) for sib in sibling_markers)
    ]
    if len(generic) == 1:
        return generic[0]

    raise MonitorCliError(
        f"cannot resolve a transport factory for check type {check_type!r} in "
        f"provider module {module.__name__!r}"
    )


def _call_filtered(func, **candidate_kwargs):
    """Call *func* (a class or a plain callable) with whichever of
    *candidate_kwargs* its signature accepts, raising a clear error if a
    required parameter has no candidate — the generic composition seam that
    lets one dispatch path serve adapter classes and transport factories
    with entirely different signatures."""
    sig = inspect.signature(func)
    params = sig.parameters
    accepts_var_kw = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    if accepts_var_kw:
        kwargs = dict(candidate_kwargs)
    else:
        kwargs = {k: v for k, v in candidate_kwargs.items() if k in params}
    missing = [
        name
        for name, param in params.items()
        if param.default is inspect.Parameter.empty
        and param.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        and name not in kwargs
    ]
    if missing:
        raise MonitorCliError(f"cannot call {func!r}: missing required argument(s) {missing}")
    return func(**kwargs)


def _build_provider_credential(module):
    """Ask the provider module for its auth object, if it declares one.

    Reflective, exactly like `_find_transport_factory`: the core never names a
    provider or an SDK. Providers that need no credential simply omit the hook.
    """
    builder = getattr(module, "build_credential", None)
    if builder is None:
        return None
    return builder()


def _default_transport_resolver(module, check_type: str, binding: Mapping[str, object]):
    """Best-effort real transport construction: find the module's transport
    factory reflectively and call it with whatever the environment binding
    itself supplies.

    `credential` and `credentials` are distinct, which the factory signatures
    already implied and #302 established: **`credential` is the auth object** a
    provider's SDK requires, while **`credentials` stays the env-resolved values**
    for any factory that genuinely wants a secret string. Passing the mapping as
    `credential` was the #302 defect — it reached an SDK expecting an object with
    `get_token()`.

    The credential is built by the **provider module**, looked up reflectively the
    same way the transport factory is. The core must not know how any provider
    authenticates — `TestProviderRegistry.test_no_provider_identifier_reaches_the_core`
    enforces that, and it caught the first attempt at this fix, which imported an SDK
    here. A module exposing no `build_credential` simply gets `credential=None`.

    Still not exercised against a real cloud SDK in this repository (none is
    installed, by design); tests inject their own resolver or a fake credential.
    """
    import os

    factory = _find_transport_factory(module, check_type)
    credentials = binding.get("credentials") or {}
    resolved_credentials = {
        key: os.environ.get(value)
        for key, value in credentials.items()
        if isinstance(value, str)
    }
    extra = {k: v for k, v in binding.items() if k not in ("provider", "credentials")}
    return _call_filtered(
        factory,
        credential=_build_provider_credential(module),
        credentials=resolved_credentials or None,
        **extra,
    )


def _build_adapter(cls, *, component: str, environment: Mapping[str, object], check: Mapping[str, object], transport, now: datetime):
    kwargs = dict(
        component=component,
        environment=environment,
        transport=transport,
        targets=check.get("targets") or [],
        reference=now,
        reference_time=now,
        query=check.get("query"),
        fingerprint_by=check.get("fingerprint_by"),
        max_message_count=check.get("max_message_count", 50),
    )
    return _call_filtered(cls, **kwargs)


def _process_check(
    *,
    check: Mapping[str, object],
    component: Mapping[str, object],
    environment: Mapping[str, object],
    transport_resolver: Callable,
    now: datetime,
):
    check_type = check.get("type")
    if check_type not in CHECK_TYPES:
        raise MonitorCliError(
            f"unknown check type {check_type!r} on component {component.get('name')!r} "
            f"— must be one of {sorted(CHECK_TYPES)}"
        )

    component_name = component.get("name")
    if check_type in _BROKER_CHECK_TYPES:
        binding = environment.get("broker") or {}
    else:
        binding = resolve_telemetry(component_name, environment)

    provider = binding.get("provider") if isinstance(binding, Mapping) else None
    if not provider:
        raise MonitorCliError(
            f"component {component_name!r}: no provider bound for check type {check_type!r}"
        )

    module = _load_provider_module(provider)
    adapter_cls = _find_adapter_class(module, check_type)
    transport = transport_resolver(module, check_type, binding)
    adapter = _build_adapter(
        adapter_cls, component=component_name, environment=environment, check=check, transport=transport, now=now
    )
    artifacts = list(adapter.fetch_failures())
    skipped = list(getattr(adapter, "skipped_targets", []))
    return artifacts, skipped


# ---------------------------------------------------------------------------
# config loading
# ---------------------------------------------------------------------------


def load_monitoring_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load and structurally validate *path*. Validation runs regardless of
    ``--dry-run`` — reading and validating the config is the thing a dry run
    is for (see the work unit's flag-scope table)."""
    findings = validate_monitoring(path)
    if findings:
        raise MonitorCliError(
            f"{path} failed schema validation:\n" + "\n".join(f"  - {f}" for f in findings)
        )
    p = Path(path)
    if not p.is_file():
        raise MonitorCliError(f"no monitoring config at {p} — see .specfuse/monitoring.yml.example")
    return _miniyaml.parse(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# watermark — best-effort per-host cache; degrades to a lookback window
# ---------------------------------------------------------------------------


def _read_watermark(path: Path, *, lookback: timedelta, now: datetime):
    """Return ``(since, fallback_reason)``. ``fallback_reason`` is ``None``
    on a clean read and names why on a missing, unreadable, or corrupt file
    — never raises."""
    if not path.is_file():
        return now - lookback, "missing"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return now - lookback, "unreadable"
    try:
        data = json.loads(raw)
        since = datetime.fromisoformat(data["since"])
    except (ValueError, KeyError, TypeError):
        return now - lookback, "corrupt"
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return since, None


def _write_watermark(path: Path, *, now: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"since": now.isoformat()}), encoding="utf-8")


# ---------------------------------------------------------------------------
# issue-lifecycle call classification (real runs only)
# ---------------------------------------------------------------------------


class _CallRecorder:
    """Wraps a runner, recording every call so this module can classify a
    `record_finding` call as create/update/throttle from the outside,
    without reaching into `issues.py`'s private state."""

    def __init__(self, inner: Callable):
        self._inner = inner
        self.calls: list = []

    def __call__(self, args, check: bool = True):
        self.calls.append(list(args))
        return self._inner(args, check=check)


def _classify(recorder: "_CallRecorder") -> str:
    verbs = {c[2] for c in recorder.calls if len(c) > 2 and c[0] == "gh" and c[1] == "issue"}
    if "create" in verbs:
        return "created"
    if "edit" in verbs:
        return "updated"
    return "throttled"


# ---------------------------------------------------------------------------
# repo resolution (for the real, non-dry-run path only)
# ---------------------------------------------------------------------------


def _resolve_repo() -> str:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"[:/]([^/:]+/[^/.]+?)(?:\.git)?$", (result.stdout or "").strip())
    if not match:
        raise MonitorCliError(
            "could not resolve a repository from 'git config remote.origin.url' — "
            "no findings can be filed"
        )
    return match.group(1)


# ---------------------------------------------------------------------------
# the run cycle
# ---------------------------------------------------------------------------


def _describe(artifact) -> str:
    """Render a finding for the run summary/dry-run listing.

    Deliberately omits `failure_signature`: `redact_artifact` never touches
    it (T03's dedupe-key contract — see `specfuse.monitor.redaction`), so an
    adapter whose signature happens to fold in raw message text is the one
    field this module cannot assume is safe to print. Every field printed
    here — including `observed_text` — has already passed through
    `redact_artifact` at the adapter boundary.
    """
    parts = [f"component={artifact.component}", f"check_type={artifact.check_type}", f"failure_class={artifact.failure_class}"]
    if artifact.target_coordinates:
        coords = ", ".join(f"{k}={v}" for k, v in sorted(artifact.target_coordinates.items()))
        parts.append(f"target=({coords})")
    parts.append(f"observed={artifact.observed_text}")
    return " ".join(parts)


def run_cycle(
    config: Mapping[str, object],
    *,
    component_filter: Optional[str] = None,
    env_filter: Optional[str] = None,
    runner: str = "local",
    dry_run: bool = False,
    repo: Optional[str] = None,
    transport_resolver: Callable = _default_transport_resolver,
    gh_runner: Optional[Callable] = None,
    now: Optional[datetime] = None,
    watermark_dir: Path = DEFAULT_WATERMARK_DIR,
    lookback: timedelta = DEFAULT_LOOKBACK,
    out=None,
) -> int:
    out = out if out is not None else sys.stdout
    now = now if now is not None else datetime.now(timezone.utc)
    gh_runner = gh_runner if gh_runner is not None else _default_runner

    environments = config.get("environments") or {}
    components = config.get("components") or []

    if env_filter is not None and env_filter not in environments:
        raise MonitorCliError(f"unknown environment {env_filter!r} — available: {sorted(environments)}")
    component_names = [c.get("name") for c in components]
    if component_filter is not None and component_filter not in component_names:
        raise MonitorCliError(f"unknown component {component_filter!r} — available: {sorted(n for n in component_names if n)}")

    selected_envs = {env_filter: environments[env_filter]} if env_filter is not None else dict(environments)
    selected_components = [
        c for c in components if component_filter is None or c.get("name") == component_filter
    ]

    summary: list = []
    total_findings = 0

    for env_name in sorted(selected_envs):
        environment = selected_envs[env_name]
        watermark_path = watermark_dir / f"{env_name}.json"
        since, fallback_reason = _read_watermark(watermark_path, lookback=lookback, now=now)
        if fallback_reason is not None:
            summary.append(
                f"environment {env_name}: watermark fallback ({fallback_reason}) — "
                f"using lookback window since {since.isoformat()}"
            )

        for component in selected_components:
            component_name = component.get("name")
            component_runner = component.get("runner")
            if component_runner not in RUNNER_VALUES:
                raise MonitorCliError(
                    f"component {component_name!r}: unknown runner {component_runner!r} "
                    f"— must be one of {sorted(RUNNER_VALUES)}"
                )
            if component_runner != runner:
                if component_runner == "in-cluster":
                    disposition = "unhandled by design (FEAT-2026-0043, not yet implemented)"
                else:
                    disposition = "runs on a different surface"
                summary.append(
                    f"{env_name}/{component_name}: skipped — runner={component_runner} "
                    f"({disposition}); this run is runner={runner!r}"
                )
                continue

            findings: list = []
            skipped: list = []
            for check in component.get("checks") or []:
                artifacts, check_skipped = _process_check(
                    check=check,
                    component=component,
                    environment=environment,
                    transport_resolver=transport_resolver,
                    now=now,
                )
                findings.extend(artifacts)
                skipped.extend(check_skipped)

            total_findings += len(findings)

            if dry_run:
                summary.append(f"{env_name}/{component_name}: {len(findings)} finding(s) — would be filed")
                for artifact in findings:
                    summary.append(f"  would file: {_describe(artifact)}")
            else:
                created = updated = throttled = 0
                for artifact in findings:
                    fingerprint = fingerprint_artifact(artifact)
                    recorder = _CallRecorder(gh_runner)
                    record_finding(fingerprint, artifact, repo, runner=recorder, now=now.timestamp())
                    outcome = _classify(recorder)
                    if outcome == "created":
                        created += 1
                    elif outcome == "updated":
                        updated += 1
                    else:
                        throttled += 1
                summary.append(
                    f"{env_name}/{component_name}: {len(findings)} finding(s) — "
                    f"created {created}, updated {updated}, throttled {throttled}"
                )

            for skip in skipped:
                summary.append(
                    f"{env_name}/{component_name}: skipped "
                    f"{getattr(skip, 'subscription', '?')}/{getattr(skip, 'function', '?')} — "
                    f"{getattr(skip, 'reason', 'unknown reason')}"
                )

        if not dry_run:
            _write_watermark(watermark_path, now=now)

    summary.append(f"total: {total_findings} finding(s) across {len(selected_components)} component(s)")
    for line in summary:
        print(line, file=out)

    return 0


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specfuse monitor")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="run one polling cycle")
    run_parser.add_argument("--component", default=None, help="restrict the run to one component")
    run_parser.add_argument("--env", default=None, help="restrict the run to one environment")
    run_parser.add_argument(
        "--runner",
        default="local",
        choices=sorted(RUNNER_VALUES),
        help="which runner surface this invocation is (default: local) — "
        "components whose 'runner' dial names a different surface are skipped and reported",
    )
    run_parser.add_argument("--dry-run", action="store_true", help="print findings; touch nothing")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2

    try:
        config = load_monitoring_config(DEFAULT_CONFIG_PATH)
        repo = None if args.dry_run else _resolve_repo()
        return run_cycle(
            config,
            component_filter=args.component,
            env_filter=args.env,
            runner=args.runner,
            dry_run=args.dry_run,
            repo=repo,
        )
    except MonitorCliError as exc:
        print(f"specfuse monitor: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
