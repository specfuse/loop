#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Issue #134 — verify() must FAIL when a gate's oracle silently degraded.

A gate command can exit 0 while its analyzer degraded to a strict subset of the
real check. The observed case: `flutter analyze --fatal-warnings` cannot build a
`custom_lint` plugin in the loop sandbox (network to pub.dev blocked), prints
"An error occurred while setting up the analyzer plugin ...", then continues with
core lints only and exits 0 — "No issues found!". The gate passes; the real CI
(plugin loads there) fails on warnings the in-loop oracle never saw. A hollow
pass.

verify() must treat a known silent-degradation signature in gate output as a
gate FAILURE even on exit 0, with an honest message naming the degraded oracle,
so the driver blocks instead of certifying `met` on a subset check.
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


# A shell command that reproduces the degraded-oracle shape: emit the analyzer
# plugin-setup error to stdout, report "No issues found!", then exit 0.
_DEGRADED_CMD = (
    "printf '%s\\n' "
    "'An error occurred while setting up the analyzer plugin custom_lint' "
    "'No issues found!'; true"
)


class TestDegradedOracle(unittest.TestCase):

    def test_plugin_setup_error_fails_gate_despite_exit_zero(self):
        cfg = {"code": [{"name": "warnings", "command": _DEGRADED_CMD}]}
        ok, msg = loop.verify(make_wu(), Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(
            ok, "exit 0 with a plugin-setup error must FAIL — oracle degraded"
        )
        self.assertIn("### warnings: FAIL", msg)
        self.assertIn("DEGRADED ORACLE", msg)

    def test_message_is_honest_about_the_cause(self):
        cfg = {"code": [{"name": "warnings", "command": _DEGRADED_CMD}]}
        _, msg = loop.verify(make_wu(), Path("/tmp/feat"), cfg=cfg)
        # The honest reason (not just the echoed marker) reaches the log: names
        # the degradation and that the oracle measured a subset, not a warning.
        self.assertIn("did not load", msg)
        self.assertIn("subset", msg)

    def test_clean_pass_still_passes(self):
        # Same "No issues found!" success WITHOUT the degradation marker: passes.
        cfg = {"code": [{"name": "warnings",
                         "command": "printf '%s\\n' 'No issues found!'; true"}]}
        ok, msg = loop.verify(make_wu(), Path("/tmp/feat"), cfg=cfg)
        self.assertTrue(ok, "clean exit 0 with no degradation marker must pass")
        self.assertIn("### warnings: PASS", msg)

    def test_marker_does_not_override_a_real_failure(self):
        # Command exits non-zero AND has the marker: still a FAIL (not masked).
        cfg = {"code": [{"name": "warnings",
                         "command": _DEGRADED_CMD.replace("; true", "; false")}]}
        ok, msg = loop.verify(make_wu(), Path("/tmp/feat"), cfg=cfg)
        self.assertFalse(ok)
        self.assertIn("### warnings: FAIL", msg)


if __name__ == "__main__":
    unittest.main()
