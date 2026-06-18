#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Issue #62 — `extra_gates` declared in WU frontmatter must be consumed by the driver.

A WU may declare `extra_gates: [<set>]` to union additional verification gate sets
(e.g. a live cluster smoke) on top of its type-default set. Before the fix, `loop.py`
never read the field: `verify()` ran only the type-selected set, so any WU relying on
an extra gate passed on its type default alone — the exact silent hollow-pass the
field exists to prevent.

These tests assert the three contract cases from the issue plus parsing + dedup:
  1. union runs, and a failing extra (live) gate fails the WU;
  2. an `extra_gates` name absent from verification.yml → named CONFIGURATION ERROR;
  3. no `extra_gates` → type set only (unchanged behavior);
  4. a set shared between the type default and an extra entry is not run twice;
  5. load_wu() parses extra_gates (absent → [], string → [str], list → list).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _write_wu(tmp: Path, *, extra_gates_line: str = "", wu_type: str = "implementation",
              filename: str = "WU-T01.md") -> dict:
    """Write a WU file and return the PLAN-graph ref dict load_wu() consumes."""
    path = tmp / filename
    path.write_text(
        f"---\nid: FEAT-2026-9999/T01\ntype: {wu_type}\n"
        f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"{extra_gates_line}"
        f"---\n\n# Extra-gates fixture\n\nbody\n"
    )
    return {"id": "FEAT-2026-9999/T01", "file": filename, "depends_on": []}


class TestExtraGatesParsing(unittest.TestCase):

    def test_absent_extra_gates_defaults_empty(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp)
            wu = loop.load_wu(tmp, ref)
            self.assertEqual(wu.extra_gates, [])

    def test_string_extra_gates_coerced_to_list(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp, extra_gates_line="extra_gates: live-verify\n")
            wu = loop.load_wu(tmp, ref)
            self.assertEqual(wu.extra_gates, ["live-verify"])

    def test_list_extra_gates_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp, extra_gates_line="extra_gates: [live-verify, smoke]\n")
            wu = loop.load_wu(tmp, ref)
            self.assertEqual(wu.extra_gates, ["live-verify", "smoke"])


class TestExtraGatesVerify(unittest.TestCase):

    def _wu_with_extra(self, tmp: Path, extra: str):
        ref = _write_wu(tmp, extra_gates_line=f"extra_gates: {extra}\n")
        return loop.load_wu(tmp, ref)

    def test_union_runs_and_failing_extra_gate_fails_wu(self):
        # type 'code' passes (`true`); extra 'live' fails (`false`). The union
        # must fail the WU. Before the fix, extra_gates was ignored → wrongly True.
        cfg = {
            "code": [{"name": "tests", "command": "true"}],
            "live": [{"name": "cluster-smoke", "command": "false"}],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu_with_extra(tmp, "[live]")
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertFalse(ok, "a failing extra gate must fail the WU")
            self.assertIn("cluster-smoke", msg)
            self.assertIn("FAIL", msg)

    def test_union_passes_when_both_type_and_extra_pass(self):
        cfg = {
            "code": [{"name": "tests", "command": "true"}],
            "live": [{"name": "cluster-smoke", "command": "true"}],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu_with_extra(tmp, "[live]")
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertTrue(ok)
            self.assertIn("cluster-smoke", msg)
            self.assertIn("tests", msg)

    def test_unknown_extra_gates_name_is_configuration_error(self):
        # 'live' is declared but absent from verification.yml → named config error,
        # same class as an empty type set, never a silent pass.
        cfg = {"code": [{"name": "tests", "command": "true"}]}
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu_with_extra(tmp, "[live]")
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertFalse(ok, "unknown extra_gates name must fail, not pass")
            self.assertIn("CONFIGURATION ERROR", msg)
            self.assertIn("live", msg)

    def test_no_extra_gates_runs_type_set_only(self):
        # Regression: a WU with no extra_gates behaves exactly as before.
        cfg = {
            "code": [{"name": "tests", "command": "true"}],
            "live": [{"name": "cluster-smoke", "command": "false"}],
        }
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ref = _write_wu(tmp)  # no extra_gates
            wu = loop.load_wu(tmp, ref)
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertTrue(ok, "no extra_gates → only the passing 'code' set runs")
            self.assertNotIn("cluster-smoke", msg)

    def test_shared_set_not_run_twice(self):
        # extra_gates names the same set the type already selects: dedup by gate
        # name so the gate runs once, not twice.
        cfg = {"code": [{"name": "tests", "command": "true"}]}
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            wu = self._wu_with_extra(tmp, "[code]")
            ok, msg = loop.verify(wu, tmp, cfg=cfg)
            self.assertTrue(ok)
            self.assertEqual(msg.count("### tests:"), 1,
                             "shared gate must not be run twice")


if __name__ == "__main__":
    unittest.main()
