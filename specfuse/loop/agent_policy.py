#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""
Specfuse agent-policy schema linter.

Validates a project's ``.specfuse/agent-policy.yml`` structurally: the
operator's priorities for what the loop works on (bug/feature queue order,
gate-review dial per feature, triage automation dial) and its budgets and
escalation contact points.

Sibling of ``lint_monitoring.py`` (unrelated schema, not an extension of it)
and, like it, parses only with ``_miniyaml`` — the package has zero runtime
dependencies. Deliberately not imported by and not importing
``lint_monitoring`` — two validators over unrelated schemas sharing a helper
couples them for no gain (``[FEAT-2026-0072/T01]`` precedent).

Unlike monitoring, an agent-policy file is NOT opt-in structurally at the
schema level — every required top-level key must be present in whatever file
is handed to the validator. (Whether the *live* ``.specfuse/agent-policy.yml``
existing at all is itself optional is a decision for the caller, e.g. T03's
triage wiring; this module only validates files that are handed to it.)

Exit 0 = clean, 1 = an ERROR finding is present (WARN-only is still exit 0).

Usage:  lint_agent_policy.py [path/to/agent-policy.yml]
"""

from __future__ import annotations

import re
from pathlib import Path

from . import _miniyaml
from .lint_roadmap import roadmap_statuses

__all__ = (
    "load_policy",
    "validate_agent_policy",
    "main",
    "SEVERITY_VALUES",
    "AUTOMERGE_VALUES",
    "GATE_REVIEW_VALUES",
)

_DONE_OR_ABANDONED = frozenset({"done", "abandoned"})

SEVERITY_VALUES = frozenset({"low", "medium", "high", "critical"})
AUTOMERGE_VALUES = frozenset({"off", "on"})
GATE_REVIEW_VALUES = frozenset({"human", "auto"})

REQUIRED_TOP_LEVEL_FIELDS = ("version", "queue", "rules", "budgets", "escalation")

_FEAT_ID_RE = re.compile(r"^FEAT-\d{4}-\d{4}$")

_REQUIRED_BUDGET_FIELDS = ("max_tokens_per_run", "max_open_prs", "max_items_per_day")
_REQUIRED_ESCALATION_FIELDS = ("webhook", "assignee", "quiet_hours", "sla_hours")

_DEFAULT_PATH = Path(".specfuse/agent-policy.yml")


def load_policy(path: str | Path | None = None) -> dict:
    """Load and parse *path* (default ``.specfuse/agent-policy.yml``).

    Raises ``FileNotFoundError`` when the path is absent — a missing policy
    file and an empty queue are different declared states, and a caller must
    be able to tell them apart rather than receive silently-defaulted output.
    """
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.is_file():
        raise FileNotFoundError(f"{p}: agent-policy file does not exist")
    return _miniyaml.parse(p.read_text())


def validate_agent_policy(path: str | Path | None = None) -> list[str]:
    """Validate *path* (default ``.specfuse/agent-policy.yml``); return findings.

    Empty list means valid. A missing file, a parse failure, and a non-mapping
    top level are each reported as findings, never a silent ``[]``.
    """
    p = Path(path) if path is not None else _DEFAULT_PATH
    if not p.is_file():
        return [f"ERROR: {p}: file does not exist"]

    try:
        parsed = _miniyaml.parse(p.read_text())
    except _miniyaml.MiniYAMLError as exc:
        return [f"ERROR: {p}: could not parse as YAML: {exc}"]

    if not isinstance(parsed, dict):
        return [f"ERROR: {p}: top level must be a mapping"]

    findings: list[str] = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in parsed:
            findings.append(f"ERROR: missing top-level '{field}' key")

    unknown = set(parsed) - set(REQUIRED_TOP_LEVEL_FIELDS)
    for key in sorted(unknown):
        findings.append(f"ERROR: unknown top-level key '{key}'")

    if "version" in parsed:
        findings.extend(_check_version(parsed["version"]))
    if "queue" in parsed:
        findings.extend(_check_queue(parsed["queue"]))
    if "rules" in parsed:
        findings.extend(_check_rules(parsed["rules"]))
    if "budgets" in parsed:
        findings.extend(_check_budgets(parsed["budgets"]))
    if "escalation" in parsed:
        findings.extend(_check_escalation(parsed["escalation"]))

    if "queue" in parsed and isinstance(parsed["queue"], list):
        findings.extend(_check_queue_against_roadmap(parsed["queue"]))

    return findings


def _check_queue_against_roadmap(queue: list) -> list[str]:
    """Cross-check queue entries against roadmap.md's FEAT-ID status.

    ERROR when a queue entry has no roadmap row at all (unresolvable, a
    human must fix it). WARN when its status is done/abandoned (normal
    backlog evolution; /groom-backlog proposes removal). No finding for
    planned/active/blocked/deferred — deferred is a legitimate parked slot,
    per the roadmap's own status legend. Skipped without error when
    roadmap.md is absent, so a policy file may exist before a roadmap does.
    """
    statuses = roadmap_statuses()
    if not statuses:
        return []

    findings: list[str] = []
    for entry in queue:
        if not isinstance(entry, str) or not _FEAT_ID_RE.match(entry):
            continue
        status = statuses.get(entry)
        if status is None:
            findings.append(f"ERROR: queue: {entry!r} has no row in roadmap.md")
        elif status in _DONE_OR_ABANDONED:
            findings.append(
                f"WARN: queue: {entry!r} is roadmap status {status!r}"
            )
    return findings


def _check_version(version: object) -> list[str]:
    if version != 1:
        return [f"ERROR: 'version' must equal 1 (got {version!r})"]
    return []


def _check_queue(queue: object) -> list[str]:
    if not isinstance(queue, list):
        return ["ERROR: 'queue' must be a list of FEAT-YYYY-NNNN strings"]

    findings: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(queue):
        if not isinstance(entry, str) or not _FEAT_ID_RE.match(entry):
            findings.append(
                f"ERROR: queue[{index}]: {entry!r} does not match "
                f"FEAT-YYYY-NNNN"
            )
            continue
        if entry in seen:
            findings.append(f"ERROR: queue: duplicate entry {entry!r}")
        seen.add(entry)
    return findings


def _check_rules(rules: object) -> list[str]:
    if not isinstance(rules, dict):
        return ["ERROR: 'rules' must be a mapping"]

    findings: list[str] = []
    for section in ("bugs", "features", "triage"):
        if section not in rules:
            findings.append(f"ERROR: missing 'rules.{section}' key")

    if "bugs" in rules:
        findings.extend(_check_rules_bugs(rules["bugs"]))
    if "features" in rules:
        findings.extend(_check_rules_features(rules["features"]))
    if "triage" in rules:
        findings.extend(_check_rules_triage(rules["triage"]))
    return findings


def _check_rules_bugs(bugs: object) -> list[str]:
    if not isinstance(bugs, dict):
        return ["ERROR: 'rules.bugs' must be a mapping"]

    findings: list[str] = []
    preempt = bugs.get("preempt")
    if not isinstance(preempt, bool):
        findings.append(
            f"ERROR: 'rules.bugs.preempt' must be a bool (got {preempt!r})"
        )

    min_severity = bugs.get("min_severity")
    if min_severity not in SEVERITY_VALUES:
        findings.append(
            f"ERROR: 'rules.bugs.min_severity' has unknown value "
            f"{min_severity!r} — must be one of {sorted(SEVERITY_VALUES)}"
        )

    automerge = bugs.get("automerge")
    if automerge not in AUTOMERGE_VALUES:
        findings.append(
            f"ERROR: 'rules.bugs.automerge' has unknown value {automerge!r} "
            f"— must be one of {sorted(AUTOMERGE_VALUES)}"
        )
    return findings


def _check_rules_features(features: object) -> list[str]:
    if not isinstance(features, dict):
        return ["ERROR: 'rules.features' must be a mapping"]

    findings: list[str] = []
    gate_review = features.get("gate_review")
    if gate_review not in GATE_REVIEW_VALUES:
        findings.append(
            f"ERROR: 'rules.features.gate_review' has unknown value "
            f"{gate_review!r} — must be one of {sorted(GATE_REVIEW_VALUES)}"
        )

    wip_limit = features.get("wip_limit")
    if not isinstance(wip_limit, int) or isinstance(wip_limit, bool) or wip_limit < 1:
        findings.append(
            f"ERROR: 'rules.features.wip_limit' must be an int >= 1 "
            f"(got {wip_limit!r})"
        )

    if "overrides" in features:
        findings.extend(_check_feature_overrides(features["overrides"]))
    return findings


def _check_feature_overrides(overrides: object) -> list[str]:
    if not isinstance(overrides, dict):
        return ["ERROR: 'rules.features.overrides' must be a mapping"]

    findings: list[str] = []
    for feat_id, value in overrides.items():
        if not _FEAT_ID_RE.match(str(feat_id)):
            findings.append(
                f"ERROR: rules.features.overrides: key {feat_id!r} does not "
                f"match FEAT-YYYY-NNNN"
            )
        if value not in GATE_REVIEW_VALUES:
            findings.append(
                f"ERROR: rules.features.overrides[{feat_id!r}]: unknown "
                f"value {value!r} — must be one of {sorted(GATE_REVIEW_VALUES)}"
            )
    return findings


def _check_rules_triage(triage: object) -> list[str]:
    if not isinstance(triage, dict):
        return ["ERROR: 'rules.triage' must be a mapping"]

    auto = triage.get("auto")
    if not isinstance(auto, bool):
        return [f"ERROR: 'rules.triage.auto' must be a bool (got {auto!r})"]
    return []


def _check_budgets(budgets: object) -> list[str]:
    if not isinstance(budgets, dict):
        return ["ERROR: 'budgets' must be a mapping"]

    findings: list[str] = []
    for field in _REQUIRED_BUDGET_FIELDS:
        if field not in budgets:
            findings.append(f"ERROR: missing 'budgets.{field}' key")
            continue
        value = budgets[field]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            findings.append(
                f"ERROR: 'budgets.{field}' must be an int > 0 (got {value!r})"
            )
    return findings


def _check_escalation(escalation: object) -> list[str]:
    if not isinstance(escalation, dict):
        return ["ERROR: 'escalation' must be a mapping"]

    findings: list[str] = []
    for field in ("webhook", "assignee", "quiet_hours"):
        if field not in escalation:
            findings.append(f"ERROR: missing 'escalation.{field}' key")
            continue
        if not isinstance(escalation[field], str):
            findings.append(
                f"ERROR: 'escalation.{field}' must be a string "
                f"(got {escalation[field]!r})"
            )

    if "sla_hours" not in escalation:
        findings.append("ERROR: missing 'escalation.sla_hours' key")
    else:
        sla_hours = escalation["sla_hours"]
        if not isinstance(sla_hours, int) or isinstance(sla_hours, bool) or sla_hours <= 0:
            findings.append(
                f"ERROR: 'escalation.sla_hours' must be an int > 0 "
                f"(got {sla_hours!r})"
            )
    return findings


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Specfuse agent-policy schema linter.",
        usage="lint_agent_policy.py [path/to/agent-policy.yml]",
    )
    parser.add_argument(
        "path", nargs="?", default=None,
        help="Path to agent-policy.yml (default .specfuse/agent-policy.yml).",
    )
    args = parser.parse_args()
    findings = validate_agent_policy(args.path)
    for finding in findings:
        print(finding)
    return 1 if any(f.startswith("ERROR: ") for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
