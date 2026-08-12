# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The repo-state snapshot the selector reads (FEAT-2026-0049/T02).

The agent has no database: every fact it acts on is either derivable from
GitHub, the roadmap, the policy file, and feature folders, or is safely
losable. `gather_snapshot` is the one place that collects those facts into
a single immutable `AgentSnapshot`, so the selector reads a value rather
than issuing calls mid-decision.

This is the first reader of `agent_policy.py`'s `queue:` key —
`validate_agent_policy` (`specfuse/loop/agent_policy.py:225`) checks it
against the roadmap and stops there; `/groom-backlog` writes it and nothing
has ever consumed it until now.

Every GitHub read goes through an injected `runner(argv, check=...)`,
following the convention `bug_lane_state.py`, `monitor/issues.py`, and
`autofix_state.py` already use: no direct `subprocess` call, so this module
is testable without a network. Only non-mutating `gh ... list` subcommands
are issued — this module performs no writes (no issue comment, no label, no
file) — the selection and the acting are different modules by design.

Reuses rather than reimplements: `agent_policy.load_policy` /
`resolve_triage_auto` / `resolve_bug_automerge` / `bug_lane_limits` for
policy, `triage.parse_marker` for the triage marker, and
`plan_baseline.load_plan_graph` + `lint_plan.read_frontmatter` (both public,
pre-existing readers under `specfuse/loop/`, consumed as-is per this WU's
Do-not-touch) for the feature-folder half — no `specfuse/loop/` file is
edited by this module.

A section whose `runner` call fails or returns unparseable output lands in
the snapshot as empty with its `*_error` field set to a reason, never as a
partial object that reads as authoritative (criterion 5). A repo with no
`.specfuse/agent-policy.yml` yields an empty queue and default dials, not an
exception (criterion 4) — `load_policy` already raises `FileNotFoundError`
for exactly this case; this module is the first caller that must let a
missing file be a normal, reportable state rather than a crash.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from specfuse.loop import agent_policy
from specfuse.loop.lint_plan import read_frontmatter
from specfuse.loop.plan_baseline import load_plan_graph
from specfuse.loop.triage import parse_marker

DEFAULT_ISSUE_LIST_LIMIT = 100
DEFAULT_PR_LIST_LIMIT = 100
_DEFAULT_FEATURES_ROOT = Path(".specfuse/features")


class _ReadFailure(Exception):
    """Internal: a `runner` call failed or returned unparseable output."""


@dataclass(frozen=True)
class IssueSummary:
    number: int
    title: str
    labels: tuple
    triage_category: Optional[str]
    triage_confidence: Optional[str]


@dataclass(frozen=True)
class PRSummary:
    number: int
    title: str
    labels: tuple
    #: The PR body, carried so a provider can tell whether an item it is
    #: about to work already has an open PR against it. `/fix-bug`'s hard
    #: contract is a `closes #<issue>` line in the body, so the body is the
    #: only place that linkage is readable from a listing. Defaults empty so
    #: a caller constructing a `PRSummary` by hand is unaffected.
    body: str = ""


@dataclass(frozen=True)
class GateSummary:
    gate: object
    status: Optional[str]


@dataclass(frozen=True)
class FeatureSummary:
    feature_id: str
    status: Optional[str]
    gates: tuple


@dataclass(frozen=True)
class AgentSnapshot:
    """Immutable repo-state snapshot. Every field is a value, not a call."""

    queue: tuple
    triage_auto: bool
    bug_automerge: bool
    bug_lane_limits: dict

    issues: tuple
    issues_error: Optional[str]

    prs: tuple
    prs_error: Optional[str]

    features: tuple
    features_errors: dict = field(default_factory=dict)


def _read_queue(policy_path: Optional[str]) -> tuple:
    """Return the ordered `queue:` list, or `()` when the policy file is
    absent, unparseable, or carries no list-typed `queue` key."""
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return ()
    if not isinstance(policy, dict):
        return ()
    queue = policy.get("queue")
    if not isinstance(queue, list):
        return ()
    return tuple(str(entry) for entry in queue)


def _read_dials(policy_path: Optional[str]) -> tuple:
    """Return `(triage_auto, bug_automerge, bug_lane_limits)`. Each resolver
    already defaults safely when the policy file is absent."""
    return (
        agent_policy.resolve_triage_auto(policy_path),
        agent_policy.resolve_bug_automerge(policy_path),
        agent_policy.bug_lane_limits(policy_path),
    )


