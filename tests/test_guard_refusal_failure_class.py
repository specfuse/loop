#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Guard refusals must carry `failure_class` / `failure_signature` (#598).

`/learnings-suggest` groups non-passing attempts by the tuple
`(payload.failure_class, payload.failure_signature)` and **skips records
missing either field**. Guard refusals wrote `null` to both, so the textbook
repeat-failure signature the skill exists to surface — the same deterministic
guard refusing the same work unit minutes apart — never reached it at all.

Observed on FEAT-2026-0057/G1-CLOSE: a `closing_deliverable_missing` refusal
costing $5.73, the single most expensive attempt in that feature, recorded
`failure_class: None` and `failure_signature: None`. The gate failure in the
same feature (`lint` / `B905`) recorded both correctly, so the gap is specific
to the guard paths rather than to the emitter.

`#596` set the precedent with `failure_class: "guard_refusal"` and the
assertion's own name as the signature. This test binds every remaining guard
refusal to that shape.

The emitter is the source of truth: this reads `loop.py` and asserts the call
sites, so a new guard refusal added without a class cannot pass silently.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LOOP_SRC = _REPO_ROOT / "specfuse" / "loop" / "loop.py"

# Refusals originating in an `assert_*` guard. #596 set the shape for these:
# `failure_class: "guard_refusal"`, signature = the assertion's own name, which
# is stable, greppable, and already what an operator searches for.
ASSERT_GUARD_OUTCOMES = {
    "closing_deliverable_missing",
    "deliverable_missing",
    "no_deliverable_files",
    "learnings_not_staged",
}

# Driver refusals that do NOT originate in an `assert_*` guard: a git failure
# and a smoke-import run. They were equally null and equally dropped by
# /learnings-suggest, so they are in scope — but stamping them `guard_refusal`
# would be false. They take their own outcome name as the class, matching the
# convention already used by `produces_not_in_diff` and
# `files_changed_mismatch` at the neighbouring call sites.
NON_ASSERT_REFUSAL_OUTCOMES = {
    "squash_commit_failed",
    "smoke_import_failed",
}

GUARD_REFUSAL_OUTCOMES = ASSERT_GUARD_OUTCOMES | NON_ASSERT_REFUSAL_OUTCOMES

# Already carried a class before this fix; left untouched deliberately. Changing
# their values would alter data consumers already read, which is a separate
# decision from filling nulls.
ALREADY_CLASSIFIED_OUTCOMES = {
    "produces_not_in_diff",
    "files_changed_mismatch",
    "failed",
}

# Deliberately NOT guard refusals. Enumerated rather than left implicit because
# #598's own warning is that a half-populated field is worse than an empty one:
# a reader must be able to see which nulls are intentional.
#
#   zero_token_skip — infrastructure/quota, no guard involved and no agent
#                     output to refuse.
#   blocked         — the AGENT's own reasoned block; its diagnostic lives in
#                     `agent_blocked_reason`, which is populated.
#   prep_halted     — a declared `prep:` command exited non-zero before
#                     dispatch. Not an `assert_*` guard; its own halt class is
#                     tracked separately by #758.
#   passed          — not a failure.
NON_GUARD_OUTCOMES = {
    "zero_token_skip",
    "blocked",
    "prep_halted",
    "passed",
}


def _emit_call(source: str, outcome: str) -> str:
    """Return the full `emit_attempt_outcome(...)` call text for *outcome*.

    Scans forward from the outcome literal balancing parentheses, so the whole
    keyword-argument list is captured however it happens to be wrapped.
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


class TestGuardRefusalsCarryAFailureClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _LOOP_SRC.read_text(encoding="utf-8")

    def test_assert_originating_refusals_use_the_guard_refusal_class(self):
        for outcome in sorted(ASSERT_GUARD_OUTCOMES):
            with self.subTest(outcome=outcome):
                call = _emit_call(self.source, outcome)
                self.assertIn(
                    'failure_class="guard_refusal"', call,
                    f"{outcome} does not set failure_class=\"guard_refusal\"; "
                    f"/learnings-suggest drops records missing it (#598)",
                )

    def test_non_assert_refusals_are_classed_by_their_own_outcome_name(self):
        for outcome in sorted(NON_ASSERT_REFUSAL_OUTCOMES):
            with self.subTest(outcome=outcome):
                call = _emit_call(self.source, outcome)
                self.assertIn(
                    f'failure_class="{outcome}"', call,
                    f"{outcome} is a driver refusal but carries no class (#598)",
                )

    def test_every_refusal_sets_a_failure_signature(self):
        # Accepts a literal OR an identifier: `closing_deliverable_missing`
        # already extracts the SPECIFIC failing assertion name, which is a far
        # better clustering key than a constant would be, so it passes a
        # variable rather than a string.
        for outcome in sorted(GUARD_REFUSAL_OUTCOMES):
            with self.subTest(outcome=outcome):
                call = _emit_call(self.source, outcome)
                sig = re.search(r'failure_signature=("([^"]*)"|[A-Za-z_]\w*)', call)
                self.assertIsNotNone(
                    sig, f"{outcome} sets no failure_signature (#598)")
                literal = sig.group(2)
                if literal is not None:
                    self.assertTrue(
                        literal.strip(),
                        f"{outcome} sets an empty failure_signature (#598)")

    def test_literal_signatures_are_distinct(self):
        # The signature is the clustering key. Two guards sharing one would
        # merge unrelated failures into a single cluster, which is the same
        # loss of signal as writing null.
        sigs = {}
        for outcome in sorted(GUARD_REFUSAL_OUTCOMES):
            call = _emit_call(self.source, outcome)
            m = re.search(r'failure_signature="([^"]*)"', call)
            if m:
                sigs[outcome] = m.group(1)
        self.assertEqual(
            len(set(sigs.values())), len(sigs),
            f"refusal signatures collide: {sigs}")

    def test_non_guard_outcomes_are_left_unclassified_on_purpose(self):
        # Guards the other direction: this fix must not blanket-stamp
        # guard_refusal onto outcomes that are not guard refusals, which would
        # make the cluster view look complete while being wrong.
        for outcome in sorted(NON_GUARD_OUTCOMES):
            with self.subTest(outcome=outcome):
                call = _emit_call(self.source, outcome)
                self.assertNotIn(
                    '"guard_refusal"', call,
                    f"{outcome} is not a guard refusal but claims to be")

    def test_the_two_sets_are_disjoint_and_cover_every_emitted_outcome(self):
        # If a new outcome is added, this fails until it is deliberately placed
        # in one set or the other -- so the audit stays complete over time.
        emitted = set(re.findall(
            r'emit_attempt_outcome\(\s*\n?\s*wu,\s*attempt,\s*"([a-z_]+)"',
            self.source))
        self.assertEqual(GUARD_REFUSAL_OUTCOMES & NON_GUARD_OUTCOMES, set())
        classified = (GUARD_REFUSAL_OUTCOMES | NON_GUARD_OUTCOMES
                      | ALREADY_CLASSIFIED_OUTCOMES)
        self.assertEqual(
            emitted - classified, set(),
            "an emitted outcome is in no set — classify it (#598)")


if __name__ == "__main__":
    unittest.main()
