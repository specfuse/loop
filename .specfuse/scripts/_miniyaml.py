#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Strict mini-YAML parser for the loop's configuration subset.

The loop reads four kinds of YAML, all small and regular:

  * Feature / GATE / WU **frontmatter** — flat block mappings of scalar values
    (the only nesting in real files is `work_units` lists in PLAN.md, which is
    not in frontmatter).
  * The PLAN.md fenced ```yaml graph block — a nested block mapping with a
    `gates:` list of objects, each containing a `work_units:` list of objects.
  * **`verification.yml`** — top-level block mapping (`code`/`doc`/`plannext`)
    each mapping to a list of `{name, command}` objects, where `command`
    values are typically double-quoted strings.
  * The agent's **RESULT block** — a forgiving consumer-side parse; on any
    malformed input the caller catches the exception and falls back to
    verify() as the exit oracle.

This parser implements EXACTLY that subset and FAILS LOUDLY on anything else.
PyYAML's safe_load is lenient and friendly; this one is the opposite by design:
the loop's structural files (PLAN, GATE, WU, verification.yml) are authored by
the operator, so a malformed file becoming a clear error is correct, not a
regression. The fail-loud principle matches `verify()`'s fail-closed posture
on a missing gate set — silent misparses are worse than crashes.

---

## Grammar (the documented subset)

  * **Block mapping** (`key: value`), nested by **2-space** indentation steps.
    Keys must match `[A-Za-z_][A-Za-z0-9_-]*`. Values are on the same line
    (scalar) or on subsequent more-indented lines (mapping/sequence).
  * **Block sequence** (`- item`). Items can be scalars or mappings. A
    mapping-item's first key sits inline after `- `; subsequent keys must
    align to the column where the first key began (`indent + 2`). A block
    sequence may sit at the **same** indent as its parent mapping key
    (YAML 1.2 §8.2.1 — the `kubectl`/Helm style) or at a deeper indent;
    both forms parse identically.
  * **Scalars:**
      - **bare strings** — everything from `: ` to end-of-line (with trailing
        whitespace stripped, and a trailing ` # ...` comment removed). May
        contain `,`, `/`, `-`, `.`, `=`, `::`, `{` / `}` / spaces, etc. The
        only forbidden bare-start characters are the ones that would invoke
        an unsupported feature (`'`, `&`, `*`, `!`, `|`, `>`, `{`).
      - **double-quoted strings** — `"..."`, supporting only `\\` and `\"`
        escapes. Any other escape is an error.
      - **integers** — `0` or a positive decimal (no sign, no leading zeros).
      - **floats** — positive decimal with required fractional part
        (`0.5`, `1.25`, `10.0125`). No sign, no leading dot, no trailing
        dot, no scientific notation. Used for things like `cost_usd`
        fields that the driver writes to WU frontmatter.
      - **booleans** — exact lowercase `true` / `false` only. `True`, `yes`,
        `on`, etc. are errors.
      - **empty value** — a key followed by `:` with nothing after is `None`.
  * **Inline (flow) lists** — `[]`, `[a]`, `[a, b]`. Items are scalars only;
    nested brackets are an error. Real usage is correlation-ID lists.
  * **Comments** — `#` starting a line (after optional whitespace), or
    `<space>#` on a value line, ends the significant content. `#` inside a
    double-quoted string is NOT a comment.
  * **Blank lines** — ignored.

## Explicitly UNSUPPORTED (fail-loud with line number)

  * Anchors and aliases (`&foo`, `*foo`).
  * Tags (`!!str`, `!Custom`).
  * Block scalars (`|`, `>`).
  * Single-quoted strings (`'...'`).
  * Flow mappings (`{key: value}`).
  * Multi-doc separators (`---` inside the body).
  * Tab characters in indentation.
  * Mixed / inconsistent indentation.
  * Nested brackets inside a flow list.
  * Escape sequences other than `\\` and `\"` in double-quoted strings.
  * Boolean spellings other than exact lowercase `true` / `false`.
  * Explicit null markers (`null`, `Null`, `NULL`, `~`).
  * Integers with sign, leading zeros, floats, hex, or underscores.

A file using any of those raises `MiniYAMLError` with a line number and a
specific message telling the operator how to simplify.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ("parse", "MiniYAMLError")


