# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`specfuse-backfill-severity` -- amend one already-marked issue with a
severity, for issues the normal triage path will never revisit
(FEAT-2026-0113/T07, gate 3's walking skeleton).

A triaged issue's marker is its idempotency key (`specfuse.loop.triage`'s
module docstring): once written it is never revisited by a normal run, so an
issue marked before `severity` existed is stranded there permanently. This
module is the maintenance mode that re-reads one such issue, amends its
marker, and projects the `severity:<value>` label -- deliberately not part of
`specfuse-agent`'s own run (`specfuse/agent/run.py` is not edited by this
gate at all; see `GATE-03.md`'s arm-checkpoint Q1). A separate console
script is one deliberate command away, not one argv typo on the binary an
unattended run uses.

**Stubbed here, and only here** (this unit is gate 3's tracer bullet,
`/authoring-work-units` §14):

- selection breadth -- takes a single issue number rather than T08's
  predicate over the whole open-issue listing;
- the marker amendment -- `_amend_marker` below, which T08's
  `amend_marker_severity` (`specfuse.loop.triage`) replaces and T09 deletes;
- classification -- `_STUB_SEVERITY` stands in for T10's classification
  session.

**Not stubbed:** the write order. The marker's `severity=` field is
authoritative and is written before the `severity:<value>` label, mirroring
`specfuse.loop.triage.apply_triage`'s own marker-first sequence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Callable, Optional

from specfuse.loop import triage

#: Stands in for T10's classification session (gate 3, walking skeleton).
_STUB_SEVERITY = "medium"


def _default_runner(argv: list, check: bool = False):
    return subprocess.run(argv, check=check, capture_output=True, text=True)


def _amend_marker(body: str, category: str, confidence: str, severity: str) -> str:
    """Replace *body*'s two-field triage marker with the three-field form
    carrying *severity*.

    Stub: assumes *body* carries the marker in exactly the form
    `triage.render_marker(category, confidence)` renders it, with no other
    fields. `specfuse.loop.triage.amend_marker_severity` (T08) is the real
    amendment this is stood in for; T09 deletes this function when it
    switches the call site over (§9).
    """
    old_marker = triage.render_marker(category, confidence)
    new_marker = triage.render_marker(category, confidence, severity)
    return body.replace(old_marker, new_marker, 1)


def _find_issue(runner: Callable, repo: str, issue_number: int) -> Optional[dict]:
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--state", "open",
            "--limit", "100",
            "--json", "number,body,labels",
        ],
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        issues = json.loads(result.stdout)
    except ValueError:
        return None
    for issue in issues:
        if issue.get("number") == issue_number:
            return issue
    return None


def backfill_severity(
    runner: Callable,
    repo: str,
    issue_number: int,
    *,
    apply: bool = False,
    severity: Optional[str] = None,
) -> dict:
    """Amend one marked, severity-less issue with a severity, marker first.

    Returns a report dict, never raises. `apply=False` (the default) reports
    what would happen without writing -- GATE-03.md Q2. *severity* overrides
    `_STUB_SEVERITY` for callers that already know the value (tests, T10's
    eventual switch-over); omitted, the stub value is used.
    """
    issue = _find_issue(runner, repo, issue_number)
    if issue is None:
        return {"number": issue_number, "amended": False, "reason": "issue not found"}

    body = issue.get("body") or ""
    fields = triage.parse_marker_fields(body)
    if fields is None:
        return {"number": issue_number, "amended": False, "reason": "no triage marker"}

    category = fields.get("category")
    confidence = fields.get("confidence")
    if not category or not confidence:
        return {"number": issue_number, "amended": False, "reason": "incomplete triage marker"}

    if fields.get("severity"):
        return {"number": issue_number, "amended": False, "reason": "already has severity"}

    chosen_severity = severity or _STUB_SEVERITY

    if not apply:
        return {
            "number": issue_number,
            "amended": False,
            "reason": "dry run",
            "would_set_severity": chosen_severity,
        }

    new_body = _amend_marker(body, category, confidence, chosen_severity)
    runner(
        ["gh", "issue", "edit", str(issue_number), "--repo", repo, "--body", new_body],
        check=True,
    )
    label = triage.severity_label_for(chosen_severity)
    runner(
        ["gh", "issue", "edit", str(issue_number), "--repo", repo, "--add-label", label],
        check=True,
    )
    return {"number": issue_number, "amended": True, "severity": chosen_severity}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specfuse-backfill-severity",
        description=(
            "Amend one already-marked, severity-less issue with a severity, "
            "marker first, label projected after."
        ),
    )
    parser.add_argument("issue", type=int, help="the issue number to backfill")
    parser.add_argument("--repo", required=True, help="OWNER/NAME")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the amendment; default is a dry run that reports intent only",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    report = backfill_severity(_default_runner, args.repo, args.issue, apply=args.apply)
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
