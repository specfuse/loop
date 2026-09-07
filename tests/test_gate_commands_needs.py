#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0102/T02 — `gate_commands.iter_code_gates` honours `needs:`.

`verification.yml` is the single source of truth `scripts/smoke-test.sh` and
CI read via `gate_commands.py`. Its parser is regex-based and, before this
unit, only matched `^  - name:` and `command:` — a `needs:` key was invisible
to it, so CI could run a dependent gate before its dependency even though the
driver (`loop._run_gate_set`, ordered by `loop.order_gate_set`,
FEAT-2026-0102/T01) already runs the same set in dependency order. These
tests assert the two orders never disagree.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from specfuse.loop import gate_commands

loop = load_loop()

_FIXTURE_YML = """\
code:
  - name: coverage
    needs: [tests]
    command: "true"

  - name: tests
    command: "true"

  - name: lint
    command: "true"

  - name: security
    command: "true"
"""

_NO_NEEDS_YML = """\
code:
  - name: tests
    command: "true"

  - name: lint
    command: "true"

  - name: security
    command: "true"
"""


class TestEmittedOrderIsTopological(unittest.TestCase):

    def test_emitted_order_is_topological(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "verification.yml"
            path.write_text(_FIXTURE_YML, encoding="utf-8")
            names = [name for name, _ in gate_commands.iter_code_gates(path)]
            self.assertLess(names.index("tests"), names.index("coverage"))


class TestOrderMatchesDriver(unittest.TestCase):

    def test_order_matches_driver(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            path = tmp / "verification.yml"
            path.write_text(_FIXTURE_YML, encoding="utf-8")
            emitted = [name for name, _ in gate_commands.iter_code_gates(path)]

            gate_set = [
                {"name": "coverage", "command": "true", "needs": ["tests"]},
                {"name": "tests", "command": "true"},
                {"name": "lint", "command": "true"},
                {"name": "security", "command": "true"},
            ]
            ordered = loop.order_gate_set(gate_set)
            results = loop._run_gate_set(ordered, tmp)
            executed = [r["name"] for r in results]

            self.assertEqual(emitted, executed)


class TestAbsentNeedsPreservesDeclaredOrder(unittest.TestCase):

    def test_absent_needs_preserves_declared_order(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "verification.yml"
            path.write_text(_NO_NEEDS_YML, encoding="utf-8")
            names = [name for name, _ in gate_commands.iter_code_gates(path)]
            self.assertEqual(names, ["tests", "lint", "security"])


if __name__ == "__main__":
    unittest.main()
