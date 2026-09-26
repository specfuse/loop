# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A dispatched session does not load the skills index unless the project asks
for it (#3423).

`dispatch()` passes `--disable-slash-commands` by default; the resolver reads
`defaults.dispatch_skills` from verification.yml and `execute_unit_attempt`
threads it through.
"""
import contextlib
import io
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
    def _cmd(self, supported: bool = True, **kw):
        fake_proc = mock.MagicMock(stdout="ignored", returncode=0)
        with mock.patch.object(loop, "claude_supports_flag", return_value=supported), \
             mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
            loop.dispatch(_wu(), failure_note=None, cost_tracking=False, **kw)
        return run.call_args[0][0]

    def test_unsupported_cli_omits_the_flag_and_warns_once(self):
        # #3432: an older CLI must not fail every dispatch on an unknown option.
        loop._FLAG_WARNED.discard("--disable-slash-commands")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            first = self._cmd(supported=False)
            second = self._cmd(supported=False)
        self.assertNotIn("--disable-slash-commands", first)
        self.assertNotIn("--disable-slash-commands", second)
        self.assertEqual(buf.getvalue().count("does not accept --disable-slash-commands"), 1)

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
        with mock.patch.object(loop, "claude_supports_flag", return_value=True), \
             mock.patch.object(loop.subprocess, "run", return_value=fake_proc) as run:
            loop.dispatch(wu, failure_note=None, cost_tracking=False)
        cmd = run.call_args[0][0]
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertIn("--disable-slash-commands", cmd)
        self.assertEqual(cmd[1], "-p")


if __name__ == "__main__":
    unittest.main()


class ProbeReadsTheHelpText(unittest.TestCase):
    def setUp(self):
        loop.claude_supports_flag.cache_clear()

    def tearDown(self):
        loop.claude_supports_flag.cache_clear()

    def test_flag_in_help_output_is_supported_and_cached(self):
        fake = mock.MagicMock(stdout="Usage: claude\n  --disable-slash-commands  Disable all skills\n", stderr="")
        with mock.patch.object(loop.subprocess, "run", return_value=fake) as run:
            self.assertTrue(loop.claude_supports_flag("--disable-slash-commands"))
            self.assertTrue(loop.claude_supports_flag("--disable-slash-commands"))
        self.assertEqual(run.call_count, 1)

    def test_flag_absent_or_cli_broken_is_not_supported(self):
        fake = mock.MagicMock(stdout="Usage: claude\n  --model <m>\n", stderr="")
        with mock.patch.object(loop.subprocess, "run", return_value=fake):
            self.assertFalse(loop.claude_supports_flag("--disable-slash-commands"))
        loop.claude_supports_flag.cache_clear()
        with mock.patch.object(loop.subprocess, "run", side_effect=OSError("no claude")):
            self.assertFalse(loop.claude_supports_flag("--disable-slash-commands"))

