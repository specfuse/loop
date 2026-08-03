#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the driver-local event-type registry (FEAT-2026-0060).

The vendored envelope schema (specfuse/loop/data/schemas/event.schema.json)
does not know about the seven event_type values the loop driver actually
emits (attempt_outcome, gate_reached, ...). This registry
(specfuse/loop/data/schemas/driver-event.schema.json) sanctions them without
touching the vendored file, and validate_event.py resolves an event's
event_type against the vendored enum first, falling through to this registry
only when absent there.

These tests exercise the REAL package schemas under specfuse/loop/data/schemas
(no SPECFUSE_SCHEMA_ROOT override) — the point is to prove the packaged
registry, not a synthetic stand-in.
"""

from __future__ import annotations

import importlib.resources
import json
import unittest
from pathlib import Path
from unittest import mock

import specfuse.loop.validate_event as ve

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_DRIVER_LOG = (
    REPO_ROOT
    / ".specfuse/features/FEAT-2026-0062-lifetime-cost-reads/events.jsonl"
)
FEATURES_DIR = REPO_ROOT / ".specfuse/features"

# The real packaged schema root — resolved independently of whatever
# SPECFUSE_SCHEMA_ROOT / module-reload state other test modules (e.g.
# test_validate_event.py, which reloads this same singleton module against a
# synthetic tempdir schema root and never restores it) may have left behind.
_REAL_SCHEMA_ROOT = importlib.resources.files("specfuse.loop").joinpath(
    "data", "schemas"
)
_REAL_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "event.schema.json"
_REAL_PER_TYPE_DIR = _REAL_SCHEMA_ROOT / "events"
_REAL_DRIVER_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "driver-event.schema.json"

_ALREADY_SANCTIONED = {"task_started", "task_completed", "human_escalation"}


class _RealSchemaRootTestCase(unittest.TestCase):
    """Base class: pin ve's module globals to the real packaged schemas for
    the duration of each test, regardless of import order across test files."""

    def setUp(self) -> None:
        super().setUp()
        patches = [
            mock.patch.object(ve, "SCHEMA_ROOT", _REAL_SCHEMA_ROOT),
            mock.patch.object(ve, "SCHEMA_PATH", _REAL_SCHEMA_PATH),
            mock.patch.object(ve, "PER_TYPE_SCHEMA_DIR", _REAL_PER_TYPE_DIR),
            mock.patch.object(ve, "DRIVER_SCHEMA_PATH", _REAL_DRIVER_SCHEMA_PATH),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        ve._PER_TYPE_CACHE.clear()
        ve._DRIVER_EVENT_TYPES_CACHE = None
        self.addCleanup(ve._PER_TYPE_CACHE.clear)
        self.addCleanup(setattr, ve, "_DRIVER_EVENT_TYPES_CACHE", None)


def _valid_event(**overrides: object) -> dict:
    base: dict = {
        "timestamp": "2026-04-20T14:32:05Z",
        "correlation_id": "FEAT-2026-0001",
        "event_type": "task_completed",
        "source": "driver",
        "source_version": "0.8.0",
        "payload": {},
    }
    base.update(overrides)
    return base


class TestDriverEventTypes(_RealSchemaRootTestCase):
    """Criteria 1-2: the real driver log is red before this WU, green after."""

    def test_real_driver_log_validates(self) -> None:
        self.assertTrue(
            REAL_DRIVER_LOG.is_file(), f"fixture missing: {REAL_DRIVER_LOG}"
        )
        validator = ve.load_validator()
        all_errors: list[str] = []
        with REAL_DRIVER_LOG.open("r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                stripped = raw.strip()
                if not stripped:
                    continue
                all_errors.extend(
                    ve.validate_line(validator, REAL_DRIVER_LOG.name, lineno, stripped)
                )
        self.assertEqual(
            all_errors, [], f"expected zero errors; got {all_errors!r}"
        )


class TestDriverLocalRegistrySanctionsDerivedTypes(_RealSchemaRootTestCase):
    """Criterion 4: every corpus-derived type is sanctioned in the registry."""

    # Union of every build_event(...) call site in specfuse/loop/loop.py and a
    # corpus sweep of every .specfuse/features/*/events.jsonl (see result for
    # the full derivation), minus the vendored envelope enum. Seven of these
    # match PLAN.md's corpus-only measurement; gate_auto_armed and
    # re_arm_rejected are additional — both are emitted by real code paths
    # that have never fired in a recorded run, so a corpus-only sweep cannot
    # see them.
    DERIVED_TYPES = frozenset({
        "attempt_outcome",
        "gate_reached",
        "auto_close_decision",
        "arm_predicate_evaluated",
        "re_arm_dispatched",
        "plan_next_draft_lint",
        "unsandboxed_dispatch",
        "gate_auto_armed",
        "re_arm_rejected",
    })

    # Call-site-only types: absent from any recorded corpus, present only
    # because a build_event(...) call site emits them (FEAT-2026-0060/T01
    # attempt 3 — a corpus-only derivation demonstrably omits these).
    CALL_SITE_ONLY_TYPES = frozenset({"gate_auto_armed", "re_arm_rejected"})

    def test_registry_contains_every_derived_type(self) -> None:
        registered = ve.load_driver_event_types()
        missing = self.DERIVED_TYPES - registered
        self.assertFalse(missing, f"types missing from registry: {missing}")

    def test_registry_contains_call_site_only_types(self) -> None:
        registered = ve.load_driver_event_types()
        missing = self.CALL_SITE_ONLY_TYPES - registered
        self.assertFalse(
            missing,
            f"call-site-only types missing from registry (a corpus-only "
            f"derivation would miss these): {missing}",
        )

    def test_each_derived_type_validates_via_fallthrough(self) -> None:
        validator = ve.load_validator()
        for event_type in self.DERIVED_TYPES:
            with self.subTest(event_type=event_type):
                errors = ve.validate_line(
                    validator, "<test>", 1,
                    json.dumps(_valid_event(event_type=event_type)),
                )
                self.assertEqual(errors, [], f"{event_type}: {errors!r}")


class TestFallThroughNotDuplication(_RealSchemaRootTestCase):
    """Criterion 6: already-sanctioned types keep validating via the vendored
    enum and must NOT be duplicated into the driver-local registry."""

    def test_already_sanctioned_types_still_validate(self) -> None:
        validator = ve.load_validator()
        for event_type in _ALREADY_SANCTIONED:
            with self.subTest(event_type=event_type):
                errors = ve.validate_line(
                    validator, "<test>", 1,
                    json.dumps(_valid_event(event_type=event_type)),
                )
                self.assertEqual(errors, [], f"{event_type}: {errors!r}")

    def test_already_sanctioned_types_absent_from_driver_registry(self) -> None:
        registered = ve.load_driver_event_types()
        overlap = _ALREADY_SANCTIONED & registered
        self.assertFalse(
            overlap,
            f"already-vendored types must not be duplicated into the "
            f"driver-local registry: {overlap}",
        )


class TestClosedSet(_RealSchemaRootTestCase):
    """Criterion 7: an event_type in neither registry still fails."""

    def test_unknown_event_type_is_rejected(self) -> None:
        validator = ve.load_validator()
        errors = ve.validate_line(
            validator, "<test>", 1,
            json.dumps(_valid_event(event_type="totally_unregistered_type_xyz")),
        )
        self.assertTrue(errors, "expected validation errors for an unknown type")
        self.assertTrue(
            any("event_type" in e for e in errors),
            f"expected an event_type error; got {errors!r}",
        )


class TestMissingRegistryDegradesGracefully(_RealSchemaRootTestCase):
    """Criterion 8: a missing/unreadable driver-local registry file degrades
    to vendored-only validation rather than raising."""

    def test_missing_file_returns_empty_set(self) -> None:
        with mock.patch.object(
            ve, "DRIVER_SCHEMA_PATH", Path("/nonexistent/driver-event.schema.json")
        ):
            ve._DRIVER_EVENT_TYPES_CACHE = None
            types = ve.load_driver_event_types()
        self.assertEqual(types, frozenset())

    def test_missing_file_falls_back_to_vendored_only(self) -> None:
        with mock.patch.object(
            ve, "DRIVER_SCHEMA_PATH", Path("/nonexistent/driver-event.schema.json")
        ):
            ve._DRIVER_EVENT_TYPES_CACHE = None
            validator = ve.load_validator()
            errors = ve.validate_line(
                validator, "<test>", 1,
                json.dumps(_valid_event(event_type="task_completed")),
            )
            self.assertEqual(errors, [], f"vendored type must still validate: {errors!r}")

            driver_only_errors = ve.validate_line(
                validator, "<test>", 1,
                json.dumps(_valid_event(event_type="attempt_outcome")),
            )
            self.assertTrue(
                driver_only_errors,
                "driver-local type must be rejected when the registry is unreadable",
            )

    def test_unreadable_json_returns_empty_set(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "driver-event.schema.json"
            bad_file.write_text("not valid json {{", encoding="utf-8")
            with mock.patch.object(ve, "DRIVER_SCHEMA_PATH", bad_file):
                ve._DRIVER_EVENT_TYPES_CACHE = None
                types = ve.load_driver_event_types()
        self.assertEqual(types, frozenset())


class TestVendoredEnvelopeUntouched(_RealSchemaRootTestCase):
    """Criterion 5: the vendored envelope carries no driver-local types."""

    def test_vendored_enum_has_no_driver_local_types(self) -> None:
        with ve.SCHEMA_PATH.open("r", encoding="utf-8") as f:
            vendored = json.load(f)
        vendored_enum = set(vendored["properties"]["event_type"]["enum"])
        driver_types = TestDriverLocalRegistrySanctionsDerivedTypes.DERIVED_TYPES
        overlap = vendored_enum & driver_types
        self.assertFalse(
            overlap, f"vendored envelope must not gain driver-local types: {overlap}"
        )


class TestCorpusWideEventTypeErrors(_RealSchemaRootTestCase):
    """Criterion 9: event_type error count over every features/*/events.jsonl
    is zero (correlation_id errors are a separately-filed, expected gap —
    FEAT-2026-0073 — and are not asserted here)."""

    def test_no_event_type_errors_across_corpus(self) -> None:
        validator = ve.load_validator()
        event_type_errors: list[str] = []
        for log_path in sorted(FEATURES_DIR.glob("*/events.jsonl")):
            with log_path.open("r", encoding="utf-8") as f:
                for lineno, raw in enumerate(f, start=1):
                    stripped = raw.strip()
                    if not stripped:
                        continue
                    try:
                        json.loads(stripped)
                    except json.JSONDecodeError:
                        continue
                    errors = ve.validate_line(
                        validator, str(log_path), lineno, stripped
                    )
                    event_type_errors.extend(
                        e for e in errors if "at event_type" in e
                    )
        self.assertEqual(
            event_type_errors, [],
            f"expected zero event_type errors across the corpus; "
            f"got {len(event_type_errors)}: {event_type_errors[:5]!r}",
        )


if __name__ == "__main__":
    unittest.main()
