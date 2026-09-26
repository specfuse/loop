# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A dispatched session does not load the skills index unless the project asks
for it (#3423).

`dispatch()` passes `--disable-slash-commands` by default; the resolver reads
`defaults.dispatch_skills` from verification.yml and `execute_unit_attempt`
threads it through.
"""
import unittest
from pathlib import Path
from unittest import mock

from tests._loop_loader import load_loop

loop = load_loop()


def _wu(**over):
    base = dict(
        wu_id="FEAT-2026-9999/T01", file=Path("WU-T01.md"), depends_on=[],
        type="implementation", model="claude-sonnet-4-6", effort="medium",
        status="pending", attempts=0, title="t", body="body",
    )
    base.update(over)
    return loop.WorkUnit(**base)


class ResolverReadsTheDefaultsBlock(unittest.TestCase):
    def test_absent_means_no_skills(self):
        self.assertFalse(loop.resolve_dispatch_skills({}))
        self.assertFalse(loop.resolve_dispatch_skills({"defaults": {}}))

    def test_true_restores_the_index(self):
        self.assertTrue(loop.resolve_dispatch_skills({"defaults": {"dispatch_skills": True}}))


class DispatchCmdCarriesTheFlag(unittest.TestCase):
    def _cmd(self, **kw):
        fake_proc = mock.MagicMock(stdout="ignored", returncode=0)
        with mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
            loop.dispatch(_wu(), failure_note=None, cost_tracking=False, **kw)
        return run.call_args[0][0]

    def test_default_disables_slash_commands_after_dash_p(self):
        cmd = self._cmd()
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("--disable-slash-commands", cmd)
        self.assertLess(cmd.index("--disable-slash-commands"), cmd.index("--model"))

    def test_opt_in_keeps_the_index(self):
        self.assertNotIn("--disable-slash-commands", self._cmd(dispatch_skills=True))

    def test_composes_with_the_sandbox_escape(self):
        fake_proc = mock.MagicMock(stdout="ignored", returncode=0)
        wu = _wu(unsandboxed=True, unsandboxed_rationale="needs gh")
        with mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
            loop.dispatch(wu, failure_note=None, cost_tracking=False)
        cmd = run.call_args[0][0]
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertIn("--disable-slash-commands", cmd)
        self.assertEqual(cmd[1], "-p")


if __name__ == "__main__":
    unittest.main()
