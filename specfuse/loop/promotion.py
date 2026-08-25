# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Promotion ledger: which triaged feature issues became roadmap rows.

`triage.py` routes a `feature` decision to `roadmap-add`, and has since it
shipped. Nothing executed that route, and — the part that made it invisible —
nothing recorded when a human executed it by hand. So a triaged feature issue
had exactly one observable state forever after: labelled `triage:feature`,
open, indistinguishable from every other one whether or not its work was
already on the roadmap.

That is why the backlog could not be counted. "How many feature requests are
still waiting for a roadmap decision" was unanswerable, so it went unasked,
and thirteen issues accumulated with no one able to say which were live.

This module supplies the missing state, on the same terms `triage.py` uses:
an HTML-comment marker in the issue body is authoritative, `gh` is reached
through an injected runner, and filtering is client-side.

**Not the adoption path, and deliberately so.** `gh_features.list_features`
feeds `/adopt-feature`, and it requires the issue *title* to carry an
allocated ID (`[FEAT-YYYY-NNNN] ...`); an untagged title is skipped. That
suits issues an orchestrator filed with an ID already assigned. An inbound
feature request has free text and no ID — measured 2026-08-25, none of the
fifteen open `triage:feature` issues in this repository would survive that
filter, including the two whose titles *look* tagged (`[feature-FEAT-...]`
does not match). Allocating the ID is `roadmap-add`'s job, which is exactly
where `triage.py` already routes them. So this records promotions; it does
not perform adoption.
"""

from __future__ import annotations

import json
import re
from typing import Callable, Optional

from specfuse.loop.triage import FEATURE_LABEL

#: Shape of an allocated roadmap ID. Narrow on purpose: the ledger's whole
#: value is the link back to a real roadmap row, and a typo'd ID records a
#: link to nothing while looking exactly like a link to something.
FEATURE_ID_RE = re.compile(r"^FEAT-\d{4}-\d{4}$")

_MARKER_TEMPLATE = "<!-- specfuse:promoted feature_id={feature_id} -->"
_MARKER_RE = re.compile(r"<!-- specfuse:promoted feature_id=(?P<feature_id>\S+) -->")

#: `gh issue list` default page size, matching `monitor/issues.py`.
DEFAULT_LIST_LIMIT = 200


def render_marker(feature_id: str) -> str:
    """Render the promotion marker for `feature_id`.

    Raises `ValueError` on an ID that is not `FEAT-YYYY-NNNN` — refusing at
    render time means a malformed ID can never reach an issue body, where it
    would be a permanent broken link that reads as a valid one.
    """
    if not FEATURE_ID_RE.match(feature_id or ""):
        raise ValueError(f"not a feature id: {feature_id!r}")
    return _MARKER_TEMPLATE.format(feature_id=feature_id)


def parse_marker(body: str) -> Optional[str]:
    """Return the feature ID `body`'s promotion marker carries, or None."""
    match = _MARKER_RE.search(body or "")
    if match is None:
        return None
    return match.group("feature_id")


def is_promoted(body: str) -> bool:
    """True when `body` records a promotion. The question the backlog count
    could not answer before this module existed."""
    return parse_marker(body) is not None


def _list_labelled(runner: Callable, repo: str, *, limit: int) -> list:
    result = runner(
        [
            "gh", "issue", "list",
            "--repo", repo,
            "--label", FEATURE_LABEL,
            "--state", "open",
            "--limit", str(limit),
            "--json", "number,title,body,labels",
        ],
        check=False,
    )
    if getattr(result, "returncode", 1) != 0 or not getattr(result, "stdout", ""):
        return []
    try:
        parsed = json.loads(result.stdout)
    except ValueError:
        return []
    return parsed if isinstance(parsed, list) else []


def list_unpromoted(runner: Callable, repo: str, limit: int = DEFAULT_LIST_LIMIT) -> list:
    """Return open `triage:feature` issues carrying no promotion marker.

    The backlog awaiting a roadmap decision. Filters on the marker rather
    than on a label, because the marker is what a promotion writes and a
    label can be added or removed by anyone at any time.

    A `gh` failure yields an empty list, matching `triage.list_untriaged`'s
    contract — but note the asymmetry that creates and do not read too much
    into a zero: an empty result means "nothing waiting" OR "could not ask".
    Callers that report a count to a human should say which, and
    `/attention` does.
    """
    rows = []
    for issue in _list_labelled(runner, repo, limit=limit):
        body = issue.get("body") or ""
        if is_promoted(body):
            continue
        row = dict(issue)
        row["promoted"] = False
        rows.append(row)
    return rows


