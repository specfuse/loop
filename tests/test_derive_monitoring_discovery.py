#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0039/T05: component-discovery reference implementation + fixtures.

Reference implementation of the `derive-monitoring` skill's deterministic
core, exercised hermetically per the `test_roadmap_add_skill.py` /
`test_roadmap_archive_skill.py` pattern: the algorithm lives in this test
module (there is no `specfuse/loop/` production module for it on purpose —
the skill itself is prose, and this reference implementation is what its
method section points at), and fixtures are built in-test from an in-module manifest via `tempfile`,
never committed under `tests/fixtures/`.

Four pure functions:

  * `discover_components(tree, patterns)` — keys candidates on deployment
    evidence (`patterns["components"][*].deployment_markers` matched within
    each candidate's `scope_prefix`), then folds in `patterns["triggers"]`
    matched inside that same scope to derive `http_serving`,
    `message_consuming`, `subscriptions`, and `schedules`. Returns sorted,
    neutral component records — one per deployable, not one per trigger.
  * `suggest_checks(component)` — maps a neutral record to a conservative
    check list. Never emits `invariant` (its `query` is operator-supplied).
  * `audit_diagnosability(tree, components, patterns)` — WARN-only findings
    against `.specfuse/rules/design-for-diagnosis.md`'s five properties.
  * `audit_credential_reuse(tree, credential_names, patterns)` — WARN-only,
    heuristic: a monitoring credential env-var name the application itself
    reads (#254).

Provider-agnostic boundary (mirrors `test_design_for_diagnosis_rule.py`'s
posture and denylist): evidence patterns are an injected, stack-specific
*input*; the core below consumes the table and emits neutral records. A new
stack is a new pattern table, never a patch to the functions themselves.

AC5 mechanism note: the core lives between the ``# === CORE:BEGIN ===`` and
``# === CORE:END ===`` marker comments below. `test_core_names_no_stack_tokens`
locates that slice by those markers and scans only it — the fixture pattern
tables and fixture trees declared afterward are stack-specific by design and
are deliberately excluded from the scan, so a denylist hit there would not
give a false pass.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.lint_monitoring import validate_monitoring
from specfuse.loop import _miniyaml

# ============================================================================
# === CORE:BEGIN ===
#
# Deterministic, pure reference implementation. No framework, logging
# library, message-broker, or cloud-vendor identifier appears below this
# line until CORE:END — see test_core_names_no_stack_tokens.
# ============================================================================

AUDIT_SEVERITIES = frozenset({"WARN"})


def discover_components(tree: dict, patterns: dict) -> list[dict]:
    """Key candidates on deployment evidence, not on trigger registrations.

    ``tree`` is a ``{relpath: content}`` mapping modelling a repo. ``patterns``
    is an injected table: ``patterns["components"]`` is a list of candidate
    descriptors, each ``{name, type, deployment_markers, scope_prefix}``. A
    candidate is only emitted if a file whose relpath starts with its
    ``scope_prefix`` contains one of its ``deployment_markers`` — that file is
    the deployable's deployment evidence.

    ``patterns["triggers"]`` is a flat list of ``{marker, kind, ...}`` entries,
    ``kind`` one of ``http``, ``subscription``, ``schedule``. Every trigger is
    matched against files inside the emitted candidate's own scope only, in
    trigger-table order. A matched ``http`` trigger sets ``http_serving``; a
    matched ``subscription`` trigger sets ``message_consuming`` and appends a
    ``{subscription, function}`` entry to the record's ``subscriptions`` list;
    a matched ``schedule`` trigger appends a ``{name, cron, timezone, dialect}``
    entry to ``schedules``. ``http_serving`` and ``message_consuming`` are always
    derived from matched triggers, never read from the candidate.

    A record's ``evidence`` is its deployment file(s) plus every scoped file a
    trigger matched in, sorted and de-duplicated. The candidate list and each
    record's evidence are both sorted, so a fixed input yields a fixed output
    sequence.
    """
    records = []
    for candidate in patterns.get("components", []):
        scope_prefix = candidate.get("scope_prefix", "")
        deployment_markers = candidate.get("deployment_markers", [])
        deployment_evidence = {
            relpath
            for relpath, content in tree.items()
            if relpath.startswith(scope_prefix)
            and any(marker in content for marker in deployment_markers)
        }
        if not deployment_evidence:
            continue

        http_serving = False
        message_consuming = False
        subscriptions = []
        schedules = []
        trigger_evidence = set()

        for trigger in patterns.get("triggers", []):
            marker = trigger["marker"]
            kind = trigger["kind"]
            matched = [
                relpath
                for relpath, content in tree.items()
                if relpath.startswith(scope_prefix) and marker in content
            ]
            if not matched:
                continue
            trigger_evidence.update(matched)
            if kind == "http":
                http_serving = True
            elif kind == "subscription":
                message_consuming = True
                subscriptions.append({
                    "subscription": trigger["subscription"],
                    "function": trigger["function"],
                })
            elif kind == "schedule":
                schedules.append({
                    "name": trigger["name"],
                    "cron": trigger["cron"],
                    "timezone": trigger["timezone"],
                    "dialect": trigger["dialect"],
                })

        records.append({
            "name": candidate["name"],
            "type": candidate["type"],
            "http_serving": http_serving,
            "message_consuming": message_consuming,
            "subscriptions": subscriptions,
            "schedules": schedules,
            "evidence": sorted(deployment_evidence | trigger_evidence),
        })
    records.sort(key=lambda r: r["name"])
    return records


def suggest_checks(component: dict) -> list[dict]:
    """Map one neutral component record to a conservative check list.

    Every component gets ``heartbeat`` and ``error-logs``. An HTTP-serving
    component also gets ``http-5xx``. A message-consuming component gets
    ``dlq`` with ``harvest_mode: peek`` only if its record carries a
    non-empty neutral ``subscriptions`` list — each entry a real
    ``{subscription, function}`` pair known from discovery — rendered one
    ``dlq`` target per entry. A message-consuming component with no known
    subscriptions gets no ``dlq`` check at all: a target needs a real
    subscription and function, and inventing either would be fabricating
    evidence. ``heartbeat`` carries one target per entry in the record's
    neutral ``schedules`` list, each a real ``{name, cron, timezone, dialect}``
    entry known from discovery; a component with no known schedules gets a
    target-less ``heartbeat`` -- the same honesty rule ``dlq`` already
    follows. ``invariant`` is never suggested — its ``query`` is
    operator-supplied by definition, so inventing one would be fabricating
    evidence too.
    """
    checks = []
    if component.get("http_serving"):
        checks.append({"type": "http-5xx"})
    if component.get("message_consuming"):
        subscriptions = component.get("subscriptions") or []
        if subscriptions:
            checks.append({
                "type": "dlq",
                "harvest_mode": "peek",
                "targets": [
                    {"subscription": s["subscription"], "function": s["function"]}
                    for s in subscriptions
                ],
            })
    schedules = component.get("schedules") or []
    heartbeat = {"type": "heartbeat"}
    if schedules:
        heartbeat["targets"] = [
            {
                "name": s["name"],
                "cron": s["cron"],
                "timezone": s["timezone"],
                "dialect": s["dialect"],
            }
            for s in schedules
        ]
    checks.append(heartbeat)
    checks.append({"type": "error-logs"})
    return checks


def _finding(check: str, message: str) -> dict:
    return {"severity": "WARN", "check": check, "message": message}


def _any_marker_present(contents, markers) -> bool:
    return any(marker in content for content in contents for marker in markers)


def audit_diagnosability(tree: dict, components: list, patterns: dict) -> list[dict]:
    """Audit a tree against the five design-for-diagnosis properties.

    Every finding this function can emit carries severity ``WARN`` — there is
    no ``ERROR`` path (see ``AUDIT_SEVERITIES``). A populated codebase that
    predates the design-for-diagnosis rule violates it everywhere by
    construction, so an ``ERROR`` predicate would be unsatisfiable on real
    input.

    ``patterns["diagnosability"]`` supplies the injected marker vocabulary:
    ``correlation_id_markers``, ``structured_logging_markers``, and
    ``dlq_context_markers``, and ``heartbeat_emission_markers``. The
    per-component role-name property needs no marker table — it checks
    whether a component's own name string is stamped somewhere in its own
    evidence files. The heartbeat-emission property (#3470) is likewise
    per-component: a component with discovered ``schedules`` (so
    ``suggest_checks`` gives it heartbeat targets) must show a heartbeat
    emission marker in its own evidence files.
    """
    diag = patterns.get("diagnosability", {})
    contents = list(tree.values())
    findings = []

    if not _any_marker_present(contents, diag.get("correlation_id_markers", [])):
        findings.append(_finding(
            "correlation-id-propagation",
            "no correlation-ID propagation evidence found across the tree",
        ))

    if not _any_marker_present(contents, diag.get("structured_logging_markers", [])):
        findings.append(_finding(
            "structured-logging",
            "no structured-logging evidence found across the tree",
        ))

    for component in components:
        name = component["name"]
        evidence = component.get("evidence", [])
        stamped = any(name in tree[relpath] for relpath in evidence if relpath in tree)
        if not stamped:
            findings.append(_finding(
                "role-names",
                f"component '{name}' does not stamp its own role name in its evidence",
            ))

    consuming = [c for c in components if c.get("message_consuming")]
    if consuming and not _any_marker_present(contents, diag.get("dlq_context_markers", [])):
        findings.append(_finding(
            "dlq-error-context",
            "no DLQ failure-context evidence found for message-consuming component(s)",
        ))

    emission_markers = diag.get("heartbeat_emission_markers", [])
    for component in components:
        if not component.get("schedules"):
            continue
        own = [tree[relpath] for relpath in component.get("evidence", []) if relpath in tree]
        if not _any_marker_present(own, emission_markers):
            findings.append(_finding(
                "heartbeat-emission",
                f"component '{component['name']}' gets heartbeat targets but "
                "its code emits no heartbeat event",
            ))

    return findings


CREDENTIAL_REUSE_EXCLUDED_PREFIXES = (".specfuse/",)
SECRETS_CHECKLIST = ".specfuse/monitoring-secrets-checklist.md"


def suggest_monitor_only_name(name: str) -> str:
    """A distinct name for a separately provisioned, monitor-only credential."""
    return "MONITOR_" + name.replace("__", "_").upper()


def _json_path_line(text: str, path: list) -> int | None:
    """1-based line of ``path``'s leaf key in a JSON document, or None.

    Key lookup is case-insensitive, matching hierarchical configuration
    binders that treat ``Section:Key`` paths that way.
    """
    try:
        node = json.loads(text)
    except ValueError:
        return None
    for key in path:
        if not isinstance(node, dict):
            return None
        match = next((k for k in node if k.lower() == key.lower()), None)
        if match is None:
            return None
        node = node[match]
    lines = text.splitlines()
    start = 0
    for key in path:
        needle = f'"{key.lower()}"'
        found = next(
            (i for i in range(start, len(lines)) if needle in lines[i].lower()), None
        )
        if found is None:
            return None
        start = found
    return start + 1


def audit_credential_reuse(tree: dict, credential_names: list, patterns: dict) -> list[dict]:
    """#254: flag monitoring credential names the application itself reads.

    A heuristic over repo text: a credential env-var name counts as an
    application read when it appears as a whole token on any line outside the
    monitoring scaffold (``CREDENTIAL_REUSE_EXCLUDED_PREFIXES``) — code env
    reads, ``.env`` files, container/deployment ``env`` blocks and
    infrastructure app settings all spell the name verbatim. A ``Section__Key``
    name additionally matches the ``Section`` -> ``Key`` path in the
    hierarchical config files named by
    ``patterns["credential_reuse"]["hierarchical_config_suffixes"]``. Indirect
    reads (a name built at runtime, a prefix-stripping config provider) are
    missed by construction.

    Every finding is ``WARN``: a project that predates the advice reuses its
    application credentials by construction.
    """
    cfg = patterns.get("credential_reuse", {})
    suffixes = tuple(cfg.get("hierarchical_config_suffixes", []))
    findings = []
    for name in sorted(set(credential_names)):
        token = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])")
        path = name.split("__") if "__" in name else None
        evidence = []
        for relpath in sorted(tree):
            if relpath.startswith(CREDENTIAL_REUSE_EXCLUDED_PREFIXES):
                continue
            text = tree[relpath]
            for lineno, line in enumerate(text.splitlines(), start=1):
                if token.search(line):
                    evidence.append(f"{relpath}:{lineno}")
            if path and suffixes and relpath.endswith(suffixes):
                lineno = _json_path_line(text, path)
                if lineno is not None:
                    evidence.append(f"{relpath}:{lineno}")
        if not evidence:
            continue
        suggested = suggest_monitor_only_name(name)
        finding = _finding(
            "credential-reuse",
            f"credential '{name}' is also read by the application "
            f"({', '.join(evidence)}); provision a separate read-only "
            f"credential under a monitor-only name such as '{suggested}' "
            f"(see {SECRETS_CHECKLIST})",
        )
        finding.update({"credential": name, "evidence": evidence, "suggested_name": suggested})
        findings.append(finding)
    return findings


