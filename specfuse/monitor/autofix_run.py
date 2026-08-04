# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The autofix firing wiring (FEAT-2026-0042/T05): where T01's decision, T02's
durable state, and T04's invoker meet.

Given a diagnosed finding issue, `run_autofix` reads the finding's fingerprint
and its most recent diagnosis comment, asks `specfuse.monitor.autofix.decide`
whether to fire, records the attempt through `specfuse.monitor.autofix_state`
*before* invoking (never after — see the module-level note on
`_invoke_and_classify`), fires through an injected invoker, and applies
`AUTOFIX_FAILED_LABEL` when the outcome is a failure.

This module composes; it shells out to nothing directly. Every GitHub read
and write, and the headless `fix-bug` launch itself, happen through an
injected `runner(argv, check=...)` callable — the same seam
`specfuse.monitor.issues` and `specfuse.monitor.autofix_state` already use.
The `invoker` parameter builds and classifies the run
(`specfuse.monitor.autofix_invoke`'s contract); this module executes what it
builds via `runner` and hands the result back to it for classification.

**Not wired into `specfuse-monitor run`.** The harvest cycle
(`specfuse/monitor/cli.py`) gains no caller here, on purpose: a routine
harvest that could launch a fix is a far wider blast radius than this gate
can verify, and it would fire on findings nobody read. `run_autofix` is its
own entry point (`python3 -m specfuse.monitor.autofix_run`), following
`specfuse/monitor/diagnose_cli.py`'s precedent.

**The safety floor is not this module's to decide.** Auto-merge belongs to
FEAT-2026-0048 and is impossible here: nothing in this module merges a pull
request, enables auto-merge, or writes to a protected branch.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Protocol

from specfuse.monitor.autofix import FIRE, decide
from specfuse.monitor.autofix_state import AUTOFIX_FAILED_LABEL, GitHubAutofixState, record_attempt

__all__ = ("AutofixRunResult", "Invoker", "run_autofix", "main")

# The two outcomes `fix-bug`'s headless mode can return that count as a
# failed fix run and get labelled. `completed` gets no failure label.
_FAILING_OUTCOMES = ("refused", "could_not_proceed")

# Reads the same documented convention `specfuse.monitor.issues` writes
# (`_MARKER_TEMPLATE` there), without importing that module's private
# symbol -- this module never invents a second marker, it only reads the
# existing one.
_FINDING_MARKER_RE = re.compile(
    r"<!-- specfuse:finding fingerprint=(?P<fingerprint>\S+) -->"
)

# Same posture for `specfuse.monitor.diagnosis`'s marker prefix: public by
# documentation, not by symbol export.
_DIAGNOSIS_MARKER_PREFIX = "<!-- specfuse:diagnosis "

_DEFAULT_WORKING_DIR = "."


class Invoker(Protocol):
    """Builds a headless `fix-bug` invocation and classifies its result
    (`specfuse.monitor.autofix_invoke`'s contract). This module executes
    the argv it builds -- the invoker itself runs nothing."""

    def build_invocation(
        self, issue_number: int, repo: str, working_dir: str
    ) -> tuple[list[str], str]: ...

    def classify_outcome(self, result_text: str) -> str: ...


@dataclass(frozen=True)
class AutofixRunResult:
    """What `run_autofix` decided and, if it fired, what happened.

    `outcome` is `None` whenever nothing fired -- `DECLINE` and
    `ROUTE_TO_HUMAN` both leave it `None`, so a caller can tell "nothing ran"
    from "something ran and produced an outcome" without inferring it from
    side effects.
    """

    decision: str
    reason: str
    outcome: Optional[str]


def _extract_fingerprint(body: str) -> str:
    match = _FINDING_MARKER_RE.search(body or "")
    return match.group("fingerprint") if match else ""


def _latest_diagnosis_comment_body(comments: list) -> str:
    for comment in reversed(comments or []):
        body = comment.get("body", "") if isinstance(comment, dict) else ""
        if _DIAGNOSIS_MARKER_PREFIX in body:
            return body
    return ""


def _read_finding_issue(runner: Callable, repo: str, issue_number: int) -> dict:
    result = runner(
        [
            "gh", "issue", "view", str(issue_number),
            "--repo", repo,
            "--json", "body,comments",
        ],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", None):
        return {}
    try:
        parsed = json.loads(result.stdout)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _components_by_name(monitoring_config: Mapping[str, Any]) -> dict:
    components = monitoring_config.get("components") if monitoring_config else None
    if not isinstance(components, list):
        return {}
    return {
        entry["name"]: entry
        for entry in components
        if isinstance(entry, dict) and "name" in entry
    }


def _apply_failed_label(runner: Callable, repo: str, issue_number: int) -> None:
    runner(
        [
            "gh", "issue", "edit", str(issue_number),
            "--repo", repo,
            "--add-label", AUTOFIX_FAILED_LABEL,
        ],
        check=True,
    )


def _invoke_and_classify(
    runner: Callable,
    invoker: Invoker,
    repo: str,
    issue_number: int,
) -> str:
    """Build, run, and classify one headless `fix-bug` session.

    Called only after `record_attempt` has already happened -- see
    `run_autofix`'s FIRE branch. Recording first means a session killed
    mid-run costs one fingerprint a run it never got; invoking first would
    risk the same fingerprint firing again on retry.
    """
    argv, prompt = invoker.build_invocation(issue_number, repo, _DEFAULT_WORKING_DIR)
    result = runner(argv + [prompt], check=False)
    return invoker.classify_outcome(getattr(result, "stdout", "") or "")


def run_autofix(
    *,
    runner: Callable,
    invoker: Invoker,
    repo: str,
    finding_issue_number: int,
    monitoring_config: Mapping[str, Any],
    component: str,
) -> AutofixRunResult:
    """Decide, record, fire, and label -- for one diagnosed finding issue.

    Reads `finding_issue_number`'s body for the fingerprint marker
    `specfuse.monitor.issues` writes and its comments for the most recent
    diagnosis comment, calls `decide`, and on `FIRE` records the attempt
    (through T02's state, before invoking), fires through `invoker`, and
    applies `AUTOFIX_FAILED_LABEL` on `refused` / `could_not_proceed`.
    `DECLINE` and `ROUTE_TO_HUMAN` do nothing further -- in particular,
    `ROUTE_TO_HUMAN` never records an attempt, since routing to a human is
    not a spent fix run.
    """
    issue = _read_finding_issue(runner, repo, finding_issue_number)
    fingerprint = _extract_fingerprint(issue.get("body", ""))
    diagnosis_body = _latest_diagnosis_comment_body(issue.get("comments", []))

    decision = decide(
        diagnosis_body=diagnosis_body,
        monitoring_config=_components_by_name(monitoring_config),
        component=component,
        fingerprint=fingerprint,
        state_reader=GitHubAutofixState(runner=runner, repo=repo),
    )

    if decision.decision != FIRE:
        return AutofixRunResult(decision=decision.decision, reason=decision.reason, outcome=None)

    record_attempt(runner, repo, fingerprint)
    outcome = _invoke_and_classify(runner, invoker, repo, finding_issue_number)

    if outcome in _FAILING_OUTCOMES:
        _apply_failed_label(runner, repo, finding_issue_number)

    return AutofixRunResult(decision=decision.decision, reason=decision.reason, outcome=outcome)


def main(argv: Optional[list[str]] = None) -> int:
    from specfuse.loop import _miniyaml
    from specfuse.loop.escalation import _default_runner
    from specfuse.monitor import autofix_invoke

    parser = argparse.ArgumentParser(
        description=(
            "Fire the autofix wiring against one diagnosed finding issue. "
            "Reads the finding's diagnosis, decides whether to fire, and "
            "records/fires/labels accordingly. Not called by the harvest "
            "cycle -- see the module docstring."
        )
    )
    parser.add_argument("repo", help="owner/name of the GitHub repository")
    parser.add_argument("issue_number", type=int, help="finding issue number")
    parser.add_argument("component", help="component name in monitoring_config")
    parser.add_argument(
        "monitoring_config",
        help="path to a monitoring.yml-shaped file (already validated)",
    )
    args = parser.parse_args(argv)

    with open(args.monitoring_config, encoding="utf-8") as handle:
        monitoring_config = _miniyaml.parse(handle.read())

    result = run_autofix(
        runner=_default_runner,
        invoker=autofix_invoke,
        repo=args.repo,
        finding_issue_number=args.issue_number,
        monitoring_config=monitoring_config,
        component=args.component,
    )

    print(json.dumps(
        {"decision": result.decision, "reason": result.reason, "outcome": result.outcome}
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
