#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`max_attempts` resolves per work unit, per project, then falls back (#2651).

`MAX_ATTEMPTS = 3` was a module constant with no override at any scope. Both
directions of that knob are wanted, and #2641 only stated one of them:

- **low (1–2)** — the shape of the work is unknown, and a failed pass means a
  human should look. Attempts 2 and 3 rediscover the same wall at full price;
  the reporting feature paid $29.30 where `1` would have capped it near $7.
- **high (5–10)** — the oracle is convergent and each attempt is an
  *iteration* rather than an independent restart (#2650). Eleven schema files
  plus two dozen registrations will not converge in three.

Precedence is work unit, then the project's `defaults.max_attempts` in
`verification.yml`, then `MAX_ATTEMPTS`. A work unit is the narrowest scope
and its author knows the shape of that unit's oracle, which is the same
"declared by the party with the context" contract
`[FEAT-2026-0059/G1-CLOSE/classify-beats-prose]` records.

A malformed value is a **configuration error, never a silent fallback**: a
`max_attempts: 0` that quietly became 3 would run a unit the author meant to
run once, and a typo that quietly became 3 would hide the typo forever.
"""

from __future__ import annotations

import unittest

from specfuse.loop.loop import MAX_ATTEMPTS, resolve_max_attempts


class _WU:
    """Minimal stand-in carrying only the field under test."""

    def __init__(self, max_attempts=None):
        self.wu_id = "FEAT-2026-9999/T01"
        self.max_attempts = max_attempts


class TestPrecedence(unittest.TestCase):
    def test_the_work_unit_wins_over_everything(self):
        self.assertEqual(
            resolve_max_attempts(_WU(7), {"defaults": {"max_attempts": 5}}), 7)

    def test_the_project_default_applies_when_the_unit_is_silent(self):
        self.assertEqual(
            resolve_max_attempts(_WU(None), {"defaults": {"max_attempts": 5}}), 5)

    def test_the_constant_applies_when_both_are_silent(self):
        self.assertEqual(resolve_max_attempts(_WU(None), {}), MAX_ATTEMPTS)

    def test_an_absent_defaults_block_is_not_an_error(self):
        self.assertEqual(
            resolve_max_attempts(_WU(None), {"code": []}), MAX_ATTEMPTS)

    def test_a_unit_may_ask_for_a_single_attempt(self):
        # The discovery case: one pass, then a human looks.
        self.assertEqual(resolve_max_attempts(_WU(1), {}), 1)

    def test_a_unit_may_ask_for_many(self):
        # The convergent case (#2650): each attempt is an iteration.
        self.assertEqual(resolve_max_attempts(_WU(10), {}), 10)


class TestAMalformedValueIsAnError(unittest.TestCase):
    """Never a silent fallback — see the module docstring."""

    def test_zero_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_max_attempts(_WU(0), {})
        self.assertIn("max_attempts", str(ctx.exception))

    def test_a_negative_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_max_attempts(_WU(-1), {})

    def test_a_non_integer_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_max_attempts(_WU("many"), {})

    def test_a_malformed_project_default_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            resolve_max_attempts(_WU(None), {"defaults": {"max_attempts": 0}})
        self.assertIn("max_attempts", str(ctx.exception))

    def test_the_error_names_the_work_unit(self):
        # A configuration error the operator has to find must say where.
        with self.assertRaises(ValueError) as ctx:
            resolve_max_attempts(_WU(0), {})
        self.assertIn("FEAT-2026-9999/T01", str(ctx.exception))

    def test_a_bool_is_not_an_integer(self):
        # `True` is an int in Python and would silently mean "1 attempt".
        with self.assertRaises(ValueError):
            resolve_max_attempts(_WU(True), {})


class TestFrontmatterParsing(unittest.TestCase):
    def test_a_work_unit_carries_the_field_off_disk(self):
        import tempfile
        from pathlib import Path

        from specfuse.loop.loop import load_wu

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "WU-01.md").write_text(
                "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
                "status: pending\nmax_attempts: 8\n---\n\n# Unit\n\nBody.\n")
            wu = load_wu(Path(tmp),
                         {"id": "FEAT-2026-9999/T01", "file": "WU-01.md"})

        self.assertEqual(wu.max_attempts, 8)

    def test_absent_frontmatter_leaves_it_unset_rather_than_defaulted(self):
        # The dataclass must not bake the default in, or the project tier
        # could never apply — the unit would always look like it asked for 3.
        import tempfile
        from pathlib import Path

        from specfuse.loop.loop import load_wu

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "WU-01.md").write_text(
                "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
                "status: pending\n---\n\n# Unit\n\nBody.\n")
            wu = load_wu(Path(tmp),
                         {"id": "FEAT-2026-9999/T01", "file": "WU-01.md"})

        self.assertIsNone(wu.max_attempts)


if __name__ == "__main__":
    unittest.main()
