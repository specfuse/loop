#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Short-circuit a guard refusal a retry provably cannot fix (#597).

A guard refusal whose inputs are static frontmatter cannot be fixed by
retrying — the agent cannot edit its own frontmatter. The driver nonetheless
retried to `MAX_ATTEMPTS` and only then escalated. Observed on a real feature
whose `produces:` named a directory: three `deliverable_missing` attempts with
a byte-identical summary, $6.42 total, of which $3.96 bought nothing.

Two conditions are required, and the second is the load-bearing one:

- the refusal summary repeats **exactly**, and
- the attempt left the tree **provably untouched**.

Identical summary alone is not enough: a work unit can legitimately fail the
same guard twice while making real progress toward passing it. An empty
`files_touched` is what says the session changed nothing, so the next run has
nothing new to work with.

**`files_touched` had to be measured before this rule could mean anything.**
Every guard-refusal path defaulted it to `[]` via the emitter's
`files_touched if files_touched is not None else []`, so the second condition
was vacuously true and the rule would have collapsed into the first. That also
makes #597's own evidence table unsound as written — its `files_touched: []`
column was the default, not an observation. The structural test at the bottom
pins the measurement so it cannot silently regress to a default again.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

load_loop()

import specfuse.loop.loop as loop_module  # noqa: E402  (after sys.path setup above)
from specfuse.loop.loop import (  # noqa: E402  (after sys.path setup above)
    detect_deterministic_refusal_repeat,
)

_LOOP_SRC = Path(__file__).resolve().parent.parent / "specfuse" / "loop" / "loop.py"

# The guard-refusal outcomes whose refusal text is deterministic. Kept in sync
# with tests/test_guard_refusal_failure_class.py, which classifies the same set.
GUARD_REFUSAL_OUTCOMES = {
    "closing_deliverable_missing",
    "deliverable_missing",
    "no_deliverable_files",
    "learnings_not_staged",
    "squash_commit_failed",
    "smoke_import_failed",
}

_SUMMARY = "deliverable_missing: declared produces path 'docs/' is a directory"


class TestDetectDeterministicRefusalRepeat(unittest.TestCase):
    def test_identical_summary_and_untouched_tree_short_circuits(self):
        self.assertTrue(
            detect_deterministic_refusal_repeat(_SUMMARY, _SUMMARY, []))

    def test_identical_summary_but_touched_tree_does_not(self):
        # The session changed something, so the next attempt has new input.
        # This is the case the rule must NOT fire on.
        self.assertFalse(
            detect_deterministic_refusal_repeat(
                _SUMMARY, _SUMMARY, ["specfuse/loop/loop.py"]))

    def test_identical_summary_and_identical_touched_set_short_circuits(self):
        # #1415: attempts 1 and 2 each wrote the same one of two declared
        # deliverables and were refused for the same missing path. That is
        # not progress — the second attempt reproduced the first exactly —
        # and the third attempt is a full-price session that buys nothing.
        self.assertTrue(
            detect_deterministic_refusal_repeat(
                _SUMMARY, _SUMMARY, ["src/a.py"], prior_files_touched=["src/a.py"]))

    def test_identical_summary_but_different_touched_set_does_not(self):
        # Same wall, different work: the agent wrote something new, so the
        # next attempt has new input. Order of paths is not a difference.
        self.assertFalse(
            detect_deterministic_refusal_repeat(
                _SUMMARY, _SUMMARY, ["src/a.py", "src/b.py"], prior_files_touched=["src/a.py"]))
        self.assertTrue(
            detect_deterministic_refusal_repeat(
                _SUMMARY, _SUMMARY, ["src/b.py", "src/a.py"],
                prior_files_touched=["src/a.py", "src/b.py"]))

    def test_deliverable_missing_retry_carries_the_present_absent_split(self):
        # #1415: the retry prompt used to repeat the one-line guard summary a
        # human already sees. The attempt note composed before the reset
        # (#1412) says which declared deliverables landed and which did not;
        # that is what the next attempt is handed.
        import inspect
        src = inspect.getsource(loop_module.run)
        branch = src[src.index('"deliverable_missing",'):]
        branch = branch[:branch.index("continue")]
        self.assertIn("failure_note = _deliv_note", branch)
        self.assertNotIn("failure_note = deliv_summary", branch)

    def test_different_summary_does_not_short_circuit(self):
        self.assertFalse(
            detect_deterministic_refusal_repeat(
                _SUMMARY, _SUMMARY + " (and one more)", []))

    def test_first_refusal_has_nothing_to_compare(self):
        self.assertFalse(
            detect_deterministic_refusal_repeat(_SUMMARY, None, []))

    def test_blank_summaries_never_short_circuit(self):
        # A non-informative summary would collapse distinct refusals into one
        # bucket and false-fire the halt — the same defence
        # _is_noninformative_signature gives the signature-repeat check.
        for blank in ("", "   ", "\n"):
            with self.subTest(summary=repr(blank)):
                self.assertFalse(
                    detect_deterministic_refusal_repeat(blank, blank, []))

    def test_whitespace_differences_alone_do_not_defeat_the_match(self):
        # Trailing whitespace is not a real difference; a retry cannot fix it
        # either. Compared on the stripped text.
        self.assertTrue(
            detect_deterministic_refusal_repeat(_SUMMARY + "\n", _SUMMARY, []))