def _render_target_value(key: str, value: object) -> object:
    """Quote a `cron` target value, matching the shipped example's spelling.

    `_miniyaml` parses the unquoted spelling correctly too — this is not a
    parser fix, it keeps this reference implementation's output
    byte-comparable with `.specfuse/monitoring.yml.example`.
    """
    if key == "cron":
        return f'"{value}"'
    return value


def render_monitoring_yml(components_with_checks: list[dict]) -> str:
    """Render a complete ``monitoring.yml`` text from rendered components.

    Each item is ``{name, type, checks}`` (the ``checks`` shape returned by
    ``suggest_checks``). One placeholder environment supplies the required
    ``telemetry``/``broker`` provider bindings. ``autofix`` is emitted quoted
    (``"off"``) — ``_miniyaml`` rejects the bare ``off``/`on` spellings as
    forbidden boolean-like tokens.
    """
    lines = [
        "environments:",
        "  staging:",
        "    telemetry:",
        "      provider: acme-telemetry",
        "      credentials:",
        "        api_key: ACME_TELEMETRY_STAGING_API_KEY",
        "    broker:",
        "      provider: acme-broker",
        "      credentials:",
        "        connection_string: ACME_BROKER_STAGING_CONNECTION_STRING",
        "",
        "components:",
    ]
    for component in components_with_checks:
        lines.append(f"  - name: {component['name']}")
        lines.append(f"    type: {component['type']}")
        lines.append("    runner: local")
        lines.append("    diagnose: manual")
        lines.append('    autofix: "off"')
        lines.append("    checks:")
        for check in component["checks"]:
            lines.append(f"      - type: {check['type']}")
            for key, value in check.items():
                if key == "type":
                    continue
                if key == "targets":
                    lines.append("        targets:")
                    for target in value:
                        items = list(target.items())
                        first_key, first_value = items[0]
                        first_value = _render_target_value(first_key, first_value)
                        lines.append(f"          - {first_key}: {first_value}")
                        for t_key, t_value in items[1:]:
                            t_value = _render_target_value(t_key, t_value)
                            lines.append(f"            {t_key}: {t_value}")
                    continue
                lines.append(f"        {key}: {value}")
    return "\n".join(lines) + "\n"


