#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Replay a work unit's recorded attempts through the CURRENT parser.

Answers one question without spending anything: given the driver in this
checkout, would the early spin halt have fired on a past escalation, and at
which attempt?

Two sources are read and reported side by side, because they can disagree:

``recorded``
    The ``(failure_class, failure_signature)`` the driver stored in
    ``events.jsonl`` at run time — what the parser of the day produced.
``replayed``
    What `parse_gate_failure_signature` in this checkout produces from the
    attempt note's raw gate output — what the parser of today would produce.

A row whose recorded value is the ``('other', 'no_gate_marker')`` sentinel
while its replayed value is anything else is a failure the old parser could
not name. Those matter beyond diagnosis:
`detect_spinning_signature_repeat` explicitly ignores that sentinel, so
while a gate produced it the early halt could not fire at all — the shape
#2557 fixed for hyphenated gate names.

**This tool grants no verdict and mutates nothing.** It reads
``events.jsonl`` and the persisted attempt notes and prints. It is a
diagnostic answering "would the driver have caught this?", which is the
cheap counterpart to re-running an escalation at full price.

Run it from a checkout at the revision you want to measure. The
`.specfuse/scripts/replay_spin.py` shim path-inserts the repo root so
``specfuse.loop`` resolves from source rather than from an installed build —
measuring the installed build while believing you measured the checkout is
its own recorded defect (#2642), and the ``driver source`` line this tool
prints first exists so that mistake is visible rather than silent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

#: Returned by `parse_gate_failure_signature` when no `### <gate>: FAIL`
#: marker was found. Duplicated as a literal rather than imported so this
#: module stays importable for tests that stub the driver.
NO_MARKER = ("other", "no_gate_marker")


def read_recorded_attempts(feature_dir: Path,
                           wu_filter: Optional[str] = None) -> list[dict]:
    """Non-passing `attempt_outcome` rows for *wu_filter*, in file order.

    Passing attempts are skipped: a spin question is only about the
    failures. A missing or unreadable `events.jsonl` yields `[]` rather than
    raising — this is a diagnostic, and a repository with no event log is a
    fact to report, not an error to crash on.
    """
    events = feature_dir / "events.jsonl"
    if not events.is_file():
        return []
    rows: list[dict] = []
    for line in events.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue  # a truncated tail is survivable; earlier rows still count
        if event.get("event_type") != "attempt_outcome":
            continue
        correlation_id = event.get("correlation_id", "")
        if wu_filter and not correlation_id.endswith(wu_filter):
            continue
        payload = event.get("payload") or {}
        if payload.get("outcome") == "passed":
            continue
        rows.append({
            "wu_id": correlation_id,
            "attempt": payload.get("attempt"),
            "cost_usd": payload.get("cost_usd") or 0.0,
            "recorded": (payload.get("failure_class"),
                         payload.get("failure_signature")),
        })
    return rows


def read_attempt_note(feature_dir: Path, wu_id: str, attempt) -> Optional[str]:
    """The persisted attempt note's text, or None when it was not kept.

    Notes are buffered during a run and only written to disk when the unit
    escalates; a unit that eventually passed discards them as scratch. So a
    missing note is the normal case for a healthy unit, not a fault.
    """
    note = (feature_dir / "work" / wu_id.replace("/", "_")
            / f"attempt-{attempt}.md")
    return note.read_text(errors="replace") if note.is_file() else None


def replay(feature_dir: Path, wu_filter: Optional[str], parse_fn,
           spin_fn) -> dict:
    """Re-derive each attempt's signature and find where a spin halt fires.

    `parse_fn` and `spin_fn` are injected rather than imported at module
    scope so a test can drive this against known inputs without depending on
    the live parser's current behaviour — the behaviour under test here is
    the replay logic, not the parser.
    """
    rows = read_recorded_attempts(feature_dir, wu_filter)
    prior = None
    halt_at = None
    for row in rows:
        note = read_attempt_note(feature_dir, row["wu_id"], row["attempt"])
        row["replayed"] = parse_fn(note) if note is not None else None
        row["note_missing"] = note is None
        # Only a re-parsed signature counts as "recovered": the recorded
        # sentinel with no note to re-read tells us nothing either way.
        row["recovered"] = (row["recorded"] == NO_MARKER
                            and row["replayed"] is not None
                            and row["replayed"] != NO_MARKER)
        if row["replayed"] is not None:
            if halt_at is None and spin_fn(row["replayed"], prior):
                halt_at = row["attempt"]
            prior = row["replayed"]
    spent = sum(r["cost_usd"] for r in rows)
    # What a halt would have avoided is strictly the attempts *after* it:
    # the attempt that trips the detector has already been paid for.
    avoidable = 0.0
    if halt_at is not None:
        avoidable = sum(r["cost_usd"] for r in rows
                        if (r["attempt"] or 0) > halt_at)
    return {
        "rows": rows,
        "halt_at": halt_at,
        "spent_usd": spent,
        "avoidable_usd": avoidable,
    }


def format_report(result: dict, driver_source: str, max_attempts) -> str:
    lines = [f"driver source: {driver_source}",
             f"MAX_ATTEMPTS:  {max_attempts}", ""]
    if not result["rows"]:
        lines.append("no non-passing attempt_outcome rows found "
                     "(nothing recorded, or the work-unit filter matched nothing)")
        return "\n".join(lines)
    for row in result["rows"]:
        lines.append(f"attempt {row['attempt']}  ${row['cost_usd']:.2f}")
        lines.append(f"  recorded  {row['recorded']}")
        if row["note_missing"]:
            lines.append("  replayed  (no attempt note on disk — cannot re-parse)")
        else:
            flag = "  <-- OLD PARSER COULD NOT NAME THIS" if row["recovered"] else ""
            lines.append(f"  replayed  {row['replayed']}{flag}")
        if result["halt_at"] == row["attempt"]:
            lines.append(f"  >>> early spin halt WOULD fire here "
                         f"(attempt {row['attempt']})")
    lines.append("")
    lines.append(f"recorded spend across non-passing attempts: "
                 f"${result['spent_usd']:.2f}")
    if result["halt_at"] is not None:
        lines.append(f"early halt at attempt {result['halt_at']} — "
                     f"${result['avoidable_usd']:.2f} of that would not "
                     f"have been spent")
    else:
        lines.append("early spin halt would NOT fire on this sequence "
                     "(signatures differ each attempt, or notes are missing)")
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay a work unit's recorded attempts through the "
                    "current failure-signature parser.")
    parser.add_argument("feature_dir",
                        help="path to a .specfuse/features/FEAT-... folder")
    parser.add_argument("wu", nargs="?", default=None,
                        help="work-unit suffix to filter on, e.g. T04")
    args = parser.parse_args(argv)

    from specfuse.loop import loop as driver

    result = replay(Path(args.feature_dir), args.wu,
                    driver.parse_gate_failure_signature,
                    driver.detect_spinning_signature_repeat)
    print(format_report(result, driver.__file__, driver.MAX_ATTEMPTS))
    return 0 if result["rows"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