class MiniYAMLError(Exception):
    """Raised when input uses YAML features outside the documented subset."""


# A key is one or more name-chars, then a `:` (and optional value after a space).
# The key body cannot contain `:` or whitespace; the optional value is the rest.
_KEY_VALUE_RE = re.compile(r"^([^:\s][^:]*?)\s*:(?:\s+(.*))?$")
_VALID_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_INT_RE = re.compile(r"^(0|[1-9]\d*)$")
# Positive decimal with required fractional part. Rejects: signed, leading
# dot, trailing dot, leading-zero non-zero integer part, scientific notation.
# Matches: 0.5, 1.5, 10.0125, 0.0
_FLOAT_RE = re.compile(r"^(0|[1-9]\d*)\.\d+$")

_FORBIDDEN_BOOLS = {
    "True", "False",
    "yes", "Yes", "YES", "no", "No", "NO",
    "on", "On", "ON", "off", "Off", "OFF",
}
_FORBIDDEN_NULLS = {"null", "Null", "NULL", "~"}


# --------------------------------------------------------------------------- #
# Public entry point                                                          #
# --------------------------------------------------------------------------- #


def parse(text: str) -> Any:
    """Parse the documented YAML subset; return a dict / list / scalar / None.

    Raises ``MiniYAMLError`` on any construct outside the subset, with a line
    number and a description of what was rejected.
    """
    if text is None or text == "":
        return None
    lines = _tokenize(text)
    if not lines:
        return None
    if lines[0].indent != 0:
        raise MiniYAMLError(
            f"line {lines[0].lineno}: top-level content must start at indent 0")
    value, pos = _parse_block(lines, 0, 0)
    if pos != len(lines):
        raise MiniYAMLError(
            f"line {lines[pos].lineno}: unexpected continuation past end of "
            f"root structure (got {lines[pos].content!r})")
    return value


# --------------------------------------------------------------------------- #
# Tokenization                                                                #
# --------------------------------------------------------------------------- #


class _Line:
    __slots__ = ("indent", "content", "lineno")

    def __init__(self, indent: int, content: str, lineno: int):
        self.indent = indent
        self.content = content
        self.lineno = lineno