# ============================================================================
# === CORE:END ===
# ============================================================================


# ---------------------------------------------------------------------------
# Fixture pattern tables (stack-specific inputs — excluded from the
# no-stack-tokens scan by construction; see test_core_names_no_stack_tokens).
# ---------------------------------------------------------------------------

# Same posture and denylist as test_design_for_diagnosis_rule.py's
# _STACK_TOKEN_DENYLIST — kept identical across the feature's two boundary
# tests rather than redrafted here.
_STACK_TOKEN_DENYLIST = (
    "aws",
    "gcp",
    "azure",
    "kubernetes",
    "kafka",
    "rabbitmq",
    "datadog",
    "splunk",
    "elasticsearch",
    "prometheus",
    "grafana",
    "sentry",
    "django",
    "flask",
    "express",
    "spring",
    "log4j",
    "winston",
    "opentelemetry",
)

# --- Stack A: two components, http-serving + message-consuming ------------

_STACK_A_PATTERNS = {
    "components": [
        {
            "name": "acme-web-api",
            "type": "http-service",
            "deployment_markers": ["ACME_A_DEPLOY_MARKER"],
            "scope_prefix": "services/web/",
        },
        {
            "name": "acme-order-worker",
            "type": "queue-consumer",
            "deployment_markers": ["ACME_A_WORKER_DEPLOY_MARKER"],
            "scope_prefix": "services/worker/",
        },
    ],
    "triggers": [
        {"marker": "ACME_A_ROUTE_MARKER", "kind": "http"},
        {
            "marker": "ACME_A_CONSUMER_MARKER",
            "kind": "subscription",
            "subscription": "acme-orders-queue-sub",
            "function": "ProcessOrder",
        },
    ],
    "diagnosability": {
        "correlation_id_markers": ["ACME_A_CORRELATION_ID_HEADER"],
        "structured_logging_markers": ["ACME_A_STRUCTURED_LOG_EVENT"],
        "dlq_context_markers": ["ACME_A_DLQ_FAILURE_CONTEXT"],
    },
}

