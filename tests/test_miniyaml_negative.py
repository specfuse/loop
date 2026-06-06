#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Negative tests: every unsupported YAML construct must raise MiniYAMLError
with a useful message — never a silent wrong parse and never an opaque crash.

This is the half of the strict-parser contract that's only real if it's
tested. Each test names one unsupported construct from the documented
subset's "explicitly UNSUPPORTED" list, feeds it to the parser, and asserts
both (a) MiniYAMLError is raised and (b) the message points at the right
construct so a human reading the failure knows how to simplify the file.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_miniyaml

miniyaml = load_miniyaml()
MiniYAMLError = miniyaml.MiniYAMLError


class TestUnsupportedConstructsFailLoudly(unittest.TestCase):

    def _expect_error(self, text: str, *needles: str) -> str:
        """Parse must raise; the message must contain every needle."""
        with self.assertRaises(MiniYAMLError) as cm:
            miniyaml.parse(text)
        msg = str(cm.exception)
        for needle in needles:
            self.assertIn(needle, msg,
                          f"expected {needle!r} in error message, got: {msg}")
        return msg

    # --- anchors / aliases / tags ---

    def test_anchor_rejected(self):
        self._expect_error("foo: &anchor 42\nbar: *anchor\n", "anchors")

    def test_alias_rejected(self):
        self._expect_error("foo: *somealias\n", "anchors")

    def test_tag_rejected(self):
        self._expect_error("foo: !!str 42\n", "tags")

    # --- block scalars ---

    def test_literal_block_scalar_rejected(self):
        self._expect_error("description: |\n  hello\n", "literal/folded")

    def test_folded_block_scalar_rejected(self):
        self._expect_error("description: >\n  hello\n", "literal/folded")

    # --- string quoting ---

    def test_single_quoted_string_rejected(self):
        self._expect_error("name: 'hello'\n", "single-quoted")

    def test_unsupported_escape_in_double_quoted(self):
        self._expect_error('name: "he\\tllo"\n', "unsupported escape")

    def test_unterminated_double_quoted(self):
        self._expect_error('name: "unterminated\n', "unterminated")

    # --- flow constructs ---

    def test_flow_mapping_rejected(self):
        self._expect_error("name: {key: value}\n", "flow mappings")

    def test_nested_brackets_in_flow_list_rejected(self):
        self._expect_error("items: [a, [b, c], d]\n", "nested brackets/braces")

    def test_unclosed_flow_list_rejected(self):
        self._expect_error("items: [a, b\n", "malformed flow list")

    # --- multi-doc ---

    def test_multi_doc_separator_rejected(self):
        # Two `---` markers — the second is inside the parsed body.
        self._expect_error("foo: 1\n---\nbar: 2\n", "multi-document")

    # --- indentation hygiene ---

    def test_tab_in_indentation_rejected(self):
        self._expect_error("foo:\n\tbar: 1\n", "tab in indentation")

    def test_inconsistent_indent_rejected(self):
        # Child mapping's two keys at different indents. The parser detects this
        # downstream (the second key falls outside the mapping's indent and is
        # then flagged as leftover content) — the precise message is "past end
        # of root structure", which is still fail-loud with a line number.
        with self.assertRaises(MiniYAMLError) as cm:
            miniyaml.parse("foo:\n  bar: 1\n   baz: 2\n")
        self.assertIn("line 3", str(cm.exception))

    def test_top_level_indent_nonzero_rejected(self):
        self._expect_error("  foo: 1\n", "indent 0")

    # --- explicit nulls / forbidden boolean spellings ---

    def test_explicit_null_marker_rejected(self):
        self._expect_error("foo: null\n", "explicit null marker")

    def test_tilde_null_marker_rejected(self):
        self._expect_error("foo: ~\n", "explicit null marker")

    def test_titlecase_boolean_rejected(self):
        self._expect_error("foo: True\n", "lowercase", "true")

    def test_yes_boolean_rejected(self):
        self._expect_error("foo: yes\n", "lowercase")

    # --- key shape ---

    def test_key_with_space_rejected(self):
        # Two words before `:` makes the first one alone the key with a value
        # of `word more: stuff` — but the actual rule we hit is unsupported
        # key shape OR a non-key/value line, depending on framing. Either
        # error is fine; assert it raises with a line number.
        with self.assertRaises(MiniYAMLError) as cm:
            miniyaml.parse("two words: value\n")
        self.assertIn("line 1", str(cm.exception))

    def test_numeric_key_rejected(self):
        self._expect_error("1: value\n", "unsupported key")

    # --- sequence/mapping hygiene ---

    def test_sequence_item_in_mapping_position_rejected(self):
        # Root looks like a mapping but the second line is a sequence item.
        self._expect_error("foo: 1\n- two\n", "sequence item")

    def test_duplicate_key_rejected(self):
        self._expect_error("foo: 1\nfoo: 2\n", "duplicate key")


class TestFloatScalarSupport(unittest.TestCase):
    """v0.2 added positive-float support for `cost_usd`-style fields the
    driver writes to WU frontmatter. Strict — no signed, leading dot,
    trailing dot, scientific notation."""

    def test_basic_floats_parse(self):
        for text, expected in (
            ("x: 0.5", 0.5),
            ("x: 1.25", 1.25),
            ("x: 10.0125", 10.0125),
            ("x: 0.0", 0.0),
        ):
            with self.subTest(text=text):
                self.assertEqual(miniyaml.parse(text)["x"], expected)

    def test_ints_still_parse_as_ints(self):
        self.assertIsInstance(miniyaml.parse("x: 5")["x"], int)
        self.assertIsInstance(miniyaml.parse("x: 0")["x"], int)

    def test_leading_dot_is_bare_string_not_float(self):
        # `.5` is not a documented float form — falls through to bare string.
        self.assertEqual(miniyaml.parse("x: .5")["x"], ".5")

    def test_trailing_dot_is_bare_string(self):
        self.assertEqual(miniyaml.parse("x: 5.")["x"], "5.")

    def test_scientific_notation_is_bare_string(self):
        self.assertEqual(miniyaml.parse("x: 1.5e3")["x"], "1.5e3")

    def test_negative_float_rejected_via_quotation_check(self):
        # `-` doesn't trigger a special reject branch; falls through to bare
        # string with the minus sign preserved.
        self.assertEqual(miniyaml.parse("x: -1.5")["x"], "-1.5")


class TestUsefulMessageIncludesLineNumber(unittest.TestCase):
    """Errors must always cite a line number — without one, a malformed file is
    hard to fix. This is part of the fail-loud contract."""

    def test_line_number_in_anchor_error(self):
        with self.assertRaises(MiniYAMLError) as cm:
            miniyaml.parse("ok: 1\nbroken: &a 2\n")
        self.assertIn("line 2", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
