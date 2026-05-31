#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Fix 2 — verify() must FAIL on a missing or empty gate set, not silently pass.

A misconfigured `verification.yml` (the wrong key for the WU type, or an empty
list) is a configuration bug. Returning True there would let work units sail
through with no oracle at all, which is exactly what we want the driver to
prevent. The failure message must name the configuration cause so a human
reading the log doesn't mistake it for an agent failure.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def make_wu(wu_type: str = "implementation"):
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=Path("/tmp/does-not-matter.md"),
        depends_on=[],
        type=wu_type,
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title="test fixture",
        body="(body unused)",
    )


class TestVerifyEmptyGateSet(unittest.TestCase):

    def test_missing_set_for_type_fails_with_config_message(self):
        # cfg has other sets but NOT the one the implementation type needs.
        cfg = {"doc": [{"name": "x", "command": "true"}]}
        wu = make_wu("implementation")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(ok, "missing 'code' set must fail, not pass")
        self.assertIn("CONFIGURATION ERROR", msg)
        self.assertIn("'code'", msg)
        self.assertIn("implementation", msg)

    def test_empty_list_for_type_fails_with_config_message(self):
        cfg = {"code": []}
        wu = make_wu("implementation")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(ok, "empty 'code' list must fail, not pass")
        self.assertIn("CONFIGURATION ERROR", msg)

    def test_null_value_for_type_fails_with_config_message(self):
        # YAML `code:` with no list under it parses to None.
        cfg = {"code": None}
        wu = make_wu("implementation")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(ok)
        self.assertIn("CONFIGURATION ERROR", msg)

    def test_completely_empty_cfg_fails(self):
        wu = make_wu("plan-next")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg={})
        self.assertFalse(ok)
        self.assertIn("CONFIGURATION ERROR", msg)
        self.assertIn("'plannext'", msg)

    def test_doc_set_missing_for_retrospective_fails(self):
        # retrospective maps to 'doc'; without it, must fail.
        cfg = {"code": [{"name": "tests", "command": "true"}]}
        wu = make_wu("retrospective")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(ok)
        self.assertIn("'doc'", msg)

    def test_passing_gate_with_real_command_still_works(self):
        # Regression: the refactor must not break the happy path.
        cfg = {"code": [{"name": "noop", "command": "true"}]}
        wu = make_wu("implementation")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertTrue(ok, "a `true` command must pass verify()")
        self.assertIn("PASS", msg)
        self.assertNotIn("CONFIGURATION ERROR", msg)

    def test_failing_gate_failure_message_is_distinguishable_from_config_error(self):
        # A genuine gate failure prints the gate's FAIL line; a config error
        # prints CONFIGURATION ERROR. Both fail, but a human reading the log
        # can tell which is which.
        cfg = {"code": [{"name": "alwaysfail", "command": "false"}]}
        wu = make_wu("implementation")
        ok, msg = loop.verify(wu, Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(ok)
        self.assertIn("FAIL", msg)
        self.assertNotIn("CONFIGURATION ERROR", msg)


if __name__ == "__main__":
    unittest.main()