_STACK_A_TREE = {
    "services/web/deploy.txt": (
        "# acme-web-api deployment\n"
        "ACME_A_DEPLOY_MARKER helm chart\n"
        "acme-web-api\n"
    ),
    "services/web/handler.txt": (
        "# acme-web-api request handler\n"
        "ACME_A_ROUTE_MARKER GET /orders\n"
        "acme-web-api\n"
        "ACME_A_CORRELATION_ID_HEADER propagated to downstream call\n"
        'ACME_A_STRUCTURED_LOG_EVENT {"event": "request.handled"}\n'
    ),
    "services/worker/deploy.txt": (
        "# acme-order-worker deployment\n"
        "ACME_A_WORKER_DEPLOY_MARKER helm chart\n"
        "acme-order-worker\n"
    ),
    "services/worker/consumer.txt": (
        "# acme-order-worker message consumer\n"
        "ACME_A_CONSUMER_MARKER orders.queue\n"
        "acme-order-worker\n"
        "ACME_A_DLQ_FAILURE_CONTEXT attempt=3\n"
    ),
    "README.txt": "acme widget backend\n",
}

# --- Stack B: same shape, entirely different marker vocabulary and names --
# (AC4 boundary — proves discover_components absorbed no stack knowledge)

_STACK_B_PATTERNS = {
    "components": [
        {
            "name": "acme-checkout-gateway",
            "type": "http-service",
            "deployment_markers": ["ACME_B_DEPLOY_TAG"],
            "scope_prefix": "src/gateway/",
        },
        {
            "name": "acme-shipment-listener",
            "type": "queue-consumer",
            "deployment_markers": ["ACME_B_LISTENER_DEPLOY_TAG"],
            "scope_prefix": "src/listener/",
        },
    ],
    "triggers": [
        {"marker": "ACME_B_ENDPOINT_TAG", "kind": "http"},
        {
            "marker": "ACME_B_SUBSCRIBER_TAG",
            "kind": "subscription",
            "subscription": "shipments-topic-sub",
            "function": "ProcessShipment",
        },
    ],
    "diagnosability": {
        "correlation_id_markers": ["ACME_B_TRACE_TOKEN"],
        "structured_logging_markers": ["ACME_B_LOG_RECORD"],
        "dlq_context_markers": ["ACME_B_DEADLETTER_CONTEXT"],
    },
}

_STACK_B_TREE = {
    "src/gateway/deploy.txt": (
        "# acme-checkout-gateway deployment\n"
        "ACME_B_DEPLOY_TAG helm chart\n"
        "acme-checkout-gateway\n"
    ),
    "src/gateway/endpoint.txt": (
        "# acme-checkout-gateway endpoint definition\n"
        "ACME_B_ENDPOINT_TAG POST /checkout\n"
        "acme-checkout-gateway\n"
    ),
    "src/listener/deploy.txt": (
        "# acme-shipment-listener deployment\n"
        "ACME_B_LISTENER_DEPLOY_TAG helm chart\n"
        "acme-shipment-listener\n"
    ),
    "src/listener/subscriber.txt": (
        "# acme-shipment-listener subscriber\n"
        "ACME_B_SUBSCRIBER_TAG shipments.topic\n"
        "acme-shipment-listener\n"
    ),
    "NOTES.txt": "acme widget shipment backend, second stack\n",
}

# --- Stack C: one deployable, 3 subscription triggers + 2 schedule triggers.
#
# Proves: the algorithm fans an N-cardinality trigger table (N > 1 on both
# kinds) into one component with N targets per check type — GATE-02.md's
# definition of done. Does NOT prove: that real repos let those coordinates
# be extracted from source without asking the operator — confirmed only
# outside this tree; see RETROSPECTIVE.md's "What the loop did NOT verify".

_STACK_C_PATTERNS = {
    "components": [
        {
            "name": "acme-functions-host",
            "type": "multi-trigger-host",
            "deployment_markers": ["ACME_C_DEPLOY_MARKER"],
            "scope_prefix": "host/",
        },
    ],
    "triggers": [
        {
            "marker": "ACME_C_SUB_ONE_MARKER",
            "kind": "subscription",
            "subscription": "acme-orders-created-sub",
            "function": "ProcessOrderCreated",
        },
        {
            "marker": "ACME_C_SUB_TWO_MARKER",
            "kind": "subscription",
            "subscription": "acme-orders-cancelled-sub",
            "function": "ProcessOrderCancelled",
        },
        {
            "marker": "ACME_C_SUB_THREE_MARKER",
            "kind": "subscription",
            "subscription": "acme-inventory-sync-sub",
            "function": "SyncInventoryLevels",
        },
        {
            "marker": "ACME_C_TIMER_ONE_MARKER",
            "kind": "schedule",
            "name": "acme-nightly-reconciliation",
            "cron": "0 2 * * *",
            "timezone": "Etc/UTC",
            "dialect": "standard-5",
        },
        {
            "marker": "ACME_C_TIMER_TWO_MARKER",
            "kind": "schedule",
            "name": "acme-hourly-cache-warm",
            "cron": "0 * * * *",
            "timezone": "Etc/UTC",
            "dialect": "standard-5",
        },
    ],
}

