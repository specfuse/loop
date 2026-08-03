#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every event_type the driver emits must resolve against the vendored envelope
enum or the driver-local registry (FEAT-2026-0060/T02).

Coverage note (LEARNINGS [FEAT-2026-0071/G1-CLOSE]): this guard covers
**event_type names only**. It does not cover payload shapes — the seven
driver-local types have no per-type payload schemas; FEAT-2026-0060's PLAN.md
scopes those OUT. A type passing this guard is not a claim its payload is
validated, only that its event_type string resolves.

The emitted-type set is derived at test time, never hard-coded, from two
independent sources so neither can drift silently:
  1. every string literal passed as build_event(...)'s first positional
     argument in specfuse/loop/loop.py (call-site derivation — catches types
     that have never fired in a recorded run, e.g. gate_auto_armed);
  2. every event_type value seen across this repository's own
     .specfuse/features/*/events.jsonl corpus (corpus derivation — catches
     anything call-site parsing might miss, e.g. a type built from a
     non-literal expression).
"""

from __future__ import annotations

import ast
import importlib.resources
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOOP_PY = REPO_ROOT / "specfuse" / "loop" / "loop.py"
FEATURES_DIR = REPO_ROOT / ".specfuse" / "features"

# Resolved independently of specfuse.loop.validate_event's module-level
# SCHEMA_ROOT: that constant is fixed at import time and some test modules
# (e.g. test_validate_event.py) reload the module against a temp schema root
# for the rest of the process. This test always wants the real vendored/
# driver-local schemas this repository ships, not whatever a sibling test
# last pointed the module at.
_REAL_SCHEMA_ROOT = importlib.resources.files("specfuse.loop").joinpath("data", "schemas")


def _call_site_event_types() -> set[str]:
    """Every string literal passed as build_event(...)'s first positional arg."""
    tree = ast.parse(LOOP_PY.read_text(encoding="utf-8"))
    types: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "build_event"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            types.add(node.args[0].value)
    return types


def _corpus_event_types() -> set[str]:
    """Every event_type value seen across this repo's own events.jsonl logs."""
    types: set[str] = set()
    for path in FEATURES_DIR.glob("*/events.jsonl"):
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("event_type") if isinstance(event, dict) else None
            if isinstance(event_type, str):
                types.add(event_type)
    return types


def _resolvable_types() -> set[str]:
    """Union of the vendored envelope enum and the driver-local registry —
    the same two-step fall-through validate_event.load_validator() builds."""
    vendored_schema = json.loads(
        _REAL_SCHEMA_ROOT.joinpath("event.schema.json").read_text(encoding="utf-8")
    )
    vendored_enum = set(vendored_schema["properties"]["event_type"]["enum"])

    driver_schema_path = _REAL_SCHEMA_ROOT.joinpath("driver-event.schema.json")
    driver_schema = json.loads(driver_schema_path.read_text(encoding="utf-8"))
    driver_types = set(driver_schema.get("event_types", []))

    return vendored_enum | driver_types


def _missing_types(emitted: set[str], resolvable: set[str]) -> list[str]:
    return sorted(emitted - resolvable)


class TestRegistryCoversEmitters(unittest.TestCase):

    def test_every_emitted_type_is_registered(self):
        """The FEAT-2026-0060 regression: an event_type with no registry entry
        makes validate_event.py reject the event outright."""
        emitted = _call_site_event_types() | _corpus_event_types()
        missing = _missing_types(emitted, _resolvable_types())
        self.assertEqual(
            missing, [],
            "event_type(s) emitted by the driver (build_event call sites and/or "
            "this repo's own events.jsonl corpus) that resolve against neither "
            "the vendored envelope enum nor driver-event.schema.json: "
            f"{missing}. validate_event.py will reject every event of this type.")

    def test_the_sweep_cannot_pass_vacuously(self):
        """A discovery walk that finds nothing satisfies 'all are registered' —
        guard against an empty emitted set reading as a clean sweep."""
        emitted = _call_site_event_types() | _corpus_event_types()
        self.assertGreaterEqual(
            len(emitted), 7,
            f"expected at least 7 emitted event types, found {len(emitted)}: "
            f"{sorted(emitted)}")

    def test_guard_fails_on_an_unregistered_type(self):
        """A guard never observed failing is a guard nobody knows works: feed
        the same check function a synthetic unregistered type and confirm it
        names the offender rather than passing vacuously."""
        emitted = _call_site_event_types() | {"a_synthetic_unregistered_type"}
        missing = _missing_types(emitted, _resolvable_types())
        self.assertEqual(missing, ["a_synthetic_unregistered_type"])


if __name__ == "__main__":
    unittest.main()
