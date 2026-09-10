#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Re-plan events reach the consumer that has waited for them since
FEAT-2026-0018/T02 (FEAT-2026-0104/T04).

Drives a real `loop.run()` through the same replan-tracer fixture
`tests/test_replan_end_to_end.py` uses, so the `replan` event asserted on
below is the driver's own emission — not a hand-built dict. Two things must
both be true of that one real event:

- it validates against the repo's own envelope (`validate_event.py`), scoped
  to the `replan` line itself, not asserted against the whole corpus (a
  previous attempt at this unit asserted zero offenders file-wide and failed
  on 19 unrelated complaints from other event types);
- `gate_eval.evaluate_auto_close` — the consumer this event was always meant
  to feed, per `docs/methodology.md:187` — reads it and disables auto-close
  for the gate.
"""

from __future__ import annotations

import importlib.resources
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import gate_eval, validate_event
from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

# Pin validate_event's module globals to the REAL packaged schemas,
# regardless of what tests.test_validate_event's module-level reload (a
# synthetic SPECFUSE_SCHEMA_ROOT tempdir, never restored) left behind in
# sys.modules — same defensive pattern as
# tests.test_validate_event_driver_types._RealSchemaRootTestCase.
_REAL_SCHEMA_ROOT = importlib.resources.files("specfuse.loop").joinpath(
    "data", "schemas"
)
_REAL_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "event.schema.json"
_REAL_PER_TYPE_DIR = _REAL_SCHEMA_ROOT / "events"
_REAL_DRIVER_SCHEMA_PATH = _REAL_SCHEMA_ROOT / "driver-event.schema.json"

_FEATURE_ID = "FEAT-2026-8802"
_SLUG = "replan-event-fixture"
_BRANCH = f"feat/{_FEATURE_ID}-{_SLUG}"
_REWRITTEN_BODY_MARKER = "REWRITTEN BODY — the re-plan turn's own output.\n"


def _scaffold(root: Path) -> Path:
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: replan-event-fixture\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Replan event fixture | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Replan event fixture\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: prove the replan event reaches gate_eval\n"
        "status: active\n"
        "---\n\n"
        f"# Plan: {_SLUG}\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {_FEATURE_ID}/T01\n"
        "        file: WU-T01.md\n"
        "        depends_on: []\n"
        "```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {_FEATURE_ID}/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "max_attempts: 3\nreplan_stub_trigger: true\n"
        f"---\n\n# T01\n\nORIGINAL BODY.\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold replan event fixture"], check=True)
    return fdir


class ReplanEventEmissionTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []
        ve_patches = [
            mock.patch.object(validate_event, "SCHEMA_ROOT", _REAL_SCHEMA_ROOT),
            mock.patch.object(validate_event, "SCHEMA_PATH", _REAL_SCHEMA_PATH),
            mock.patch.object(validate_event, "PER_TYPE_SCHEMA_DIR", _REAL_PER_TYPE_DIR),
            mock.patch.object(validate_event, "DRIVER_SCHEMA_PATH", _REAL_DRIVER_SCHEMA_PATH),
        ]
        for p in ve_patches:
            p.start()
            self.addCleanup(p.stop)
        validate_event._PER_TYPE_CACHE.clear()
        validate_event._DRIVER_EVENT_TYPES_CACHE = None
        self.addCleanup(validate_event._PER_TYPE_CACHE.clear)
        self.addCleanup(setattr, validate_event, "_DRIVER_EVENT_TYPES_CACHE", None)

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_replan_event_emitted_validates_and_disables_autoclose(self):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            if wu.body.startswith(loop._REPLAN_BRIEF_MARKER):
                return _REWRITTEN_BODY_MARKER
            return "```result\nstatus: complete\n```\n"

        verify_calls = {"n": 0}

        def fake_verify(wu, feature_dir, gate_file=None):
            verify_calls["n"] += 1
            if verify_calls["n"] < 3:
                return False, "synthetic failure for the replan event test"
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0,
                             "the gate must run to completion, not halt")

            events_path = feature_dir / "events.jsonl"
            lines = [
                json.loads(raw)
                for raw in events_path.read_text().splitlines() if raw.strip()
            ]
            replan_events = [e for e in lines if e.get("event_type") == "replan"]
            self.assertEqual(
                len(replan_events), 1,
                "exactly one replan event, emitted by the one re-plan turn "
                "this fixture triggers")
            replan_event = replan_events[0]
            self.assertEqual(replan_event["correlation_id"],
                              f"{_FEATURE_ID}/T01")

            # Scoped to the one `replan` line this unit emits — not the
            # whole corpus (see module docstring).
            validator = validate_event.load_validator()
            errors = validate_event.validate_line(
                validator, str(events_path), 1, json.dumps(replan_event))
            self.assertEqual(errors, [],
                              "the emitted replan event must validate "
                              "against the repo's own envelope")

            # The real consumer: gate_eval.evaluate_auto_close, reading the
            # event this unit just wrote to disk (not a hand-built dict).
            decision = gate_eval.evaluate_auto_close(feature_dir, 1)
            self.assertFalse(
                decision.auto,
                "a gate whose unit needed a re-plan must not auto-close")
            self.assertTrue(
                any(r.startswith("replan_event:") for r in decision.reasons),
                f"expected a replan_event reason, got {decision.reasons}")


if __name__ == "__main__":
    unittest.main()
