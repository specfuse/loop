# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Guards LABEL_REGISTRY against drift from escalation.py's label vocabulary."""

from __future__ import annotations

import re
import unittest

from specfuse.loop import escalation, gh_features
from specfuse.monitor import issues
from specfuse.loop.labels import LABEL_REGISTRY

_COLOUR_RE = re.compile(r"^[0-9a-f]{6}$")


class TestLabelRegistry(unittest.TestCase):
    def test_registry_has_exactly_eight_entries(self):
        # Seven at FEAT-2026-0071; the eighth is the harvester's finding label,
        # added by #300 after `gh issue create` rejected it on a fresh repository.
        # A bare count is a weak invariant — it fails on every legitimate addition
        # and catches nothing a coverage assertion does not. The real guard is
        # tests/test_label_registry_covers_consumers.py, which discovers every
        # label constant in the package and asserts each is declared here.
        self.assertEqual(len(LABEL_REGISTRY), 8)

    def test_entries_expose_nonempty_string_fields(self):
        for entry in LABEL_REGISTRY:
            self.assertIsInstance(entry.name, str)
            self.assertTrue(entry.name)
            self.assertIsInstance(entry.colour, str)
            self.assertTrue(entry.colour)
            self.assertIsInstance(entry.description, str)
            self.assertTrue(entry.description)

    def test_colours_are_six_lowercase_hex_digits(self):
        for entry in LABEL_REGISTRY:
            self.assertRegex(entry.colour, _COLOUR_RE)

    def test_registry_covers_every_escalation_label(self):
        expected = (
            {escalation.NEEDS_HUMAN_LABEL}
            | set(escalation.CATEGORY_LABELS)
            | {gh_features.FEATURE_LABEL}
            | {issues.FINDING_LABEL}
        )
        actual = {entry.name for entry in LABEL_REGISTRY}
        self.assertEqual(actual, expected)

    def test_specfuse_monitor_is_not_a_registry_entry(self):
        names = {entry.name for entry in LABEL_REGISTRY}
        self.assertNotIn("specfuse-monitor", names)

    def test_registry_names_are_unique(self):
        names = [entry.name for entry in LABEL_REGISTRY]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