_STACK_C_TREE = {
    "host/deploy.txt": (
        "# acme-functions-host deployment\n"
        "ACME_C_DEPLOY_MARKER helm chart\n"
        "acme-functions-host\n"
    ),
    "host/sub_one.txt": "ACME_C_SUB_ONE_MARKER queue subscription\n",
    "host/sub_two.txt": "ACME_C_SUB_TWO_MARKER queue subscription\n",
    "host/sub_three.txt": "ACME_C_SUB_THREE_MARKER queue subscription\n",
    "host/timer_one.txt": "ACME_C_TIMER_ONE_MARKER nightly timer\n",
    "host/timer_two.txt": "ACME_C_TIMER_TWO_MARKER hourly timer\n",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDeploymentKeyedDiscovery(unittest.TestCase):
    """T06 AC1/AC5: one deployment artifact plus two trigger registrations
    inside its scope is one component, not one per trigger."""

    _PATTERNS = {
        "components": [
            {
                "name": "acme-functions-host",
                "type": "functions-host",
                "deployment_markers": ["ACME_T06_DEPLOY_MARKER"],
                "scope_prefix": "host/",
            },
        ],
        "triggers": [
            {
                "marker": "ACME_T06_SUB_MARKER",
                "kind": "subscription",
                "subscription": "acme-t06-sub",
                "function": "HandleOne",
            },
            {
                "marker": "ACME_T06_TIMER_MARKER",
                "kind": "schedule",
                "name": "acme-t06-timer",
                "cron": "0 * * * *",
                "timezone": "UTC",
                "dialect": "standard-5",
            },
        ],
    }

    _TREE = {
        "host/deploy.txt": "ACME_T06_DEPLOY_MARKER helm chart\nacme-functions-host\n",
        "host/sub_trigger.txt": "ACME_T06_SUB_MARKER queue subscription\n",
        "host/timer_trigger.txt": "ACME_T06_TIMER_MARKER hourly timer\n",
    }

    def test_one_deployable_with_two_triggers_is_one_component(self):
        components = discover_components(self._TREE, self._PATTERNS)
        self.assertEqual(len(components), 1)


class TestDiscoveredConfigPassesLint(unittest.TestCase):
    """AC1: discovery + suggestion output satisfies gate 1's validator."""

    def test_discovered_config_passes_lint_monitoring(self):
        components = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        rendered = [
            {"name": c["name"], "type": c["type"], "checks": suggest_checks(c)}
            for c in components
        ]
        text = render_monitoring_yml(rendered)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "monitoring.yml"
            path.write_text(text)
            findings = validate_monitoring(path)
        self.assertEqual(findings, [], f"unexpected findings: {findings}")


class TestFixtureTreeYieldsExpectedComponents(unittest.TestCase):
    """AC2: a stylized two-component fixture yields exactly the two records."""

    def test_fixture_tree_yields_expected_components(self):
        components = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        self.assertEqual(len(components), 2)

        by_name = {c["name"]: c for c in components}
        self.assertIn("acme-web-api", by_name)
        self.assertIn("acme-order-worker", by_name)

        web = by_name["acme-web-api"]
        self.assertEqual(web["type"], "http-service")
        self.assertTrue(web["http_serving"])
        self.assertFalse(web["message_consuming"])
        self.assertEqual(
            web["evidence"], ["services/web/deploy.txt", "services/web/handler.txt"]
        )

        worker = by_name["acme-order-worker"]
        self.assertEqual(worker["type"], "queue-consumer")
        self.assertFalse(worker["http_serving"])
        self.assertTrue(worker["message_consuming"])
        self.assertEqual(
            worker["evidence"],
            ["services/worker/consumer.txt", "services/worker/deploy.txt"],
        )


class TestOutputIsDeterministic(unittest.TestCase):
    """AC3: the same tree yields the identical record sequence every call."""

    def test_output_is_deterministic(self):
        first = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        second = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        self.assertTrue(first)
        self.assertEqual(first, second)


class TestNeutralRecordsSurviveASecondStack(unittest.TestCase):
    """AC4 boundary test: a second, differently-named stack yields
    structurally identical neutral records — same types, same dials, same
    suggested check types — differing only in names and evidence paths."""

    @staticmethod
    def _signature(record):
        return (
            record["type"],
            record["http_serving"],
            record["message_consuming"],
            tuple(sorted(c["type"] for c in suggest_checks(record))),
        )

    def test_neutral_records_survive_a_second_stack(self):
        stack_a = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        stack_b = discover_components(_STACK_B_TREE, _STACK_B_PATTERNS)

        self.assertEqual(len(stack_a), 2)
        self.assertEqual(len(stack_a), len(stack_b))

        sigs_a = sorted(self._signature(r) for r in stack_a)
        sigs_b = sorted(self._signature(r) for r in stack_b)
        self.assertEqual(sigs_a, sigs_b)

        names_a = {r["name"] for r in stack_a}
        names_b = {r["name"] for r in stack_b}
        self.assertEqual(names_a.isdisjoint(names_b), True)

        evidence_a = {ev for r in stack_a for ev in r["evidence"]}
        evidence_b = {ev for r in stack_b for ev in r["evidence"]}
        self.assertEqual(evidence_a.isdisjoint(evidence_b), True)

    def test_second_stacks_render_also_passes_lint(self):
        stack_b = discover_components(_STACK_B_TREE, _STACK_B_PATTERNS)
        rendered = [
            {"name": c["name"], "type": c["type"], "checks": suggest_checks(c)}
            for c in stack_b
        ]
        text = render_monitoring_yml(rendered)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "monitoring.yml"
            path.write_text(text)
            findings = validate_monitoring(path)
        self.assertEqual(findings, [], f"unexpected findings: {findings}")


class TestCoreNamesNoStackTokens(unittest.TestCase):
    """AC5 boundary test: the core functions' own source contains no
    framework/logging-library/cloud-vendor token from the denylist above.

    Mechanism: this test reads its own module source and slices the text
    strictly between the ``# === CORE:BEGIN ===`` and ``# === CORE:END ===``
    marker comments, then scans only that slice. The fixture pattern tables
    and trees declared below CORE:END are excluded by construction — they are
    stack-specific inputs by design, and scanning them too would let a real
    core violation hide behind a vacuous pass.
    """

    def test_core_names_no_stack_tokens(self):
        source = Path(__file__).read_text()
        begin = source.index("# === CORE:BEGIN ===")
        end = source.index("# === CORE:END ===")
        self.assertGreater(end, begin, "CORE markers out of order or missing")
        core_slice = source[begin:end].lower()

        hits = [tok for tok in _STACK_TOKEN_DENYLIST if tok in core_slice]
        self.assertEqual(hits, [], f"stack tokens leaked into core: {hits}")


class TestSuggestChecksNeverInvariant(unittest.TestCase):
    """AC8: suggest_checks never emits an invariant check — its query is
    operator-supplied by definition."""

    def test_no_invariant_for_http_component(self):
        component = {"name": "x", "type": "http-service",
                     "http_serving": True, "message_consuming": False}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("invariant", types)

    def test_no_invariant_for_queue_component(self):
        component = {"name": "y", "type": "queue-consumer",
                     "http_serving": False, "message_consuming": True}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("invariant", types)

    def test_no_invariant_for_plain_component(self):
        component = {"name": "z", "type": "batch-job",
                     "http_serving": False, "message_consuming": False}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("invariant", types)


class TestSuggestChecksNeverQueueStalled(unittest.TestCase):
    """T04 AC9: suggest_checks never emits queue-stalled — its stall
    threshold is operator judgement, the same class as invariant.query."""

    def test_no_queue_stalled_for_http_component(self):
        component = {"name": "x", "type": "http-service",
                     "http_serving": True, "message_consuming": False}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("queue-stalled", types)

    def test_no_queue_stalled_for_queue_component(self):
        component = {"name": "y", "type": "queue-consumer",
                     "http_serving": False, "message_consuming": True}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("queue-stalled", types)

    def test_no_queue_stalled_for_plain_component(self):
        component = {"name": "z", "type": "batch-job",
                     "http_serving": False, "message_consuming": False}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("queue-stalled", types)


class TestSuggestChecksHonestDlq(unittest.TestCase):
    """AC6/AC7: `dlq` targets come only from a neutral `subscriptions` list
    on the record, one target per entry; a message-consuming component with
    no known subscriptions gets no `dlq` check at all — never a fabricated
    placeholder target."""

    def test_message_consuming_without_subscriptions_gets_no_dlq_check(self):
        component = {"name": "worker", "type": "queue-consumer",
                     "http_serving": False, "message_consuming": True}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("dlq", types)

    def test_message_consuming_with_subscriptions_emits_one_target_per_entry(self):
        component = {
            "name": "worker", "type": "queue-consumer",
            "http_serving": False, "message_consuming": True,
            "subscriptions": [
                {"subscription": "orders-sub", "function": "ProcessOrder"},
                {"subscription": "refunds-sub", "function": "ProcessRefund"},
            ],
        }
        checks = suggest_checks(component)
        dlq_checks = [c for c in checks if c["type"] == "dlq"]
        self.assertEqual(len(dlq_checks), 1)
        self.assertEqual(dlq_checks[0]["harvest_mode"], "peek")
        self.assertEqual(dlq_checks[0]["targets"], [
            {"subscription": "orders-sub", "function": "ProcessOrder"},
            {"subscription": "refunds-sub", "function": "ProcessRefund"},
        ])

    def test_non_message_consuming_component_gets_no_dlq_check_regardless(self):
        component = {"name": "api", "type": "http-service",
                     "http_serving": True, "message_consuming": False,
                     "subscriptions": [{"subscription": "x", "function": "y"}]}
        types = {c["type"] for c in suggest_checks(component)}
        self.assertNotIn("dlq", types)


class TestHeartbeatTargetsFromSchedules(unittest.TestCase):
    """AC4/AC5: `heartbeat` targets come only from a neutral `schedules`
    list on the record, one target per entry; a component with no known
    schedules gets a target-less `heartbeat` — never an empty `targets`
    list and never a fabricated placeholder target."""

    def test_component_without_schedules_gets_a_targetless_heartbeat(self):
        component = {"name": "worker", "type": "queue-consumer",
                     "http_serving": False, "message_consuming": False}
        checks = suggest_checks(component)
        heartbeat_checks = [c for c in checks if c["type"] == "heartbeat"]
        self.assertEqual(len(heartbeat_checks), 1)
        self.assertNotIn("targets", heartbeat_checks[0])

    def test_component_with_schedules_emits_one_target_per_entry(self):
        component = {
            "name": "host", "type": "multi-trigger-host",
            "http_serving": False, "message_consuming": False,
            "schedules": [
                {"name": "nightly", "cron": "0 2 * * *", "timezone": "Etc/UTC",
                 "dialect": "standard-5"},
                {"name": "hourly", "cron": "0 * * * *", "timezone": "Etc/UTC",
                 "dialect": "standard-5"},
            ],
        }
        checks = suggest_checks(component)
        heartbeat_checks = [c for c in checks if c["type"] == "heartbeat"]
        self.assertEqual(len(heartbeat_checks), 1)
        self.assertEqual(heartbeat_checks[0]["targets"], [
            {"name": "nightly", "cron": "0 2 * * *", "timezone": "Etc/UTC",
             "dialect": "standard-5"},
            {"name": "hourly", "cron": "0 * * * *", "timezone": "Etc/UTC",
             "dialect": "standard-5"},
        ])


class TestRenderTargetsRoundTrip(unittest.TestCase):
    """AC8: nested `targets` list-of-mappings render at correct indentation
    and round-trip through `_miniyaml.parse` unchanged. Asserted on the
    parsed structure, not the rendered string."""

    def test_dlq_targets_round_trip_through_miniyaml(self):
        targets = [
            {"subscription": "orders-sub", "function": "ProcessOrder"},
            {"subscription": "refunds-sub", "function": "ProcessRefund"},
        ]
        rendered = [{
            "name": "worker",
            "type": "queue-consumer",
            "checks": [{"type": "dlq", "harvest_mode": "peek", "targets": targets}],
        }]
        text = render_monitoring_yml(rendered)
        parsed = _miniyaml.parse(text)
        dlq_check = parsed["components"][0]["checks"][0]
        self.assertEqual(dlq_check["targets"], targets)


class TestAuditFindingsAreAllWarn(unittest.TestCase):
    """AC6: every finding audit_diagnosability can emit is WARN; the
    function exposes no ERROR severity at all."""

    def test_audit_findings_are_all_warn(self):
        self.assertEqual(AUDIT_SEVERITIES, frozenset({"WARN"}))

        undiagnosable_tree = {"src/app.txt": "acme-undiagnosable-app plain text log\n"}
        components = [{
            "name": "acme-undiagnosable-app",
            "type": "http-service",
            "http_serving": True,
            "message_consuming": True,
            "evidence": ["src/app.txt"],
        }]
        findings = audit_diagnosability(undiagnosable_tree, components, _STACK_A_PATTERNS)
        self.assertTrue(findings, "expected at least one finding on an undiagnosable fixture")
        for finding in findings:
            self.assertIn(finding["severity"], AUDIT_SEVERITIES)
            self.assertEqual(finding["severity"], "WARN")


class TestAuditFiresOnAnUndiagnosableTree(unittest.TestCase):
    """AC7 (negative observation): a tree with no correlation-ID propagation
    and no structured logging produces a non-empty finding list naming both
    gaps."""

    def test_audit_fires_on_an_undiagnosable_tree(self):
        tree = {"src/app.txt": "acme-plain-app has no diagnosability evidence at all\n"}
        findings = audit_diagnosability(tree, [], _STACK_A_PATTERNS)
        checks_fired = {f["check"] for f in findings}
        self.assertIn("correlation-id-propagation", checks_fired)
        self.assertIn("structured-logging", checks_fired)


class TestAuditIsQuietOnADiagnosableTree(unittest.TestCase):
    """AC7 companion: zero findings on a fixture that satisfies all four
    properties, so the audit is proven not to fire on everything."""

    def test_audit_is_quiet_on_a_diagnosable_tree(self):
        tree = {
            "services/web/handler.txt": (
                "acme-web-api\n"
                "ACME_A_CORRELATION_ID_HEADER propagated end to end\n"
                'ACME_A_STRUCTURED_LOG_EVENT {"event": "request.handled"}\n'
            ),
            "services/worker/consumer.txt": (
                "acme-order-worker\n"
                "ACME_A_DLQ_FAILURE_CONTEXT attempt=1\n"
            ),
        }
        components = [
            {
                "name": "acme-web-api",
                "type": "http-service",
                "http_serving": True,
                "message_consuming": False,
                "evidence": ["services/web/handler.txt"],
            },
            {
                "name": "acme-order-worker",
                "type": "queue-consumer",
                "http_serving": False,
                "message_consuming": True,
                "evidence": ["services/worker/consumer.txt"],
            },
        ]
        findings = audit_diagnosability(tree, components, _STACK_A_PATTERNS)
        self.assertEqual(findings, [])


class TestAuditFlagsHeartbeatTargetsNothingEmits(unittest.TestCase):
    """#3470: a component that gets heartbeat targets but whose evidence
    emits no heartbeat event is a design-for-diagnosis gap — its heartbeat
    check would report every target as a silent schedule from its first
    run. A component that does emit, or that has no schedules, is quiet."""

    _PATTERNS = {
        **_STACK_C_PATTERNS,
        "diagnosability": {
            "correlation_id_markers": ["ACME_C_CORRELATION"],
            "structured_logging_markers": ["ACME_C_STRUCTURED_LOG"],
            "dlq_context_markers": ["ACME_C_DLQ_CONTEXT"],
            "heartbeat_emission_markers": ["ACME_C_HEARTBEAT_EMIT"],
        },
    }

    def _heartbeat_findings(self, tree):
        components = discover_components(tree, self._PATTERNS)
        self.assertTrue(components[0]["schedules"])
        findings = audit_diagnosability(tree, components, self._PATTERNS)
        return [f for f in findings if f["check"] == "heartbeat-emission"]

    def test_scheduled_component_without_emission_is_flagged(self):
        findings = self._heartbeat_findings(_STACK_C_TREE)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "WARN")
        self.assertIn("acme-functions-host", findings[0]["message"])

    def test_scheduled_component_that_emits_is_quiet(self):
        tree = dict(_STACK_C_TREE)
        tree["host/timer_one.txt"] += "ACME_C_HEARTBEAT_EMIT once per firing\n"
        self.assertEqual(self._heartbeat_findings(tree), [])

    def test_component_without_schedules_is_quiet(self):
        components = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        self.assertFalse(any(c["schedules"] for c in components))
        findings = audit_diagnosability(_STACK_A_TREE, components, _STACK_A_PATTERNS)
        self.assertNotIn("heartbeat-emission", {f["check"] for f in findings})


