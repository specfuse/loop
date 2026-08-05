"""FEAT-2026-0057/T05: shipped seeds must document prep/oracles/extra_gates."""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "specfuse" / "loop" / "data" / "templates" / "WU.template.md"
VERIFICATION_EXAMPLE = REPO_ROOT / "specfuse" / "loop" / "data" / "verification.yml.example"


class TestSeeds(unittest.TestCase):
    def test_wu_template_documents_prerun_keys(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for key in ("prep", "oracles", "extra_gates"):
            self.assertIn(
                f"`{key}`",
                text,
                f"WU.template.md must document the `{key}` frontmatter key",
            )

        example_text = VERIFICATION_EXAMPLE.read_text(encoding="utf-8")
        self.assertTrue(
            re.search(r"^\s*#?\s*oracles:", example_text, re.MULTILINE),
            "verification.yml.example must carry an `oracles:` set (commented or live)",
        )


if __name__ == "__main__":
    unittest.main()
