#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the correlation_id driver-local override (FEAT-2026-0073).

The vendored envelope schema (specfuse/loop/data/schemas/event.schema.json)
constrains correlation_id to
``^(FEAT|INIT)-\\d{4}-\\d{4}(/F\\d{2})?(/T\\d{2})?$`` — a substantive work unit
and nothing else. `.specfuse/rules/correlation-ids.md` documents two further
shapes: closing-sequence units (``G<n>-<NAME>``) and hygiene units
(``T<NN>H[N...]``). This registers those shapes in the driver-local registry
(specfuse/loop/data/schemas/driver-event.schema.json's ``correlation_id`` key)
and widens the pattern on a deep copy in validate_event.py's load_validator,
the same fall-through mechanism FEAT-2026-0060 established for event_type.

These tests exercise the REAL package schemas under specfuse/loop/data/schemas
(no SPECFUSE_SCHEMA_ROOT override) — the point is to prove the packaged
registry, not a synthetic stand-in.
"""

from __future__ import annotations

import importlib.resources
import json
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

import specfuse.loop.validate_event as ve

REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURES_DIR = REPO_ROOT / ".specfuse/features"
CORRELATION_IDS_RULE = REPO_ROOT / ".specfuse/rules/correlation-ids.md"
VENDORED_SCHEMA_PATH = REPO_ROOT / "specfuse/loop/data/schemas/event.schema.json"

_REAL_SCHEMA_ROOT = importlib.resources.files("specfuse.loop").joinpath(
    "data", "schemas"
)
_REAL_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "event.schema.json"
_REAL_PER_TYPE_DIR = _REAL_SCHEMA_ROOT / "events"
_REAL_DRIVER_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "driver-event.schema.json"


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
        ve._DRIVER_CORRELATION_PATTERNS_CACHE = ve._UNSET
        self.addCleanup(ve._PER_TYPE_CACHE.clear)
        self.addCleanup(setattr, ve, "_DRIVER_EVENT_TYPES_CACHE", None)
        self.addCleanup(setattr, ve, "_DRIVER_CORRELATION_PATTERNS_CACHE", ve._UNSET)


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


def _correlation_errors(validator: ve.Draft202012Validator, correlation_id: str) -> list[str]:
    errors = ve.validate_line(
        validator, "<test>", 1,
        json.dumps(_valid_event(correlation_id=correlation_id)),
    )
    return [e for e in errors if "at correlation_id" in e]


class TestCorrelationIdOverride(_RealSchemaRootTestCase):
    """Criteria 1-2: closing-sequence shapes are red on the vendored pattern
    alone and green through the driver-local override."""

    CLOSING_IDS = [
        "FEAT-2026-0042/G1-CLOSE",
        "FEAT-2026-0042/G1-PLAN",
        "FEAT-2026-0042/G1-CLOSE-INTERMEDIATE",
        "FEAT-2026-0042/G1-RETRO",
        "FEAT-2026-0042/G1-LESSONS",
        "FEAT-2026-0042/G1-DOCS",
        "FEAT-2026-0042/G10-CLOSE",
    ]

    def test_closing_sequence_ids_are_rejected_by_the_vendored_pattern_alone(self) -> None:
        with VENDORED_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            vendored = json.load(f)
        pattern = re.compile(vendored["properties"]["correlation_id"]["pattern"])
        for correlation_id in self.CLOSING_IDS:
            with self.subTest(correlation_id=correlation_id):
                self.assertIsNone(
                    pattern.match(correlation_id),
                    f"{correlation_id} unexpectedly matches the vendored "
                    "pattern alone; the override would then be a no-op",
                )

    def test_closing_sequence_ids_validate(self) -> None:
        validator = ve.load_validator()
        for correlation_id in self.CLOSING_IDS:
            with self.subTest(correlation_id=correlation_id):
                errors = _correlation_errors(validator, correlation_id)
                self.assertEqual(errors, [], f"{correlation_id}: {errors!r}")


class TestHygieneIdsValidate(_RealSchemaRootTestCase):
    """Criterion 3: hygiene (TNNH[N...]) shapes validate through the override."""

    def test_hygiene_ids_validate(self) -> None:
        validator = ve.load_validator()
        for correlation_id in [
            "FEAT-2026-0042/T01H",
            "FEAT-2026-0042/T01H2",
        ]:
            with self.subTest(correlation_id=correlation_id):
                errors = _correlation_errors(validator, correlation_id)
                self.assertEqual(errors, [], f"{correlation_id}: {errors!r}")


class TestWideningIsAdditive(_RealSchemaRootTestCase):
    """Criterion 4: every shape that validates on HEAD still validates."""

    PRE_EXISTING_IDS = [
        "FEAT-2026-0001",
        "FEAT-2026-0001/T01",
        "FEAT-2026-0001/F01",
        "FEAT-2026-0001/F01/T01",
        "INIT-2026-0001/F01",
        "INIT-2026-0001/F01/T01",
    ]

    def test_pre_existing_shapes_still_validate(self) -> None:
        validator = ve.load_validator()
        for correlation_id in self.PRE_EXISTING_IDS:
            with self.subTest(correlation_id=correlation_id):
                errors = _correlation_errors(validator, correlation_id)
                self.assertEqual(errors, [], f"{correlation_id}: {errors!r}")


class TestStillAConstraint(_RealSchemaRootTestCase):
    """Criterion 5: genuinely malformed IDs are still rejected."""

    MALFORMED_IDS = [
        "not-an-id-at-all",
        "BUG-2026-0001",
        "FEAT-2026-0001/",
        "FEAT-2026-0042/G1-NOTAREALNAME",
    ]

    def test_malformed_ids_are_rejected(self) -> None:
        validator = ve.load_validator()
        for correlation_id in self.MALFORMED_IDS:
            with self.subTest(correlation_id=correlation_id):
                errors = _correlation_errors(validator, correlation_id)
                self.assertTrue(errors, f"expected {correlation_id!r} to be rejected")


class TestVendoredEnvelopeUntouched(_RealSchemaRootTestCase):
    """Criterion 6: the vendored envelope file is byte-identical to HEAD."""

    def test_vendored_schema_has_no_working_tree_diff(self) -> None:
        result = subprocess.run(
            [
                "git", "diff", "--exit-code",
                "specfuse/loop/data/schemas/event.schema.json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            f"vendored schema has a working-tree diff:\n{result.stdout}",
        )
        self.assertEqual(result.stdout, "")


class TestMissingRegistryDegradesGracefully(_RealSchemaRootTestCase):
    """Criterion 7: a missing/unreadable registry leaves the vendored
    correlation_id pattern in force rather than raising."""

    def test_missing_file_returns_none(self) -> None:
        with mock.patch.object(
            ve, "DRIVER_SCHEMA_PATH", Path("/nonexistent/driver-event.schema.json")
        ):
            ve._DRIVER_CORRELATION_PATTERNS_CACHE = ve._UNSET
            patterns = ve.load_driver_correlation_patterns()
        self.assertIsNone(patterns)

    def test_missing_file_falls_back_to_vendored_pattern_only(self) -> None:
        with mock.patch.object(
            ve, "DRIVER_SCHEMA_PATH", Path("/nonexistent/driver-event.schema.json")
        ):
            ve._DRIVER_EVENT_TYPES_CACHE = None
            ve._DRIVER_CORRELATION_PATTERNS_CACHE = ve._UNSET
            validator = ve.load_validator()

            errors = _correlation_errors(validator, "FEAT-2026-0001/T01")
            self.assertEqual(errors, [], f"vendored shape must still validate: {errors!r}")

            closing_errors = _correlation_errors(validator, "FEAT-2026-0001/G1-CLOSE")
            self.assertTrue(
                closing_errors,
                "closing-sequence shape must be rejected when the registry "
                "is unreadable",
            )

    def test_unparseable_json_returns_none(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "driver-event.schema.json"
            bad_file.write_text("not valid json {{", encoding="utf-8")
            with mock.patch.object(ve, "DRIVER_SCHEMA_PATH", bad_file):
                ve._DRIVER_CORRELATION_PATTERNS_CACHE = ve._UNSET
                patterns = ve.load_driver_correlation_patterns()
        self.assertIsNone(patterns)


class TestRulesFileAndRegistryAgree(_RealSchemaRootTestCase):
    """Criterion 8: correlation-ids.md and the registry state the same set
    of closing-sequence shapes — compared mechanically, not by eye."""

    def test_closing_names_match(self) -> None:
        rule_text = CORRELATION_IDS_RULE.read_text(encoding="utf-8")
        match = re.search(
            r"G<n>-<NAME>.*?\bone of\b\s*(.+?)\.\s",
            rule_text,
            re.DOTALL,
        )
        self.assertIsNotNone(
            match, "could not locate the closing-name enumeration in "
            "correlation-ids.md; the doc's prose shape changed"
        )
        # The prose also names PLAN as CLOSE-INTERMEDIATE's paired WU, so the
        # backtick sweep can repeat a name; de-duplicate via set().
        names_from_rule = sorted(
            {n.strip("` ") for n in re.findall(r"`([A-Z][A-Z-]*)`", match.group(1))}
        )

        with ve.DRIVER_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            registry = json.load(f)
        names_from_registry = sorted(registry["correlation_id"]["closing_names"])

        self.assertEqual(
            names_from_rule, names_from_registry,
            f"correlation-ids.md documents {names_from_rule} but the registry "
            f"states {names_from_registry}",
        )


class TestCorpusCorrelationIdErrors(_RealSchemaRootTestCase):
    """Criterion 9: report the corpus-wide correlation_id error count. A
    different total than PLAN.md's drafting-time measurement is expected."""

    def test_zero_correlation_id_errors_across_corpus(self) -> None:
        validator = ve.load_validator()
        kind_counts: Counter[str] = Counter()
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
                    for e in ve.validate_line(validator, str(log_path), lineno, stripped):
                        if "at correlation_id" in e:
                            kind_counts["correlation_id"] += 1
                        elif "at event_type" in e:
                            kind_counts["event_type"] += 1
                        else:
                            kind_counts["other"] += 1
        self.assertEqual(
            kind_counts.get("correlation_id", 0), 0,
            f"expected zero correlation_id errors across the corpus after "
            f"the override; breakdown: {dict(kind_counts)}",
        )


if __name__ == "__main__":
    unittest.main()
