#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Model-alias acceptance — FEAT-2026-0007/T01.

Verifies that:
  1. load_wu() accepts family aliases ('sonnet', 'opus', 'haiku') in the
     model: frontmatter field without error.
  2. execute_unit_attempt() passes the alias verbatim so the CLI receives
     --model sonnet (not an expanded concrete ID).
  3. lint_plan.lint() accepts aliases and full IDs, and rejects garbage.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop, load_lint

loop = load_loop()
lint = load_lint()


def _write_wu(tmp: Path, model: str) -> Path:
    path = tmp / "WU-T01.md"
    path.write_text(
        f"---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
        f"model: {model}\nstatus: pending\nattempts: 0\n---\n\n"
        "# Test unit\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    return path


class TestLoadWuModelAlias(unittest.TestCase):

    def _load(self, model: str):
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), model)
            ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md",
                   "depends_on": []}
            return loop.load_wu(Path(tmp), ref)

    def test_alias_sonnet_loads_without_error(self):
        wu = self._load("sonnet")
        self.assertEqual(wu.model, "sonnet")

    def test_alias_opus_loads_without_error(self):
        wu = self._load("opus")
        self.assertEqual(wu.model, "opus")

    def test_alias_haiku_loads_without_error(self):
        wu = self._load("haiku")
        self.assertEqual(wu.model, "haiku")

    def test_full_id_still_loads(self):
        wu = self._load("claude-sonnet-4-6")
        self.assertEqual(wu.model, "claude-sonnet-4-6")

    def test_default_model_unchanged(self):
        """load_wu default when model key absent is still claude-sonnet-4-6."""
        with tempfile.TemporaryDirectory() as tmp:
            path = tmp / "WU-T01.md" if isinstance(tmp, Path) else Path(tmp) / "WU-T01.md"
            path.write_text(
                "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
                "status: pending\nattempts: 0\n---\n\n# Test unit\n"
            )
            ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md",
                   "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)
            self.assertEqual(wu.model, "claude-sonnet-4-6")


class TestDispatchReceivesAliasVerbatim(unittest.TestCase):

    def test_dispatch_stub_called_with_model_sonnet(self):
        """execute_unit_attempt passes wu.model='sonnet' verbatim to dispatch_fn,
        which means CLAUDE_CMD would be invoked as: claude -p --model sonnet."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), "sonnet")
            ref = {"id": "FEAT-2026-9999/T01", "file": "WU-T01.md",
                   "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)

            captured = {}

            def fake_dispatch(wu_arg, failure_note):
                captured["model"] = wu_arg.model
                return (
                    "(stub)\n```result\nstatus: complete\nsummary: ok\n"
                    "files_changed: []\nacceptance_criteria: []\n```\n"
                )

            loop.execute_unit_attempt(
                wu, Path(tmp), None,
                dispatch_fn=fake_dispatch,
                verify_fn=lambda wu, fd, cfg=None: (True, "pass"),
            )

            self.assertEqual(captured["model"], "sonnet")
            # Verify the CLAUDE_CMD template expansion produces --model sonnet.
            cmd = [p.replace("{model}", captured["model"]) for p in loop.CLAUDE_CMD]
            idx = cmd.index("--model")
            self.assertEqual(cmd[idx + 1], "sonnet")


class TestLintPlanModelAlias(unittest.TestCase):

    def _make_feature(self, tmp: Path, model: str) -> Path:
        fdir = tmp / "FEAT-2026-9999-alias"
        fdir.mkdir()
        _write_wu(fdir, model)
        plan = (
            "---\nfeature_id: FEAT-2026-9999\ntitle: alias test\n"
            "branch: feat/alias\nroadmap_goal: test\nstatus: active\n---\n\n"
            "```yaml\ngates:\n"
            "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
            "      - id: FEAT-2026-9999/T01\n        file: WU-T01.md\n"
            "        depends_on: []\n"
            "      - id: FEAT-2026-9999/G1-RETRO\n        file: WU-G1-RETRO.md\n"
            "        depends_on: [FEAT-2026-9999/T01]\n"
            "      - id: FEAT-2026-9999/G1-LESSONS\n        file: WU-G1-LESSONS.md\n"
            "        depends_on: [FEAT-2026-9999/G1-RETRO]\n"
            "      - id: FEAT-2026-9999/G1-DOCS\n        file: WU-G1-DOCS.md\n"
            "        depends_on: [FEAT-2026-9999/G1-LESSONS]\n"
            "      - id: FEAT-2026-9999/G1-PLAN\n        file: WU-G1-PLAN.md\n"
            "        depends_on: [FEAT-2026-9999/G1-DOCS]\n"
            "```\n"
        )
        (fdir / "PLAN.md").write_text(plan)
        (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        body = (
            "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n"
        )
        for wu_id, wu_type in [
            ("FEAT-2026-9999/G1-RETRO", "retrospective"),
            ("FEAT-2026-9999/G1-LESSONS", "lessons"),
            ("FEAT-2026-9999/G1-DOCS", "docs"),
            ("FEAT-2026-9999/G1-PLAN", "plan-next"),
        ]:
            tnn = wu_id.split("/")[-1]
            (fdir / f"WU-{tnn}.md").write_text(
                f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-sonnet-4-6\n"
                f"status: pending\nattempts: 0\n---\n\n# {tnn}{body}"
            )
        return fdir

    def test_sonnet_alias_passes_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(Path(tmp), "sonnet")
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "model" in e]
            self.assertEqual(model_errs, [],
                             f"unexpected model errors: {model_errs}")

    def test_opus_alias_passes_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(Path(tmp), "opus")
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "model" in e]
            self.assertEqual(model_errs, [])

    def test_haiku_alias_passes_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(Path(tmp), "haiku")
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "model" in e]
            self.assertEqual(model_errs, [])

    def test_full_model_id_still_passes_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(Path(tmp), "claude-opus-4-7")
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "model" in e]
            self.assertEqual(model_errs, [])

    def test_garbage_model_fails_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = self._make_feature(Path(tmp), "gpt-4o")
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "invalid model" in e]
            self.assertEqual(len(model_errs), 1)

    def test_model_aliases_constant_is_explicit_set(self):
        """MODEL_ALIASES in both loop and lint_plan are explicit sets, not regexes."""
        self.assertIsInstance(loop.MODEL_ALIASES, frozenset)
        self.assertIsInstance(lint.MODEL_ALIASES, frozenset)
        self.assertEqual(loop.MODEL_ALIASES, frozenset({"sonnet", "opus", "haiku"}))
        self.assertEqual(lint.MODEL_ALIASES, frozenset({"sonnet", "opus", "haiku"}))


if __name__ == "__main__":
    unittest.main()
