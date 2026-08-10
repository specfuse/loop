#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Derive the last-run timestamp from repo state and flag silence (FEAT-2026-0047/T04).

A silent agent is indistinguishable from an idle one, and that is the bug: an
agent that stalls, dies, or was never scheduled produces the same observable —
nothing — as an agent with nothing to do. This module makes the difference
visible.

The newest event across ``.specfuse/features/*/events.jsonl`` **is** the
last-run time; it is derived, never stored. Per
`[FEAT-2026-0042/G1-CLOSE-INTERMEDIATE/ephemeral-runner-state-fails-open]`, a
written heartbeat file on an ephemeral runner is decorative, and here it would
also be redundant — the events log already answers the question exactly.

``silence_check`` returns a verdict; it never posts. `/attention` calls it on
open and prints the staleness line (no webhook — a human is already looking).
A scheduled invocation (FEAT-2026-0049's concern, not this module's) calls it
and posts through ``notify.post_notification`` when stale. This module adds no
scheduler.
"""

from __future__ import annotations

import glob
import json
import os

from . import agent_policy

__all__ = ("last_run_at", "silence_check")

_DEFAULT_SILENCE_HOURS = 24


def last_run_at(repo_root: str | None = None) -> float | None:
    """Newest event timestamp (epoch seconds) across every feature's events.jsonl.

    Returns ``None`` when there are no events at all. Malformed or
    unparseable lines are skipped, not fatal. Read-only — never writes.
    """
    root = repo_root or "."
    pattern = os.path.join(root, ".specfuse", "features", "*", "events.jsonl")

    newest: float | None = None
    for path in glob.glob(pattern):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    envelope = json.loads(line)
                    timestamp = envelope["timestamp"]
                    from datetime import datetime

                    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError):
                    continue
                epoch = parsed.timestamp()
                if newest is None or epoch > newest:
                    newest = epoch
    return newest


def _resolve_silence_hours(policy_path: str | None) -> int:
    try:
        policy = agent_policy.load_policy(policy_path)
    except FileNotFoundError:
        return _DEFAULT_SILENCE_HOURS
    escalation = policy.get("escalation") if isinstance(policy, dict) else None
    if not isinstance(escalation, dict):
        return _DEFAULT_SILENCE_HOURS
    silence_hours = escalation.get("silence_hours")
    if (
        not isinstance(silence_hours, int)
        or isinstance(silence_hours, bool)
        or silence_hours <= 0
    ):
        return _DEFAULT_SILENCE_HOURS
    return silence_hours


def silence_check(
    *,
    now: float,
    repo_root: str | None = None,
    policy_path: str | None = None,
) -> dict:
    """Verdict on whether the repo has gone silent.

    ``now`` (epoch seconds) is injected — this module calls no clock
    directly. Performs no post of its own; the caller decides what to do
    with the verdict.

    A repo with no events at all is reported as a distinct state
    (``no_events: True``) rather than as stale-with-``hours_since: 0`` or as
    healthy — a fresh repo that has never run differs from one that stopped.
    """
    silence_hours = _resolve_silence_hours(policy_path)
    last = last_run_at(repo_root)

    if last is None:
        return {
            "stale": False,
            "no_events": True,
            "last_run_at": None,
            "hours_since": None,
            "silence_hours": silence_hours,
        }

    hours_since = (now - last) / 3600.0
    return {
        "stale": hours_since > silence_hours,
        "no_events": False,
        "last_run_at": last,
        "hours_since": hours_since,
        "silence_hours": silence_hours,
    }
