# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The findings-diagnose provider (FEAT-2026-0049/T10): T05's protocol over
`specfuse.monitor.diagnose_cli.render_headless`, with
`specfuse.agent.diagnose_invoke` supplying the headless analysis step and
`specfuse.agent.monitoring_read` (T09) supplying the component/dial reads
`AgentSnapshot` cannot answer.

`advertise` returns one `kind="finding-diagnose"` item per open snapshot
issue carrying `specfuse.monitor.issues.FINDING_LABEL` that has no diagnosis
comment yet. The snapshot's `IssueSummary` carries no body, so this
provider reads each candidate's body and comments itself with
`gh issue view N --json body,comments` -- the same read
`autofix_run._read_finding_issue` performs and the same softening of "the
selector reads a value, not a call" T08 accepted (`GATE-02-REVIEW.md`). An
existing diagnosis is detected with `specfuse.monitor.diagnosis.parse`, not
a marker string spelled here.

A component whose `diagnose` dial is not `auto`, or a finding whose
component cannot be resolved from its body, or an absent monitoring config
entirely, is not advertised (OQ-2 in `GATE-03-REVIEW.md`; drafted
conservatively on purpose).

The rendered comment body is `diagnosis.render`'s, unaltered -- this module
holds no heading template and no marker string of its own. An unparseable
analysis result posts nothing: `execute` escalates with the parse error's
own message and never retries, defaults a field, or posts a partial body.
This provider performs no git mutation and no label write of its own; a
diagnosis is a comment.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Sequence

from specfuse.agent.diagnose_invoke import AnalysisParseError, build_invocation, read_result
from specfuse.agent.invoke import run_claude, usage_spend
from specfuse.agent.monitoring_read import (
    component_diagnose_dial,
    component_for_finding,
    load_monitoring_config,
)
from specfuse.agent.run import (
    KIND_FINDING_DIAGNOSE,
    STATUS_COMPLETED,
    STATUS_ESCALATED,
    ActionItem,
    ActionOutcome,
    EscalationPayload,
    _default_runner,
)
from specfuse.agent.state import AgentSnapshot
from specfuse.monitor.diagnosis import DiagnosisParseError, parse
from specfuse.monitor.issues import FINDING_LABEL

_ITEM_ID_PREFIX = "finding-diagnose-"
_DEFAULT_MONITORING_CONFIG_PATH = ".specfuse/monitoring.yml"
_DIAGNOSE_DIAL_AUTO = "auto"


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


def _already_diagnosed(comments: list) -> bool:
    for comment in comments or []:
        body = comment.get("body", "") if isinstance(comment, dict) else ""
        try:
            if parse(body) is not None:
                return True
        except DiagnosisParseError:
            continue
    return False


def _unparseable_diagnosis_payload(number: int, error: str) -> EscalationPayload:
    return EscalationPayload(
        target_issue=number,
        done_so_far=(
            f"The agent ran a headless diagnosis session against this finding. "
            f"The session returned output that could not be parsed as a "
            f"diagnosis: {error}"
        ),
        issue_summary=(
            f"Finding #{number} could not be diagnosed automatically -- the "
            f"session's output did not parse."
        ),
        decision_needed=(
            "Whether a human should diagnose this finding by hand, or leave it "
            "for a later run."
        ),
        why_not_auto=(
            "A diagnosis is only useful if it carries the structured fields "
            "downstream decisions read. Unparseable output has none of them, "
            "so nothing can be recorded on the finding."
        ),
        options=[
            (
                "Diagnose by hand",
                "unblocks the finding and records a usable root cause",
                "costs a human's time",
            ),
            (
                "Leave it for a later run",
                "cheap; a transient session failure may not repeat",
                "the finding stays undiagnosed and nothing routes it",
            ),
        ],
        recommendation=(
            "Read the session output before re-running -- output that does not "
            "parse is usually a prompt or component-context problem that will "
            "repeat, not a transient failure."
        ),
        category="blocked-wu",
    )


class FindingsDiagnoseProvider:
    """`ActionProvider` over `diagnose_cli.render_headless` plus headless
    analysis."""

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

        items = []
        for issue in snapshot.issues:
            if FINDING_LABEL not in issue.labels:
                continue

            raw = _read_issue(self._runner, self._repo, issue.number)
            body = raw.get("body", "") or ""
            comments = raw.get("comments", []) or []

            component = component_for_finding(body)
            if component is None:
                continue
            dial = component_diagnose_dial(monitoring_config, component)
            if dial != _DIAGNOSE_DIAL_AUTO:
                continue

            if _already_diagnosed(comments):
                continue

            item_id = f"{_ITEM_ID_PREFIX}{issue.number}"
            self._rows[item_id] = {"number": issue.number, "title": issue.title, "body": body}
            items.append(
                ActionItem(
                    item_id=item_id,
                    kind=KIND_FINDING_DIAGNOSE,
                    summary=issue.title,
                    queue_key=None,
                )
            )
        return items

    def execute(self, item: ActionItem) -> ActionOutcome:
        number = int(item.item_id[len(_ITEM_ID_PREFIX) :])
        row = self._rows.get(item.item_id)
        if row is None:
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"issue #{number} is no longer available for diagnosis",
                escalation_waived=(
                    "the finding left the diagnosable set between the snapshot "
                    "and this item; nothing for a human to decide"
                ),
            )

        title = row["title"]
        body = row["body"]

        argv, prompt = build_invocation(number, title, body, self._repo, self._working_dir)
        invoked = run_claude(argv, prompt, runner=self._runner)
        spend = usage_spend(invoked.usage)

        try:
            rendered = read_result(invoked.text)
        except AnalysisParseError as exc:
            return ActionOutcome(
                status=STATUS_ESCALATED,
                detail=f"issue #{number}: {exc}",
                escalation=_unparseable_diagnosis_payload(number, str(exc)),
                spend=spend,
            )

        self._runner(
            [
                "gh", "issue", "comment", str(number),
                "--repo", self._repo,
                "--body", rendered,
            ],
            check=False,
        )
        return ActionOutcome(
            status=STATUS_COMPLETED,
            detail=f"issue #{number} diagnosed",
            spend=spend,
        )

    def reconcile(self, item: ActionItem, outcome: ActionOutcome) -> None:
        return None
