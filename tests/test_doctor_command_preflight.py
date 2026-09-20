# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`specfuse doctor` checks that dispatched slash commands resolve (#3347).

#3342 is what this exists to catch before a run rather than after: the bug lane
dispatched a command that resolved nowhere, and the first thing to notice was
the run itself — after it had dispatched 55 triaged bugs, collected
`Unknown command: /fix-bug` from every one, and labelled all 55 `needs-human`.

The failure mode is not specific to that spelling. It fires whenever the
command a lane dispatches and the command the project can resolve disagree: a
plugin not enabled, a plugin enabled under a different marketplace key, a
project-level `.claude/skills/` copy removed, a skill renamed upstream.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop.scaffold import (
    dispatched_skill_commands,
    doctor,
    resolve_slash_command,
)

_PLUGIN_KEY = "specfuse@specfuse"


def _manifest(tmp: Path, *, installed: bool) -> Path:
    path = tmp / "installed_plugins.json"
    payload = {"plugins": {_PLUGIN_KEY: [{"version": "0.7.1"}]}} if installed else {"plugins": {}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _project(tmp: Path, *, enabled: bool, bare_skill: str | None = None) -> Path:
    target = tmp / "repo"
    (target / ".claude").mkdir(parents=True)
    (target / ".specfuse").mkdir()
    settings = {"enabledPlugins": {_PLUGIN_KEY: True}} if enabled else {}
    (target / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    if bare_skill:
        skill_dir = target / ".claude" / "skills" / bare_skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    return target


class TheDispatchedSetIsReadFromTheLanes(unittest.TestCase):

    def test_both_shipping_lanes_are_listed(self):
        commands = dispatched_skill_commands()
        self.assertIn("/specfuse:fix-bug", commands.values())
        self.assertIn("/specfuse:draft-feature", commands.values())

    def test_the_set_is_not_a_hand_maintained_literal(self):
        # Read from the lanes' own DEFAULT_COMMAND, so a third lane is covered
        # without editing this check. Asserted by comparing against the
        # constants themselves rather than against a copy.
        from specfuse.agent import drafting_invoke
        from specfuse.monitor import autofix_invoke

        self.assertEqual(
            set(dispatched_skill_commands().values()),
            {autofix_invoke.DEFAULT_COMMAND, drafting_invoke.DEFAULT_COMMAND},
        )


class ResolvingOneCommand(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_qualified_resolves_when_the_plugin_is_installed_and_enabled(self):
        target = _project(self.tmp, enabled=True)
        ok, why = resolve_slash_command(
            "/specfuse:fix-bug", target,
            plugins_manifest_path=_manifest(self.tmp, installed=True),
        )
        self.assertTrue(ok, why)

    def test_qualified_does_not_resolve_when_the_plugin_is_not_enabled(self):
        target = _project(self.tmp, enabled=False)
        ok, why = resolve_slash_command(
            "/specfuse:fix-bug", target,
            plugins_manifest_path=_manifest(self.tmp, installed=True),
        )
        self.assertFalse(ok)
        self.assertIn("enabled", why)

    def test_qualified_does_not_resolve_when_the_plugin_is_not_installed(self):
        target = _project(self.tmp, enabled=True)
        ok, why = resolve_slash_command(
            "/specfuse:fix-bug", target,
            plugins_manifest_path=_manifest(self.tmp, installed=False),
        )
        self.assertFalse(ok)
        self.assertIn("install", why)

    def test_a_bare_command_resolves_from_a_project_level_skill(self):
        target = _project(self.tmp, enabled=False, bare_skill="fix-bug")
        ok, why = resolve_slash_command(
            "/fix-bug", target,
            plugins_manifest_path=_manifest(self.tmp, installed=False),
        )
        self.assertTrue(ok, why)

    def test_a_bare_command_without_a_project_skill_does_not_resolve(self):
        target = _project(self.tmp, enabled=True)
        ok, why = resolve_slash_command(
            "/fix-bug", target,
            plugins_manifest_path=_manifest(self.tmp, installed=True),
        )
        self.assertFalse(ok)
        self.assertIn(".claude/skills/fix-bug", why)


class DoctorReportsIt(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _doctor(self, *, enabled: bool, installed: bool) -> dict:
        target = _project(self.tmp, enabled=enabled)
        (target / ".specfuse" / "VERSION").write_text("0.21.0\n", encoding="utf-8")
        return doctor(
            target,
            installed_driver_version="0.21.0",
            plugins_manifest_path=_manifest(self.tmp, installed=installed),
        )

    def test_a_resolvable_project_reports_every_command_resolving(self):
        report = self._doctor(enabled=True, installed=True)
        self.assertIn("dispatched_commands", report)
        self.assertTrue(all(e["resolves"] for e in report["dispatched_commands"].values()))
        self.assertNotIn("resolves nowhere", report["recommended_action"])

    def test_an_unresolvable_command_is_named_in_the_recommended_action(self):
        report = self._doctor(enabled=False, installed=True)
        self.assertFalse(any(e["resolves"] for e in report["dispatched_commands"].values()))
        self.assertIn("resolves nowhere", report["recommended_action"])
        self.assertIn("/specfuse:fix-bug", report["recommended_action"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
