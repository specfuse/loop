# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Single registry of every GitHub label this package reads.

Each entry names the label, its provisioning colour/description, and the
consumer that reads it. Names are imported from the modules that own the
vocabulary (``escalation.py``, ``gh_features.py``) rather than retyped here,
so the registry cannot drift from what those consumers actually query.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from specfuse.loop import (
    bug_lane, closing_requirements, escalation, gh_features, notify_sla, triage,
)
from specfuse.monitor import autofix_state, issues


@dataclass(frozen=True)
class LabelSpec:
    name: str
    colour: str
    description: str
    consumer: str


LABEL_REGISTRY: tuple[LabelSpec, ...] = (
    LabelSpec(
        name=gh_features.FEATURE_LABEL,
        colour="1d76db",
        description="A roadmap-candidate feature request specfuse discovery reads",
        consumer="gh_features.py",
    ),
    LabelSpec(
        name=escalation.NEEDS_HUMAN_LABEL,
        colour="d93f0b",
        description="The loop stopped and needs a human decision",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="gate-review",
        colour="fbca04",
        description="A gate is at awaiting_review and needs review-and-arm",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="blocked-wu",
        colour="e99695",
        description="A work unit stopped and needs an operator decision",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="triage-question",
        colour="c5def5",
        description="An inbound issue needs categorising before it can be routed",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="drafting-needed",
        colour="bfd4f2",
        description="A queued feature has no folder yet and needs /draft-feature",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="merge-approval",
        colour="0e8a16",
        description="A pull request is green and waiting on a merge decision",
        consumer="escalation.py",
    ),
    # FEAT-2026-0085/T03: a not_met close's FOLLOW-UPS.md entries and a met
    # close's PLAN.md "Post-merge checklist" each file as their own issue,
    # not as needs-human (nothing here needs a human decision to unblock the
    # loop -- it is discharge-later tracking, so `gh issue create --label`
    # would 422 without these two entries).
    LabelSpec(
        name=closing_requirements.FOLLOW_UP_LABEL,
        colour="0052cc",
        description="A tracked follow-up from a not_met close's FOLLOW-UPS.md",
        consumer="loop/loop.py (file_followup_issues)",
    ),
    LabelSpec(
        name=closing_requirements.POST_MERGE_LABEL,
        colour="5319e7",
        description="A met close's PLAN.md Post-merge checklist, tracked post-merge",
        consumer="loop/loop.py (file_followup_issues)",
    ),
    # The harvester's findings carry their own label rather than reusing
    # `needs-human`: they are failure artifacts, not operator escalations, and a
    # distinct label lets `gh issue list` scope to exactly that lifecycle. It was
    # missing here until #300 — `gh issue create` rejects an unknown label, so the
    # harvester could not file a single finding on any repository that had not had
    # this label made by hand.
    LabelSpec(
        name=issues.FINDING_LABEL,
        colour="b60205",
        description="A failure artifact reported by specfuse monitor",
        consumer="monitor/issues.py",
    ),
    # Registered ahead of its consumer (gate 2, FEAT-2026-0042) on purpose:
    # #300 was `gh issue create`/`--add-label` rejecting every call because
    # the label a module queried was never declared here.
    LabelSpec(
        name=autofix_state.AUTOFIX_FAILED_LABEL,
        colour="5319e7",
        description="auto-fix attempted, failed",
        consumer="monitor/autofix_state.py",
    ),
    # FEAT-2026-0045/T01: the category->label projection of the triage
    # marker. `question` reuses the existing `triage-question` entry above
    # rather than minting a second label -- see triage.py's module docstring.
    LabelSpec(
        name=triage.BUG_LABEL,
        colour="ededed",
        description="An inbound issue triaged as a bug",
        consumer="loop/triage.py",
    ),
    LabelSpec(
        name=triage.FEATURE_LABEL,
        colour="006b75",
        description="An inbound issue triaged as a feature request",
        consumer="loop/triage.py",
    ),
    LabelSpec(
        name=triage.DUPLICATE_LABEL,
        colour="f9d0c4",
        description="An inbound issue triaged as a duplicate",
        consumer="loop/triage.py",
    ),
    LabelSpec(
        name=triage.WONTFIX_LABEL,
        colour="bfdadc",
        description="An inbound issue triaged as won't-fix",
        consumer="loop/triage.py",
    ),
    LabelSpec(
        name=notify_sla.PARKED_LABEL,
        colour="c2e0c6",
        description="An unanswered escalation was re-pinged once and is now parked",
        consumer="loop/notify_sla.py",
    ),
    # Bug-lane declining reasons (#1420). Every name here is a value in
    # `bug_lane.DECLINE_LABELS`; the lane cannot emit a label this registry does
    # not declare, and tests/test_bug_lane_labels_registered.py asserts it.
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_NO_TEST_EVIDENCE],
        colour="fbca04",
        description="Bug-lane auto-merge declined: the diff adds no test file",
        consumer="loop/bug_lane_run.py",
    ),
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_CI_NOT_GREEN],
        colour="fbca04",
        description="Bug-lane auto-merge declined: CI did not conclude success",
        consumer="loop/bug_lane_run.py",
    ),
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_DIFF_TOO_LARGE],
        colour="fbca04",
        description="Bug-lane auto-merge declined: diff exceeds rules.bugs.max_diff_lines",
        consumer="loop/bug_lane_run.py",
    ),
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_JUDGE_PATH_TOUCHED],
        colour="fbca04",
        description="Bug-lane auto-merge declined: the diff touches a never-auto-merge path",
        consumer="loop/bug_lane_run.py",
    ),
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_UNTRACEABLE],
        colour="fbca04",
        description="Bug-lane auto-merge declined: not traced to a triaged issue or diagnosed finding",
        consumer="loop/bug_lane_run.py",
    ),
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_DAILY_CAP_REACHED],
        colour="fbca04",
        description="Bug-lane auto-merge declined: rolling 24h merge cap reached",
        consumer="loop/bug_lane_run.py",
    ),
    LabelSpec(
        name=bug_lane.DECLINE_LABELS[bug_lane.REASON_UNREADABLE_INPUT],
        colour="fbca04",
        description="Bug-lane auto-merge declined: a guardrail input could not be read",
        consumer="loop/bug_lane_run.py",
    ),
)


