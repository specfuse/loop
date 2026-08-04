#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Run validate_event.py over this repository's own event logs, over the
full envelope (FEAT-2026-0073/T02).

Repo-internal hygiene tooling (like leak_scan.py) — not shipped scaffold API.

Originally scoped to event_type errors only (FEAT-2026-0060/T02) because 279
correlation_id errors made a whole-envelope gate impossible: the vendored
envelope's correlation_id pattern rejected the closing-sequence (G<n>-CLOSE,
G<n>-PLAN, ...) and hygiene (TNNH) ID shapes
.specfuse/rules/correlation-ids.md documents as valid. FEAT-2026-0073/T01
closed that gap with a driver-local pattern widening
(specfuse/loop/validate_event.py's deep-copy fall-through), so this gate now
checks every envelope error, not event_type alone.

Exit codes:
    0 — no validation error across the corpus
    1 — at least one validation error (offenders on stderr)
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from specfuse.loop import validate_event  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / ".specfuse" / "features"


def main() -> int:
    validator = validate_event.load_validator()
    offenders: list[str] = []
    checked = 0

    event_files = sorted(FEATURES_DIR.glob("*/events.jsonl"))
    for path in event_files:
        for lineno, raw in validate_event.iter_lines_from_file(path):
            checked += 1
            offenders.extend(validate_event.validate_line(validator, str(path), lineno, raw))

    if offenders:
        for msg in offenders:
            sys.stderr.write(msg + "\n")
        sys.stderr.write(f"\n{len(offenders)} validation error(s).\n")
        return 1

    sys.stdout.write(
        f"ok: no validation errors across {len(event_files)} events.jsonl "
        f"file(s), {checked} event(s) checked\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