def _run_json_list(runner: Callable, argv: list) -> list:
    """Run a `gh ... --json ...` listing command and return its parsed rows.

    Raises `_ReadFailure` on anything that would otherwise make this
    section's data untrustworthy: the runner itself raising, a non-zero
    exit, or output that is not parseable JSON.
    """
    try:
        result = runner(argv, check=False)
    except Exception as exc:  # noqa: BLE001 - any runner failure is a read failure
        raise _ReadFailure(f"runner raised: {exc}") from exc
    if result.returncode != 0:
        stderr = (getattr(result, "stderr", "") or "").strip()
        raise _ReadFailure(f"{' '.join(argv)} exited {result.returncode}: {stderr}")
    try:
        parsed = json.loads(result.stdout)
    except ValueError as exc:
        raise _ReadFailure(f"{' '.join(argv)} returned unparseable JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise _ReadFailure(f"{' '.join(argv)} returned non-list JSON: {parsed!r}")
    return parsed


def _to_issue_summary(raw: dict) -> IssueSummary:
    labels = tuple(
        entry.get("name", "") for entry in (raw.get("labels") or []) if isinstance(entry, dict)
    )
    marker = parse_marker(raw.get("body") or "")
    category, confidence = marker if marker is not None else (None, None)
    return IssueSummary(
        number=raw.get("number"),
        title=raw.get("title", ""),
        labels=labels,
        triage_category=category,
        triage_confidence=confidence,
    )


def _to_pr_summary(raw: dict) -> PRSummary:
    labels = tuple(
        entry.get("name", "") for entry in (raw.get("labels") or []) if isinstance(entry, dict)
    )
    return PRSummary(
        number=raw.get("number"),
        title=raw.get("title", ""),
        labels=labels,
        body=raw.get("body") or "",
    )


def _read_issues(runner: Callable, repo: str, *, limit: int) -> tuple:
    """Return `(issues, error)`. `issues` is `()` and `error` is set when the
    listing call fails; never a partial list read as complete."""
    try:
        raw = _run_json_list(
            runner,
            [
                "gh", "issue", "list",
                "--repo", repo,
                "--state", "open",
                "--limit", str(limit),
                "--json", "number,title,labels,body",
            ],
        )
    except _ReadFailure as exc:
        return (), str(exc)
    return tuple(_to_issue_summary(entry) for entry in raw), None


def _read_prs(runner: Callable, repo: str, *, limit: int) -> tuple:
    """Return `(prs, error)`, same contract as `_read_issues`."""
    try:
        raw = _run_json_list(
            runner,
            [
                "gh", "pr", "list",
                "--repo", repo,
                "--state", "open",
                "--limit", str(limit),
                "--json", "number,title,labels,body",
            ],
        )
    except _ReadFailure as exc:
        return (), str(exc)
    return tuple(_to_pr_summary(entry) for entry in raw), None


def _feature_summary(feature_dir: Path) -> FeatureSummary:
    plan_fm, _ = read_frontmatter(feature_dir / "PLAN.md")
    graph = load_plan_graph(feature_dir)
    gates = []
    for gate_entry in graph.get("gates") or []:
        gate_num = gate_entry.get("gate")
        gate_status = None
        gate_file = gate_entry.get("file")
        if gate_file:
            gate_path = feature_dir / gate_file
            if gate_path.is_file():
                gate_fm, _ = read_frontmatter(gate_path)
                gate_status = gate_fm.get("status")
        gates.append(GateSummary(gate=gate_num, status=gate_status))
    return FeatureSummary(
        feature_id=plan_fm.get("feature_id", feature_dir.name),
        status=plan_fm.get("status"),
        gates=tuple(gates),
    )


def read_feature_summaries(features_root: "Path | str") -> tuple:
    """Return `(features, errors)`. A feature folder whose `PLAN.md` cannot
    be parsed lands in `errors` keyed by directory name, never silently
    dropped and never allowed to abort the walk of the other folders —
    the same non-shrinking-denominator discipline `arm_sweep.py` uses.

    *features_root* is normalised here rather than at each call site (#1746).
    `FeatureProvider`'s no-argument fallback is the string
    `".specfuse/features"`, so requiring a `Path` made a bare
    `specfuse-agent run` — the invocation with no `--features-root` — raise
    `AttributeError` from inside `_select_next`, which is not wrapped in a
    per-provider guard and therefore ended the whole run. One normalisation
    point, at the boundary that actually touches the filesystem.
    """
    features_root = Path(features_root)
    if not features_root.is_dir():
        return (), {}
    features = []
    errors: dict = {}
    for feature_dir in sorted(p for p in features_root.iterdir() if p.is_dir()):
        if not (feature_dir / "PLAN.md").exists():
            continue
        try:
            features.append(_feature_summary(feature_dir))
        except Exception as exc:  # noqa: BLE001 - a malformed folder is a ledger entry
            errors[feature_dir.name] = f"{type(exc).__name__}: {exc}"
    return tuple(features), errors


_read_features = read_feature_summaries


def gather_snapshot(
    runner: Callable,
    repo: str,
    *,
    policy_path: Optional[str] = None,
    features_root: Optional[Path] = None,
    issue_limit: int = DEFAULT_ISSUE_LIST_LIMIT,
    pr_limit: int = DEFAULT_PR_LIST_LIMIT,
) -> AgentSnapshot:
    """Gather the one repo-state snapshot the selector reads.

    `runner` is called only with non-mutating `gh ... list` subcommands
    (`check=False`, so a failure is inspected here rather than raised) — this
    function performs no writes. `policy_path` defaults to
    `.specfuse/agent-policy.yml` (via `agent_policy.load_policy`'s own
    default) and `features_root` to `.specfuse/features`.
    """
    features_root = Path(features_root) if features_root is not None else _DEFAULT_FEATURES_ROOT

    queue = _read_queue(policy_path)
    triage_auto, bug_automerge, bug_lane_limits = _read_dials(policy_path)
    issues, issues_error = _read_issues(runner, repo, limit=issue_limit)
    prs, prs_error = _read_prs(runner, repo, limit=pr_limit)
    features, features_errors = _read_features(features_root)

    return AgentSnapshot(
        queue=queue,
        triage_auto=triage_auto,
        bug_automerge=bug_automerge,
        bug_lane_limits=bug_lane_limits,
        issues=issues,
        issues_error=issues_error,
        prs=prs,
        prs_error=prs_error,
        features=features,
        features_errors=features_errors,
    )