def _tokenize(text: str) -> list[_Line]:
    """Split into significant lines, stripping comments and blanks."""
    lines: list[_Line] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        leading = raw[:len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in leading:
            raise MiniYAMLError(
                f"line {n}: tab in indentation unsupported — use spaces")
        if raw.lstrip(" ").startswith("---") and n > 1:
            # Multi-doc separator inside the body is unsupported. (A leading
            # `---` only ever reaches the parser via direct callers that have
            # already stripped frontmatter delimiters, so it should not appear.)
            raise MiniYAMLError(
                f"line {n}: multi-document separator `---` unsupported")
        stripped = _strip_trailing_comment(raw, n)
        if stripped.strip() == "":
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        content = stripped[indent:].rstrip()
        lines.append(_Line(indent, content, n))
    return lines


def _strip_trailing_comment(line: str, lineno: int) -> str:
    """Remove a trailing ``# ...`` comment.

    A ``#`` only starts a comment when it sits at the start of the line OR is
    preceded by whitespace (matching PyYAML behaviour). ``#`` inside a
    double-quoted string is preserved.
    """
    in_string = False
    escape = False
    for i, c in enumerate(line):
        if escape:
            escape = False
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
            continue
        if c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line


# --------------------------------------------------------------------------- #
# Block / sequence / mapping                                                  #
# --------------------------------------------------------------------------- #


def _parse_block(lines: list[_Line], pos: int, indent: int) -> tuple[Any, int]:
    """Dispatch to mapping or sequence at the given indent."""
    line = lines[pos]
    if line.indent != indent:
        raise MiniYAMLError(
            f"line {line.lineno}: expected indent {indent}, got {line.indent}")
    if line.content == "-" or line.content.startswith("- "):
        return _parse_sequence(lines, pos, indent)
    return _parse_mapping(lines, pos, indent)


def _parse_mapping(lines: list[_Line], pos: int, indent: int) -> tuple[dict, int]:
    result: dict = {}
    while pos < len(lines) and lines[pos].indent == indent:
        line = lines[pos]
        if line.content.startswith("-"):
            raise MiniYAMLError(
                f"line {line.lineno}: sequence item where mapping key expected")
        key, rhs = _split_key_value(line.content, line.lineno)
        if key in result:
            raise MiniYAMLError(
                f"line {line.lineno}: duplicate key {key!r} in mapping")
        pos += 1
        result[key], pos = _resolve_value(lines, pos, rhs, indent, line.lineno)
    return result, pos


def _parse_sequence(lines: list[_Line], pos: int, indent: int) -> tuple[list, int]:
    result: list = []
    while (pos < len(lines)
           and lines[pos].indent == indent
           and (lines[pos].content == "-" or lines[pos].content.startswith("- "))):
        line = lines[pos]
        if line.content == "-":
            pos += 1
            if pos >= len(lines) or lines[pos].indent <= indent:
                raise MiniYAMLError(
                    f"line {line.lineno}: empty `-` item without a value")
            value, pos = _parse_block(lines, pos, lines[pos].indent)
            result.append(value)
            continue
        rest = line.content[2:]
        m = _KEY_VALUE_RE.match(rest)
        if m and _VALID_KEY_RE.match(m.group(1).strip()):
            item, pos = _parse_inline_mapping_item(lines, pos, indent, rest)
            result.append(item)
        else:
            result.append(_parse_scalar(rest, line.lineno))
            pos += 1
    return result, pos


def _parse_inline_mapping_item(
    lines: list[_Line], pos: int, indent: int, first_rest: str,
) -> tuple[dict, int]:
    """Parse a `- key: value [<newline>   more_keys]` mapping item."""
    line = lines[pos]
    sub_indent = indent + 2
    item: dict = {}
    key, rhs = _split_key_value(first_rest, line.lineno)
    pos += 1
    item[key], pos = _resolve_value(lines, pos, rhs, sub_indent, line.lineno)
    # Subsequent keys for this same item are at sub_indent, not starting with `-`.
    while (pos < len(lines)
           and lines[pos].indent == sub_indent
           and not lines[pos].content.startswith("-")):
        kline = lines[pos]
        k, v = _split_key_value(kline.content, kline.lineno)
        if k in item:
            raise MiniYAMLError(
                f"line {kline.lineno}: duplicate key {k!r} in mapping item")
        pos += 1
        item[k], pos = _resolve_value(lines, pos, v, sub_indent, kline.lineno)
    return item, pos


def _resolve_value(
    lines: list[_Line], pos: int, rhs: str | None,
    enclosing_indent: int, lineno: int,
) -> tuple[Any, int]:
    """Given the rhs of a `key:` line, return (value, new_pos).

    If rhs is empty, look for the value on subsequent lines:
      * a block sequence at the **same** indent as the parent key (YAML 1.2
        §8.2.1 — `kubectl`-style and many human-edited configs use this); OR
      * any block (sequence or sub-mapping) at a **deeper** indent.
    If neither, the value is None.

    Same-indent extension applies only to sequences. A sub-mapping at the
    same indent is genuinely ambiguous with a sibling mapping key, so that
    case stays an error.
    """
    if rhs is None or rhs == "":
        if pos < len(lines):
            nxt = lines[pos]
            if (nxt.indent == enclosing_indent
                    and (nxt.content == "-" or nxt.content.startswith("- "))):
                value, pos = _parse_sequence(lines, pos, enclosing_indent)
                return value, pos
            if nxt.indent > enclosing_indent:
                child_indent = nxt.indent
                value, pos = _parse_block(lines, pos, child_indent)
                return value, pos
        return None, pos
    return _parse_scalar(rhs, lineno), pos


def _split_key_value(content: str, lineno: int) -> tuple[str, str | None]:
    """Split a `key: value` (or `key:`) line. Returns (key, rhs_or_None)."""
    m = _KEY_VALUE_RE.match(content)
    if not m:
        raise MiniYAMLError(
            f"line {lineno}: not a `key: value` line — got {content!r}")
    key = m.group(1).strip()
    if not _VALID_KEY_RE.match(key):
        raise MiniYAMLError(
            f"line {lineno}: unsupported key {key!r} — keys must match "
            f"[A-Za-z_][A-Za-z0-9_-]*")
    rhs = m.group(2)
    if rhs is not None:
        rhs = rhs.strip()
    return key, rhs


# --------------------------------------------------------------------------- #
# Scalars                                                                     #
# --------------------------------------------------------------------------- #


def _parse_scalar(text: str, lineno: int) -> Any:
    """Parse a scalar value — string, int, bool, empty/null, or flow list."""
    text = text.strip() if text else ""
    if text == "":
        return None
    if text.startswith("'"):
        raise MiniYAMLError(
            f"line {lineno}: single-quoted strings unsupported — use \"...\"")
    if text.startswith("&") or text.startswith("*"):
        raise MiniYAMLError(f"line {lineno}: anchors/aliases unsupported")
    if text.startswith("!"):
        raise MiniYAMLError(f"line {lineno}: tags unsupported")
    if text.startswith("|") or text.startswith(">"):
        raise MiniYAMLError(
            f"line {lineno}: literal/folded block scalars unsupported")
    if text.startswith("{"):
        # Positional rule (LOAD-BEARING — do not tighten without thought):
        # `{` is a fail-loud trigger ONLY when it starts the scalar — i.e. the
        # value begins with `{`, which would be the start of a flow mapping.
        # Braces appearing INSIDE a bare scalar are kept as ordinary content,
        # because real agent result summaries routinely contain prose with
        # braces (e.g. `summary: added GET /health returning {status, version}`),
        # and matching PyYAML on that case is pinned by the equivalence tests.
        # Tightening this to "any `{` anywhere rejects" would crash the
        # forgiving result-block parse path on real agent output.
        raise MiniYAMLError(
            f"line {lineno}: flow mappings unsupported — use a block mapping")
    if text in _FORBIDDEN_NULLS:
        raise MiniYAMLError(
            f"line {lineno}: explicit null marker unsupported — leave value empty")
    if text in _FORBIDDEN_BOOLS:
        raise MiniYAMLError(
            f"line {lineno}: only lowercase `true`/`false` accepted as "
            f"booleans (got {text!r})")
    if text[0] == "[":
        return _parse_flow_list(text, lineno)
    if text[0] == '"':
        return _decode_double_quoted(text, lineno)
    if text == "true":
        return True
    if text == "false":
        return False
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    return text


def _parse_flow_list(text: str, lineno: int) -> list:
    if not text.endswith("]"):
        raise MiniYAMLError(
            f"line {lineno}: malformed flow list (no closing `]`)")
    inner = text[1:-1].strip()
    if inner == "":
        return []
    return [_parse_scalar(item, lineno) for item in _split_flow_items(inner, lineno)]


def _split_flow_items(inner: str, lineno: int) -> list[str]:
    """Split `a, b, c` on commas, respecting double-quoted strings; fail on
    nested brackets."""
    items: list[str] = []
    buf: list[str] = []
    in_string = False
    escape = False
    for c in inner:
        if escape:
            buf.append(c)
            escape = False
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            buf.append(c)
            continue
        if c == '"':
            in_string = True
            buf.append(c)
            continue
        if c in "[]{}":
            raise MiniYAMLError(
                f"line {lineno}: nested brackets/braces in flow list unsupported")
        if c == ",":
            items.append("".join(buf).strip())
            buf = []
            continue
        buf.append(c)
    if in_string:
        raise MiniYAMLError(
            f"line {lineno}: unterminated double-quoted string inside flow list")
    items.append("".join(buf).strip())
    if any(item == "" for item in items):
        raise MiniYAMLError(f"line {lineno}: empty item in flow list")
    return items


def _decode_double_quoted(text: str, lineno: int) -> str:
    if len(text) < 2 or not text.endswith('"'):
        raise MiniYAMLError(f"line {lineno}: unterminated double-quoted string")
    body = text[1:-1]
    out: list[str] = []
    i = 0
    while i < len(body):
        c = body[i]
        if c == "\\":
            if i + 1 >= len(body):
                raise MiniYAMLError(
                    f"line {lineno}: dangling backslash in double-quoted string")
            n = body[i + 1]
            if n == "\\":
                out.append("\\")
            elif n == '"':
                out.append('"')
            else:
                raise MiniYAMLError(
                    f"line {lineno}: unsupported escape \\{n} in "
                    f"double-quoted string (only \\\\ and \\\" supported)")
            i += 2
        elif c == '"':
            raise MiniYAMLError(
                f"line {lineno}: unescaped quote inside double-quoted string")
        else:
            out.append(c)
            i += 1
    return "".join(out)