class TestGuardRefusalsMeasureFilesTouched(unittest.TestCase):
    """The rule is only meaningful if `files_touched` is measured, not defaulted."""

    @classmethod
    def setUpClass(cls):
        cls.source = _LOOP_SRC.read_text(encoding="utf-8")

    def _emit_call(self, outcome: str) -> str:
        anchor = re.search(
            r"emit_attempt_outcome\(\s*\n?\s*wu,\s*attempt,\s*%s" % re.escape(f'"{outcome}"'),
            self.source)
        self.assertIsNotNone(anchor, f"no emit site for {outcome!r}")
        start = self.source.index("emit_attempt_outcome(", anchor.start())
        depth = 0
        for i in range(start, len(self.source)):
            if self.source[i] == "(":
                depth += 1
            elif self.source[i] == ")":
                depth -= 1
                if depth == 0:
                    return self.source[start:i + 1]
        raise AssertionError("unbalanced parens")

    def test_every_guard_refusal_passes_files_touched_explicitly(self):
        for outcome in sorted(GUARD_REFUSAL_OUTCOMES):
            with self.subTest(outcome=outcome):
                call = self._emit_call(outcome)
                self.assertIn(
                    "files_touched=", call,
                    f"{outcome} lets files_touched default to [] — the #597 "
                    f"short-circuit's second condition would be vacuous")

    def test_every_guard_refusal_records_into_the_refusal_ledger(self):
        # The predicate is only reached for refusals that were recorded. One
        # guard path that forgets to append is one that keeps burning attempts
        # silently, which is the whole defect.
        self.assertEqual(
            self.source.count("refusal_history.append"),
            len(GUARD_REFUSAL_OUTCOMES),
            "every guard-refusal path must record into refusal_history")

    def test_the_diff_is_measured_before_any_reset(self):
        # reset_preserving_events wipes the working tree, so a measurement
        # taken after it reads empty by construction. Assert the measurement
        # precedes the first reset in the attempt loop.
        measure = self.source.index('_refusal_touched = git_diff_names(')
        first_reset = self.source.index(
            "reset_preserving_events(head_before, events_path,", measure - 6000)
        self.assertLess(
            measure, self.source.index(
                "reset_preserving_events(head_before, events_path,", measure),
            "files_touched must be measured before the tree is reset")
        self.assertGreater(first_reset, 0)

    def test_the_short_circuit_runs_before_dispatch(self):
        # Firing after dispatch would still pay for the session it exists to
        # avoid. Assert the check precedes the attempt-counter bump, which is
        # the first statement of the normal path.
        check = self.source.index("detect_deterministic_refusal_repeat(\n")
        bump = self.source.index('backend.set_wu(wu, "attempts", attempt)')
        self.assertLess(
            check, bump,
            "the #597 check must run before the attempt is dispatched")


if __name__ == "__main__":
    unittest.main()
