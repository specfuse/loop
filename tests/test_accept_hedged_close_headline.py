# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0059/T02: /accept-hedged-close's step 2 must lead with the
# verdict ceiling T01's classification implies, and scaffold the reason
# prompt from that classification, instead of quoting the raw record and
# demanding a one-line reason after a wall of text.
#
# AC1/AC2: step 2 instructs the ceiling headline to be printed before the
#          entry detail, and names both branches.
# AC3: the skill documents the mapping from each of T01's four kinds to its
#      ceiling contribution, and that only externally-verifiable-later
#      implies rework exists.
# AC4: the skill still requires the operator's own words, states the
#      never-author rule explicitly, and contains no pre-filled reason
#      string an operator could accept unread.
# AC5: the skill states what to do with an entry carrying no kind: — report
#      unclassified, fall back, never guess from wording.
# AC6: both SKILL.md copies are byte-identical (also covered generically by
#      test_skills_vendored_in_sync.py); skill discovery + scaffold sync
#      tests still pass.

import io
import pathlib
import re
import subprocess
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "accept-hedged-close" / "SKILL.md"
_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "accept-hedged-close" / "SKILL.md"


def _skill_text() -> str:
    return _CANONICAL.read_text(encoding="utf-8")


def _step_2_text(text: str) -> str:
    start = text.index("### 2.")
    end = text.index("### 3.")
    return text[start:end]


def _run_suites_in_process(test_case, module_names):
    """Run named unittest modules in-process and assert they pass.

    NOT a `python3 -m pytest` subprocess: pytest is a dependency of nothing in
    this repository -- it appears in no pyproject.toml extra and no CI workflow --
    so the subprocess form passes on a developer venv that happens to have it and
    fails on the runner with `No module named pytest`. The whole repository runs
    on `python3 -m unittest discover -s tests`. See tests/test_no_pytest_subprocess.py,
    which exists to stop this recurring a fourth time.
    """
    suite = unittest.TestSuite()
    for name in module_names:
        loaded = unittest.defaultTestLoader.loadTestsFromName(name)
        test_case.assertGreater(
            loaded.countTestCases(), 0,
            f"{name} loaded zero tests -- a vacuous pass is exactly the failure "
            f"this assertion exists to prevent")
        suite.addTest(loaded)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    test_case.assertTrue(
        result.wasSuccessful(),
        msg=chr(10).join(t for _, t in (result.failures + result.errors))
            or "suite failed with no captured output")


class TestAcceptHedgedCloseHeadline(unittest.TestCase):
    def test_skill_leads_with_the_verdict_ceiling(self):
        step2 = _step_2_text(_skill_text())

        headline_idx = step2.index("no in-repo rework can raise this verdict")
        rework_match = re.search(r"rework\s+exists:", step2)
        self.assertIsNotNone(rework_match, "rework-exists branch not found")
        detail_idx = step2.rindex("quote every entry")

        self.assertLess(
            headline_idx, detail_idx,
            "the no-in-repo-rework branch must be instructed before entry detail",
        )
        self.assertLess(
            rework_match.start(), detail_idx,
            "the rework-exists branch must be instructed before entry detail",
        )

    def test_both_ceiling_branches_are_named(self):
        step2 = _step_2_text(_skill_text())
        self.assertIn("no in-repo rework can raise this verdict", step2)
        self.assertRegex(step2, r"rework\s+exists:")

    def test_headline_printed_before_quoting_any_entry(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(
            step2,
            r"(?i)headline first, before quoting any entry",
        )

    def test_documents_mapping_from_all_four_kinds_to_ceiling(self):
        text = _skill_text()
        for kind in (
            "acceptance-discharged",
            "externally-verifiable-later",
            "routed-finding",
            "inherent",
        ):
            self.assertIn(kind, text, f"missing kind in skill text: {kind}")

    def test_only_externally_verifiable_later_implies_rework_exists(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(
            step2,
            r"(?i)Only `externally-verifiable-later` implies rework exists",
        )
        # The other three collapse to no-in-repo-rework, stated explicitly.
        self.assertRegex(
            step2,
            r"(?i)other\s+three\s+kinds\s+all\s+collapse\s+to.{0,10}"
            r"\"no in-repo rework can raise this verdict\"",
        )

    # The assertion that this step names the verdict-ceiling helper and the
    # follow-up classification set is gone: FEAT-2026-0085/T01 deleted both
    # with the verdicts they served, so pinning the skill's prose to their
    # names would require it to cite code that no longer exists. The skill
    # itself is retired by FEAT-2026-0085/T05, which owns `plugins/`; until
    # then its remaining prose assertions below still hold.


class TestUnclassifiedEntryFallback(unittest.TestCase):
    def test_states_no_ceiling_on_missing_or_unrecognized_kind(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(
            step2,
            r"(?i)no `?kind:`?, or an unrecognized one",
        )

    def test_states_never_guess_from_wording(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(step2, r"(?i)do \*{0,2}not\*{0,2} guess one from the entry's wording")

    def test_states_fallback_to_todays_behaviour(self):
        step2 = _step_2_text(_skill_text())
        self.assertRegex(step2, r"(?i)fall\s+back\s+to\s+today's\s+behaviour")


class TestReasonPromptScaffoldedNotAuthored(unittest.TestCase):
    def test_requires_operators_own_words(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)the human supplies every word of the reason")

    def test_states_never_author_rule_explicitly(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)never-author rule")
        self.assertIn("operator-escalation.md", text)

    def test_prompt_names_what_is_accepted_not_a_reason(self):
        text = _skill_text()
        self.assertIn("you are accepting that no in-repo rework", text)
        self.assertIn("you are accepting now instead of waiting", text)

    def test_no_pre_filled_reason_string_an_operator_could_accept_unread(self):
        text = _skill_text()
        self.assertRegex(
            text,
            r"(?i)contains\s+no\s+reason\s+text\s+an\s+operator\s+could\s+accept\s+unread",
        )
        self.assertRegex(
            text,
            r"(?i)worse\s+than\s+a\s+blank\s+line.{0,60}"
            r"invites\s+accepting\s+a\s+sentence\s+the\s+operator\s+never\s+thought",
        )

    def test_fallback_prompt_unchanged_when_ceiling_not_computed(self):
        text = _skill_text()
        self.assertIn(
            "no ceiling computed (an unclassified entry is present): fall back to",
            text,
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
        _run_suites_in_process(self, ["tests.test_skill_discovery_links"])

    def test_scaffold_sync_suite_passes(self):
        _run_suites_in_process(self, ["tests.test_skills_vendored_in_sync",
                                      "tests.test_prepare_scaffold_sync"])


if __name__ == "__main__":
    unittest.main()
