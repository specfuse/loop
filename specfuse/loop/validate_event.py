#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Validate component-repo event log entries against the orchestrator's event schema.

This is the component-repo copy of the orchestrator's scripts/validate-event.py.
Per binding rules (rules/never-touch.md), schema files are NOT duplicated into
component repos. Instead, this script resolves the schema root from the
orchestrator at runtime.

Schema-root resolution (first match wins):
    1. SPECFUSE_SCHEMA_ROOT — absolute path to orchestrator/shared/schemas/
    2. Relative sibling-repo fallback: this file at .specfuse/scripts/ →
       <repo>/.specfuse/ → <repo> → <parent> → <parent>/orchestrator/shared/schemas/.
       Works when the orchestrator and component repos sit as siblings under
       the same parent directory (the standard local-dev layout).

Supported invocation patterns (only two):

    # Stdin — pipe a single event or a JSONL file:
    echo '{"timestamp": "...", ...}' | python3 .specfuse/scripts/validate-event.py
    cat events/FEAT-2026-0001.jsonl | python3 .specfuse/scripts/validate-event.py
    python3 .specfuse/scripts/validate-event.py --stdin   # explicit alias

    # File — pass a path to a .jsonl file:
    python3 .specfuse/scripts/validate-event.py --file events/FEAT-2026-0001.jsonl

Exit codes:
    0 — every event validated successfully
    1 — at least one event failed validation (details on stderr)
    2 — setup error (missing dependency, schema not found, bad input, etc.)

