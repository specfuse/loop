"""Issue #3293 part 1 — a `complete` RESULT over a produced document that
says BLOCKED is a contradiction, not a pass.

FEAT-2026-0167/T04 (generator) ran a consumer loop, found two feature-
blocking regressions, wrote `CONSUMER-VERIFICATION.md` with the heading
`## Verdict: BLOCKED — ...`, and reported `status: complete`. The driver
reads only the RESULT block, so the unit flipped to `done` and an opus
close was dispatched against a gate the document itself says is not met.

For a unit whose deliverable *is* a verdict, the document is the stronger
signal. `execute_unit_attempt` now scans the unit's produced Markdown for
a heading that carries a blocking verdict and treats `complete` over it as
a failed attempt whose note names the line — the same treatment a
`files_changed` mismatch gets. Closing units are exempt: a close writes a
`not_met` verdict into RETROSPECTIVE.md and reports `complete` by design.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

_COMPLETE_STDOUT = (
    "(stub)\n```result\nstatus: complete\nsummary: ok\n"
    "files_changed: []\nacceptance_criteria: []\n```\n"
)


def _make_wu(wu_type: str, produces: list[str]) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T04",
        file=Path("FAKE-WU.md"),
        depends_on=[],
        type=wu_type,
        model="opus",
        status="pending",
        attempts=0,
        title="consumer verification",
        body=_WU_BODY,
        produces=list(produces),
    )


def _fake_verify(wu, feature_dir, *args, **kwargs):
    return True, "(verify was called)"


class TestProducedDocumentVerdictGuard(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        self.feature_dir = Path(".specfuse/features/FEAT-2026-9999-x")
        self.feature_dir.mkdir(parents=True)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def _attempt(self, wu):
        return loop.execute_unit_attempt(
            wu, self.feature_dir, None,
            dispatch_fn=lambda w, n: _COMPLETE_STDOUT,
            verify_fn=_fake_verify, cost_tracking=False,
        )

    def test_blocked_verdict_heading_fails_the_attempt(self):
        doc = self.feature_dir / "CONSUMER-VERIFICATION.md"
        doc.write_text(
            "# Consumer verification\n\n"
            "## Verdict: BLOCKED — two generator defects, both in `src/`\n\n"
            "prose\n"
        )
        wu = _make_wu("implementation", [str(doc)])
        outcome, payload, _ = self._attempt(wu)
        self.assertEqual(outcome, "failed")
        self.assertIn("### produced-document-verdict: FAIL", payload)
        self.assertIn("CONSUMER-VERIFICATION.md", payload)
        self.assertIn("## Verdict: BLOCKED", payload)
        self.assertIn("status: blocked", payload,
                      "the note tells the retry what the honest RESULT is")
        cls, sig = loop.parse_gate_failure_signature(payload)
        self.assertEqual(cls, "guard_refusal")
        self.assertIn("BLOCKED", sig)

    def test_tokens_in_a_heading_without_the_word_verdict_also_fire(self):
        doc = self.feature_dir / "REPORT.md"
        doc.write_text("# Report\n\n## NOT SHIPPABLE: report.py fails\n")
        wu = _make_wu("qa_execution", [str(doc)])
        outcome, payload, _ = self._attempt(wu)
        self.assertEqual(outcome, "failed")
        self.assertIn("NOT SHIPPABLE", payload)

    def test_tokens_in_prose_do_not_fire(self):
        doc = self.feature_dir / "NOTES.md"
        doc.write_text(
            "# Notes\n\nA previous run was BLOCKED on credentials; this one "
            "is not. The word incomplete appears in prose too.\n\n"
            "## Verdict: SHIPPABLE\n"
        )
        wu = _make_wu("implementation", [str(doc)])
        outcome, _, _ = self._attempt(wu)
        self.assertEqual(outcome, "passed")

    def test_a_close_unit_is_exempt(self):
        retro = self.feature_dir / "RETROSPECTIVE.md"
        retro.write_text("# Retro\n\n## Verdict\n\nverdict: not_met\n\n"
                         "## Verdict: BLOCKED\n")
        wu = _make_wu("close", [str(retro)])
        outcome, _, _ = self._attempt(wu)
        self.assertEqual(outcome, "passed")

    def test_non_markdown_and_missing_paths_are_ignored(self):
        wu = _make_wu("implementation", ["src/foo.py", "docs/missing.md"])
        Path("src").mkdir()
        Path("src/foo.py").write_text("# BLOCKED\n")
        outcome, _, _ = self._attempt(wu)
        self.assertEqual(outcome, "passed")


if __name__ == "__main__":
    unittest.main()