def list_promoted(runner: Callable, repo: str, limit: int = DEFAULT_LIST_LIMIT) -> list:
    """Return open `triage:feature` issues that DO carry a marker, each with
    the `feature_id` it became.

    An issue promoted but still open is not a defect — the roadmap row can
    land long before the work does, and closing it then would lose the
    request while its feature is still unbuilt.
    """
    rows = []
    for issue in _list_labelled(runner, repo, limit=limit):
        feature_id = parse_marker(issue.get("body") or "")
        if feature_id is None:
            continue
        row = dict(issue)
        row["promoted"] = True
        row["feature_id"] = feature_id
        rows.append(row)
    return rows


def record_promotion(
    runner: Callable,
    repo: str,
    number: int,
    feature_id: str,
    body: str,
) -> dict:
    """Record that issue `number` became `feature_id`. Idempotent.

    Returns a report mapping: `number`, `feature_id`, `written` (False when
    it was already recorded), and `already` (the ID a prior marker carried,
    present only when this call wrote nothing).

    Validates before writing, so a bad ID costs nothing. A body that already
    carries a marker is never rewritten — including when the recorded ID
    differs from the one passed. Silently repointing a promotion would erase
    the only record of where the work actually went; the caller is told and
    decides.
    """
    if not FEATURE_ID_RE.match(feature_id or ""):
        raise ValueError(f"not a feature id: {feature_id!r}")

    existing = parse_marker(body)
    if existing is not None:
        return {
            "number": number,
            "feature_id": feature_id,
            "written": False,
            "already": existing,
        }

    marker = render_marker(feature_id)
    new_body = f"{body}\n\n{marker}" if body else marker
    runner(
        ["gh", "issue", "edit", str(number), "--repo", repo, "--body", new_body],
        check=True,
    )
    return {"number": number, "feature_id": feature_id, "written": True}


def _gh_runner(args: list, check: bool = False):
    import subprocess
    return subprocess.run(args, capture_output=True, text=True, check=check)


def main(argv: list | None = None, *, runner: Callable = _gh_runner) -> int:
    """CLI: `list` the unpromoted backlog, or `record` a promotion.

    A real entry point, not a convenience. A ledger nothing can write to is
    the hollow shape recorded as `[FEAT-2026-0008/G1-CLOSE]` — the mechanism
    passes its tests and the state it exists to track never changes. The
    `/roadmap-add` interview should call `record` on accept; until it does,
    this is what a human uses, and the ledger is populated either way.

        python3 -m specfuse.loop.promotion list <repo>
        python3 -m specfuse.loop.promotion record <repo> <issue> <FEAT-ID>
    """
    import sys

    args = sys.argv[1:] if argv is None else argv
    if len(args) >= 2 and args[0] == "list":
        rows = list_unpromoted(runner, args[1])
        if not rows:
            print("no unpromoted triage:feature issues (or gh was unreachable)")
            return 0
        print(f"{len(rows)} triage:feature issue(s) awaiting a roadmap decision:")
        for row in rows:
            print(f"  #{row['number']:<6} {(row.get('title') or '')[:64]}")
        return 0

    if len(args) >= 4 and args[0] == "record":
        _cmd, repo, number, feature_id = args[0], args[1], args[2], args[3]
        result = runner(
            ["gh", "issue", "view", str(number), "--repo", repo, "--json", "body"],
            check=False,
        )
        if getattr(result, "returncode", 1) != 0:
            print(f"error: could not read issue #{number}", file=sys.stderr)
            return 1
        try:
            body = json.loads(result.stdout).get("body") or ""
        except ValueError:
            print(f"error: could not parse issue #{number}", file=sys.stderr)
            return 1
        try:
            report = record_promotion(runner, repo, number, feature_id, body)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if report["written"]:
            print(f"recorded: #{number} -> {feature_id}")
        else:
            print(
                f"already recorded: #{number} -> {report['already']}"
                + (f" (not repointed to {feature_id})"
                   if report["already"] != feature_id else "")
            )
        return 0

    print(
        "usage:\n"
        "  python3 -m specfuse.loop.promotion list <repo>\n"
        "  python3 -m specfuse.loop.promotion record <repo> <issue> <FEAT-ID>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    import sys
    sys.exit(main())
