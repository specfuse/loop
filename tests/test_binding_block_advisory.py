#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The binding-block budget check must actually run (#3320).

FEAT-2026-0111/T04 shipped `check_binding_block_budget` and described the
2,500-word cap as having moved from an advisory comment to enforcement. It had
no caller: its only callers were its own tests, so the cap enforced exactly as
much after the feature as before — nothing.

It is wired as a **once-per-gate advisory, not a blocking gate**, deliberately.
Measured across 17 real projects carrying a binding block on 2026-09-14, **15
were over the cap** — the generator at 12,187 words, nearly 5x it. A blocking
gate would have red-lined almost every consuming project on upgrade, which is
the unsatisfiable-predicate defect `planning-discipline.md` §2 names. #3320
said not to ship blocking before that was measured; it is measured, and this
is the answer.

These assert on what a real `loop.run()` prints, not on the helper in
isolation — the defect was that nothing called it, and a test that calls it
directly would have passed throughout.
"""
from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()


def _write_binding_block(root: Path, rule_words: int) -> None:
    """A CLAUDE.md whose binding block references one rule of *rule_words*."""
    rules = root / ".specfuse" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    (rules / "result-contract.md").write_text(
        "# Rule\n\n" + " ".join(["word"] * rule_words) + "\n", encoding="utf-8")
    claude = root / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "CLAUDE.md").write_text(
        "# Notes\n\n"
        "## Specfuse binding rules (read before any work-unit dispatch)\n"
        "@.specfuse/rules/result-contract.md\n",
        encoding="utf-8")


class BindingBlockAdvisoryIsPrintedByARealRun(unittest.TestCase):

    def setUp(self):
        self._patches: list[tuple] = []
        self._cwd = os.getcwd()

    def tearDown(self):
        for name, original in reversed(self._patches):
            setattr(loop, name, original)
        os.chdir(self._cwd)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _run(self, rule_words: int) -> str:
        from tests.test_spinout_brief_end_to_end import write_feature
        with integration_workspace() as root:
            os.chdir(root)
            write_feature(root, "FEAT-2026-9601", "budget-advisory",
                          "feat/budget-advisory", [("FEAT-2026-9601/T01", "")])
            _write_binding_block(Path(root), rule_words)

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: [])

            captured = io.StringIO()
            with redirect_stdout(captured):
                loop.run(None, dry_run=False)
            return captured.getvalue()

    def test_a_block_over_the_cap_is_reported_by_the_run(self):
        stdout = self._run(rule_words=3000)
        self.assertIn("binding block", stdout.lower())
        self.assertIn("2500", stdout.replace(",", ""))

    def test_a_block_under_the_cap_says_nothing(self):
        # The control. Without it, printing the advisory unconditionally passes.
        stdout = self._run(rule_words=50)
        self.assertNotIn("binding block", stdout.lower())

    def test_the_advisory_never_blocks_the_run(self):
        # 15 of 17 real projects are over the cap; an advisory that halts them
        # is the defect, not the fix.
        stdout = self._run(rule_words=3000)
        self.assertNotIn("Gate halted", stdout)


if __name__ == "__main__":
    unittest.main()
