#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Specfuse monitoring-schema linter.

Validates a project's ``.specfuse/monitoring.yml`` structurally:

  - top-level ``environments:`` and ``components:`` keys parse,
  - each environment's ``telemetry``/``broker`` provider bindings are present
    and carry a ``provider`` name (an opaque string; this module does not
    interpret it — see FEAT-2026-0040 for provider adapters),
  - credential-shaped values are environment-variable references, never
    inline literals,
  - each component carries its required fields and its ``runner``/
    ``diagnose``/``autofix`` dials are one of the neutral enum values,
  - each check's ``type`` is one of the neutral set.

Sibling of ``lint_plan.py`` (unrelated artifact, not an extension of it) and,
like it, parses only with ``_miniyaml`` — the package has zero runtime
dependencies.

Monitoring is opt-in: an absent ``monitoring.yml`` is a correct final state,
not an error. ``validate_monitoring`` returns ``[]`` in that case.

Exit 0 = clean (including "file absent"), 1 = findings printed.

Usage:  lint_monitoring.py [path/to/monitoring.yml]
"""

from __future__ import annotations

import re
from pathlib import Path

from . import _miniyaml

__all__ = ("validate_monitoring", "main", "CRON_DIALECTS")

RUNNER_VALUES = frozenset({"local", "gh-actions", "in-cluster"})
DIAGNOSE_VALUES = frozenset({"manual", "auto"})
AUTOFIX_VALUES = frozenset({"off", "on"})
CHECK_TYPES = frozenset(
    {"dlq", "error-logs", "http-5xx", "heartbeat", "invariant", "queue-stalled"}
)
HARVEST_MODE_VALUES = frozenset({"peek", "quarantine"})

# A `heartbeat` target's `cron` dialect, declared rather than inferred: a
# 5-field standard cron and a 6-field seconds-first cron (Azure Functions
# timer triggers) are both well-formed and mean different things, and field
# count alone cannot disambiguate a new dialect arriving later. The value is
# the expression's required whitespace-separated field count.
CRON_DIALECTS = {
    "standard-5": 5,
    "seconds-first-6": 6,
}

REQUIRED_COMPONENT_FIELDS = ("name", "type", "runner", "diagnose", "autofix", "checks")
REQUIRED_PROVIDER_BINDINGS = ("telemetry", "broker")

# Keys whose value is a credential reference, wherever they appear nested
# under `environments:`. Matched case-insensitively against the trailing
# name segment (e.g. `api_key`, `connection_string`, `token`).
_CREDENTIAL_KEY_RE = re.compile(
    r"(?i)(^|_)(key|token|secret|password|credential|connection[_-]?string)s?$"
)
# An environment-variable-NAME reference: the schema admits credentials by
# env-var name only, e.g. `TELEMETRY_API_KEY` or `Section__Key`.
#
# The property enforced is "this is a variable NAME, not a secret VALUE" — which
# does not require upper case. `UPPER_SNAKE_CASE` is a convention; POSIX permits
# lowercase, and `Section__Key` (case preserved, double-underscore separator) is
# the canonical spelling for hierarchical configuration in .NET, Spring, and
# other stacks. Requiring upper case rejected the true name of a variable the
# application actually reads and taught the operator nothing (#246).
#
# This is a structural shape check, NOT a secret detector: a value that happens
# to be name-shaped (`hunter2`) cannot be distinguished from a name here, and
# never could — the old pattern accepted `ABC123DEF456` just as readily. Secret
# detection is the `leak-scan` gate's job (gitleaks over the tree); this check
# exists to catch the common authoring slip of pasting a connection string where
# a variable name belongs, which every marker a literal carries (whitespace,
# `=`, `;`, `://`, `.`, `,`, quotes) still trips.
_ENV_VAR_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_DEFAULT_PATH = Path(".specfuse/monitoring.yml")


def validate_monitoring(path: str | Path | None = None) -> list[str]:
    """Validate *path* (default ``.specfuse/monitoring.yml``); return findings.

    Empty list means valid (including "file does not exist" — monitoring is
    opt-in). A parse failure is reported as a one-element finding list, never
    a silent ``[]``.
    """
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.is_file():
        return []

    try:
        parsed = _miniyaml.parse(p.read_text())
    except _miniyaml.MiniYAMLError as exc:
        return [f"{p}: could not parse as YAML: {exc}"]

    if not isinstance(parsed, dict):
        return [f"{p}: top level must be a mapping with 'environments' and "
                f"'components' keys"]

    findings: list[str] = []
    findings.extend(_check_environments(parsed.get("environments")))
    findings.extend(_check_components(parsed.get("components")))
    return findings


def _check_environments(environments: object) -> list[str]:
    findings: list[str] = []
    if environments is None:
        findings.append("missing top-level 'environments' key")
        return findings
    if not isinstance(environments, dict):
        findings.append("'environments' must be a mapping of environment "
                         "name to its bindings")
        return findings

    for env_name, env_body in environments.items():
        if not isinstance(env_body, dict):
            findings.append(f"environment '{env_name}': must be a mapping")
            continue
        for binding in REQUIRED_PROVIDER_BINDINGS:
            value = env_body.get(binding)
            if value is None:
                findings.append(
                    f"environment '{env_name}': missing '{binding}' binding"
                )
            elif not isinstance(value, dict) or not str(value.get("provider") or "").strip():
                findings.append(
                    f"environment '{env_name}': '{binding}' binding missing "
                    f"a 'provider' name"
                )
        findings.extend(
            _check_credentials(env_body, f"environment '{env_name}'")
        )
    return findings


def _check_credentials(node: object, where: str) -> list[str]:
    """Recursively find credential-shaped keys and reject inline literals."""
    findings: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if _CREDENTIAL_KEY_RE.search(str(key)) and isinstance(value, str):
                if not _ENV_VAR_NAME_RE.match(value):
                    findings.append(
                        f"{where}: credential '{key}' must be an "
                        f"environment-variable NAME (e.g. ACME_API_KEY or "
                        f"Section__Key), not a value"
                    )
            findings.extend(_check_credentials(value, where))
    elif isinstance(node, list):
        for item in node:
            findings.extend(_check_credentials(item, where))
    return findings


def _check_components(components: object) -> list[str]:
    findings: list[str] = []
    if components is None:
        findings.append("missing top-level 'components' key")
        return findings
    if not isinstance(components, list):
        findings.append("'components' must be a list of component mappings")
        return findings

    for index, component in enumerate(components):
        if not isinstance(component, dict):
            findings.append(f"component[{index}]: must be a mapping")
            continue
        label = str(component.get("name") or f"component[{index}]")

        for field in REQUIRED_COMPONENT_FIELDS:
            if component.get(field) is None:
                findings.append(f"component '{label}': missing '{field}' field")

        runner = component.get("runner")
        if runner is not None and runner not in RUNNER_VALUES:
            findings.append(
                f"component '{label}': 'runner' has unknown value {runner!r} "
                f"— must be one of {sorted(RUNNER_VALUES)}"
            )
        diagnose = component.get("diagnose")
        if diagnose is not None and diagnose not in DIAGNOSE_VALUES:
            findings.append(
                f"component '{label}': 'diagnose' has unknown value "
                f"{diagnose!r} — must be one of {sorted(DIAGNOSE_VALUES)}"
            )
        autofix = component.get("autofix")
        if autofix is not None and autofix not in AUTOFIX_VALUES:
            findings.append(
                f"component '{label}': 'autofix' has unknown value "
                f"{autofix!r} — must be one of {sorted(AUTOFIX_VALUES)}"
            )

        checks = component.get("checks")
        if checks is not None:
            findings.extend(_check_checks(checks, label))

    return findings


def _check_checks(checks: object, component_label: str) -> list[str]:
    findings: list[str] = []
    if not isinstance(checks, list):
        findings.append(f"component '{component_label}': 'checks' must be a list")
        return findings

    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            findings.append(
                f"component '{component_label}': checks[{index}]: must be a mapping"
            )
            continue
        check_type = check.get("type")
        if check_type not in CHECK_TYPES:
            findings.append(
                f"component '{component_label}': checks[{index}]: unknown "
                f"check type {check_type!r} — must be one of "
                f"{sorted(CHECK_TYPES)}"
            )
            continue
        if check_type == "dlq":
            harvest_mode = check.get("harvest_mode")
            if harvest_mode not in HARVEST_MODE_VALUES:
                findings.append(
                    f"component '{component_label}': checks[{index}]: 'dlq' "
                    f"check has unknown 'harvest_mode' {harvest_mode!r} — "
                    f"must be one of {sorted(HARVEST_MODE_VALUES)}"
                )
            if check.get("targets") is None:
                findings.append(
                    f"component '{component_label}': checks[{index}]: 'dlq' "
                    f"check requires 'targets' — each target needs "
                    f"'subscription' and 'function'"
                )
        elif check_type == "queue-stalled":
            if check.get("targets") is None:
                findings.append(
                    f"component '{component_label}': checks[{index}]: "
                    f"'queue-stalled' check requires 'targets' — each target "
                    f"needs 'subscription' and 'function'"
                )
        elif check_type == "invariant":
            for field in ("query", "fingerprint_by"):
                if not check.get(field):
                    findings.append(
                        f"component '{component_label}': checks[{index}]: "
                        f"'invariant' check missing '{field}'"
                    )

        findings.extend(
            _check_targets(check.get("targets"), check_type, component_label, index)
        )

    return findings


# Per check-type target coordinates: the fields a `targets[]` entry must
# carry. `error-logs` and `http-5xx` are absent from this map on purpose —
# they are role-name keyed and therefore genuinely component-scoped; see
# `_TARGETLESS_CHECK_TYPES` below.
_TARGET_REQUIRED_FIELDS = {
    "dlq": ("subscription", "function"),
    "heartbeat": ("name",),
    "queue-stalled": ("subscription", "function"),
}
# Check types that must never carry `targets` at all.
_TARGETLESS_CHECK_TYPES = frozenset({"error-logs", "http-5xx", "invariant"})


def _check_targets(
    targets: object, check_type: str, component_label: str, check_index: int
) -> list[str]:
    """Validate an optional `checks[].targets` list.

    Structural only, per T01's scope: a target's required coordinates must
    be present, but coordinate *contents* are opaque — `timezone` and
    `invariant.query` are never parsed here. FEAT-2026-0040/T04 moved one
    line of that opacity: a `heartbeat` target's `cron` *field count* is now
    checked against its declared `dialect` (see `CRON_DIALECTS`), because a
    heartbeat check computing "should this have fired?" must interpret the
    expression's arity to do its job — the one coordinate whose contents a
    check type is required to interpret. `cron`'s field *values* stay
    opaque; only the field *count* is checked. `timezone` and
    `invariant.query` are untouched by this and remain fully opaque.
    `targets` itself is required for `dlq` and `queue-stalled` (enforced in
    `_check_checks`, since a missing key and an empty/malformed one are
    different findings). `error-logs`, `http-5xx`, and `invariant` must not
    carry `targets` at all; every other check type treats `targets` as
    optional.
    """
    if targets is None:
        return []

    where = f"component '{component_label}': checks[{check_index}]"

    if check_type in _TARGETLESS_CHECK_TYPES:
        return [f"{where}: '{check_type}' check must not carry 'targets'"]

    if not isinstance(targets, list):
        return [f"{where}: 'targets' must be a list"]

    if not targets:
        return [f"{where}: 'targets' must not be empty — omit the key for \"none\""]

    required_fields = _TARGET_REQUIRED_FIELDS.get(check_type, ())
    findings: list[str] = []
    for t_index, target in enumerate(targets):
        if not isinstance(target, dict):
            findings.append(
                f"{where}: targets[{t_index}]: must be a mapping"
            )
            continue
        for field in required_fields:
            if not target.get(field):
                findings.append(
                    f"{where}: targets[{t_index}]: '{check_type}' target "
                    f"missing '{field}'"
                )
        if check_type == "heartbeat":
            findings.extend(_check_cron_dialect(target, where, t_index))
    return findings


def _check_cron_dialect(target: dict, where: str, t_index: int) -> list[str]:
    """Enforce the four cron-dialect rules on one `heartbeat` target.

    1. `cron` without `dialect` is a finding.
    2. `dialect` outside `CRON_DIALECTS` is a finding.
    3. Given a valid `dialect` and a `cron`, the expression's
       whitespace-separated field count must equal the dialect's arity.
    4. `dialect` without `cron` is a finding — a declared dialect for no
       expression means the expression was dropped, not that dialect means
       nothing.
    """
    cron = target.get("cron")
    dialect = target.get("dialect")
    findings: list[str] = []

    if cron and not dialect:
        findings.append(
            f"{where}: targets[{t_index}]: 'heartbeat' target carries 'cron' "
            f"but no 'dialect' — must be one of {sorted(CRON_DIALECTS)}"
        )
    elif dialect and not cron:
        findings.append(
            f"{where}: targets[{t_index}]: 'dialect' declared without 'cron' "
            f"— a dialect with no expression is not valid"
        )

    if dialect:
        if dialect not in CRON_DIALECTS:
            findings.append(
                f"{where}: targets[{t_index}]: 'dialect' has unknown value "
                f"{dialect!r} — must be one of {sorted(CRON_DIALECTS)}"
            )
        elif cron:
            arity = CRON_DIALECTS[dialect]
            field_count = len(str(cron).split())
            if field_count != arity:
                findings.append(
                    f"{where}: targets[{t_index}]: 'cron' expression has "
                    f"{field_count} field(s), dialect {dialect!r} requires "
                    f"{arity}"
                )

    return findings


def main() -> int:
    import argparse

    from specfuse.loop.build_provenance import warn_if_out_of_tree
    warn_if_out_of_tree()

    parser = argparse.ArgumentParser(
        description="Specfuse monitoring-schema linter.",
        usage="lint_monitoring.py [path/to/monitoring.yml]",
    )
    parser.add_argument(
        "path", nargs="?", default=None,
        help="Path to monitoring.yml (default .specfuse/monitoring.yml). "
             "An absent file is not an error.",
    )
    args = parser.parse_args()
    findings = validate_monitoring(args.path)
    if findings:
        print(f"FAIL — {len(findings)} finding(s):")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("OK — monitoring config is structurally valid (or absent).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