class TestAutofixQuotedInEmittedYaml(unittest.TestCase):
    """AC10: emitted YAML quotes autofix; round-trips through _miniyaml as
    the string "off"."""

    def test_autofix_round_trips_as_quoted_off_string(self):
        components = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        rendered = [
            {"name": c["name"], "type": c["type"], "checks": suggest_checks(c)}
            for c in components
        ]
        text = render_monitoring_yml(rendered)
        self.assertIn('autofix: "off"', text)
        parsed = _miniyaml.parse(text)
        for component in parsed["components"]:
            self.assertEqual(component["autofix"], "off")
            self.assertIsInstance(component["autofix"], str)


class TestOneDeployableManyTriggers(unittest.TestCase):
    """GATE-02.md's definition of done: a repo whose single deployable
    carries N triggers yields 1 component with N targets — not N
    components. Stack C carries 3 subscription triggers and 2 schedule
    triggers, so both trigger kinds have cardinality > 1 and a per-target
    assertion cannot be satisfied by accident.

    This proves the algorithm fans a trigger table into a target list; it
    does not prove real repositories are shaped so a trigger table can be
    built without asking the operator — see `_STACK_C_PATTERNS`'s own
    comment and RETROSPECTIVE.md's "What the loop did NOT verify"."""

    def test_single_deployable_with_n_triggers_yields_one_component_with_n_targets(self):
        components = discover_components(_STACK_C_TREE, _STACK_C_PATTERNS)
        self.assertEqual(len(components), 1)

        component = components[0]
        rendered = [{
            "name": component["name"],
            "type": component["type"],
            "checks": suggest_checks(component),
        }]
        checks = rendered[0]["checks"]

        dlq_checks = [c for c in checks if c["type"] == "dlq"]
        self.assertEqual(len(dlq_checks), 1)
        self.assertEqual(len(dlq_checks[0]["targets"]), 3)
        for target in dlq_checks[0]["targets"]:
            self.assertEqual(set(target), {"subscription", "function"})

        heartbeat_checks = [c for c in checks if c["type"] == "heartbeat"]
        self.assertEqual(len(heartbeat_checks), 1)
        self.assertEqual(len(heartbeat_checks[0]["targets"]), 2)
        for target in heartbeat_checks[0]["targets"]:
            self.assertEqual(set(target), {"name", "cron", "timezone", "dialect"})

        text = render_monitoring_yml(rendered)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "monitoring.yml"
            path.write_text(text)
            findings = validate_monitoring(path)
        self.assertEqual(findings, [], f"unexpected findings: {findings}")


