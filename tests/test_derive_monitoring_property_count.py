# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""#3586: the derive-monitoring skill must not state a fixed count of the
design-for-diagnosis properties its audit checks. Step 2 said "five
properties" while auditing eight; every property added since made the count
staler. With no number in the prose, adding a property cannot make it wrong."""

from __future__ import annotations

import pathlib
import re
import unittest

_SKILL_DIR = pathlib.Path(__file__).parent.parent / "plugins" / "specfuse" / "skills" / "derive-monitoring"

_NUMBER_WORDS = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
_COUNTED_PROPERTIES = re.compile(
    rf"\b(?:{_NUMBER_WORDS}|\d+)\s+(?:diagnosability\s+)?properties\b", re.IGNORECASE
)


class TestNoFixedPropertyCount(unittest.TestCase):
    def test_skill_files_state_no_property_count(self):
        for name in ("SKILL.md", "PROMPT.md"):
            with self.subTest(name):
                text = (_SKILL_DIR / name).read_text(encoding="utf-8")
                self.assertEqual(_COUNTED_PROPERTIES.findall(text), [])

    def test_detector_catches_the_original_wording(self):
        self.assertTrue(_COUNTED_PROPERTIES.search("the rule's five properties: correlation-ID"))
        self.assertTrue(_COUNTED_PROPERTIES.search("the five diagnosability\n  properties"))


if __name__ == "__main__":
    unittest.main()
