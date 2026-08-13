# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The feature provider (FEAT-2026-0049/T14): advance the queue top,
escalate what is not workable, switch to the next entry.

`advertise` re-reads feature state through `state.read_feature_summaries`
on every call rather than trusting the run's single `AgentSnapshot.features`
-- this provider's own `execute` is what moves that state (a `specfuse run`
subprocess advances a gate), so a stale snapshot would re-advertise a gate
that already passed. `snapshot.queue` is still trusted: the queue order
itself does not change mid-run, only what each entry resolves to.

Every un-workable disposition `queue_read.classify_queue_entry` can return
gets one `blocked-wu` or `drafting-needed` escalation here; drafting a
feature is out of scope for this provider (`PLAN.md` "Scope boundary") --
`needs_drafting` always escalates, never invokes anything under
`/draft-feature`.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional, Sequence

from specfuse.agent import driver_invoke, queue_read, state
from specfuse.agent.run import (
    KIND_FEATURE,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    _default_runner,
)
from specfuse.agent.state import AgentSnapshot

_ITEM_ID_PREFIX = "feature-"

_ARM_GATE_DRAFTING_FEATURE = "FEAT-2026-0050"


def _first_unpassed_gate(gates: tuple) -> Optional[int]:
    for gate in gates:
        if gate.status != "passed":
            return gate.gate
    return None


def _lookup_error(errors: dict, feature_id: str) -> Optional[str]:
    for dir_name, message in errors.items():
        if dir_name.startswith(feature_id):
            return message
    return None