This script is the normative gate for appending to events/*.jsonl per
rules/verify-before-report.md §3 and the pr-submission / verification /
escalation component-agent skills.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write(
        "error: the 'jsonschema' package is required.\n"
        "       install it with: pip install 'jsonschema>=4.0'\n"
    )
    sys.exit(2)


def _resolve_schema_root() -> Path:
    """Return the orchestrator shared/schemas/ directory.

    Order:
        1. $SPECFUSE_SCHEMA_ROOT (absolute path)
        2. Sibling-repo fallback relative to this file's location:
           .specfuse/scripts/validate-event.py
             .parent  = .specfuse/scripts
             .parent  = .specfuse
             .parent  = <component-repo>
             .parent  = <workspace parent>
           Then / "orchestrator" / "shared" / "schemas".
    """
    env = os.environ.get("SPECFUSE_SCHEMA_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "orchestrator"
        / "shared"
        / "schemas"
    )


SCHEMA_ROOT = _resolve_schema_root()
SCHEMA_PATH = SCHEMA_ROOT / "event.schema.json"
PER_TYPE_SCHEMA_DIR = SCHEMA_ROOT / "events"


def load_validator() -> Draft202012Validator:
    if not SCHEMA_PATH.is_file():
        sys.stderr.write(
            f"error: schema not found at {SCHEMA_PATH}\n"
            "       set SPECFUSE_SCHEMA_ROOT to the absolute path of\n"
            "       orchestrator/shared/schemas/ (or place the orchestrator\n"
            "       repo as a sibling of this component repo).\n"
        )
        sys.exit(2)
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


_PER_TYPE_CACHE: dict[str, Draft202012Validator | None] = {}


def load_per_type_validator(event_type: str) -> Draft202012Validator | None:
    """Return a per-type payload validator if one exists, else None.

    Per-type schemas are additive: an event type without a schema file in
    PER_TYPE_SCHEMA_DIR validates against the top-level envelope alone,
    preserving the Phase 1 freeze contract for component-agent emissions
    whose per-type schemas have not been authored.
    """
    if event_type in _PER_TYPE_CACHE:
        return _PER_TYPE_CACHE[event_type]

    schema_file = PER_TYPE_SCHEMA_DIR / f"{event_type}.schema.json"
    if not schema_file.is_file():
        _PER_TYPE_CACHE[event_type] = None
        return None

    try:
        with schema_file.open("r", encoding="utf-8") as f:
            schema = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"error: failed to read per-type schema {schema_file}: {exc}\n")
        sys.exit(2)

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema raises SchemaError, keep generic
        sys.stderr.write(f"error: invalid per-type schema {schema_file}: {exc}\n")
        sys.exit(2)

    validator = Draft202012Validator(schema)
    _PER_TYPE_CACHE[event_type] = validator
    return validator


def format_error(source: str, line_number: int, path: str, message: str) -> str:
    location = f"{source}:{line_number}" if line_number else source
    prefix = f"{location}"
    if path:
        prefix += f" at {path}"
    return f"{prefix}: {message}"


def validate_line(
    validator: Draft202012Validator,
    source: str,
    line_number: int,
    raw: str,
) -> list[str]:
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [format_error(source, line_number, "", f"invalid JSON — {exc.msg} (line {exc.lineno}, col {exc.colno})")]

    errors: list[str] = []
    for err in sorted(validator.iter_errors(event), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(format_error(source, line_number, path, err.message))

    # Per-type payload validation. Applied only when the top-level envelope
    # is valid enough to name the event_type and the payload is a dict;
    # otherwise the top-level errors above are the signal.
    event_type = event.get("event_type") if isinstance(event, dict) else None
    payload = event.get("payload") if isinstance(event, dict) else None
    if isinstance(event_type, str) and isinstance(payload, dict):
        per_type = load_per_type_validator(event_type)
        if per_type is not None:
            for err in sorted(per_type.iter_errors(payload), key=lambda e: list(e.absolute_path)):
                sub_path = "/".join(str(p) for p in err.absolute_path) or "(root)"
                path = f"payload/{sub_path}" if sub_path != "(root)" else "payload"
                errors.append(format_error(source, line_number, path, err.message))

    return errors


def iter_lines_from_file(path: Path) -> list[tuple[int, str]]:
    if not path.is_file():
        sys.stderr.write(f"error: file not found: {path}\n")
        sys.exit(2)
    lines: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            stripped = raw.strip()
            if stripped:
                lines.append((lineno, stripped))
    return lines


def iter_lines_from_stdin() -> list[tuple[int, str]]:
    data = sys.stdin.read()
    if not data.strip():
        sys.stderr.write("error: no input on stdin\n")
        sys.exit(2)
    lines: list[tuple[int, str]] = []
    for lineno, raw in enumerate(data.splitlines(), start=1):
        stripped = raw.strip()
        if stripped:
            lines.append((lineno, stripped))
    return lines


_UNSUPPORTED_HINT = (
    "Supported invocation patterns:\n"
    "  cat events/FEAT-XXXX-NNNN.jsonl | .specfuse/scripts/validate-event.py     # stdin\n"
    "  .specfuse/scripts/validate-event.py --stdin                                 # stdin (explicit)\n"
    "  .specfuse/scripts/validate-event.py --file events/FEAT-XXXX-NNNN.jsonl    # file\n"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate events against the orchestrator's event schema.",
        epilog=_UNSUPPORTED_HINT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=Path,
        metavar="PATH",
        help="Path to a .jsonl file of events to validate.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        default=False,
        help="Explicitly read events from stdin (same behaviour as omitting --file).",
    )

    # Reject unsupported positional arguments before parsing flags.
    # argparse would otherwise accept them silently.
    known, unknown = parser.parse_known_args()
    if unknown:
        sys.stderr.write(
            f"error: unsupported argument(s): {' '.join(unknown)}\n\n"
            + _UNSUPPORTED_HINT
        )
        return 2

    args = known

    if args.file is not None and args.stdin:
        sys.stderr.write(
            "error: --file and --stdin are mutually exclusive.\n\n"
            + _UNSUPPORTED_HINT
        )
        return 2

    validator = load_validator()

    if args.file is not None:
        source = str(args.file)
        entries = iter_lines_from_file(args.file)
    else:
        # Both explicit --stdin and the no-flag default route here.
        source = "<stdin>"
        entries = iter_lines_from_stdin()

    all_errors: list[str] = []
    for lineno, raw in entries:
        all_errors.extend(validate_line(validator, source, lineno, raw))

    if all_errors:
        for msg in all_errors:
            sys.stderr.write(msg + "\n")
        sys.stderr.write(
            f"\n{len(all_errors)} validation error(s) across {len(entries)} event(s).\n"
        )
        return 1

    sys.stdout.write(
        f"ok: {len(entries)} event(s) validated against {SCHEMA_PATH.name}"
        f" (with per-type payload schemas under {PER_TYPE_SCHEMA_DIR.name}/ where present)\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