# --- #254: credential reuse ------------------------------------------------

_SKILL_DIR = Path(__file__).parent.parent / "plugins" / "specfuse" / "skills" / "derive-monitoring"

_CREDENTIAL_REUSE_PATTERNS = {
    "credential_reuse": {
        "hierarchical_config_suffixes": ["appsettings.json", "appsettings.Production.json"],
    },
}

_CREDENTIAL_REUSE_TREE = {
    "src/app.py": (
        "import os\n"
        "\n"
        'conn = os.environ["ACME_BUS_CONNECTION_STRING"]\n'
        'other = os.environ["ACME_BUS_CONNECTION_STRING_V2"]\n'
    ),
    "deploy/.env": "ACME_BUS_CONNECTION_STRING=placeholder\n",
    "src/Api/appsettings.json": (
        "{\n"
        '  "Logging": {"LogLevel": {"Default": "Information"}},\n'
        '  "ApplicationInsights": {\n'
        '    "ConnectionString": ""\n'
        "  }\n"
        "}\n"
    ),
    ".specfuse/monitoring.yml": (
        "connection_string: ACME_BUS_CONNECTION_STRING\n"
        "api_key: ApplicationInsights__ConnectionString\n"
        "api_key: ACME_MONITOR_ONLY_KEY\n"
    ),
}