class FeatureProvider:
    """`ActionProvider` over `queue:` entries, mediated by T12's classifier
    and T13's subprocess invocation."""

    def __init__(
        self,
        *,
        repo: str,
        runner: Callable = _default_runner,
        policy_path: Any = None,
        features_root: Any = None,
        stream_driver_output: bool = False,
        reporter: Optional[Callable[[str], None]] = None,
    ):
        self._repo = repo
        self._runner = runner
        self._policy_path = policy_path
        self._features_root = features_root if features_root is not None else ".specfuse/features"
        self._rows: dict = {}
        #: Opt-in rather than default-on so every existing caller that injects
        #: its own `runner` keeps using it. The tests here inject recording
        #: runners whose `on_call` side effects are what drive their
        #: assertions; a provider that quietly built its own runner instead
        #: would make those side effects stop firing. `default_providers`
        #: turns this on for the real invocation, where `runner` is only ever
        #: the module default and streaming is what the operator wants.
        self._stream_driver_output = stream_driver_output
        self._reporter = reporter

    def advertise(self, snapshot: AgentSnapshot) -> Sequence[ActionItem]:
        features, errors = state.read_feature_summaries(self._features_root)
        wip_limit = queue_read.resolve_wip_limit(self._policy_path)
        workable, needs_attention = queue_read.select_workable(
            snapshot.queue, features, errors, wip_limit=wip_limit
        )
        feature_by_id = {summary.feature_id: summary for summary in features}

        self._rows = {}
        items = []

        for entry in workable:
            summary = feature_by_id.get(entry)
            gate_num = _first_unpassed_gate(summary.gates) if summary is not None else None
            item_id = (
                f"{_ITEM_ID_PREFIX}{entry}-g{gate_num}"
                if gate_num is not None
                else f"{_ITEM_ID_PREFIX}{entry}"
            )
            self._rows[item_id] = {
                "disposition": queue_read.DISPOSITION_WORKABLE,
                "feature_id": entry,
            }
            items.append(
                ActionItem(
                    item_id=item_id,
                    kind=KIND_FEATURE,
                    summary=f"advance {entry}",
                    queue_key=entry,
                )
            )

        for entry, disposition in needs_attention:
            item_id = f"{_ITEM_ID_PREFIX}{entry}"
            detail = None
            if disposition == queue_read.DISPOSITION_BLOCKED:
                summary = feature_by_id.get(entry)
                detail = summary.status if summary is not None else None
            elif disposition == queue_read.DISPOSITION_UNREADABLE:
                detail = _lookup_error(errors, entry)
            self._rows[item_id] = {
                "disposition": disposition,
                "feature_id": entry,
                "detail": detail,
            }
            items.append(
                ActionItem(
                    item_id=item_id,
                    kind=KIND_FEATURE,
                    summary=f"{entry}: {disposition}",
                    queue_key=entry,
                )
            )

        return items

    def execute(self, item: ActionItem) -> ActionOutcome:
        row = self._rows.get(item.item_id)
        if row is None:
            return ActionOutcome(status=STATUS_COMPLETED, detail="nothing to do")

        disposition = row["disposition"]
        feature_id = row["feature_id"]

        if disposition == queue_read.DISPOSITION_WORKABLE:
            halt = driver_invoke.advance_feature(
                self._driver_runner(feature_id),
                feature_id,
                features_root=self._features_root,
            )
            return self._map_halt(feature_id, halt)

        if disposition == queue_read.DISPOSITION_NEEDS_DRAFTING:
            escalation = EscalationPayload(
                done_so_far=f"{feature_id} is in the queue but has no feature folder.",
                issue_summary=(
                    f"{feature_id} needs to be drafted before it can be advanced."
                ),
                decision_needed=f"Draft {feature_id} — its gate skeleton and gate 1 work units.",
                why_not_auto=(
                    "Drafting a feature is out of this provider's scope; async "
                    f"drafting is tracked by {_ARM_GATE_DRAFTING_FEATURE}, which "
                    f"lists this feature as its blocker."
                ),
                options=[
                    (
                        "Draft the feature by hand or via /draft-feature",
                        "unblocks the queue entry",
                        "costs a human's time",
                    ),
                    (
                        "Remove it from the queue",
                        "no immediate cost",
                        "the feature stays undrafted",
                    ),
                ],
                recommendation=f"Draft {feature_id} via /draft-feature.",
                category="drafting-needed",
            )
            return ActionOutcome(
                status=STATUS_ESCALATED, detail="needs drafting", escalation=escalation
            )

        # DISPOSITION_BLOCKED, DISPOSITION_UNREADABLE
        detail = row.get("detail")
        escalation = EscalationPayload(
            done_so_far=f"{feature_id} was read from the queue and its feature folder.",
            issue_summary=f"{feature_id} is not workable: {disposition} ({detail}).",
            decision_needed=f"Whether a human should unblock or repair {feature_id}.",
            why_not_auto=(
                "The agent only advances features that are active or planned; "
                f"{feature_id}'s disposition is {disposition!r}."
            ),
            options=[
                (
                    "Unblock or repair the feature",
                    "unblocks the queue entry",
                    "costs a human's time",
                ),
                (
                    "Leave it as-is",
                    "no immediate cost",
                    "the feature stays stuck",
                ),
            ],
            recommendation=f"Investigate {feature_id}'s {disposition} state.",
            category="blocked-wu",
        )
        return ActionOutcome(
            status=STATUS_ESCALATED,
            detail=f"{disposition}: {detail}",
            escalation=escalation,
        )

    def _driver_runner(self, feature_id: str) -> Callable:
        """The runner one `specfuse run` invocation gets.

        The injected `runner` unless streaming was asked for -- see the
        `_stream_driver_output` note in `__init__` for why the default is off.
        A log path that cannot be resolved (no feature directory found) still
        yields a teeing runner: streaming to the console is the half the
        operator is watching, and the file is the durable extra.
        """
        if not self._stream_driver_output:
            return self._runner

        stamp = time.strftime("%Y%m%dT%H%M%S")
        log_path = driver_invoke.driver_log_path(
            self._features_root, feature_id, stamp=stamp
        )
        if self._reporter is not None and log_path is not None:
            self._reporter(f"{feature_id}: driver output → {log_path}")
        return driver_invoke.teeing_runner(log_path, reporter=self._reporter)

    def _map_halt(self, feature_id: str, halt) -> ActionOutcome:
        halt_class, detail = halt.halt_class, halt.detail

        if halt_class == driver_invoke.HALT_ADVANCED:
            return ActionOutcome(status=STATUS_COMPLETED, detail=f"advanced: {detail}")

        if halt_class == driver_invoke.HALT_FEATURE_DONE:
            return ActionOutcome(status=STATUS_COMPLETED, detail="feature done")

        if halt_class == driver_invoke.HALT_AWAITING_REVIEW:
            gate_review = queue_read.resolve_gate_review(self._policy_path, feature_id)
            if gate_review == "auto":
                return ActionOutcome(
                    status=STATUS_COMPLETED,
                    detail=f"awaiting_review under gate_review=auto: {detail}",
                    escalation=None,
                )
            escalation = EscalationPayload(
                done_so_far=f"specfuse run advanced {feature_id} to a gate boundary.",
                issue_summary=f"{feature_id} is awaiting_review: {detail}.",
                decision_needed=f"Whether to arm {feature_id}'s next gate via /arm-gate.",
                why_not_auto=(
                    "The agent cannot arm a gate -- that flips a draft work unit to "
                    "pending, which is /arm-gate's job."
                ),
                options=[
                    (
                        "Run /arm-gate",
                        "unblocks the next gate",
                        "costs a human's time",
                    ),
                    (
                        "Leave the gate unarmed",
                        "no immediate cost",
                        "the feature stalls",
                    ),
                ],
                recommendation=f"Run /arm-gate for {feature_id}.",
                category="gate-review",
            )
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"awaiting_review: {detail}",
                escalation=escalation,
            )

        if halt_class == driver_invoke.HALT_NOT_ARMED:
            escalation = EscalationPayload(
                done_so_far=f"specfuse run was invoked for {feature_id} and exited not-armed.",
                issue_summary=f"{feature_id}'s next gate holds only draft work units.",
                decision_needed=f"Whether to arm {feature_id}'s gate via /arm-gate.",
                why_not_auto="The agent cannot arm a gate; only /arm-gate can.",
                options=[
                    (
                        "Run /arm-gate",
                        "unblocks the gate",
                        "costs a human's time",
                    ),
                    (
                        "Leave it unarmed",
                        "no immediate cost",
                        "the feature stalls",
                    ),
                ],
                recommendation=f"Run /arm-gate for {feature_id}.",
                category="gate-review",
            )
            return ActionOutcome(
                status=STATUS_ESCALATED, detail="not_armed", escalation=escalation
            )

        if halt_class == driver_invoke.HALT_BLOCKED:
            detail_dict = detail if isinstance(detail, dict) else {}
            wu_id = detail_dict.get("wu_id")
            reason = detail_dict.get("reason")
            escalation = EscalationPayload(
                done_so_far=f"specfuse run advanced {feature_id} until a work unit blocked.",
                issue_summary=f"Work unit {wu_id} in {feature_id} blocked: {reason}.",
                decision_needed=f"Whether a human should unblock work unit {wu_id}.",
                why_not_auto="The driver halted with a human_escalation event; the agent cannot resolve it.",
                options=[
                    (
                        "Unblock the work unit",
                        "unblocks the feature",
                        "costs a human's time",
                    ),
                    (
                        "Leave it blocked",
                        "no immediate cost",
                        "the feature stalls",
                    ),
                ],
                recommendation=f"Investigate and unblock {wu_id}.",
                category="blocked-wu",
            )
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"blocked: wu={wu_id} reason={reason}",
                escalation=escalation,
            )

        # HALT_DRIVER_ERROR
        escalation = EscalationPayload(
            done_so_far=f"specfuse run was invoked for {feature_id} and exited with an error.",
            issue_summary=f"{feature_id}'s driver invocation failed: {detail}.",
            decision_needed=f"Whether a human should investigate {feature_id}'s driver error.",
            why_not_auto="The driver exited non-zero with no human_escalation event to explain why.",
            options=[
                (
                    "Investigate the driver error",
                    "unblocks the feature",
                    "costs a human's time",
                ),
                (
                    "Leave it as-is",
                    "no immediate cost",
                    "the feature stalls",
                ),
            ],
            recommendation=f"Investigate {feature_id}'s driver error.",
            category="blocked-wu",
        )
        return ActionOutcome(
            status=STATUS_ESCALATED,
            detail=f"driver_error: {detail}",
            escalation=escalation,
        )

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