@dataclass
class ProvisionReport:
    """Outcome of a provision_labels run. Never raised; always returned."""

    created: list = field(default_factory=list)
    already_present: list = field(default_factory=list)
    failed: list = field(default_factory=list)
    skipped: bool = False
    reason: str = ""


def _default_runner(args: list, cwd=None, check: bool = True):
    """Shell out to gh with the given argument list. Not called in tests."""
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def provision_labels(
    target: str | Path,
    *,
    runner: Optional[Callable] = None,
    repo: Optional[str] = None,
) -> ProvisionReport:
    """Create every LABEL_REGISTRY label the repo at ``target`` is missing.

    *repo* (``OWNER/NAME``) selects the repository with ``--repo`` instead of
    inferring it from *target* as the working directory. **Pass it whenever
    you inject a runner** (#2081).

    This module's own default runner takes ``cwd``; every other runner in the
    codebase is ``(argv, check)`` -- `agent.run`, `escalation`, `gh_backend`
    all use that shape, and `labels` is the sole outlier. So injecting any of
    them raised ``TypeError: got an unexpected keyword argument 'cwd'`` on the
    very first ``gh`` call, which this function then caught into
    ``ProvisionReport.reason`` and returned as ``skipped``.

    That is not theoretical. `bug_lane_run.add_guardrail_label` has injected
    the lane's runner since #1785 added on-demand provisioning, so **the
    on-demand path has never once created a label** -- the seven
    ``bug-lane:*`` entries were registered by FEAT-2026-0048 and no repository
    has them, while every label `scaffold.py` provisions (it passes no runner,
    so it gets the compatible default) exists.

    With *repo* set, no ``cwd`` is passed and the runner is called as
    ``runner(argv, check=False)``, which every caller in the codebase
    satisfies.

    Best-effort and idempotent: lists existing labels first and creates only
    what is missing, never overwriting so an operator's edited colour or
    description is left alone. Every failure mode (no gh binary, unauthenticated,
    not a git repo, remote not GitHub, list failure, a single create failure)
    is captured in the returned ProvisionReport rather than raised.
    """
    runner = runner if runner is not None else _default_runner
    report = ProvisionReport()

    def _invoke(argv: list):
        """Call *runner* with the contract its caller actually implements."""
        if repo is not None:
            return runner(argv + ["--repo", repo], check=False)
        return runner(argv, cwd=target, check=False)

    try:
        listed = _invoke(
            ["gh", "label", "list", "--json", "name,color,description", "--limit", "1000"]
        )
    except FileNotFoundError:
        report.skipped = True
        report.reason = "gh binary not found on PATH"
        return report
    except Exception as exc:  # noqa: BLE001 - never raise out of provision_labels
        report.skipped = True
        report.reason = f"gh label list raised: {exc}"
        return report

    if listed.returncode != 0:
        report.skipped = True
        stderr = (getattr(listed, "stderr", "") or "").strip()
        report.reason = stderr or "gh label list failed"
        return report

    try:
        existing = json.loads(listed.stdout or "[]")
        existing_names = {item["name"] for item in existing}
    except (ValueError, TypeError, KeyError) as exc:
        report.skipped = True
        report.reason = f"could not parse gh label list output: {exc}"
        return report

    for spec in LABEL_REGISTRY:
        if spec.name in existing_names:
            report.already_present.append(spec.name)
            continue
        try:
            created = _invoke(
                [
                    "gh", "label", "create", spec.name,
                    "--color", spec.colour,
                    "--description", spec.description,
                ]
            )
        except Exception:  # noqa: BLE001 - keep provisioning remaining labels
            report.failed.append(spec.name)
            continue
        if created.returncode == 0:
            report.created.append(spec.name)
        else:
            report.failed.append(spec.name)

    return report
