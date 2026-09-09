#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The pin marker must not reach a child that runs the project's own code.

FEAT-2026-0109/T08 passes the pin identity to the re-exec'd driver through
`SPECFUSE_LOOP_PINNED_TREE`. Environment is inherited, so without an explicit
strip at the spawn boundary every descendant sees it — including the gate
subprocesses that run this repository's test suite.

That is what gate 3's once-per-gate broad run caught:
`test_driver_edit_halts_before_next_dispatch` asserts the halt fires, saw the
inherited marker, took the pinned "record, do not halt" branch, and failed. The
failure was invisible to `smoke-test.sh`, to CI, and to any local run, because
none of those has the marker set — only a gate subprocess of a *pinned driver*
does. Reproduction:

    env SPECFUSE_LOOP_PINNED_TREE=<hash> python3 -m unittest \\
        tests.test_driver_restart_halt_wiring     # -> FAILED

These tests assert the strip itself rather than any one downstream symptom, so
a future pin-conditional branch inherits the protection instead of having to
rediscover the hazard.
"""

from __future__ import annotations

import os
import unittest
import unittest.mock

from tests._loop_loader import load_loop

loop = load_loop()


class TestPinMarkerNotInherited(unittest.TestCase):

    def test_marker_is_stripped_from_a_child_environment(self):
        with unittest.mock.patch.dict(
            os.environ, {loop.PINNED_BUILD_ENV_VAR: "deadbeef"}, clear=False
        ):
            self.assertEqual(os.environ.get(loop.PINNED_BUILD_ENV_VAR), "deadbeef",
                             "precondition: the marker is set for this process")
            env = loop.child_env_without_pin_marker()
        self.assertNotIn(
            loop.PINNED_BUILD_ENV_VAR, env,
            "a child that runs the project's own code must not inherit the "
            "driver's pin marker — it decides pin-conditional branches")

    def test_the_rest_of_the_environment_survives(self):
        # Stripping must be surgical: gate commands need PATH, VIRTUAL_ENV and
        # everything else, and a wholesale clean env would break them in ways
        # far louder but no less wrong than the leak.
        with unittest.mock.patch.dict(
            os.environ,
            {loop.PINNED_BUILD_ENV_VAR: "deadbeef", "SPECFUSE_TEST_CANARY": "kept"},
            clear=False,
        ):
            env = loop.child_env_without_pin_marker()
        self.assertEqual(env.get("SPECFUSE_TEST_CANARY"), "kept")
        self.assertIn("PATH", env)

    def test_absent_marker_is_not_an_error(self):
        # The common case: an unpinned driver has no marker to strip.
        env_copy = dict(os.environ)
        env_copy.pop(loop.PINNED_BUILD_ENV_VAR, None)
        with unittest.mock.patch.dict(os.environ, env_copy, clear=True):
            env = loop.child_env_without_pin_marker()
        self.assertNotIn(loop.PINNED_BUILD_ENV_VAR, env)

    def test_the_gate_runner_passes_a_stripped_environment(self):
        """The wiring, not just the helper — a defined-but-uncalled strip is
        the unwired-helper hollow pass this feature family keeps auditing for.

        Asserted through observed behaviour: the gate command reports the
        marker it can actually see, with the marker set in this process.
        """
        gate = {
            "name": "echo-marker",
            "command": (
                'python3 -c "import os;'
                "print('MARKER=' + os.environ.get('SPECFUSE_LOOP_PINNED_TREE', 'ABSENT'))\""
            ),
        }
        with unittest.mock.patch.dict(
            os.environ, {loop.PINNED_BUILD_ENV_VAR: "deadbeef"}, clear=False
        ):
            results = loop._run_gate_set([gate], loop.Path("."))
        self.assertEqual(len(results), 1, f"results={results!r}")
        self.assertIn(
            "MARKER=ABSENT", results[0]["report"],
            "the gate subprocess saw the driver's pin marker; it must be "
            f"stripped at the spawn boundary. report={results[0]['report']!r}")


if __name__ == "__main__":
    unittest.main()
