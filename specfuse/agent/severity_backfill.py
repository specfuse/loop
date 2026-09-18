# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`specfuse-backfill-severity` -- amend already-marked, severity-less issues
with a severity, for issues the normal triage path will never revisit
(FEAT-2026-0113).

A triaged issue's marker is its idempotency key (`specfuse.loop.triage`'s
module docstring): once written it is never revisited by a normal run, so an
issue marked before `severity` existed is stranded there permanently. This
module is the maintenance mode that re-reads such issues, amends their
markers, and projects the `severity:<value>` label -- deliberately not part
of `specfuse-agent`'s own run (`specfuse/agent/run.py` is not edited by this
gate at all; see `GATE-03.md`'s arm-checkpoint Q1). A separate console
script is one deliberate command away, not one argv typo on the binary an
unattended run uses.

`run_backfill` (T10) is the real run shape: `triage.list_severity_backfill_candidates`
(T08) selects the open, marked, severity-less issues; `labels.read_severity_rubric`
is read exactly once per run; each candidate is classified through
`triage_invoke.build_invocation` + `triage_invoke.classify_severity` -- the same
classifier a fresh triage uses, so a low-confidence or out-of-rubric answer fails
closed exactly as it does there; and nothing is written unless the caller passes
`apply=True`. `apply_severity_backfill` (T09) is the bulk, decision-list write
path `run_backfill` drives for the candidates that classified cleanly.

`backfill_severity` (T07) is gate 3's tracer bullet: a single-issue path, still
used by `GATE-03.md`'s `feature_oracle`, that stands in `_STUB_SEVERITY` for a
classification session. `run_backfill` does not call it and does not share its
stub -- the two coexist because the oracle that proved the write order end to
end is not rewritten out from under itself.

The marker amendment itself is `specfuse.loop.triage.amend_marker_severity`
(T08). The write order -- marker before label -- is `apply_severity_backfill`'s
(T09), mirroring `specfuse.loop.triage.apply_triage`'s own marker-first
sequence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Callable, Optional

from specfuse.agent.invoke import run_claude
from specfuse.agent.triage_invoke import build_invocation, classify_severity
from specfuse.loop.labels import read_severity_rubric

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


def run_backfill(
    runner: Callable,
    repo: str,
    working_dir: str = ".",
    *,
    apply: bool = False,
    limit: int = triage.DEFAULT_LIST_LIMIT,
    model: str = "sonnet",
    effort: str = "medium",
) -> dict:
    """Select, classify, and (only under `apply=True`) write severities for
    every open, marked, severity-less issue in `repo` -- the real run shape
    T07's single-issue tracer bullet stood in for.

    The rubric is read exactly once, before any candidate is even selected:
    an empty rubric (`labels.read_severity_rubric`'s degradation path, or a
    repository whose whole `severity:*` scheme lies outside
    `agent_policy.SEVERITY_VALUES`) makes the run a no-op -- `reason` is set,
    `rows` is empty, and neither a candidate listing nor a `claude`
    invocation nor a `gh issue edit` call is ever issued, because there is
    nothing a classification could be checked against.

    Each candidate is classified through the same `triage_invoke.build_invocation`
    + `classify_severity` pair a fresh triage uses -- fails closed to `None`
    on a missing field, an out-of-rubric value, or a `confidence` that is not
    `high`. Only candidates that classify cleanly become decisions;
    `apply_severity_backfill` (T09) is the one call site that ever writes,
    and only when `apply=True`. A row that failed to classify carries no
    `severity` and is never handed to that call, so it issues zero
    `gh issue edit` calls regardless of `apply`.

    Returns `{"rubric": ..., "candidates": [...], "rows": [...], "reason":
    <str | None>}`. Each row is `{"number", "classified", "severity"}` plus,
    once `apply_severity_backfill` has run over it, that function's own
    `skipped`/`marker_written`/`label_written` fields.
    """
    rubric = read_severity_rubric(working_dir, runner=runner, repo=repo)
    if not rubric:
        return {
            "rubric": {},
            "candidates": [],
            "rows": [],
            "reason": (
                "the repository's severity rubric is empty -- nothing for a "
                "classification to be checked against"
            ),
        }

    candidates = triage.list_severity_backfill_candidates(runner, repo, limit=limit)

    if not candidates:
        return {
            "rubric": rubric,
            "candidates": [],
            "rows": [],
            "reason": (
                f"no severity-backfill candidates found in {repo} under limit={limit}"
            ),
        }

    rows = []
    decisions = []
    for issue in candidates:
        number = issue.get("number")
        title = issue.get("title", "")
        body = issue.get("body") or ""

        argv, prompt = build_invocation(
            number, title, body, repo, working_dir, model=model, effort=effort, rubric=rubric
        )
        invoked = run_claude(argv, prompt, runner=runner)
        severity = classify_severity(invoked.text, rubric)

        if severity is None:
            rows.append({"number": number, "classified": False, "severity": None})
            continue

        rows.append({"number": number, "classified": True, "severity": severity})
        decisions.append({"number": number, "body": body, "severity": severity})

    if apply and decisions:
        write_results = apply_severity_backfill(runner, repo, decisions)
        by_number = {result["number"]: result for result in write_results}
        for row in rows:
            result = by_number.get(row["number"])
            if result is not None:
                row.update(result)

    return {"rubric": rubric, "candidates": candidates, "rows": rows, "reason": None}


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
            "Amend every open, marked, severity-less issue with a severity, "
            "marker first, label projected after."
        ),
    )
    parser.add_argument("--repo", required=True, help="OWNER/NAME")
    parser.add_argument(
        "--limit", type=int, default=triage.DEFAULT_LIST_LIMIT,
        help="maximum number of candidates to select",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the amendments; default is a dry run that reports intent only",
    )
    return parser


def _print_run_report(report: dict) -> None:
    if report["reason"] is not None:
        print(report["reason"])
        return
    for row in report["rows"]:
        if not row["classified"]:
            print(f"#{row['number']}: no usable classification, skipped")
            continue
        print(f"#{row['number']}: severity={row['severity']}")


def main(argv: Optional[list] = None) -> int:
    warn_if_out_of_tree()
    args = build_parser().parse_args(argv)
    report = run_backfill(
        _default_runner, args.repo, apply=args.apply, limit=args.limit
    )
    _print_run_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
