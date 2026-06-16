#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Content-scan runner — scan a GitHub event payload for leaks (FEAT-2026-0024/T03).

Reads a single GitHub event payload (the JSON at ``$GITHUB_EVENT_PATH``) and
scans the title/body/comment fields present for the triggering event, exiting
non-zero on any finding and naming the offending field. This is the
unit-testable seam gate 2's Action (T04) invokes.

It does NOT re-derive the scanner: it reuses gate 1's :func:`leak_scan.scan_text`
(full structural + plaintext denylist + gitleaks) and the hashed-denylist
primitives (:func:`leak_scan.load_hashed_denylist`,
:func:`leak_scan.hashed_denylist_hits`) as a library.

Scope is the fields present in the single event payload — the new-content
surface the Action fires on per open/edit:
  - ``issues``                          -> issue.title, issue.body
  - ``pull_request``                    -> pull_request.title, pull_request.body
  - ``issue_comment`` /
    ``pull_request_review_comment``     -> comment.body

Whole-history scanning would require the REST API, flagged unreliable inside
dispatched subprocesses (LEARNINGS FEAT-2026-0014/T01/gh-claudeP-broken); it is
an Open Verification for the operator, not committed here. Closes the runner
half of issue #46.

Public API:
  scan_event(payload, hashes_path=None) -> list[str]
  main(argv) -> int
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import leak_scan

# Fields scanned, in (field-name, payload-path) form. The field name is what a
# finding is prefixed with; the path is the nested-key lookup into the payload.
# Missing fields are skipped — a given event carries only its own subset.
_SCAN_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("issue.title", ("issue", "title")),
    ("issue.body", ("issue", "body")),
    ("pull_request.title", ("pull_request", "title")),
    ("pull_request.body", ("pull_request", "body")),
    ("comment.body", ("comment", "body")),
)


def _dig(payload: dict, path: tuple[str, ...]) -> object:
    """Return the nested value at *path*, or None if any step is missing."""
    cur: object = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def scan_event(payload: dict, hashes_path: Path | None = None) -> list[str]:
    """Scan the fields present in *payload* for leaks.

    Extracts the title/body/comment fields present (missing fields skipped,
    never crash), scans each with the gate-1 scanner (:func:`leak_scan.scan_text`
    — full structural + plaintext denylist + gitleaks) plus the committed hashed
    denylist, and returns findings each prefixed with the originating field name
    (``issue.body: <finding>``). An empty list means clean.

    The hashed denylist is loaded via gate 1's
    :func:`leak_scan.load_hashed_denylist`; when the ``.hashes`` file is absent
    it contributes nothing (no crash), mirroring ``scan_repo``'s additive
    behavior.
    """
    salt, lengths, hashes = leak_scan.load_hashed_denylist(hashes_path)
    findings: list[str] = []
    for field_name, path in _SCAN_FIELDS:
        value = _dig(payload, path)
        if not isinstance(value, str):
            continue
        for hit in leak_scan.scan_text(value):
            findings.append(f"{field_name}: {hit}")
        if hashes:
            for lineno, line in enumerate(value.splitlines() or [value], 1):
                if leak_scan.hashed_denylist_hits(line, salt, lengths, hashes):
                    findings.append(f"{field_name}: line {lineno}: denylist-hash")
    return findings


def main(argv: list[str] | None = None) -> int:
    """CLI entry: scan the event payload, print findings, return 1 on any hit.

    Reads the event-payload path from an explicit ``--event-path`` argument,
    falling back to the ``GITHUB_EVENT_PATH`` environment variable by name (never
    by reading any secret). A missing or unparseable event file returns a
    non-zero exit with a diagnostic — fail closed: an unreadable payload is not a
    pass.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan a GitHub event payload for leaks (FEAT-2026-0024). "
        "Exit 1 on any finding, non-zero on an unreadable payload."
    )
    parser.add_argument(
        "--event-path",
        default=None,
        help="path to the event-payload JSON; defaults to $GITHUB_EVENT_PATH",
    )
    parser.add_argument(
        "--hashes-path",
        default=None,
        help="path to a leak_denylist.hashes file; defaults to the committed one",
    )
    args = parser.parse_args(argv)

    event_path = args.event_path or os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print(
            "leak-scan-content: no event path (pass --event-path or set "
            "GITHUB_EVENT_PATH)",
            file=sys.stderr,
        )
        return 2

    try:
        raw = Path(event_path).read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"leak-scan-content: cannot read event payload {event_path!r}: {exc}",
            file=sys.stderr,
        )
        return 2

    if not isinstance(payload, dict):
        print(
            f"leak-scan-content: event payload {event_path!r} is not a JSON object",
            file=sys.stderr,
        )
        return 2

    hashes_path = Path(args.hashes_path) if args.hashes_path else None
    findings = scan_event(payload, hashes_path)
    if findings:
        print("leak-scan-content: FINDINGS")
        for f in findings:
            print("  " + f)
        return 1
    print("leak-scan-content: clean")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
