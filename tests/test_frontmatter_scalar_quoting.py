#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#3085: driver-written frontmatter strings must survive the driver's own parser.

`write_frontmatter_field` interpolated every value as a bare YAML scalar. A
string sourced from captured process output — `escalation_failure_signature`
on a `spinning_signature_repeat` escalation, whose text is the first line of
the failing gate's output — can start with `[` (`[main] INFO …` from any
SLF4J/Maven default), and `_miniyaml` then reads it as an unclosed flow list.
The next `specfuse run` or `specfuse lint` on that feature raises before
dispatching anything, and a human has to hand-edit the file. #2948 fixed the
same defect for one field in the gate baseline block; this pins the class.

The writer also carries values that are meant to be read back as YAML, not
as strings — `auto_close_reasons: []`, `auto_close: true`, `attempts: 0` —
so the test asserts those keep their types.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def _wu(tmp: Path) -> Path:
    p = tmp / "WU-01-x.md"
    p.write_text("---\nid: FEAT-2026-0001/T01\ntype: implementation\nstatus: pending\nattempts: 0\n---\n\n# x\n")
    return p


class TestDriverWrittenStringsRoundTrip(unittest.TestCase):
    def test_bracket_prefixed_signature_round_trips_and_file_still_parses(self):
        sig = "[main] INFO dev.specfuse.generator.validation.ArazzoValidator - Arazzo validation completed. Found 1"
        with tempfile.TemporaryDirectory() as td:
            p = _wu(Path(td))
            loop.write_frontmatter_field(p, "escalation_reason", "spinning_signature_repeat")
            loop.write_frontmatter_field(p, "escalation_failure_class", "tests")
            loop.write_frontmatter_field(p, "escalation_failure_signature", sig)
            fm, _ = loop.read_frontmatter(p)  # the call that crashed load_wu
            self.assertEqual(fm["escalation_failure_signature"], sig)
            self.assertEqual(fm["escalation_reason"], "spinning_signature_repeat")

    def test_other_yaml_significant_strings_round_trip(self):
        cases = [
            "{status, version} braces first",
            "# looks like a comment",
            'quoted "inner" text',
            "back\\slash",
            "key: value with colon-space",
            "trailing hash # not a comment",
            "'single-quoted start",
            "&anchor *alias !tag |literal >folded %directive @at",
        ]
        with tempfile.TemporaryDirectory() as td:
            p = _wu(Path(td))
            for i, text in enumerate(cases):
                loop.write_frontmatter_field(p, f"field_{i}", text)
            fm, _ = loop.read_frontmatter(p)
            for i, text in enumerate(cases):
                self.assertEqual(fm[f"field_{i}"], text, f"case {i}")

    def test_values_meant_as_yaml_keep_their_types(self):
        with tempfile.TemporaryDirectory() as td:
            p = _wu(Path(td))
            loop.write_frontmatter_field(p, "auto_close", "true")
            loop.write_frontmatter_field(p, "auto_close_reasons", "[]")
            loop.write_frontmatter_field(p, "attempts", "3")
            loop.write_frontmatter_field(p, "cost_usd", "1.25")
            loop.write_frontmatter_field(p, "started_at", "2026-09-03T12:00:00+00:00")
            loop.write_frontmatter_field(p, "status", "done")
            loop.write_frontmatter_field(p, "model", "claude-opus-4-8")
            loop.write_frontmatter_field(p, "reason", "")
            fm, _ = loop.read_frontmatter(p)
            self.assertIs(fm["auto_close"], True)
            self.assertEqual(fm["auto_close_reasons"], [])
            self.assertEqual(fm["attempts"], 3)
            self.assertEqual(fm["cost_usd"], 1.25)
            self.assertEqual(fm["started_at"], "2026-09-03T12:00:00+00:00")
            self.assertEqual(fm["status"], "done")
            self.assertEqual(fm["model"], "claude-opus-4-8")
            self.assertIsNone(fm["reason"])  # an empty write still reads as absent


if __name__ == "__main__":
    unittest.main()
