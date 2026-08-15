# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Classify `queue:` entries as workable, and read `rules.features` dials
(FEAT-2026-0049/T12).

`AgentSnapshot` (`specfuse/agent/state.py`) already carries `queue:` and
`features`/`features_errors`; nothing has ever matched a queue entry against
a feature until this module. `classify_queue_entry` and `select_workable` do
that matching once, so gate 4's provider (T14) advertises against a rule
rather than re-deriving it.

`resolve_wip_limit` and `resolve_gate_review` read `rules.features.wip_limit`
and `rules.features.gate_review` (with `rules.features.overrides`), following
the safe-default shape `run._resolve_bugs_preempt` uses for `rules.bugs.preempt`:
an absent policy file, an absent key, or a wrong-typed value resolves to the
conservative default rather than raising.

This module does not re-implement the driver's arm check — a feature whose
first un-passed gate holds only `draft` work units is still `WORKABLE` here;
the driver itself answers that by exiting `2`, and the caller (T13/T14)
classifies that outcome. This module performs no write, issues no `gh` call,
and reads no work-unit file.
"""

from __future__ import annotations

from typing import Optional

from specfuse.loop import agent_policy

DISPOSITION_WORKABLE = "workable"
DISPOSITION_NEEDS_DRAFTING = "needs_drafting"
DISPOSITION_BLOCKED = "blocked"
DISPOSITION_DONE = "done"
DISPOSITION_UNREADABLE = "unreadable"

_BLOCKED_STATUSES = {"blocked", "deferred"}
_DONE_STATUSES = {"done", "abandoned"}
_WORKABLE_STATUSES = {"active", "planned"}

_DEFAULT_WIP_LIMIT = 1
_DEFAULT_GATE_REVIEW = "human"


def classify_queue_entry(entry: str, features: tuple, features_errors: dict) -> str:
    """Classify one `queue:` entry against the snapshot's feature state.

    Precedence: an unreadable folder (in `features_errors`) beats an absent
    one, because a folder that exists but failed to parse is
    indistinguishable from an absent one by `feature_id` alone — escalating
    it as "needs drafting" would tell the operator to draft a feature that
    already exists.
    """
    for dir_name in features_errors:
        if dir_name.startswith(entry):
            return DISPOSITION_UNREADABLE

    match = None
    for summary in features:
        if summary.feature_id == entry:
            match = summary
            break

    if match is None:
        return DISPOSITION_NEEDS_DRAFTING

    status = match.status
    if status in _BLOCKED_STATUSES:
        return DISPOSITION_BLOCKED
    if status in _DONE_STATUSES:
        return DISPOSITION_DONE
    if status in _WORKABLE_STATUSES:
        return DISPOSITION_WORKABLE
    return DISPOSITION_UNREADABLE


def select_workable(
    queue: tuple,
    features: tuple,
    features_errors: dict,
    *,
    wip_limit: int,
):
    """Return `(workable, needs_attention)`.

    `workable` is the `WORKABLE` entries in `queue:` order, capped at
    `wip_limit`. `needs_attention` is every non-`WORKABLE`, non-`DONE` entry
    paired with its disposition. `DONE` entries appear in neither list and
    consume no `wip_limit` slot.
    """
    workable = []
    needs_attention = []
    for entry in queue:
        disposition = classify_queue_entry(entry, features, features_errors)
        if disposition == DISPOSITION_WORKABLE:
            if len(workable) < wip_limit:
                workable.append(entry)
        elif disposition != DISPOSITION_DONE:
            needs_attention.append((entry, disposition))
    return tuple(workable), tuple(needs_attention)


def resolve_wip_limit(policy_path: Optional[str] = None) -> int:
    """Resolve `rules.features.wip_limit`. Absent file, absent key, or a
    wrong-typed value all resolve to `1`, never raising."""
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return _DEFAULT_WIP_LIMIT
    rules = policy.get("rules") if isinstance(policy, dict) else None
    if not isinstance(rules, dict):
        return _DEFAULT_WIP_LIMIT
    features = rules.get("features")
    if not isinstance(features, dict):
        return _DEFAULT_WIP_LIMIT
    wip_limit = features.get("wip_limit")
    if not isinstance(wip_limit, int) or isinstance(wip_limit, bool) or wip_limit < 1:
        return _DEFAULT_WIP_LIMIT
    return wip_limit


def resolve_gate_review(policy_path: Optional[str] = None, feature_id: Optional[str] = None) -> str:
    """Resolve `rules.features.gate_review`, honouring
    `rules.features.overrides[feature_id]` when present. Absent file, absent
    key, or a wrong-typed value all resolve to `"human"`, never raising."""
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return _DEFAULT_GATE_REVIEW
    rules = policy.get("rules") if isinstance(policy, dict) else None
    if not isinstance(rules, dict):
        return _DEFAULT_GATE_REVIEW
    features = rules.get("features")
    if not isinstance(features, dict):
        return _DEFAULT_GATE_REVIEW

    if feature_id is not None:
        overrides = features.get("overrides")
        if isinstance(overrides, dict):
            override = overrides.get(feature_id)
            if override in agent_policy.GATE_REVIEW_VALUES:
                return override

    gate_review = features.get("gate_review")
    if gate_review not in agent_policy.GATE_REVIEW_VALUES:
        return _DEFAULT_GATE_REVIEW
    return gate_review
