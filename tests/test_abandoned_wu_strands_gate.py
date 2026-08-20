#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression test for specfuse/loop#2396.

Abandoning a work unit strands every WU that transitively `depends_on` it —
`ready()` only treats `done` as a satisfied dependency, so a dependent of an
`abandoned` WU can never become ready. Before the fix, the driver's while-loop
frontier goes empty, nothing sets `blocked`, and the run falls through to the
gate-completion path — printing "Gate N complete (retro, lessons, docs,
plan-next)" and flipping the gate to `awaiting_review` even though the closing
sequence never ran.
"""

from __future__ import annotations

import os
import unittest

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace
from tests.test_driver_integration import write_minimal_feature, _read_frontmatter

loop = load_loop()


class TestAbandonedWuStrandsGate(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_gate_halts_instead_of_falsely_reporting_complete(self):
        with integration_workspace() as root:
            os.chdir(root)
            # T01 is already `abandoned`. write_minimal_feature chains
            # depends_on across all WUs in order, so the closing sequence
            # (G1-RETRO -> G1-LESSONS -> G1-DOCS -> G1-PLAN) transitively
            # depends on the abandoned T01 and can never become ready.
            write_minimal_feature(root, "FEAT-2026-9201", "stranded-close",
                                  "feat/test-stranded", [
                                      ("FEAT-2026-9201/T01", "implementation",
                                       "abandoned"),
                                  ])

            # No WU should ever be dispatchable, so dispatch/verify must not
            # even be called — but stub them so a regression that DOES
            # dispatch fails loudly rather than hanging on a real subprocess.
            def fake_dispatch(wu, failure_note, cost_tracking=True):
                raise AssertionError(
                    f"dispatch() must not be called for stranded WU {wu.wu_id}")

            def fake_verify(wu, feature_dir, cfg=None):
                raise AssertionError(
                    f"verify() must not be called for stranded WU {wu.wu_id}")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(
                rc, 1,
                "a stranded closing sequence must halt the driver, not "
                "exit 0 as if the gate completed")

            fdir = root / ".specfuse/features/FEAT-2026-9201-stranded-close"
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(
                gate_fm.get("status"), "open",
                "the gate must not be flipped to awaiting_review when its "
                "closing sequence never actually ran")

            retro_fm = _read_frontmatter(fdir / "WU-G1-RETRO.md")
            self.assertEqual(
                retro_fm.get("status"), "pending",
                "the retrospective WU must still be pending — the closing "
                "sequence must not be reported as having run")


if __name__ == "__main__":
    unittest.main()