_CREDENTIAL_NAMES = [
    "ACME_BUS_CONNECTION_STRING",
    "ApplicationInsights__ConnectionString",
    "ACME_MONITOR_ONLY_KEY",
]


class TestCredentialReuseAudit(unittest.TestCase):
    """#254: a monitoring credential env-var name that the application itself
    reads is the application's credential, not a separately provisioned
    read-only one. The audit flags it WARN with file:line evidence and a
    suggested monitor-only name; a name only the monitoring files mention is
    quiet."""

    def _findings(self):
        return audit_credential_reuse(
            _CREDENTIAL_REUSE_TREE, _CREDENTIAL_NAMES, _CREDENTIAL_REUSE_PATTERNS
        )

    def _by_name(self):
        return {f["credential"]: f for f in self._findings()}

    def test_reused_names_are_flagged_warn(self):
        findings = self._findings()
        self.assertEqual(
            sorted(f["credential"] for f in findings),
            ["ACME_BUS_CONNECTION_STRING", "ApplicationInsights__ConnectionString"],
        )
        for finding in findings:
            self.assertEqual(finding["severity"], "WARN")
            self.assertIn(finding["severity"], AUDIT_SEVERITIES)
            self.assertEqual(finding["check"], "credential-reuse")

    def test_env_reads_carry_file_line_evidence(self):
        finding = self._by_name()["ACME_BUS_CONNECTION_STRING"]
        self.assertEqual(finding["evidence"], ["deploy/.env:1", "src/app.py:3"])

    def test_section_key_name_matches_hierarchical_config_path(self):
        finding = self._by_name()["ApplicationInsights__ConnectionString"]
        self.assertEqual(finding["evidence"], ["src/Api/appsettings.json:4"])

    def test_finding_suggests_a_monitor_only_name_and_the_checklist(self):
        for finding in self._findings():
            with self.subTest(credential=finding["credential"]):
                self.assertTrue(finding["suggested_name"].startswith("MONITOR_"))
                self.assertNotEqual(finding["suggested_name"], finding["credential"])
                self.assertIn(finding["suggested_name"], finding["message"])
                self.assertIn("monitoring-secrets-checklist.md", finding["message"])

    def test_monitoring_files_and_longer_names_do_not_count_as_reads(self):
        findings = audit_credential_reuse(
            {
                ".specfuse/monitoring.yml": "api_key: ACME_MONITOR_ONLY_KEY\n",
                "src/app.py": 'os.environ["ACME_MONITOR_ONLY_KEY_OLD"]\n',
            },
            ["ACME_MONITOR_ONLY_KEY"],
            _CREDENTIAL_REUSE_PATTERNS,
        )
        self.assertEqual(findings, [])


class TestSkillNamesTheCredentialReuseCheck(unittest.TestCase):
    """#254: the skill prose carries the check the reference implements, so
    the two cannot diverge silently."""

    def test_skill_and_prompt_name_credential_reuse(self):
        for name in ("SKILL.md", "PROMPT.md"):
            text = (_SKILL_DIR / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                self.assertIn("credential-reuse", text)
                self.assertIn("monitoring-secrets-checklist.md", text)
                self.assertIn("heuristic", text)


if __name__ == "__main__":
    unittest.main()
