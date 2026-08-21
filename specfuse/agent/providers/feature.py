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
gets one `blocked-wu` or `drafting-needed` escalation here, except
`needs_drafting`, which has two branches (FEAT-2026-0050/T07): the injected
`answer_gate` is asked for `feature_id`'s answer-gate result, and a
`draft_ready` result dispatches the headless drafting session through the
provider's own `runner` instead of escalating; a `fallback` result still
escalates with the plain `drafting-needed` payload
(`drafting_answers.fallback_escalation`), unchanged from before this unit.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional, Sequence

from specfuse.agent import driver_command as driver_command_module
from specfuse.agent import driver_invoke, queue_read, state
from specfuse.agent import drafting_answers, drafting_invoke
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

    #: How many times one item may re-dispatch the driver after a restart
    #: halt. Two covers the real shape -- a unit edits the driver, the fresh
    #: process finishes the gate -- with one spare, and stops a unit that
    #: re-edits on every attempt from consuming the run.
    MAX_DRIVER_RESTARTS = 2

    def __init__(
        self,
        *,
        repo: str,
        runner: Callable = _default_runner,
        policy_path: Any = None,
        features_root: Any = None,
        stream_driver_output: bool = False,
        reporter: Optional[Callable[[str], None]] = None,
        driver_command: Optional[Sequence[str]] = None,
        answer_gate: Optional[
            Callable[[str], drafting_answers.AnswerGateResult]
        ] = None,
    ):
        self._repo = repo
        self._runner = runner
        self._policy_path = policy_path
        self._features_root = features_root if features_root is not None else ".specfuse/features"
        #: Defaults to a fallback-only reader so a caller that injects nothing
        #: keeps today's behaviour -- no answers exist anywhere yet to read,
        #: so `needs_drafting` still escalates every time (D3).
        self._answer_gate = answer_gate or self._fallback_answer_gate
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
        #: Resolved once per provider, not per dispatch: which build gets run
        #: is a property of where the conductor is standing, and re-deciding
        #: it mid-run could dispatch two different drivers in one run (#2186).
        self._driver_command = driver_command_module.resolve_driver_command(
            override=driver_command
        )

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
            return self._advance(feature_id)

        if disposition == queue_read.DISPOSITION_NEEDS_DRAFTING:
            return self._dispatch_drafting(feature_id)

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

    def _fallback_answer_gate(self, feature_id: str) -> drafting_answers.AnswerGateResult:
        return drafting_answers.AnswerGateResult(
            outcome=drafting_answers.OUTCOME_FALLBACK,
            escalation=drafting_answers.fallback_escalation(feature_id),
        )

    def _dispatch_drafting(self, feature_id: str) -> ActionOutcome:
        """`needs_drafting`'s two branches (FEAT-2026-0050/T07).

        A `fallback` gate result escalates with the same payload this branch
        has always produced (D3); a `draft_ready` result builds the headless
        `/draft-feature` invocation and dispatches it through the provider's
        own `runner`, the same one `_advance` uses for `specfuse run`.
        """
        gate_result = self._answer_gate(feature_id)
        if gate_result.outcome != drafting_answers.OUTCOME_DRAFT_READY:
            escalation = gate_result.escalation or drafting_answers.fallback_escalation(
                feature_id
            )
            return ActionOutcome(
                status=STATUS_ESCALATED, detail="needs drafting", escalation=escalation
            )

        argv, prompt = drafting_invoke.build_invocation(feature_id, gate_result)
        self._runner(argv + [prompt], check=False)
        return ActionOutcome(
            status=STATUS_COMPLETED,
            detail=f"{feature_id}: drafting session dispatched",
        )

    def _advance(self, feature_id: str) -> ActionOutcome:
        """Dispatch `specfuse run` for one feature, restarting the driver as
        many as `MAX_DRIVER_RESTARTS` times.

        A restart halt is not a failure and not a gate boundary: the driver
        stopped because a work unit edited its own importable surface, and it
        left every gate and WU status untouched precisely so a fresh process
        picks up where it stopped. The next `advance_feature` *is* that fresh
        process, so the conductor can answer this itself -- which is what it
        failed to do when the halt arrived misclassified as
        `awaiting_review: None`, costing an escalation, a filed issue, and a
        triage item while the gate's remaining units stayed pending (#2321).

        Bounded because "restart me" is only progress if something changed. A
        unit that edits the driver on every attempt would otherwise spin here
        for the whole run; past the cap it becomes a human's problem, named as
        one.
        """
        restarts = 0
        prior: tuple | None = None
        self._say(
            f"{feature_id}: "
            f"{driver_command_module.describe_command(self._driver_command)}"
        )
        while True:
            halt = driver_invoke.advance_feature(
                self._driver_runner(feature_id),
                feature_id,
                features_root=self._features_root,
                command=self._driver_command,
            )
            if halt.halt_class != driver_invoke.HALT_DRIVER_RESTART:
                return self._map_halt(feature_id, halt)

            detail = halt.detail if isinstance(halt.detail, dict) else {}
            # The cap counts *consecutive restarts that changed nothing*, not
            # restarts (#2617). A gate whose units each edit a driver module
            # once -- complete, halt for a reload, hand off to the next -- is
            # maximally productive, and counting raw restarts escalated it as
            # a spin on the third unit. Observed on FEAT-2026-0058 (#2616),
            # whose gate stalled one unit from its close.
            current = self._restart_progress_key(detail)
            if prior is not None and current is not None and current != prior:
                restarts = 0
            prior = current

            if restarts >= self.MAX_DRIVER_RESTARTS:
                return self._restart_exhausted(feature_id, detail, restarts)

            restarts += 1
            self._say(
                f"{feature_id}: driver halted for restart after "
                f"{detail.get('wu_id') or 'a work unit'} edited it "
                f"({', '.join(detail.get('driver_paths') or []) or 'driver modules'}) "
                f"— dispatching a fresh driver ({restarts}/{self.MAX_DRIVER_RESTARTS})"
            )

    @staticmethod
    def _restart_progress_key(detail: dict) -> "tuple | None":
        """What the gate looked like at this restart, or None if unknowable.

        Two restarts whose keys differ mean the gate advanced between them.
        `remaining_wu_ids` is the direct signal -- it shrinks as units finish
        -- with `wu_id` carried alongside so a re-edited unit under an
        unchanged remaining list is still read as standing still.

        **None when there is no evidence**, which the caller treats as no
        progress rather than as progress. `_find_restart_detail` returns `{}`
        when the halting event cannot be re-read, and `driver_invoke` is
        explicit that such a run is still a restart; resetting the counter
        there would make the cap unreachable exactly when the driver is least
        legible.
        """
        remaining = detail.get("remaining_wu_ids")
        if remaining is None:
            return None
        return (detail.get("wu_id"), tuple(remaining))

    def _restart_exhausted(self, feature_id: str, detail: dict, restarts: int) -> ActionOutcome:
        """Escalate a feature that asked for a restart more times than the cap
        allows -- the one case where re-dispatching has stopped being progress."""
        wu_id = detail.get("wu_id") or "a work unit"
        remaining = ", ".join(detail.get("remaining_wu_ids") or []) or "(none reported)"
        paths = ", ".join(detail.get("driver_paths") or []) or "driver modules"
        escalation = EscalationPayload(
            done_so_far=(
                f"specfuse run was dispatched for {feature_id} {restarts + 1} times; "
                f"each run halted asking for a driver restart after {wu_id} edited "
                f"{paths}. Work units still pending in the gate: {remaining}."
            ),
            issue_summary=(
                f"{feature_id} has asked for a driver restart {restarts + 1} times in "
                f"one run — {wu_id} keeps editing the driver's own importable surface."
            ),
            decision_needed=(
                f"Whether {feature_id}'s gate can make progress, or whether {wu_id} "
                f"needs to be split so it stops re-editing the driver every attempt."
            ),
            why_not_auto=(
                "The agent restarts the driver on this halt, but a unit that "
                "triggers it on every attempt is not making progress and would "
                "otherwise spin for the rest of the run."
            ),
            options=[
                (
                    f"Run 'specfuse run --feature {feature_id}' by hand",
                    "shows whether a fresh process gets further",
                    "costs a human's time",
                ),
                (
                    "Split the work unit so it stops editing the driver mid-gate",
                    "removes the restart loop at its source",
                    "requires re-authoring the unit",
                ),
                (
                    "Leave it",
                    "no immediate cost",
                    "the gate stalls with work units pending",
                ),
            ],
            recommendation=(
                f"Run the driver by hand for {feature_id} and read what {wu_id} edits."
            ),
            category="blocked-wu",
        )
        return ActionOutcome(
            status=STATUS_ESCALATED,
            detail=f"driver restart loop: {wu_id} after {restarts + 1} dispatches",
            escalation=escalation,
        )

    def _say(self, message: str) -> None:
        if self._reporter is not None:
            self._reporter(message)

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
