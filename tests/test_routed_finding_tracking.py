# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0059/T03: at acceptance, each `routed-finding` entry prompts for
# a tracking surface — an existing issue/roadmap reference, or an offer to
# create one — so an accepted follow-up lands somewhere a human meets it
# again, instead of only in retrospective prose nobody reopens.
#
# AC1/AC2: the prompt exists in SKILL.md's step 2, offering an existing
#          issue/roadmap reference or /roadmap-add / gh issue create.
# AC3: the answer is written into the acceptance record next to the entry
#      it belongs to, not as a loose appendix.
# AC4: the other three kinds do not trigger the prompt, with the reason
#      stated (discharged / inherent / already carries its re-run
#      condition).
# AC5: "tracked nowhere, deliberately" is an accepted, non-blocking answer.
# AC6: T02's ceiling headline is still present and unmodified.
# AC7: both SKILL.md copies are byte-identical; skill discovery + scaffold
#      sync tests still pass.

import pathlib
import subprocess
import sys
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "accept-hedged-close" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "accept-hedged-close" / "SKILL.md"


def _skill_text() -> str:
    return _CANONICAL.read_text(encoding="utf-8")


def _step_text(text: str, step: str, next_step: str) -> str:
    start = text.index(f"### {step}.")
    end = text.index(f"### {next_step}.")
    return text[start:end]


def _step_2_text(text: str) -> str:
    return _step_text(text, "2", "3")


def _step_4_text(text: str) -> str:
    return _step_text(text, "4", "5")


class TestRoutedFindingTracking(unittest.TestCase):
    def test_routed_finding_prompts_for_a_tracking_surface(self):
        step2 = _step_2_text(_skill_text())
        self.assertIn("routed-finding", step2)
        self.assertRegex(step2, r"(?i)where is it tracked")
        self.assertIn("/roadmap-add", step2)
        self.assertIn("gh issue create", step2)
        self.assertRegex(step2, r"(?i)existing issue or roadmap\s+reference")


class TestTrackingAnswerRecordedNextToEntry(unittest.TestCase):
    def test_recorded_next_to_the_entry_not_as_an_appendix(self):
        step4 = _step_4_text(_skill_text())
        self.assertRegex(step4, r"(?i)written immediately next to that entry")
        self.assertRegex(step4, r"(?i)never as a loose\s+appendix")

    def test_untracked_finding_and_reference_readable_together(self):
        step4 = _step_4_text(_skill_text())
        self.assertRegex(step4, r"(?i)readable\s+together")


class TestOtherKindsDoNotTriggerPrompt(unittest.TestCase):
    def test_other_three_kinds_named_with_reason_they_are_excluded(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(
            step2,
            r"(?i)`acceptance-discharged`\s+is\s+discharged\s+by\s+the\s+acceptance\s+itself",
        )
        self.assertRegex(
            step2, r"(?i)`inherent`\s+is\s+never\s+actionable\s+by\s+anyone"
        )
        self.assertRegex(
            step2,
            r"(?i)`externally-verifiable-later`\s+already\s+carries\s+its\s+exact\s+"
            r"re-run\s+condition",
        )

    def test_prompt_scoped_to_routed_finding_only(self):
        step2 = _step_2_text(_skill_text())
        idx = step2.index("For each `routed-finding` entry")
        self.assertRegex(
            step2[idx:idx + 900], r"(?i)other\s+three\s+kinds\s+never\s+trigger\s+this\s+prompt"
        )


class TestTrackedNowhereDeliberatelyAccepted(unittest.TestCase):
    def test_nowhere_deliberately_is_an_accepted_answer(self):
        step2 = _step_2_text(_skill_text())
        self.assertIn("nowhere, deliberately", step2)

    def test_prompt_is_not_a_gate(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(step2, r"(?i)this\s+prompt\s+is\s+not\s+a\s+gate")
        self.assertRegex(step2, r"(?i)single-confirm\s+skill")

    def test_prompt_does_not_block_step_3_confirmations(self):
        text = _skill_text()
        step3 = _step_text(text, "3", "4")
        # Step 3's four required inputs must still be exactly feature ID,
        # done/hedged confirmation, one-line reason, and follow-up
        # acknowledgment — the tracking prompt must not have become a fifth
        # mandatory gate there.
        self.assertIn("1. **The feature ID**", step3)
        self.assertIn(
            "2. **Confirmation the close WU is `done` with a hedged verdict**",
            step3,
        )
        self.assertIn("3. **A one-line operator reason**", step3)
        self.assertIn(
            "4. **Explicit acknowledgment of the standing follow-up list**",
            step3,
        )
        self.assertNotIn("5. **", step3)


class TestCeilingHeadlineStillPresentAndUnmodified(unittest.TestCase):
    def test_ceiling_headline_unchanged(self):
        step2 = _step_2_text(_skill_text())
        self.assertIn("no in-repo rework can raise this verdict", step2)
        self.assertRegex(step2, r"rework\s+exists:")
        self.assertRegex(
            step2,
            r"(?i)Only `externally-verifiable-later` implies rework exists",
        )


class TestBothSkillCopiesByteIdentical(unittest.TestCase):
    def test_canonical_and_vendored_identical(self):
        result = subprocess.run(
            ["diff", str(_CANONICAL), str(_VENDORED)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=f"diff output:\n{result.stdout}")
        self.assertEqual(result.stdout, "")

    def test_skill_discovery_links_suite_passes(self):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             str(_REPO_ROOT / "tests" / "test_skill_discovery_links.py")],
            capture_output=True, text=True, cwd=_REPO_ROOT, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_scaffold_sync_suite_passes(self):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             str(_REPO_ROOT / "tests" / "test_skills_vendored_in_sync.py"),
             str(_REPO_ROOT / "tests" / "test_prepare_scaffold_sync.py")],
            capture_output=True, text=True, cwd=_REPO_ROOT, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
