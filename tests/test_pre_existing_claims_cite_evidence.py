# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# #2075: twice in one day an agent-authored PR reported a large "pre-existing"
# failure baseline that did not exist, and reasoned from it. #1876 claimed
# "113 pre-existing errors" and coverage "88%, below the repo-wide 90% floor"
# on a branch that measured 3118 tests OK at 93% — converting a passing gate
# into an accepted failure. #2028 claimed "2 failures / 110 errors — identical
# to the pre-fix baseline (diffed test-by-test)" on a branch with zero of
# either; a real diff against a real baseline would have shown zero on both
# sides, so the comparison it asserts cannot have happened.
#
# The issue separates two defects. (a) the sandbox produces false failures —
# real, and known here: the suite is routinely run unsandboxed for exactly
# that reason. (b) the session writes "pre-existing" without ever measuring a
# baseline. (b) survives any fix to (a): a session that will call an
# inconvenient failure pre-existing is unreliable in every environment.
#
# Fixed here is (b), by making the false claim unwritable: "pre-existing" is a
# claim about a DIFFERENT commit, so it must name the command and the commit it
# was measured on, and a baseline that cannot be measured is a blocked outcome
# rather than an asserted number.
#
# Scope: the same constraint belongs in `verification-discipline.md` as neutral
# substrate, but that file is vendored FROM the methodology core (see
# scripts/sync-scaffold.sh's CORE_FILES) and is not this repository's to edit.
# The two surfaces asserted below are loop-owned: the verification skill, and
# result-contract.md, which sync-scaffold.sh names as staying loop-local.

import pathlib
import unittest

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_SKILL_CANONICAL = (
    _REPO_ROOT / "plugins" / "specfuse" / "skills" / "verification" / "SKILL.md"
)
_SKILL_VENDORED = _REPO_ROOT / ".specfuse" / "skills" / "verification" / "SKILL.md"
_RESULT_CONTRACT = _REPO_ROOT / ".specfuse" / "rules" / "result-contract.md"
_RESULT_CONTRACT_PACKAGED = (
    _REPO_ROOT / "specfuse" / "loop" / "data" / "rules" / "result-contract.md"
)


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class TestVerificationSkillRequiresCitation(unittest.TestCase):
    def test_the_skill_names_the_constraint(self):
        for path in (_SKILL_CANONICAL, _SKILL_VENDORED):
            with self.subTest(tree=path.parts[-4]):
                text = _read(path)
                self.assertIn("pre-existing", text)

    def test_the_claim_must_name_a_command_and_a_commit(self):
        """A claim about a different commit is evidence only if that commit was
        run. Naming both is what makes it checkable."""
        for path in (_SKILL_CANONICAL, _SKILL_VENDORED):
            with self.subTest(tree=path.parts[-4]):
                text = _read(path).lower()
                self.assertIn("merge-base", text)

    def test_an_unmeasurable_baseline_is_blocked_not_asserted(self):
        """The honest outcome when the baseline cannot be measured — the issue's
        fix (2) reached in prose rather than machinery."""
        for path in (_SKILL_CANONICAL, _SKILL_VENDORED):
            with self.subTest(tree=path.parts[-4]):
                text = _read(path)
                section = text[text.index("## Forbidden shortcuts"):]
                self.assertIn("pre-existing", section)


class TestResultContractRequiresCitation(unittest.TestCase):
    def test_the_rule_carries_the_constraint(self):
        for path in (_RESULT_CONTRACT, _RESULT_CONTRACT_PACKAGED):
            with self.subTest(tree=path.parts[-3]):
                self.assertIn("pre-existing", _read(path))

    def test_it_lives_among_the_numbered_rules(self):
        """Not an aside — a rule, in the list a session is held to."""
        for path in (_RESULT_CONTRACT, _RESULT_CONTRACT_PACKAGED):
            with self.subTest(tree=path.parts[-3]):
                text = _read(path)
                rules = text[text.index("## Rules"):text.index("## Closing obligations")]
                self.assertIn("pre-existing", rules)


class TestCoreOwnedRuleIsNotEdited(unittest.TestCase):
    """`verification-discipline.md` is vendored from the methodology core. A
    local edit diverges from core and halts the sync, so the constraint is
    handed off in #2075 rather than written here. This test fails if a later
    change quietly adds it, which would be the drift the vendoring prevents."""

    def test_the_vendored_rule_is_untouched(self):
        vendored = _REPO_ROOT / ".specfuse" / "rules" / "verification-discipline.md"
        packaged = (
            _REPO_ROOT / "specfuse" / "loop" / "data" / "rules"
            / "verification-discipline.md"
        )
        self.assertEqual(_read(vendored), _read(packaged))
        self.assertNotIn("merge-base", _read(vendored))


if __name__ == "__main__":
    unittest.main()
