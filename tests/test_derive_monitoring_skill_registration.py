# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0039/T07: the derive-monitoring skill is present, registered, and
# internally consistent in both trees.
#
# AC1: SKILL.md/PROMPT.md exist and are non-empty in plugins/specfuse/skills/
#      and .specfuse/skills/ (this test fails on HEAD before T07's edits,
#      since neither directory exists yet).
# AC2: byte-identity across the two trees is asserted by
#      tests/test_skills_vendored_in_sync.py; not re-asserted here.
# AC3: SKILL.md's frontmatter names the skill and the artifact it drafts.
# AC4: SKILL.md states a draft-never-write hard rule; neither file instructs
#      writing monitoring.yml without explicit user consent.
# AC5: SKILL.md references design-for-diagnosis.md (T04) and the discovery
#      reference implementation's path (T05).
# AC6: the diagnosability audit's severity is WARN; no ERROR instruction.
# AC7: the .claude/skills/derive-monitoring symlink is named as an operator
#      prerequisite, not agent work.
# AC8: every credential token in either file is UPPER_SNAKE_CASE, matching
#      lint_monitoring._ENV_VAR_NAME_RE — with a negative case proving the
#      detector actually rejects an inline-literal string.
# AC9: /derive-monitoring is registered in docs/skills.md (checked here);
#      tests/test_scaffold_data_in_sync.py separately asserts the packaged
#      copy matches byte-for-byte.

import pathlib
import re
import unittest

from specfuse.loop.lint_monitoring import _ENV_VAR_NAME_RE

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL_DIR = _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring"
_VENDORED_DIR = _REPO_ROOT / ".specfuse" / "skills" / "derive-monitoring"
_DOCS_SKILLS = _REPO_ROOT / "docs" / "skills.md"

# A credential-shaped literal: a connection-string scheme, or a long
# base64/hex-ish run — the same shape lint_monitoring rejects inline. Used
# for the AC8 negative case only.
_SUSPICIOUS_LITERAL_RE = re.compile(r"://\S+|[A-Za-z0-9+/]{24,}")

# Backtick-wrapped, all-caps-starting identifiers — the same convention
# tests/test_monitoring_bootstrap_artifacts.py uses to find credential
# tokens in prose. A dotted token like `SKILL.md` does not match: the
# capture group cannot reach the closing backtick past the '.'.
_BACKTICK_TOKEN_RE = re.compile(r"`([A-Z][A-Z0-9_]*)`")


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class TestSkillPresentInBothTrees(unittest.TestCase):
    def test_skill_present_in_both_trees(self):
        for base in (_CANONICAL_DIR, _VENDORED_DIR):
            skill_md = base / "SKILL.md"
            prompt_md = base / "PROMPT.md"
            self.assertTrue(skill_md.is_file(), f"missing: {skill_md}")
            self.assertTrue(prompt_md.is_file(), f"missing: {prompt_md}")
            self.assertGreater(len(_read(skill_md).strip()), 0, f"empty: {skill_md}")
            self.assertGreater(len(_read(prompt_md).strip()), 0, f"empty: {prompt_md}")


class TestFrontmatterNamesSkillAndArtifact(unittest.TestCase):
    def test_frontmatter_names_skill_and_artifact(self):
        text = _read(_CANONICAL_DIR / "SKILL.md")
        self.assertTrue(text.startswith("---\n"), "SKILL.md must open with YAML frontmatter")
        end = text.index("\n---\n", 4)
        frontmatter = text[4:end]

        self.assertRegex(frontmatter, r"(?m)^name:\s*derive-monitoring\s*$")

        description_match = re.search(r"(?ms)^description:\s*(.+?)(?=\n\w+:|\Z)", frontmatter)
        self.assertIsNotNone(description_match, "no 'description' field in frontmatter")
        description = description_match.group(1)
        self.assertIn("monitoring.yml", description)


class TestDraftNeverWriteHardRule(unittest.TestCase):
    def test_skill_states_draft_never_write(self):
        text = _read(_CANONICAL_DIR / "SKILL.md")
        self.assertIn("Draft, do not write", text)

    def test_neither_file_instructs_writing_without_consent(self):
        forbidden = re.compile(
            r"write.{0,40}monitoring\.yml.{0,40}(automatically|without asking|"
            r"without confirm|without consent|silently)",
            re.IGNORECASE | re.DOTALL,
        )
        for name in ("SKILL.md", "PROMPT.md"):
            text = _read(_CANONICAL_DIR / name)
            self.assertIsNone(
                forbidden.search(text),
                f"{name} appears to instruct writing monitoring.yml without consent",
            )


