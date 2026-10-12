# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A headless `/fix-bug` session cannot background a command (#3418).

A headless session started its test suite with the Bash tool's background
mode and ended its turn to wait for the completion notification. In a
`claude -p` session nothing arrives once the turn ends: it exited with no
outcome marker, `classify_outcome` failed closed to `could_not_proceed`, and a
possibly complete fix was parked on a `wip/` ref (clabonte/generator#2115).

The fix-bug skill has told headless sessions to run gates in the foreground
since #3248; the session backgrounded anyway. So the boundary is the process,
not the prompt: the session is launched with
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` set through `--settings`, which removes
`run_in_background` from its tools. Through argv rather than the runner's
environment so every runner -- the bug lane's and the monitor autofix lane's
-- carries it with no new keyword.
"""

from __future__ import annotations

import json
import unittest

from specfuse.monitor.autofix_invoke import build_invocation


def _settings(argv):
    return json.loads(argv[argv.index("--settings") + 1])


class TestHeadlessFixBugCannotBackground(unittest.TestCase):
    def test_background_tasks_are_disabled_for_the_session(self):
        argv, _prompt = build_invocation(2115, "o/r", "/tmp/tree")

        self.assertIn("--settings", argv)
        self.assertEqual(
            _settings(argv)["env"].get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"), "1",
        )

    def test_it_holds_for_every_model_and_effort(self):
        argv, _prompt = build_invocation(2115, "o/r", ".", model="opus", effort="high")

        self.assertEqual(
            _settings(argv)["env"].get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"), "1",
        )

    def test_the_session_is_still_a_claude_dispatch(self):
        # `_bounded_runner` applies the item timeout and the worktree cwd only
        # to a call whose argv starts with `claude` (#3420).
        argv, _prompt = build_invocation(2115, "o/r", ".")

        self.assertEqual(argv[:2], ["claude", "-p"])


if __name__ == "__main__":
    unittest.main()
