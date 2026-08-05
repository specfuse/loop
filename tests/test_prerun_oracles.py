#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0057/T01 — the pre-dispatch runner for `prep` and `oracles`.

`verify()` runs every declared command at work-unit *exit* ("the exit
oracle", `loop.py:2855`). Captured output therefore reaches an agent only as
failure feedback on a retry, and a fail-fast environment-prep step has no
representation at all. `specfuse.loop.prerun.run_pre_dispatch` adds the
missing timing: it resolves a WU's `prep` and `oracles` frontmatter sets
against a verification.yml-shaped cfg dict and runs them before dispatch —
`prep` fail-fast, `oracles` capture-all.

These tests assert the contract from WU-01's acceptance criteria:
  1. a failing prep entry halts before any oracle runs, and a later prep
     entry never runs once an earlier one has failed;
  2. prep success runs every oracle regardless of individual failure;
  3. an unresolvable `prep`/`oracles` name is a named CONFIGURATION ERROR;
  4. no `prep` and no `oracles` declared -> empty outcome, `_run_gate_set`
     never invoked.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop

load_loop()  # ensures specfuse.loop.loop is importable the same way other tests load it

from specfuse.loop.prerun import (  # noqa: E402  (after sys.path setup above)
    PREP_HALT_CLASS,
    resolve_prerun_sets,
    run_pre_dispatch,
)


class _FakeWU:
    """Minimal stand-in for loop.WorkUnit exposing wu_id/prep/oracles.

    prerun.py reads these three attributes via getattr; it does not require
    a real WorkUnit, so tests do not need loop.load_wu (which does not parse
    `prep`/`oracles` — those keys are this feature's own, not loop.py's).
    """

    def __init__(self, wu_id="FEAT-2026-9999/T01", prep=None, oracles=None):
        self.wu_id = wu_id
        self.prep = prep or []
        self.oracles = oracles or []


class TestPreDispatch(unittest.TestCase):

    def test_prep_failure_halts_before_dispatch(self):
        # 'setup' has two entries: the first fails, the second would prove it
        # ran (writes a marker file) if prep did not stop fail-fast. Oracles
        # must not run either.
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            marker = tmp / "second-prep-ran"
            cfg = {
                "setup": [
                    {"name": "clone-sync", "command": "false"},
                    {"name": "marker", "command": f"touch {marker}"},
                ],
                "smoke": [{"name": "smoke-check", "command": "true"}],
            }
            wu = _FakeWU(prep=["setup"], oracles=["smoke"])
            outcome = run_pre_dispatch(wu, tmp, cfg)

            self.assertTrue(outcome["halted"], "a failing prep entry must halt")
            self.assertEqual(outcome["halt_class"], PREP_HALT_CLASS)
            self.assertEqual(len(outcome["prep_results"]), 1,
                              "the second prep entry must not run")
            self.assertFalse(outcome["prep_results"][0]["ok"])
            self.assertEqual(outcome["oracle_results"], [],
                              "oracles must not run when prep halts")
            self.assertFalse(marker.exists(),
                              "the second prep entry ran despite the first failing")

    def test_oracles_run_capture_all_regardless_of_individual_failure(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cfg = {
                "smoke": [
                    {"name": "ok-check", "command": "true"},
                    {"name": "bad-check", "command": "false"},
                ],
            }
            wu = _FakeWU(oracles=["smoke"])
            outcome = run_pre_dispatch(wu, tmp, cfg)

            self.assertFalse(outcome["halted"])
            names = [r["name"] for r in outcome["oracle_results"]]
            self.assertEqual(names, ["ok-check", "bad-check"],
                              "every oracle entry must run regardless of failure")
            oks = {r["name"]: r["ok"] for r in outcome["oracle_results"]}
            self.assertTrue(oks["ok-check"])
            self.assertFalse(oks["bad-check"])
            for r in outcome["oracle_results"]:
                self.assertIn("report", r)

    def test_unknown_prep_name_is_configuration_error(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cfg = {"smoke": [{"name": "smoke-check", "command": "true"}]}
            wu = _FakeWU(wu_id="FEAT-2026-9999/T01", prep=["missing-set"])
            outcome = run_pre_dispatch(wu, tmp, cfg)

            self.assertTrue(outcome["halted"])
            self.assertEqual(outcome["halt_class"], PREP_HALT_CLASS)
            self.assertIn("CONFIGURATION ERROR", outcome["message"])
            self.assertIn("missing-set", outcome["message"])
            self.assertIn("FEAT-2026-9999/T01", outcome["message"])
            self.assertEqual(outcome["prep_results"], [])

    def test_unknown_oracles_name_is_configuration_error(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            cfg = {"setup": [{"name": "clone-sync", "command": "true"}]}
            wu = _FakeWU(prep=["setup"], oracles=["missing-set"])
            outcome = run_pre_dispatch(wu, tmp, cfg)

            self.assertTrue(outcome["halted"])
            self.assertIn("CONFIGURATION ERROR", outcome["message"])
            self.assertIn("missing-set", outcome["message"])

    def test_no_prep_or_oracles_is_a_no_op(self):
        wu = _FakeWU()
        with mock.patch("specfuse.loop.prerun._run_gate_set") as mocked:
            outcome = run_pre_dispatch(wu, Path("/nonexistent"), {})
        mocked.assert_not_called()
        self.assertEqual(outcome, {
            "halted": False, "halt_class": None, "message": None,
            "prep_results": [], "oracle_results": [],
        })

    def test_resolve_prerun_sets_dedups_shared_gate_name(self):
        cfg = {"setup": [{"name": "clone-sync", "command": "true"}]}
        wu = _FakeWU(prep=["setup", "setup"])
        prep_gates, oracle_gates, err = resolve_prerun_sets(wu, cfg)
        self.assertIsNone(err)
        self.assertEqual(len(prep_gates), 1)
        self.assertEqual(oracle_gates, [])


if __name__ == "__main__":
    unittest.main()