class TestReferencesDesignForDiagnosisAndDiscoveryImpl(unittest.TestCase):
    def test_references_design_for_diagnosis_rule(self):
        text = _read(_CANONICAL_DIR / "SKILL.md")
        self.assertIn(".specfuse/rules/design-for-diagnosis.md", text)

    def test_references_discovery_reference_implementation(self):
        text = _read(_CANONICAL_DIR / "SKILL.md")
        self.assertIn("tests/test_derive_monitoring_discovery.py", text)


class TestStep1IsDeploymentKeyed(unittest.TestCase):
    """FEAT-2026-0069/T08: Step 1's prose must describe deployment-keyed
    discovery — a component is a deployable, a trigger is evidence of its
    type and the source of its target list, never a component in its own
    right — and must name the record fields T07's reference implementation
    actually emits."""

    def _step_1_text(self) -> str:
        text = _read(_CANONICAL_DIR / "SKILL.md")
        start = text.index("### Step 1")
        end = text.index("### Step 2", start)
        return text[start:end]

    def test_step_1_describes_deployment_keyed_discovery(self):
        step_1 = self._step_1_text()

        self.assertRegex(
            step_1,
            r"(?i)deployment evidence",
            "Step 1 must name deployment evidence as the discovery key",
        )
        self.assertIn(
            "subscriptions",
            step_1,
            "Step 1 must name `subscriptions` as an emitted record field",
        )
        self.assertIn(
            "schedules",
            step_1,
            "Step 1 must name `schedules` as an emitted record field",
        )


class TestAuditSeverityIsWarnNotError(unittest.TestCase):
    def test_states_warn_severity(self):
        text = _read(_CANONICAL_DIR / "SKILL.md")
        self.assertIn("`WARN`", text)

    def test_no_instruction_to_report_as_error(self):
        error_as_severity = re.compile(
            r"(report|severity|findings?).{0,30}\bERROR\b", re.IGNORECASE | re.DOTALL
        )
        for name in ("SKILL.md", "PROMPT.md"):
            text = _read(_CANONICAL_DIR / name)
            for match in error_as_severity.finditer(text):
                # "never ERROR" / "not ERROR" is the WARN-not-ERROR posture
                # statement itself, not an instruction to use ERROR.
                window = text[max(0, match.start() - 15):match.end()]
                self.assertRegex(
                    window,
                    r"(?i)never|no.*error|not.*error",
                    f"{name} appears to instruct an ERROR severity: {window!r}",
                )


class TestClaudeSkillsSymlinkIsOperatorPrerequisite(unittest.TestCase):
    def test_symlink_named_as_operator_prerequisite(self):
        text = _read(_CANONICAL_DIR / "SKILL.md")
        self.assertIn(".claude/skills/derive-monitoring", text)
        self.assertIn("operator prerequisite", text)
        self.assertNotRegex(
            text,
            r"(?i)the (agent|skill|session) (will |should |must )?creates? the "
            r"\.claude/skills/derive-monitoring symlink",
        )


class TestCredentialTokensAreEnvVarNamesOnly(unittest.TestCase):
    def test_backtick_tokens_are_env_var_shaped(self):
        found_any = False
        for name in ("SKILL.md", "PROMPT.md"):
            text = _read(_CANONICAL_DIR / name)
            for token in _BACKTICK_TOKEN_RE.findall(text):
                found_any = True
                self.assertRegex(
                    token, _ENV_VAR_NAME_RE, f"{name}: token {token!r} is not UPPER_SNAKE_CASE"
                )
        self.assertTrue(found_any, "expected at least one credential-shaped token")

    def test_no_suspicious_literal_in_either_file(self):
        for name in ("SKILL.md", "PROMPT.md"):
            text = _read(_CANONICAL_DIR / name)
            self.assertIsNone(
                _SUSPICIOUS_LITERAL_RE.search(text),
                f"{name} appears to contain a literal credential-shaped value",
            )

    def test_suspicious_literal_regex_fires_on_a_real_literal(self):
        # Negative case: prove the same detector rejects a literal it should.
        literal = "postgres://user:hunter2@db.example.com:5432/orders"
        self.assertIsNotNone(_SUSPICIOUS_LITERAL_RE.search(literal))
        key_shaped = "AKIA" + "Q" * 30
        self.assertIsNotNone(_SUSPICIOUS_LITERAL_RE.search(key_shaped))


class TestDeriveMonitoringRegisteredInDocsSkills(unittest.TestCase):
    def test_registered_in_docs_skills(self):
        text = _read(_DOCS_SKILLS)
        self.assertIn("/derive-monitoring", text)


if __name__ == "__main__":
    unittest.main()
