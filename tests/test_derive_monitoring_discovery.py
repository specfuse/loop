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

Three pure functions:

  * `discover_components(tree, patterns)` — matches an injected
    evidence-pattern table against a `{relpath: content}` tree and returns
    sorted, neutral component records.
  * `suggest_checks(component)` — maps a neutral record to a conservative
    check list. Never emits `invariant` (its `query` is operator-supplied).
  * `audit_diagnosability(tree, components, patterns)` — WARN-only findings
    against `.specfuse/rules/design-for-diagnosis.md`'s four properties.

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
    """Match an evidence-pattern table against a repo tree.

    ``tree`` is a ``{relpath: content}`` mapping modelling a repo. ``patterns``
    is an injected table: ``patterns["components"]`` is a list of candidate
    descriptors, each ``{name, type, http_serving, message_consuming,
    evidence_markers}``. A candidate is only emitted if at least one file in
    the tree contains one of its markers; the matching relpaths become its
    evidence. Both the candidate list and each candidate's evidence relpaths
    are sorted, so a fixed input yields a fixed output sequence.
    """
    records = []
    for candidate in patterns.get("components", []):
        markers = candidate.get("evidence_markers", [])
        evidence = sorted(
            relpath
            for relpath, content in tree.items()
            if any(marker in content for marker in markers)
        )
        if not evidence:
            continue
        records.append({
            "name": candidate["name"],
            "type": candidate["type"],
            "http_serving": bool(candidate.get("http_serving")),
            "message_consuming": bool(candidate.get("message_consuming")),
            "evidence": evidence,
        })
    records.sort(key=lambda r: r["name"])
    return records


def suggest_checks(component: dict) -> list[dict]:
    """Map one neutral component record to a conservative check list.

    Every component gets ``heartbeat`` and ``error-logs``. An HTTP-serving
    component also gets ``http-5xx``; a message-consuming component also gets
    ``dlq`` with ``harvest_mode: peek``. ``invariant`` is never suggested —
    its ``query`` is operator-supplied by definition, so inventing one would
    be fabricating evidence.
    """
    checks = []
    if component.get("http_serving"):
        checks.append({"type": "http-5xx"})
    if component.get("message_consuming"):
        checks.append({"type": "dlq", "harvest_mode": "peek"})
    checks.append({"type": "heartbeat"})
    checks.append({"type": "error-logs"})
    return checks


def _finding(check: str, message: str) -> dict:
    return {"severity": "WARN", "check": check, "message": message}


def _any_marker_present(contents, markers) -> bool:
    return any(marker in content for content in contents for marker in markers)


def audit_diagnosability(tree: dict, components: list, patterns: dict) -> list[dict]:
    """Audit a tree against the four design-for-diagnosis properties.

    Every finding this function can emit carries severity ``WARN`` — there is
    no ``ERROR`` path (see ``AUDIT_SEVERITIES``). A populated codebase that
    predates the design-for-diagnosis rule violates it everywhere by
    construction, so an ``ERROR`` predicate would be unsatisfiable on real
    input.

    ``patterns["diagnosability"]`` supplies the injected marker vocabulary:
    ``correlation_id_markers``, ``structured_logging_markers``, and
    ``dlq_context_markers``. The per-component role-name property needs no
    marker table — it checks whether a component's own name string is
    stamped somewhere in its own evidence files.
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

    return findings


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
            "http_serving": True,
            "message_consuming": False,
            "evidence_markers": ["ACME_A_ROUTE_MARKER"],
        },
        {
            "name": "acme-order-worker",
            "type": "queue-consumer",
            "http_serving": False,
            "message_consuming": True,
            "evidence_markers": ["ACME_A_CONSUMER_MARKER"],
        },
    ],
    "diagnosability": {
        "correlation_id_markers": ["ACME_A_CORRELATION_ID_HEADER"],
        "structured_logging_markers": ["ACME_A_STRUCTURED_LOG_EVENT"],
        "dlq_context_markers": ["ACME_A_DLQ_FAILURE_CONTEXT"],
    },
}

_STACK_A_TREE = {
    "services/web/handler.txt": (
        "# acme-web-api request handler\n"
        "ACME_A_ROUTE_MARKER GET /orders\n"
        "acme-web-api\n"
        "ACME_A_CORRELATION_ID_HEADER propagated to downstream call\n"
        'ACME_A_STRUCTURED_LOG_EVENT {"event": "request.handled"}\n'
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
            "http_serving": True,
            "message_consuming": False,
            "evidence_markers": ["ACME_B_ENDPOINT_TAG"],
        },
        {
            "name": "acme-shipment-listener",
            "type": "queue-consumer",
            "http_serving": False,
            "message_consuming": True,
            "evidence_markers": ["ACME_B_SUBSCRIBER_TAG"],
        },
    ],
    "diagnosability": {
        "correlation_id_markers": ["ACME_B_TRACE_TOKEN"],
        "structured_logging_markers": ["ACME_B_LOG_RECORD"],
        "dlq_context_markers": ["ACME_B_DEADLETTER_CONTEXT"],
    },
}

_STACK_B_TREE = {
    "src/gateway/endpoint.txt": (
        "# acme-checkout-gateway endpoint definition\n"
        "ACME_B_ENDPOINT_TAG POST /checkout\n"
        "acme-checkout-gateway\n"
    ),
    "src/listener/subscriber.txt": (
        "# acme-shipment-listener subscriber\n"
        "ACME_B_SUBSCRIBER_TAG shipments.topic\n"
        "acme-shipment-listener\n"
    ),
    "NOTES.txt": "acme widget shipment backend, second stack\n",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


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
        self.assertEqual(web["evidence"], ["services/web/handler.txt"])

        worker = by_name["acme-order-worker"]
        self.assertEqual(worker["type"], "queue-consumer")
        self.assertFalse(worker["http_serving"])
        self.assertTrue(worker["message_consuming"])
        self.assertEqual(worker["evidence"], ["services/worker/consumer.txt"])


class TestOutputIsDeterministic(unittest.TestCase):
    """AC3: the same tree yields the identical record sequence every call."""

    def test_output_is_deterministic(self):
        first = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
        second = discover_components(_STACK_A_TREE, _STACK_A_PATTERNS)
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


if __name__ == "__main__":
    unittest.main()
