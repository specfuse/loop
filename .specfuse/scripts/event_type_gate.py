#!/usr/bin/env python3
#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Run validate_event.py over this repository's own event logs, scoped to
event_type errors only (FEAT-2026-0060/T02).

Repo-internal hygiene tooling (like leak_scan.py) — not shipped scaffold API.

An unconditional "any validation error" gate cannot be green on this tree:
279 correlation_id errors remain across 36 files because the vendored
envelope's correlation_id pattern rejects the closing-sequence (G<n>-CLOSE,
G<n>-PLAN, ...) and hygiene (TNNH) ID shapes
.specfuse/rules/correlation-ids.md documents as valid (FEAT-2026-0073, not this
feature's work). This gate is deliberately scoped to event_type errors —
the gap FEAT-2026-0060 exists to close — so it can be wired now instead of
waiting on 0073, and widened once 0073 lands.

Exit codes:
    0 — no event_type validation error across the corpus
    1 — at least one event_type validation error (offenders on stderr)
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

    for path in sorted(FEATURES_DIR.glob("*/events.jsonl")):
        for lineno, raw in validate_event.iter_lines_from_file(path):
            errors = validate_event.validate_line(validator, str(path), lineno, raw)
            offenders.extend(err for err in errors if " at event_type:" in err or err.endswith("at event_type"))

    if offenders:
        for msg in offenders:
            sys.stderr.write(msg + "\n")
        sys.stderr.write(f"\n{len(offenders)} event_type validation error(s).\n")
        return 1

    sys.stdout.write(
        f"ok: no event_type validation errors across "
        f"{len(list(FEATURES_DIR.glob('*/events.jsonl')))} events.jsonl file(s)\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
