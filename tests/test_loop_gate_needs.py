#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0102/T01 — a gate set is a dependency graph, not a flat list.

A gate may declare `needs: [<gate>]`. `_run_gate_set` orders the set
topologically and skips (never passes) a gate whose dependency failed. Both
`verify()` and `probe_baseline()` share the ordering/validation helper
(`order_gate_set`) so an unknown `needs` target or a `needs` cycle is a
CONFIGURATION ERROR from either caller — the same class already used for an
unknown `extra_gates` name.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tests._loop_loader import load_loop

loop = load_loop()


def _write_wu(tmp: Path, *, wu_type: str = "implementation",
              filename: str = "WU-T01.md") -> dict:
    path = tmp / filename
    path.write_text(
        f"---\nid: FEAT-2026-9999/T01\ntype: {wu_type}\n"
        f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"---\n\n# gate-needs fixture\n\nbody\n"
    )
    return {"id": "FEAT-2026-9999/T01", "file": filename, "depends_on": []}


class TestDependentSkippedWhenDependencyFails(unittest.TestCase):

    def test_dependent_skipped_when_dependency_fails(self):
        cfg = {
            "code": [
                {"name": "tests", "command": "false"},
                {"name": "coverage", "command": "echo SHOULD_NOT_RUN",
                 "needs": ["tests"]},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = loop.load_wu(tmp, _write_wu(tmp))
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertFalse(ok)
            self.assertNotIn("SHOULD_NOT_RUN", msg)
            self.assertIn("### coverage: SKIP", msg)

    def test_skip_report_does_not_capture_failure_attribution(self):
        cfg = {
            "code": [
                {"name": "tests", "command": "false"},
                {"name": "coverage", "command": "echo SHOULD_NOT_RUN",
                 "needs": ["tests"]},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = loop.load_wu(tmp, _write_wu(tmp))
            _, msg = loop.verify(wu, tmp, cfg=cfg)
            failure_class, _ = loop.parse_gate_failure_signature(msg)
            self.assertEqual(failure_class, "tests")


class TestDeclaredOrderIsTopological(unittest.TestCase):

    def test_declared_order_is_topological(self):
        cfg = {
            "code": [
                {"name": "coverage", "command": "true", "needs": ["tests"]},
                {"name": "tests", "command": "true"},
                {"name": "lint", "command": "true"},
                {"name": "security", "command": "true"},
            ],
        }
        ordered = loop.order_gate_set(cfg["code"])
        names = [g["name"] for g in ordered]
        self.assertLess(names.index("tests"), names.index("coverage"))
        # lint and security have no edges to anything: declared relative
        # order (lint before security) is preserved.
        self.assertLess(names.index("lint"), names.index("security"))


class TestUnknownNeedsTargetIsConfigurationError(unittest.TestCase):

    def test_unknown_needs_target_is_configuration_error(self):
        cfg = {
            "code": [
                {"name": "coverage", "command": "true", "needs": ["ghost"]},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = loop.load_wu(tmp, _write_wu(tmp))
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertFalse(ok)
            self.assertIn("CONFIGURATION ERROR", msg)
            self.assertIn("coverage", msg)
            self.assertIn("ghost", msg)

            failing = loop.probe_baseline(tmp, cfg=cfg)
            self.assertEqual(len(failing), 1)
            self.assertEqual(failing[0]["failure_class"], "configuration_error")
            self.assertIn("CONFIGURATION ERROR", failing[0]["failure_signature"])
            self.assertIn("coverage", failing[0]["failure_signature"])
            self.assertIn("ghost", failing[0]["failure_signature"])


class TestNeedsCycleIsConfigurationError(unittest.TestCase):

    def test_needs_cycle_is_configuration_error(self):
        cfg = {
            "code": [
                {"name": "a", "command": "true", "needs": ["b"]},
                {"name": "b", "command": "true", "needs": ["a"]},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = loop.load_wu(tmp, _write_wu(tmp))
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertFalse(ok)
            self.assertIn("CONFIGURATION ERROR", msg)
            self.assertIn("cycle", msg)

            failing = loop.probe_baseline(tmp, cfg=cfg)
            self.assertEqual(len(failing), 1)
            self.assertEqual(failing[0]["failure_class"], "configuration_error")
            self.assertIn("CONFIGURATION ERROR", failing[0]["failure_signature"])
            self.assertIn("cycle", failing[0]["failure_signature"])


class TestAbsentNeedsIsInert(unittest.TestCase):

    def test_absent_needs_is_inert(self):
        cfg = {
            "code": [
                {"name": "tests", "command": "true"},
                {"name": "lint", "command": "true"},
                {"name": "security", "command": "true"},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = loop.load_wu(tmp, _write_wu(tmp))
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertTrue(ok)
            self.assertIn("### tests: PASS", msg)
            self.assertIn("### lint: PASS", msg)
            self.assertIn("### security: PASS", msg)
            order = [msg.index("### tests:"), msg.index("### lint:"),
                     msg.index("### security:")]
            self.assertEqual(order, sorted(order))


if __name__ == "__main__":
    unittest.main()
