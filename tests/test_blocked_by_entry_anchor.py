#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A Blocked-by fragment into a YAML or JSON decision file is checked (#3567).

`decisions.entryKey` names the key holding an entry's id. Without it, a fragment
into a non-Markdown file stays unchecked, as it was before the key existed.
"""

import json
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import layout
from specfuse.loop.lint_roadmap import SEVERITY_ERROR, lint_roadmap

LAYOUT = """decisions:
  style: entries
  location: decisions
  link: "{location}/{domain}.yaml#{id}"
"""
KEYED_LAYOUT = LAYOUT + "  entryKey: name\n"

DECISIONS = """entries:
  - name: pricing-is-per-seat
    why: "cost tracks usage"
    tags: [billing, pricing]
    limits: {seats: 5}
    detail: |
      Long rationale that the loop's own YAML parser refuses.
  - "name": "quoted-id"  # a trailing comment
  -   name: 'single-quoted-id'
"""


def _errors(root, href, *, layout_text=KEYED_LAYOUT, files=None):
    root = Path(root)
    (root / ".specfuse").mkdir()
    (root / ".specfuse" / "layout.yml").write_text(layout_text)
    (root / ".specfuse" / "roadmap.md").write_text(
        "# Roadmap\n\n| Feature ID | Title | Status | Folder | Detail |\n|---|---|---|---|---|\n"
        "| FEAT-2026-0001 | T | blocked | — | — |\n\n"
        '<a id="feat-2026-0001"></a>\n## FEAT-2026-0001 — T\n\n'
        f"**Blocked by.** [D]({href}) — awaiting signature.\n"
    )
    (root / "decisions").mkdir()
    for name, text in (files or {"billing.yaml": DECISIONS}).items():
        (root / "decisions" / name).write_text(text)
    return [
        f.message
        for f in lint_roadmap(root)
        if f.severity == SEVERITY_ERROR and "Blocked-by" in f.message
    ]


class YamlTargets(unittest.TestCase):
    def _lint(self, fragment, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            return _errors(tmp, f"../decisions/billing.yaml#{fragment}", **kwargs)

    def test_a_typo_is_an_error_worded_like_markdown(self):
        errors = self._lint("pricing-is-per-sat")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(
            "points at '../decisions/billing.yaml', which has no anchor 'pricing-is-per-sat'",
            errors[0],
        )

    def test_an_existing_id_passes_beside_syntax_the_loop_parser_rejects(self):
        self.assertEqual(self._lint("pricing-is-per-seat"), [])

    def test_quoted_key_and_values_with_a_comment_pass(self):
        self.assertEqual(self._lint("quoted-id"), [])
        self.assertEqual(self._lint("single-quoted-id"), [])

    def test_yml_suffix_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = _errors(
                tmp, "../decisions/billing.yml#nope", files={"billing.yml": DECISIONS}
            )
        self.assertEqual(len(errors), 1, errors)

    def test_a_file_with_no_entries_under_the_key_names_the_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = _errors(
                tmp, "../decisions/billing.yaml#x", files={"billing.yaml": "id: x\n"}
            )
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("no entries under entryKey 'name'", errors[0])

    def test_without_entry_key_a_typo_still_passes(self):
        self.assertEqual(self._lint("pricing-is-per-sat", layout_text=LAYOUT), [])

    def test_a_link_with_no_fragment_passes_for_a_decision_still_under_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_errors(tmp, "../decisions/billing.yaml"), [])


class JsonTargets(unittest.TestCase):
    TEXT = json.dumps({"entries": [{"name": "real", "nested": {"name": "inner"}}, {"name": 7}]})

    def _lint(self, fragment, text=TEXT):
        with tempfile.TemporaryDirectory() as tmp:
            return _errors(
                tmp, f"../decisions/billing.json#{fragment}", files={"billing.json": text}
            )

    def test_existing_ids_pass(self):
        self.assertEqual(self._lint("real"), [])
        self.assertEqual(self._lint("7"), [])

    def test_a_typo_is_an_error(self):
        errors = self._lint("reel")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("has no anchor 'reel'", errors[0])

    def test_malformed_json_is_a_finding_not_a_silent_pass(self):
        errors = self._lint("real", text="{not json")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("could not be read", errors[0])


class MarkdownTargets(unittest.TestCase):
    def test_markdown_still_answers_to_anchors_when_the_key_is_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = _errors(
                tmp, "../decisions/d.md#pricing", files={"d.md": "## Pricing\n"}
            )
        self.assertEqual(errors, [])


class LayoutKey(unittest.TestCase):
    def _write(self, tmp, text):
        (Path(tmp) / ".specfuse").mkdir()
        (Path(tmp) / ".specfuse" / "layout.yml").write_text(text)

    def _errors(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, text)
            return [f.message for f in layout.validate(tmp) if f.severity == SEVERITY_ERROR]

    def test_get_returns_the_key_and_empty_when_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(layout.get(layout.load(tmp), "decisions.entryKey"), "")
            self._write(tmp, KEYED_LAYOUT)
            self.assertEqual(layout.get(layout.load(tmp), "decisions.entryKey"), "name")

    def test_a_valid_key_has_no_findings(self):
        self.assertEqual(self._errors(KEYED_LAYOUT), [])

    def test_a_key_that_cannot_name_a_mapping_key_is_an_error(self):
        errors = self._errors(LAYOUT + '  entryKey: "not a key"\n')
        self.assertTrue(any("decisions.entryKey" in m for m in errors), errors)

    def test_the_key_is_refused_under_adr_style(self):
        errors = self._errors("decisions:\n  style: adr\n  entryKey: name\n")
        self.assertTrue(any("decisions.entryKey" in m for m in errors), errors)


if __name__ == "__main__":
    unittest.main()
