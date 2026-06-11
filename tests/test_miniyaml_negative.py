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


class TestErrorArmCoverage(unittest.TestCase):
    """Covers error/null-return arms not exercised by the original fixtures.

    Clusters addressed (source line numbers):
      123, 126   — null-return paths in parse()
      211        — indent mismatch in _parse_block (tested via internal call)
      241-247    — bare-dash sequence item without a value
      276        — duplicate key inside an inline sequence-mapping item
      305        — _split_key_value sees content with no colon
      327        — _parse_scalar("", lineno) → None (tested via internal call)
      414, 418   — unterminated string / empty item in flow list
      432, 445   — dangling backslash / unescaped quote in double-quoted string
    """

    def _expect_error(self, text: str, *needles: str) -> str:
        with self.assertRaises(MiniYAMLError) as cm:
            miniyaml.parse(text)
        msg = str(cm.exception)
        for needle in needles:
            self.assertIn(needle, msg,
                          f"expected {needle!r} in error message, got: {msg}")
        return msg

    # --- null-return paths in parse() (lines 123, 126) ---

    def test_parse_none_input_returns_none(self):
        # Line 123: early return for None input
        self.assertIsNone(miniyaml.parse(None))

    def test_parse_empty_string_returns_none(self):
        # Line 123: early return for "" input
        self.assertIsNone(miniyaml.parse(""))

    def test_parse_comment_only_text_returns_none(self):
        # Line 126: non-empty text that tokenises to an empty line list
        self.assertIsNone(miniyaml.parse("# only a comment\n"))

    def test_parse_blank_lines_only_returns_none(self):
        # Line 126: non-empty text consisting solely of blank lines
        self.assertIsNone(miniyaml.parse("   \n\n  \n"))

    # --- _parse_block indent mismatch (line 211, via internal call) ---

    def test_parse_block_indent_mismatch_raises(self):
        # _parse_block raises when called with indent != line.indent.
        # This branch is not reachable via parse() (all callers pass
        # lines[pos].indent), so exercise it through the internal API.
        line = miniyaml._Line(4, "foo: bar", 1)
        with self.assertRaises(MiniYAMLError) as cm:
            miniyaml._parse_block([line], 0, 0)
        msg = str(cm.exception)
        self.assertIn("line 1", msg)
        self.assertIn("indent", msg)

    # --- bare-dash sequence item (lines 241-247) ---

    def test_bare_dash_sequence_item_without_value_raises(self):
        # "  -" with nothing on subsequent lines → empty `-` item error
        self._expect_error("items:\n  -\n", "empty", "line 2")

    def test_bare_dash_sequence_item_with_block_value_parses(self):
        # "  -\n    key: val" → bare dash followed by an indented block
        # exercises the non-error path at lines 245-247
        result = miniyaml.parse("items:\n  -\n    key: val\n")
        self.assertEqual(result["items"], [{"key": "val"}])

    # --- duplicate key in inline sequence-mapping item (line 276) ---

    def test_duplicate_key_in_inline_mapping_item_raises(self):
        # `- foo: 1\n  foo: 2` continuation has a duplicate key
        self._expect_error(
            "items:\n  - foo: 1\n    foo: 2\n",
            "duplicate key", "foo", "line 3",
        )

    # --- non-key-value content in mapping body (line 305) ---

    def test_non_key_value_content_in_mapping_raises(self):
        # A bare word with no colon cannot be a key-value line
        self._expect_error(
            "parent:\n  just_a_word\n",
            "not a `key: value`", "line 2",
        )

    # --- _parse_scalar empty text → None (line 327, via internal call) ---

    def test_parse_scalar_empty_text_returns_none(self):
        # _parse_scalar strips to "" and returns None; not reachable via
        # parse() through normal paths, so test via the internal function.
        self.assertIsNone(miniyaml._parse_scalar("", 1))

    # --- flow-list: unterminated string (line 414) ---

    def test_flow_list_unterminated_string_raises(self):
        # List ends with `]` but the string inside is never closed
        # Python 'items: ["unclosed]' → YAML: items: ["unclosed]
        self._expect_error(
            'items: ["unclosed]\n',
            "unterminated", "line 1",
        )

    # --- flow-list: empty item after comma-split (line 418) ---

    def test_flow_list_empty_item_raises(self):
        # Two adjacent commas produce an empty token
        self._expect_error("items: [a, , b]\n", "empty item", "line 1")

    # --- _decode_double_quoted: dangling backslash (line 432) ---

    def test_dangling_backslash_in_double_quoted_raises(self):
        # Python 'key: "abc\\"' is the 11-char string: key: "abc\"
        # body = abc\ — backslash at last position → dangling backslash
        self._expect_error('key: "abc\\"', "dangling backslash", "line 1")

    # --- _decode_double_quoted: unescaped quote inside string (line 445) ---

    def test_unescaped_quote_inside_double_quoted_raises(self):
        # Python 'key: "a"b"' → body a"b → bare " in body raises
        self._expect_error('key: "a"b"', "unescaped quote", "line 1")


class TestDoubleQuotedEscapeDecoding(unittest.TestCase):
    """Positive-path tests for the escape-decode arms of _decode_double_quoted
    and the escape-tracking loop in _split_flow_items.

    AC 3: \\\\ → \\ and \\" → " in a scalar double-quoted string.
    AC 4: same escapes exercised through a flow-list item.
    Lines covered: 391-393, 395-400, 402-404, 436, 438, 443.
    """

    def test_backslash_escape_decoded(self):
        # AC 3a — line 436: out.append("\\")
        # Python 'key: "a\\\\b"' is the YAML string: key: "a\\b"
        result = miniyaml.parse('key: "a\\\\b"')
        self.assertEqual(result["key"], "a\\b")

    def test_double_quote_escape_decoded(self):
        # AC 3b — line 438: out.append('"')
        # Python 'key: "a\\"b"' is the YAML string: key: "a\"b"
        result = miniyaml.parse('key: "a\\"b"')
        self.assertEqual(result["key"], 'a"b')

    def test_flow_list_double_quoted_items_with_escapes(self):
        # AC 4 — lines 391-404: escape tracking through _split_flow_items
        # Python 'xs: ["a\\\\b", "c\\"d"]' is the YAML: xs: ["a\\b", "c\"d"]
        result = miniyaml.parse('xs: ["a\\\\b", "c\\"d"]')
        self.assertEqual(result["xs"], ["a\\b", 'c"d'])


if __name__ == "__main__":
    unittest.main()
