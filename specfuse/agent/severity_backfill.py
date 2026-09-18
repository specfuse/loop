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
- classification -- `_STUB_SEVERITY` stands in for T10's classification
  session.

The marker amendment itself is `specfuse.loop.triage.amend_marker_severity`
(T08); `apply_severity_backfill` below (T09) is the bulk, decision-list write
path T10 will drive.

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
from specfuse.loop.build_provenance import warn_if_out_of_tree

#: Stands in for T10's classification session (gate 3, walking skeleton).
_STUB_SEVERITY = "medium"


def _default_runner(argv: list, check: bool = False):
    return subprocess.run(argv, check=check, capture_output=True, text=True)


def apply_severity_backfill(runner: Callable, repo: str, decisions: list) -> list:
    """Record each decision in `decisions` against its GitHub issue, marker
    first, label second.

    Each decision is a mapping carrying `number`, `body` (the issue's
    current body, as read at selection time) and `severity`. Mirrors
    `specfuse.loop.triage.apply_triage`'s shape: the marker write is the
    idempotency key, so a decision whose body already carries a
    `severity=` field produces no `gh` calls at all and is reported
    `skipped` on its row -- this is what bounds a repeat run over the same
    candidates. A failed marker write leaves the label unwritten; a failed
    label write is recorded on the row and never raised, leaving the
    amended marker in place -- the marker is the authoritative record, the
    label a projection re-derived from it (`PLAN.md`'s "Record
    precedence").
    """
    results = []
    for decision in decisions:
        number = decision["number"]
        body = decision.get("body") or ""
        severity = decision["severity"]

        fields = triage.parse_marker_fields(body)
        if fields is None or fields.get("severity"):
            results.append(
                {
                    "number": number,
                    "skipped": True,
                    "marker_written": False,
                    "label_written": False,
                }
            )
            continue

        row = {
            "number": number,
            "severity": severity,
            "skipped": False,
        }

        new_body = triage.amend_marker_severity(body, severity)
        try:
            runner(
                ["gh", "issue", "edit", str(number), "--repo", repo, "--body", new_body],
                check=True,
            )
        except Exception as exc:  # noqa: BLE001 - recorded, not raised
            row["marker_written"] = False
            row["marker_error"] = str(exc)
            row["label_written"] = False
            results.append(row)
            continue
        row["marker_written"] = True

        label = triage.severity_label_for(severity)
        try:
            runner(
                ["gh", "issue", "edit", str(number), "--repo", repo, "--add-label", label],
                check=True,
            )
        except Exception as exc:  # noqa: BLE001 - label failure never raises
            row["label_written"] = False
            row["label_error"] = str(exc)
        else:
            row["label_written"] = True

        results.append(row)
    return results


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

    new_body = triage.amend_marker_severity(body, chosen_severity)
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
    warn_if_out_of_tree()
    args = build_parser().parse_args(argv)
    report = backfill_severity(_default_runner, args.repo, args.issue, apply=args.apply)
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
