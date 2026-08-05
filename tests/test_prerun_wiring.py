#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0057/T04 — wire the pre-dispatch runner into the driver's dispatch path.

Gate 1 closed `partially_met`: T01 (`specfuse/loop/prerun.py`) and T02
(`specfuse/loop/prerun_capture.py`) are correct and tested, but `WorkUnit` had
no `prep`/`oracles` field, `load_wu` never parsed either key, and no dispatch
path called either module. A work unit declaring both keys produced exactly
the same pre-dispatch outcome as one declaring neither.

These tests assert the wiring the close's FU-1/FU-2 named as the re-run
condition:
  1. `load_wu` parses `prep`/`oracles` the same way it parses `extra_gates`;
  2. a real WU file declaring both, loaded through `load_wu` and passed to
     `run_pre_dispatch`, returns non-empty `prep_results`/`oracle_results`
     (the exact close-time probe, now inverted);
  3. `execute_unit_attempt` calls `run_pre_dispatch` before `dispatch_fn` and
     halts with `PREP_HALT_CLASS` on a failing prep entry, without ever
     invoking `dispatch_fn`;
  4. a passing prep run's `oracle_results` are formatted via
     `format_oracle_capture` and appended to the WU body handed to dispatch;
  5. a WU declaring neither key is untouched (no pre-dispatch work, body
     unchanged).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

from specfuse.loop.prerun import PREP_HALT_CLASS, run_pre_dispatch  # noqa: E402


def _write_wu(tmp: Path, *, prep_line: str = "", oracles_line: str = "",
              wu_type: str = "implementation", filename: str = "WU-T01.md") -> dict:
    """Write a WU file and return the PLAN-graph ref dict load_wu() consumes."""
    path = tmp / filename
    path.write_text(
        f"---\nid: FEAT-2026-9999/T01\ntype: {wu_type}\n"
        f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"{prep_line}{oracles_line}"
        f"---\n\n# Prerun-wiring fixture\n\nbody\n"
    )
    return {"id": "FEAT-2026-9999/T01", "file": filename, "depends_on": []}


class TestWiring(unittest.TestCase):
    def test_declared_prep_and_oracles_reach_the_runner(self):
        # The exact close-time probe from RETROSPECTIVE.md, inverted: a real
        # WU declaring `prep: [setup]` and `oracles: [smoke]`, loaded through
        # load_wu (not a fake stand-in), must now reach run_pre_dispatch and
        # produce non-empty results — proof the declaration is no longer
        # silently dropped.
        cfg = {
            "setup": [{"name": "clone-sync", "command": "true"}],
            "smoke": [{"name": "smoke-check", "command": "true"}],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(
                tmp, prep_line="prep: [setup]\n", oracles_line="oracles: [smoke]\n",
            )
            wu = loop.load_wu(tmp, ref)

            self.assertTrue(hasattr(wu, "prep"))
            self.assertTrue(hasattr(wu, "oracles"))
            self.assertEqual(wu.prep, ["setup"])
            self.assertEqual(wu.oracles, ["smoke"])

            outcome = run_pre_dispatch(wu, tmp, cfg)

            self.assertFalse(outcome["halted"])
            self.assertNotEqual(outcome["prep_results"], [])
            self.assertNotEqual(outcome["oracle_results"], [])


class TestPrepOraclesParsing(unittest.TestCase):
    def test_absent_defaults_empty(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp)
            wu = loop.load_wu(tmp, ref)
            self.assertEqual(wu.prep, [])
            self.assertEqual(wu.oracles, [])

    def test_string_coerced_to_list(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp, prep_line="prep: setup\n", oracles_line="oracles: smoke\n")
            wu = loop.load_wu(tmp, ref)
            self.assertEqual(wu.prep, ["setup"])
            self.assertEqual(wu.oracles, ["smoke"])

    def test_list_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(
                tmp, prep_line="prep: [setup, warm]\n", oracles_line="oracles: [smoke, matrix]\n",
            )
            wu = loop.load_wu(tmp, ref)
            self.assertEqual(wu.prep, ["setup", "warm"])
            self.assertEqual(wu.oracles, ["smoke", "matrix"])

    def test_wrong_type_raises(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp, prep_line="prep:\n  bad: 1\n")
            with self.assertRaises(ValueError):
                loop.load_wu(tmp, ref)


class TestExecuteUnitAttemptWiring(unittest.TestCase):
    def _wu(self, tmp: Path, *, prep=None, oracles=None):
        prep_line = f"prep: [{', '.join(prep)}]\n" if prep else ""
        oracles_line = f"oracles: [{', '.join(oracles)}]\n" if oracles else ""
        ref = _write_wu(tmp, prep_line=prep_line, oracles_line=oracles_line)
        return loop.load_wu(tmp, ref)

    def test_failing_prep_halts_before_dispatch(self):
        cfg = {"setup": [{"name": "clone-sync", "command": "false"}]}
        dispatch_calls = []

        def _dispatch_fn(wu, failure_note):
            dispatch_calls.append(wu)
            return "should never run", None

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu(tmp, prep=["setup"])

            outcome, payload, usage = loop.execute_unit_attempt(
                wu, tmp, None, dispatch_fn=_dispatch_fn, prerun_cfg=cfg,
            )

            self.assertEqual(outcome, "prep_halted")
            self.assertEqual(payload["halt_class"], PREP_HALT_CLASS)
            self.assertIsNone(usage)
            self.assertEqual(dispatch_calls, [], "dispatch_fn must never run on a prep halt")

    def test_oracle_capture_appended_to_body_before_dispatch(self):
        cfg = {"smoke": [{"name": "smoke-check", "command": "echo hello"}]}
        seen_bodies = []

        def _dispatch_fn(wu, failure_note):
            seen_bodies.append(wu.body)
            return "STOP", None

        def _verify_fn(wu, feature_dir):
            return True, "ok"

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu(tmp, oracles=["smoke"])

            loop.execute_unit_attempt(
                wu, tmp, None, dispatch_fn=_dispatch_fn, verify_fn=_verify_fn,
                prerun_cfg=cfg,
            )

            self.assertEqual(len(seen_bodies), 1)
            self.assertIn("## Captured oracle output (pre-dispatch)", seen_bodies[0])
            self.assertIn("### oracle: smoke-check (OK)", seen_bodies[0])

    def test_no_prep_no_oracles_is_a_no_op(self):
        cfg = {"smoke": [{"name": "smoke-check", "command": "false"}]}
        seen_bodies = []

        def _dispatch_fn(wu, failure_note):
            seen_bodies.append(wu.body)
            return "STOP", None

        def _verify_fn(wu, feature_dir):
            return True, "ok"

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu(tmp)
            original_body = wu.body

            outcome, payload, usage = loop.execute_unit_attempt(
                wu, tmp, None, dispatch_fn=_dispatch_fn, verify_fn=_verify_fn,
                prerun_cfg=cfg,
            )

            self.assertNotEqual(outcome, "prep_halted")
            self.assertEqual(seen_bodies, [original_body])
            self.assertNotIn("## Captured oracle output (pre-dispatch)", seen_bodies[0])


if __name__ == "__main__":
    unittest.main()
