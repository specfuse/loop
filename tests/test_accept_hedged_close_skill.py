# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0070/T03: the accept-hedged-close skill lets an operator accept a
# standing hedged (met_locally / partially_met) close verdict, recording the
# reason and carried-forward follow-ups, then firing the terminal flips
# exclusively through T02's `--recheck-verdict` primitive.
#
# AC1/AC2: plugins/specfuse/skills/accept-hedged-close/SKILL.md exists with
#          valid frontmatter (name, description). Fails on HEAD before this
#          WU (the directory does not exist yet).
# AC3: SKILL.md contains no instruction to edit PLAN.md's status, the gate
#      status, or the roadmap row directly, and names T02's primitive
#      (--recheck-verdict / recheck_terminal_verdict) as the mechanism.
# AC4: the method requires, before any write: feature ID, confirmation the
#      close WU is done with a hedged verdict, a mandatory one-line reason
#      (empty/whitespace refused and re-prompted), and explicit
#      acknowledgment of the follow-up list.
# AC5: the acceptance record names the accepted verdict, the operator
#      reason, each follow-up carried forward verbatim, and the timestamp.
# AC6: refuses on verdict == met, verdict == not_met, and close WU not done
#      -- one test per condition.
# AC7: does not discharge or close the follow-ups; text says so.
# AC8: byte-identity across trees is asserted generically by
#      tests/test_skills_vendored_in_sync.py; not re-asserted here.
# AC9: ends with the RESULT block per result-contract.md.

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL_DIR = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "accept-hedged-close"
_VENDORED_DIR = _REPO_ROOT / ".specfuse" / "skills" / "accept-hedged-close"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _skill_text() -> str:
    return _read(_CANONICAL_DIR / "SKILL.md")


class TestSkillRegistration(unittest.TestCase):
    def test_skill_is_registered_and_canonical(self):
        skill_md = _CANONICAL_DIR / "SKILL.md"
        self.assertTrue(skill_md.is_file(), f"missing: {skill_md}")

        text = _read(skill_md)
        self.assertTrue(text.startswith("---\n"), "SKILL.md must open with YAML frontmatter")
        end = text.index("\n---\n", 4)
        frontmatter = text[4:end]

        self.assertRegex(frontmatter, r"(?m)^name:\s*accept-hedged-close\s*$")
        description_match = re.search(r"(?ms)^description:\s*(.+?)(?=\n\w+:|\Z)", frontmatter)
        self.assertIsNotNone(description_match, "no 'description' field in frontmatter")
        self.assertGreater(len(description_match.group(1).strip()), 0)


class TestDoesNotWriteTerminalStateDirectly(unittest.TestCase):
    """AC3, the load-bearing criterion: SKILL.md must not instruct a direct
    edit of PLAN.md's status, the gate status, or the roadmap row, and must
    name T02's primitive as the mechanism instead."""

    # An instruction-shaped write to one of the three forbidden surfaces,
    # NOT immediately qualified by a negation word in the surrounding text.
    _FORBIDDEN = re.compile(
        r"(set|edit|flip|write)\b[^.\n]{0,60}"
        r"(PLAN\.md.{0,15}status|gate.{0,15}status|roadmap row)",
        re.IGNORECASE,
    )
    _NEGATION_RE = re.compile(r"(?i)\b(not|never|does\s+not|do\s+not|n't|untouched|remain)\b")

    def test_no_unqualified_instruction_to_write_terminal_state(self):
        text = _skill_text()
        for match in self._FORBIDDEN.finditer(text):
            window = text[max(0, match.start() - 40):match.end() + 10]
            self.assertRegex(
                window,
                self._NEGATION_RE,
                f"unqualified instruction to write terminal state directly: {window!r}",
            )

    def test_forbidden_pattern_fires_on_a_real_positive_instruction(self):
        # Negative case: prove the detector actually catches an unqualified
        # instruction, so the qualifying test above isn't vacuously true.
        bad = "Now set PLAN.md's status to done and flip the roadmap row to done."
        self.assertIsNotNone(self._FORBIDDEN.search(bad))

    def test_names_t02_primitive_as_the_mechanism(self):
        text = _skill_text()
        self.assertIn("--recheck-verdict", text)
        self.assertIn("recheck_terminal_verdict", text)
        self.assertIn("fire_terminal_flips", text)

    def test_states_it_never_calls_fire_terminal_flips_itself(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)never calls `?fire_terminal_flips`? itself")


class TestOperatorInputsRequiredBeforeAnyWrite(unittest.TestCase):
    def test_requires_feature_id(self):
        self.assertIn("feature ID", _skill_text())

    def test_requires_confirmation_close_wu_done_with_hedged_verdict(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)close WU is `?done`? with a hedged verdict")

    def test_requires_mandatory_one_line_reason(self):
        text = _skill_text()
        self.assertIn("one-line", text)
        self.assertIn("acceptance reason required", text)

    def test_requires_explicit_acknowledgment_of_follow_up_list(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)acknowledg\w* of the standing follow-up list")


class TestAcceptanceRecordFields(unittest.TestCase):
    def test_record_names_accepted_verdict(self):
        self.assertIn("accepted verdict", _skill_text())

    def test_record_names_operator_reason(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)operator'?s reason")

    def test_record_carries_follow_ups_forward_verbatim(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)carried forward \*{0,2}verbatim\*{0,2}")

    def test_record_names_timestamp(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)the timestamp \(ISO 8601 UTC\)")


class TestRefusalConditions(unittest.TestCase):
    def test_refuses_on_verdict_met(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)verdict.{0,15}is `?met`?.{0,40}nothing to accept")

    def test_refuses_on_verdict_not_met(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)verdict.{0,15}is `?not_met`?")

    def test_refuses_on_close_wu_not_done(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)status.{0,15}is not `?done`?")


class TestDoesNotDischargeFollowUps(unittest.TestCase):
    def test_states_it_does_not_discharge_or_close_follow_ups(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)does not discharge.{0,10}or close.{0,20}follow-up")


class TestEndsWithResultContract(unittest.TestCase):
    def test_references_result_contract(self):
        text = _skill_text()
        self.assertIn("result-contract.md", text)

    def test_blocked_reserved_for_refusal_or_unavailable_operator(self):
        text = _skill_text()
        self.assertRegex(text, r"(?i)`status: blocked` is reserved for")


if __name__ == "__main__":
    unittest.main()
