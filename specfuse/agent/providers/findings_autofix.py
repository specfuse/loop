# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The findings-autofix provider (FEAT-2026-0049/T11): T05's protocol over
`specfuse.monitor.autofix_run.run_autofix`, the shipped decide-record-fire-
label caller. This module adds no judgment of its own -- `decide`'s
confidence threshold, `fix_scope` routing, fingerprint rate limit, and daily
cap all stay in `specfuse.monitor.autofix`/`autofix_state`, read only
through `run_autofix`.

`advertise` returns one `kind="finding-autofix"` item per open snapshot
issue carrying `specfuse.monitor.issues.FINDING_LABEL` that already has a
diagnosis comment -- the mirror of T10's filter, read the same way via
`gh issue view N --json body,comments` and `specfuse.monitor.diagnosis.parse`.
The `(monitoring_config, component)` pair comes from T09's
`specfuse.agent.monitoring_read`; a finding whose component is absent from
the config, or any finding when no config is present, is not advertised --
`decide` would only decline it as `unreadable_input`, and spending an item
slot to be told that is not selection.

`execute` maps `AutofixRunResult` to `ActionOutcome` by `decision`/`outcome`
alone:

    FIRE / completed              -> completed
    FIRE / refused|could_not_proceed -> escalated, no escalation payload
                                        (run_autofix already applied
                                        AUTOFIX_FAILED_LABEL)
    ROUTE_TO_HUMAN                -> escalated, with an escalation payload
    DECLINE                       -> completed (the predicate working, not
                                      a failure to report)

`ActionOutcome.detail` always carries `decide`'s own `reason` string. This
provider performs no git mutation of its own -- it invokes through
`specfuse.monitor.autofix_invoke`, passed straight through as
`run_autofix`'s `invoker=`, and never commits, branches, pushes, or merges.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Sequence

from specfuse.agent.monitoring_read import component_for_finding, load_monitoring_config
from specfuse.agent.run import (
    KIND_FINDING_AUTOFIX,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    _default_runner,
)
from specfuse.agent.state import AgentSnapshot
from specfuse.monitor import autofix_invoke
from specfuse.monitor.autofix import DECLINE, FIRE, ROUTE_TO_HUMAN
from specfuse.monitor.autofix_run import run_autofix
from specfuse.monitor.diagnosis import DiagnosisParseError, parse
from specfuse.monitor.issues import FINDING_LABEL

_ITEM_ID_PREFIX = "finding-autofix-"
_DEFAULT_MONITORING_CONFIG_PATH = ".specfuse/monitoring.yml"
_FAILING_OUTCOMES = ("refused", "could_not_proceed")


def _read_issue(runner: Callable, repo: str, issue_number: int) -> dict:
    result = runner(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "body,comments"],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return {}
    try:
        parsed = json.loads(result.stdout)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _has_diagnosis(comments: list) -> bool:
    for comment in comments or []:
        body = comment.get("body", "") if isinstance(comment, dict) else ""
        try:
            if parse(body) is not None:
                return True
        except DiagnosisParseError:
            continue
    return False


def _known_components(monitoring_config: Any) -> set:
    components = monitoring_config.get("components") if isinstance(monitoring_config, dict) else None
    if not isinstance(components, list):
        return set()
    return {entry.get("name") for entry in components if isinstance(entry, dict)}


class FindingsAutofixProvider:
    """`ActionProvider` over `autofix_run.run_autofix`."""

    def __init__(
        self,
        *,
        repo: str,
        runner: Callable = _default_runner,
        working_dir: str = ".",
        policy_path: Any = None,
        monitoring_config_path: str = _DEFAULT_MONITORING_CONFIG_PATH,
    ):
        self._repo = repo
        self._runner = runner
        self._working_dir = working_dir
        self._policy_path = policy_path
        self._monitoring_config_path = monitoring_config_path
        self._rows: dict = {}

    def advertise(self, snapshot: AgentSnapshot) -> Sequence[ActionItem]:
        self._rows = {}
        monitoring_config = load_monitoring_config(self._monitoring_config_path)
        if monitoring_config is None:
            return ()

        known_components = _known_components(monitoring_config)

        items = []
        for issue in snapshot.issues:
            if FINDING_LABEL not in issue.labels:
                continue

            raw = _read_issue(self._runner, self._repo, issue.number)
            body = raw.get("body", "") or ""
            comments = raw.get("comments", []) or []

            component = component_for_finding(body)
            if component is None or component not in known_components:
                continue

            if not _has_diagnosis(comments):
                continue

            item_id = f"{_ITEM_ID_PREFIX}{issue.number}"
            self._rows[item_id] = {
                "number": issue.number,
                "component": component,
                "monitoring_config": monitoring_config,
            }
            items.append(
                ActionItem(
                    item_id=item_id,
                    kind=KIND_FINDING_AUTOFIX,
                    summary=issue.title,
                    queue_key=None,
                )
            )
        return items

    def execute(self, item: ActionItem) -> ActionOutcome:
        row = self._rows.get(item.item_id)
        if row is None:
            number = item.item_id[len(_ITEM_ID_PREFIX):]
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"issue #{number} is no longer available for autofix",
            )

        number = row["number"]
        result = run_autofix(
            runner=self._runner,
            invoker=autofix_invoke,
            repo=self._repo,
            finding_issue_number=number,
            monitoring_config=row["monitoring_config"],
            component=row["component"],
        )
        return self._map_outcome(number, result)

    def _map_outcome(self, number: int, result) -> ActionOutcome:
        if result.decision == FIRE:
            if result.outcome in _FAILING_OUTCOMES:
                return ActionOutcome(
                    status=STATUS_ESCALATED,
                    detail=result.reason,
                    escalation=None,
                )
            return ActionOutcome(status=STATUS_COMPLETED, detail=result.reason)

        if result.decision == ROUTE_TO_HUMAN:
            escalation = EscalationPayload(
                done_so_far=(
                    f"Finding issue #{number} was diagnosed and evaluated by "
                    "the autofix predicate."
                ),
                issue_summary=(
                    f"The autofix predicate routed finding #{number} to a "
                    f"human: {result.reason}."
                ),
                decision_needed="Whether a human should apply the fix directly or decline it.",
                why_not_auto=(
                    "The diagnosis's fix scope or confidence put this "
                    "finding outside an automated fix run's competence."
                ),
                options=[
                    (
                        "Apply the fix by hand",
                        "unblocks the fix directly",
                        "costs a human's time",
                    ),
                    (
                        "Decline and leave the finding open",
                        "no immediate cost",
                        "the underlying issue stays unfixed",
                    ),
                ],
                recommendation="Review the diagnosis and apply the fix by hand.",
                category="blocked-wu",
            )
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=result.reason,
                escalation=escalation,
            )

        assert result.decision == DECLINE
        return ActionOutcome(status=STATUS_COMPLETED, detail=result.reason)

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
