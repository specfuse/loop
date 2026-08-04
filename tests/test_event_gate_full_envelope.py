#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the widened .specfuse/scripts/event_type_gate.py (FEAT-2026-0073/T02).

The gate used to check event_type errors only (FEAT-2026-0060/T02) because a
whole-envelope gate could not be green: 279+ correlation_id errors remained
across the corpus, rejected by the vendored pattern even though
correlation-ids.md documents the closing-sequence (G<n>-<NAME>) and hygiene
(TNNH) ID shapes as valid. FEAT-2026-0073/T01 widened the pattern via
validate_event.py's driver-local deep-copy fall-through; this test module
proves the gate now checks the full envelope, not event_type alone.

test_non_event_type_error_now_fails_the_gate is the regression pin: it fails
on HEAD before this work unit lands, because today's gate ignores every
non-event_type error and a fixture carrying only a malformed correlation_id
would exit 0.

In-process (not subprocess) for the fixture cases, so FEATURES_DIR can be
monkeypatched onto a throwaway tree — the gate hardcodes its scan root
relative to its own file location, not cwd or an env override. The real
schema globals are pinned to the packaged copy per test (see
_RealSchemaRootTestCase, mirroring test_correlation_id_override.py) because
test_validate_event.py mutates os.environ["SPECFUSE_SCHEMA_ROOT"] and
reloads the same validate_event singleton at import time without restoring
it, which would otherwise leak a synthetic schema root into this module
depending on test discovery order.
"""

from __future__ import annotations

import contextlib
import importlib.resources
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / ".specfuse" / "scripts" / "event_type_gate.py"

_spec = importlib.util.spec_from_file_location("event_type_gate", GATE_SCRIPT)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)
ve = gate.validate_event

_REAL_SCHEMA_ROOT = importlib.resources.files("specfuse.loop").joinpath(
    "data", "schemas"
)
_REAL_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "event.schema.json"
_REAL_PER_TYPE_DIR = _REAL_SCHEMA_ROOT / "events"
_REAL_DRIVER_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "driver-event.schema.json"

_VALID_EVENT = (
    '{{"timestamp": "2026-08-04T00:00:00Z", "correlation_id": "{cid}", '
    '"event_type": "feature_created", "source": "driver", '
    '"source_version": "1.0.0", "payload": {{}}}}'
)


class _RealSchemaRootTestCase(unittest.TestCase):
    """Pin ve's module globals to the real packaged schemas for the
    duration of each test, regardless of import order across test files."""

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


def _run_gate_over(features_dir: Path) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(gate, "FEATURES_DIR", features_dir):
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gate.main()
    return code, out.getvalue(), err.getvalue()


class TestEventGateFullEnvelope(_RealSchemaRootTestCase):
    def test_non_event_type_error_now_fails_the_gate(self) -> None:
        """A malformed correlation_id — not an event_type error — must fail
        the gate, name the offending file/line/field, and exit 1.

        Malformed under T01's widened pattern (not merely the pre-0073
        pattern): G<n>-BOGUS is not one of the closing_names the widened
        registry admits (CLOSE, CLOSE-INTERMEDIATE, DOCS, LESSONS, PLAN,
        RETRO), so it still fails after widening.
        """
        with tempfile.TemporaryDirectory() as tmp:
            features_dir = Path(tmp) / "features"
            feature_dir = features_dir / "FEAT-2026-9999-fixture"
            feature_dir.mkdir(parents=True)
            events_file = feature_dir / "events.jsonl"
            events_file.write_text(
                _VALID_EVENT.format(cid="FEAT-2026-9999/G1-BOGUS") + "\n",
                encoding="utf-8",
            )

            code, _out, err = _run_gate_over(features_dir)

        self.assertEqual(code, 1, msg=err)
        self.assertIn(str(events_file), err)
        self.assertIn(":1", err)
        self.assertIn("correlation_id", err)

    def test_clean_corpus_exits_zero_with_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            features_dir = Path(tmp) / "features"
            feature_dir = features_dir / "FEAT-2026-9999-fixture"
            feature_dir.mkdir(parents=True)
            events_file = feature_dir / "events.jsonl"
            events_file.write_text(
                _VALID_EVENT.format(cid="FEAT-2026-9999/T01") + "\n"
                + _VALID_EVENT.format(cid="FEAT-2026-9999/G1-CLOSE") + "\n",
                encoding="utf-8",
            )

            code, out, err = _run_gate_over(features_dir)

        self.assertEqual(code, 0, msg=err)
        self.assertIn("ok:", out)
        self.assertIn("events.jsonl", out)
        self.assertIn("2 event(s) checked", out)


class TestEventGateRealCorpusSubprocess(unittest.TestCase):
    def test_real_corpus_exits_zero(self) -> None:
        """The gate must be green against this repository's real corpus.

        Runs in a subprocess with SPECFUSE_SCHEMA_ROOT stripped: other test
        modules in this suite leak that env var into os.environ without
        restoring it (see test_validate_event.py), and a subprocess inherits
        whatever os.environ holds at the moment this test runs, regardless
        of test file order.
        """
        env = dict(os.environ)
        env.pop("SPECFUSE_SCHEMA_ROOT", None)
        result = subprocess.run(
            [sys.executable, str(GATE_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("ok:", result.stdout)


if __name__ == "__main__":
    unittest.main()
