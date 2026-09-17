#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Headless lanes must dispatch a command the plugin actually answers to (#3342).

`specfuse/monitor/autofix_invoke.py` and `specfuse/agent/drafting_invoke.py`
build prompts whose first line is a slash command. Both hardcoded the bare
spelling (`/fix-bug`, `/draft-feature`), which resolves only where a
project-level `.claude/skills/<name>/` copy survives. The skills ship in the
`specfuse@specfuse` plugin, where they are addressed `/specfuse:<name>`; on
2026-09-17 a run against a repo provisioned exactly as the docs prescribe
dispatched 55 bug items and every one came back `Unknown command: /fix-bug`.

These tests pin the dispatched spelling at both sites and the override seam a
caller uses when the bare form is the one that resolves.
"""

from __future__ import annotations

import unittest

from specfuse.agent.drafting_invoke import build_invocation as build_drafting
from specfuse.agent.drafting_answers import OUTCOME_DRAFT_READY, AnswerGateResult
from specfuse.monitor.autofix_invoke import build_invocation as build_autofix


class BugLaneDispatchesAResolvableCommand(unittest.TestCase):

    def test_prompt_opens_with_the_plugin_qualified_command(self):
        _, prompt = build_autofix(
            issue_number=42, repo="acme-widget/example", working_dir="/tmp/scratch"
        )
        self.assertTrue(
            prompt.startswith("/specfuse:fix-bug 42"),
            f"expected a plugin-qualified first line, got {prompt.splitlines()[0]!r}",
        )

    def test_bare_spelling_is_not_dispatched_by_default(self):
        _, prompt = build_autofix(
            issue_number=42, repo="acme-widget/example", working_dir="/tmp/scratch"
        )
        self.assertNotIn(
            "\n/fix-bug ", "\n" + prompt,
            "the bare command resolves only where a legacy project-level copy "
            "survives; it must not be what the lane dispatches",
        )

    def test_caller_can_override_the_command_spelling(self):
        _, prompt = build_autofix(
            issue_number=42,
            repo="acme-widget/example",
            working_dir="/tmp/scratch",
            command="/fix-bug",
        )
        self.assertTrue(prompt.startswith("/fix-bug 42"))


class DraftingDispatchesAResolvableCommand(unittest.TestCase):

    def _gate_result(self):
        return AnswerGateResult(
            outcome=OUTCOME_DRAFT_READY,
            answers={"roadmap-goal": "Keep the widget catalog in sync."},
            assumptions=(),
        )

    def test_prompt_opens_with_the_plugin_qualified_command(self):
        _, prompt = build_drafting("FEAT-2026-0099", self._gate_result())
        self.assertTrue(
            prompt.startswith("/specfuse:draft-feature FEAT-2026-0099"),
            f"expected a plugin-qualified first line, got {prompt.splitlines()[0]!r}",
        )

    def test_caller_can_override_the_command_spelling(self):
        _, prompt = build_drafting(
            "FEAT-2026-0099", self._gate_result(), command="/draft-feature"
        )
        self.assertTrue(prompt.startswith("/draft-feature FEAT-2026-0099"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
