#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Validate event log entries against the loop's vendored event schema.

The event schema is the shared Specfuse methodology substrate, consolidated in
the core at specfuse/methodology/schemas/ and vendored into this package under
specfuse/loop/data/schemas/ (see scripts/sync-scaffold.sh). This script reads
that vendored copy — there is no cross-repo path dependency.

Schema-root resolution (first match wins):
    1. SPECFUSE_SCHEMA_ROOT — absolute path to a schemas/ directory (an
       override/escape hatch; also used by the test suite to point at a
       self-contained temporary schema root).
    2. The package's own vendored copy: specfuse/loop/data/schemas/, located via
       importlib.resources — the same mechanism scaffold.py uses for packaged
       data.

A driver-emitted event's event_type resolves in two steps (FEAT-2026-0060):
first against the vendored envelope's event_type enum (event.schema.json,
do-not-touch — owned by the orchestrator repo this schema is vendored from);
only when absent there does it fall through to driver-event.schema.json, a
registry this repository owns for driver-local mechanics the orchestrator has
no concept of (gate_reached, attempt_outcome, ...). A missing or unreadable
driver-event.schema.json degrades to vendored-only validation rather than
raising, mirroring load_per_type_validator's additive contract.

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
import copy
import importlib.resources
import json
import os
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:
    sys.stderr.write(
        "error: the 'jsonschema' package is required.\n"
        "       install it with: pip install 'jsonschema>=4.0'\n"
    )
    sys.exit(2)


