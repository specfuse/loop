#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Guard refusals must carry `failure_excerpt` (issue #2504).

`#598` fixed `failure_class` / `failure_signature` being null on
`guard_refusal` attempts, but left `failure_excerpt` null in all of them. A
refused attempt retries with no more information than the attempt before it
had, so the failure repeats until `MAX_ATTEMPTS` is exhausted. The sibling
classes `produces_not_in_diff` and `files_changed_mismatch` already populate
`failure_excerpt` via `extract_failure_excerpt(...)` at their own call sites
— this binds every `guard_refusal` call site to the same shape.

The emitter is the source of truth: this reads `loop.py` and asserts the
call sites, so a new guard refusal added without an excerpt cannot pass
silently.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LOOP_SRC = _REPO_ROOT / "specfuse" / "loop" / "loop.py"

# The four `assert_*`-originating guard_refusal outcomes established by #598.
ASSERT_GUARD_OUTCOMES = {
    "closing_deliverable_missing",
    "deliverable_missing",
    "no_deliverable_files",
    "learnings_not_staged",
}


def _emit_call(source: str, outcome: str) -> str:
    """Return the full `emit_attempt_outcome(...)` call text for *outcome*.

    Scans forward from the outcome literal balancing parentheses, so the
    whole keyword-argument list is captured however it happens to be
    wrapped.
    """
    anchor = re.search(
        r"emit_attempt_outcome\(\s*\n?\s*wu,\s*attempt,\s*%s" % re.escape(f'"{outcome}"'),
        source,
    )
    assert anchor, f"no emit_attempt_outcome call site found for {outcome!r}"
    start = source.index("emit_attempt_outcome(", anchor.start())
    depth = 0
    for i in range(start, len(source)):
        if source[i] == "(":
            depth += 1
        elif source[i] == ")":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise AssertionError(f"unbalanced parentheses at {outcome!r} call site")


class TestGuardRefusalsCarryAFailureExcerpt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _LOOP_SRC.read_text(encoding="utf-8")

    def test_assert_originating_refusals_set_a_failure_excerpt(self):
        for outcome in sorted(ASSERT_GUARD_OUTCOMES):
            with self.subTest(outcome=outcome):
                call = _emit_call(self.source, outcome)
                self.assertIn(
                    "failure_excerpt=", call,
                    f"{outcome} does not set failure_excerpt; a refused "
                    f"attempt retries blind (#2504)",
                )
                self.assertNotIn(
                    "failure_excerpt=None", call,
                    f"{outcome} sets failure_excerpt=None explicitly, "
                    f"which is the bug this test guards against (#2504)",
                )


if __name__ == "__main__":
    unittest.main()
