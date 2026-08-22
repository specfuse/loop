#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The resume command must run the build the halt came from (#2642).

When a work unit edits the driver's own importable surface the driver halts
and tells the operator how to resume. That command was the hardcoded literal
`specfuse run --feature <id>`. In a checkout carrying its own source —
every contributor's tree, and this repository's own dogfood — `specfuse`
resolves to the **pipx-installed build**, so following the driver's own
instruction resumes against different code than the one being worked on.

The driver already knew: `build_provenance.out_of_tree_warning` detects
exactly that condition and prints "Run instead: python3 -m
specfuse.loop.loop". One half of the driver emitted a command the other half
warned against.

Silent, not loud — the run proceeds and looks normal, so a resumed gate can
be verified against stale driver code and reported green. Hit while
resuming FEAT-2026-0058 (#2616) against installed 0.12.1 with a 0.13.0
checkout carrying four driver fixes merged the same day.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from specfuse.loop import build_provenance
from specfuse.loop.loop import resume_command_for


class TestInASourceTree(unittest.TestCase):
    def test_it_names_the_module_form_not_the_console_script(self):
        # This test file lives in the source tree, so the detection is live
        # rather than mocked.
        cmd = resume_command_for("FEAT-2026-9999", start=Path(__file__).parent)

        self.assertIn("python3 -m specfuse.loop.loop", cmd)
        self.assertNotIn("specfuse run", cmd)

    def test_it_still_names_the_feature(self):
        cmd = resume_command_for("FEAT-2026-9999", start=Path(__file__).parent)

        self.assertIn("FEAT-2026-9999", cmd)

    def test_it_agrees_with_the_provenance_warning(self):
        # The two must not drift: the warning tells the operator what to run,
        # and the resume command is the operator running it. Same source.
        self.assertIn(build_provenance._SHIM_HINT.split()[0],
                      resume_command_for("X", start=Path(__file__).parent))


class TestOutsideASourceTree(unittest.TestCase):
    def test_it_keeps_the_console_script_form(self):
        # An installed-only environment has no checkout to prefer, and the
        # console script is the right thing to name there.
        cmd = resume_command_for("FEAT-2026-9999", start=Path("/"))

        self.assertEqual(cmd, "specfuse run --feature FEAT-2026-9999")


class TestTheHaltUsesIt(unittest.TestCase):
    def test_the_staleness_halt_does_not_hardcode_the_console_script(self):
        # The regression: a literal f"specfuse run --feature {feature_id}"
        # at the halt site is what shipped the wrong command.
        import inspect

        from specfuse.loop import loop as driver

        src = inspect.getsource(driver.run)
        self.assertNotIn('resume_command=f"specfuse run --feature', src)
        self.assertIn("resume_command=resume_command_for(", src)


if __name__ == "__main__":
    unittest.main()
