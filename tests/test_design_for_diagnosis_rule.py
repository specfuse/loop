# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.

"""FEAT-2026-0039/T04: design-for-diagnosis rule is seeded, reference-only.

AC1/AC2: the rule seeds into a fresh init() tree but is not @-imported into
CLAUDE.md's _RULES_BLOCK — the reference-only posture is a recorded decision
in PLAN.md, not an oversight.
AC3: the packaged copy is byte-identical to the canonical .specfuse/ source.
AC6/AC7: at least 4 "## " sections, no vendor/framework/stack tokens.
"""

import pathlib
import tempfile
import unittest

from specfuse.loop import scaffold
from specfuse.loop.scaffold import init, read_scaffold

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CANONICAL_RULE = _REPO_ROOT / ".specfuse" / "rules" / "design-for-diagnosis.md"

# Same posture as the provider-agnostic boundary T05 holds: no framework,
# logging-library, cloud-provider, or vendor-specific identifier.
_STACK_TOKEN_DENYLIST = (
    "aws",
    "gcp",
    "azure",
    "kubernetes",
    "kafka",
    "rabbitmq",
    "datadog",
    "splunk",
    "elasticsearch",
    "prometheus",
    "grafana",
    "sentry",
    "django",
    "flask",
    "express",
    "spring",
    "log4j",
    "winston",
    "opentelemetry",
)


class TestDesignForDiagnosisRule(unittest.TestCase):
    def test_rule_is_seeded(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = init(pathlib.Path(tmp))
        self.assertIn("rules/design-for-diagnosis.md", written)

    def test_rule_is_not_at_imported(self):
        self.assertNotIn("design-for-diagnosis", scaffold._RULES_BLOCK)

    def test_rule_byte_identical_to_packaged_copy(self):
        self.assertTrue(_CANONICAL_RULE.exists(), f"{_CANONICAL_RULE} not found")
        self.assertEqual(
            _CANONICAL_RULE.read_bytes(),
            read_scaffold("rules/design-for-diagnosis.md"),
        )

    def test_rule_has_at_least_four_sections(self):
        text = _CANONICAL_RULE.read_text(encoding="utf-8")
        section_count = sum(1 for line in text.splitlines() if line.startswith("## "))
        self.assertGreaterEqual(section_count, 4)

    def test_rule_names_no_stack_specific_identifier(self):
        text = _CANONICAL_RULE.read_text(encoding="utf-8").lower()
        found = [token for token in _STACK_TOKEN_DENYLIST if token in text]
        self.assertEqual(found, [], f"stack-specific tokens found: {found}")


if __name__ == "__main__":
    unittest.main()