def _resolve_schema_root():
    """Return the schemas/ directory to validate against.

    Order:
        1. $SPECFUSE_SCHEMA_ROOT (absolute path) — override / escape hatch, also
           used by the test suite to point at a self-contained temporary root.
        2. The package's own vendored copy: specfuse/loop/data/schemas/, located
           via importlib.resources (the same mechanism scaffold.py uses). This is
           a byte-for-byte copy of the methodology core's schemas — no cross-repo
           path dependency.

    The env branch returns a filesystem Path; the default branch returns an
    importlib.resources Traversable. Both support the .is_file()/.open()/`/`/
    .name operations the rest of this module uses.
    """
    env = os.environ.get("SPECFUSE_SCHEMA_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    return importlib.resources.files("specfuse.loop").joinpath("data", "schemas")


SCHEMA_ROOT = _resolve_schema_root()
SCHEMA_PATH = SCHEMA_ROOT / "event.schema.json"
PER_TYPE_SCHEMA_DIR = SCHEMA_ROOT / "events"
DRIVER_SCHEMA_PATH = SCHEMA_ROOT / "driver-event.schema.json"


_DRIVER_EVENT_TYPES_CACHE: frozenset[str] | None = None
_UNSET = object()
_DRIVER_CORRELATION_PATTERNS_CACHE: dict | None | object = _UNSET


def load_driver_event_types() -> frozenset[str]:
    """Return the driver-local event-type registry (FEAT-2026-0060).

    Additive to the vendored envelope's event_type enum: types listed here are
    driver mechanics the orchestrator schema has no concept of (gate_reached,
    attempt_outcome, gate_auto_armed, re_arm_rejected, ...). The last two are
    emitted by real code paths that have never fired in a recorded run, so a
    corpus-only sweep misses them — the registry is derived from the union of
    build_event(...) call sites and the corpus, not the corpus alone.
    task_started/task_completed/human_escalation are already in the vendored
    enum and must not appear here — see driver-event.schema.json's own
    description.

    A missing or unreadable registry file degrades to an empty set rather than
    raising, matching load_per_type_validator's additive contract.
    """
    global _DRIVER_EVENT_TYPES_CACHE
    if _DRIVER_EVENT_TYPES_CACHE is not None:
        return _DRIVER_EVENT_TYPES_CACHE

    try:
        with DRIVER_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        types = frozenset(schema.get("event_types", []))
    except (OSError, json.JSONDecodeError):
        types = frozenset()

    _DRIVER_EVENT_TYPES_CACHE = types
    return types


def load_driver_correlation_patterns() -> dict | None:
    """Return the driver-local correlation_id shape registry, or None.

    Additive to the vendored envelope's ``correlation_id`` pattern
    (FEAT-2026-0073): closing-sequence units (``G<n>-<NAME>``) and hygiene
    units (``T<NN>H[N...]``) are shapes `.specfuse/rules/correlation-ids.md`
    documents but the vendored pattern rejects. ``closing_names`` and
    ``hygiene_suffix_pattern`` here are read by ``_widen_correlation_id_pattern``
    to build a widened pattern on a deep copy of the vendored schema; the file
    on disk is never touched.

    A missing, unreadable, or structurally incomplete registry file degrades
    to None (no widening — vendored-only validation) rather than raising,
    matching ``load_driver_event_types``'s existing contract.
    """
    global _DRIVER_CORRELATION_PATTERNS_CACHE
    if _DRIVER_CORRELATION_PATTERNS_CACHE is not _UNSET:
        return _DRIVER_CORRELATION_PATTERNS_CACHE

    patterns: dict | None
    try:
        with DRIVER_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        raw = schema.get("correlation_id")
        if (
            isinstance(raw, dict)
            and isinstance(raw.get("closing_names"), list)
            and raw["closing_names"]
            and isinstance(raw.get("hygiene_suffix_pattern"), str)
        ):
            patterns = {
                "closing_names": sorted(str(n) for n in raw["closing_names"]),
                "hygiene_suffix_pattern": raw["hygiene_suffix_pattern"],
            }
        else:
            patterns = None
    except (OSError, json.JSONDecodeError):
        patterns = None

    _DRIVER_CORRELATION_PATTERNS_CACHE = patterns
    return patterns


def _widen_correlation_id_pattern(vendored_pattern: str, patterns: dict) -> str:
    """Widen the vendored ``(/T\\d{2})?$`` task-id tail to also admit the
    closing-sequence and hygiene shapes ``patterns`` describes.

    Additive only: every string the vendored pattern accepted still matches
    the result, since ``T\\d{2}`` remains one branch of the widened
    alternation. If the vendored pattern's tail does not look as expected,
    the pattern is returned unchanged rather than guessing.
    """
    old_tail = r"(/T\d{2})?$"
    if not vendored_pattern.endswith(old_tail):
        return vendored_pattern

    closing_alt = "|".join(patterns["closing_names"])
    hygiene = patterns["hygiene_suffix_pattern"]
    new_tail = rf"(/(T\d{{2}}({hygiene})?|G\d+-({closing_alt})))?$"
    return vendored_pattern[: -len(old_tail)] + new_tail


def load_validator() -> Draft202012Validator:
    if not SCHEMA_PATH.is_file():
        sys.stderr.write(
            f"error: schema not found at {SCHEMA_PATH}\n"
            "       the vendored schema ships under specfuse/loop/data/schemas/;\n"
            "       set SPECFUSE_SCHEMA_ROOT to override the schemas/ directory.\n"
        )
        sys.exit(2)
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    # Fall-through resolution (FEAT-2026-0060): a driver event's event_type
    # resolves against the vendored envelope enum first; only types absent
    # there are admitted from the driver-local registry. Implemented as a
    # union on a deep copy so the vendored schema on disk is never touched.
    driver_types = load_driver_event_types()
    correlation_patterns = load_driver_correlation_patterns()
    if driver_types or correlation_patterns:
        schema = copy.deepcopy(schema)
        if driver_types:
            enum = schema["properties"]["event_type"]["enum"]
            enum.extend(sorted(t for t in driver_types if t not in enum))
        if correlation_patterns:
            # Same deep-copy fall-through (FEAT-2026-0073): widen
            # correlation_id to also admit closing-sequence and hygiene
            # shapes documented in correlation-ids.md, on the same copy.
            correlation_id_prop = schema["properties"]["correlation_id"]
            correlation_id_prop["pattern"] = _widen_correlation_id_pattern(
                correlation_id_prop["pattern"], correlation_patterns
            )

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
    except SchemaError as exc:
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
        description="Validate events against the loop's vendored event schema.",
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
