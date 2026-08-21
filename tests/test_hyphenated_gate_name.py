# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""`parse_gate_failure_signature` must see a hyphenated gate name (#2557).

The marker is written with the gate's raw name (`loop.py:3435`, `:3485`):

    f"### {gate['name']}: FAIL\\n```\\n$ {command}\\n"

while the parser accepted only `\\w+`, which excludes `-`. The two ends
disagreed about what a gate name may contain, so a failing gate whose name
carries a hyphen fell through to the `('other', 'no_gate_marker')` sentinel
-- the value meaning *no gate reported failure at all*. 16 of this repo's
20 configured gates are hyphenated, so most of the gate set could never be
named as the cause of a failure.

Observed on FEAT-2026-0058/T01 (#2541): the real failure was
`### sync-scaffold-symlinks-bats: FAIL`, the recorded signature was
`no_gate_marker`, the retry got nothing actionable, and the unit burned its
whole attempt budget before escalating `spinning_detected`.

Same family as #2390 (tsc diagnostics never reaching the retry): the
verdict layer blind to a failure shape, degrading a precisely-named fault
to an unactionable `other`.
"""

from __future__ import annotations

import unittest

from specfuse.loop.loop import parse_gate_failure_signature


def _fail_block(gate_name: str, body: str) -> str:
    return f"### {gate_name}: FAIL\n```\n$ some-command\n{body}\n```\n"


class TestHyphenatedGateNamesAreRecognised(unittest.TestCase):
    def test_a_hyphenated_gate_is_not_reported_as_no_marker(self):
        # The regression itself: the sentinel means "nothing failed", so
        # returning it for a gate that plainly did fail is a false negative
        # the retry cannot act on.
        out = _fail_block(
            "sync-scaffold-symlinks-bats",
            "not ok 1 sync creates a missing discovery link",
        )

        failure_class, signature = parse_gate_failure_signature(out)

        self.assertNotEqual((failure_class, signature), ("other", "no_gate_marker"))

    def test_every_hyphenated_gate_name_in_this_repo_is_matched(self):
        # Named individually rather than globbed from verification.yml: the
        # point is that these exact shapes parse, not that whatever the file
        # currently holds parses.
        for name in (
            "leak-scan", "agent-policy-example-lint", "event-type-gate",
            "roadmap-link-gate", "arm-sweep-gate", "monitoring-example-lint",
            "leak-scan-hook", "sync-scaffold-bats", "sync-scaffold-symlinks-bats",
            "init-sh-shim-bats", "init-skills-bats", "hookspath-conflict-bats",
            "artifact-changed", "plan-lint", "recent-commits", "diff-stat",
        ):
            with self.subTest(gate=name):
                _, signature = parse_gate_failure_signature(
                    _fail_block(name, "not ok 1 something broke"))
                self.assertNotEqual(signature, "no_gate_marker")

    def test_an_underscored_gate_name_still_matches(self):
        _, signature = parse_gate_failure_signature(
            _fail_block("some_gate", "not ok 1 something broke"))

        self.assertNotEqual(signature, "no_gate_marker")

    def test_a_hyphenated_gate_falls_in_the_other_class(self):
        # Only tests/lint/security/coverage carry a dedicated class; the rest
        # are `other` *by classification*, which is different from `other`
        # by failure-to-parse. The signature is what distinguishes them.
        failure_class, signature = parse_gate_failure_signature(
            _fail_block("leak-scan", "leak-scan: FINDINGS"))

        self.assertEqual(failure_class, "other")
        self.assertNotEqual(signature, "no_gate_marker")


class TestTheSignatureNamesTheFaultNotTheCommand(unittest.TestCase):
    """Adjacent defect the marker fix exposes rather than causes.

    `other`-class gates have no `_SIG_PATTERNS` entry, so they fall to the
    first-informative-line heuristic. The emitter writes the command echo
    (`$ <command>`) as the first line inside the fence, and that line is
    **identical across every failure of a given gate** -- so two genuinely
    different faults in the same gate produce the same signature, which is
    the collapse #167 added `_is_noninformative_signature` to prevent.

    Before the marker fix these gates returned `no_gate_marker` and never
    reached this code, so the command-echo collapse was unreachable and
    unobserved.
    """

    def test_two_different_bats_failures_do_not_share_a_signature(self):
        first = parse_gate_failure_signature(_fail_block(
            "sync-scaffold-symlinks-bats",
            "not ok 1 sync creates a missing discovery link"))
        second = parse_gate_failure_signature(_fail_block(
            "sync-scaffold-symlinks-bats",
            "not ok 3 sync does not modify an entry resolving outside"))

        self.assertNotEqual(first, second)

    def test_a_bats_failure_names_the_failing_case(self):
        _, signature = parse_gate_failure_signature(_fail_block(
            "init-sh-shim-bats", "not ok 2 upgrade mode: delegates to specfuse"))

        self.assertIn("upgrade mode", signature)

    def test_the_command_echo_is_never_the_signature(self):
        _, signature = parse_gate_failure_signature(_fail_block(
            "leak-scan", "leak-scan: FINDINGS\n  pull_request.body: line 5"))

        self.assertFalse(signature.startswith("$ "))


class TestUnchangedBehaviourIsPreserved(unittest.TestCase):
    def test_a_plain_gate_name_still_extracts_its_test_id(self):
        failure_class, signature = parse_gate_failure_signature(
            "### tests: FAIL\nFAIL: test_foo (mod.Class.test_foo)\n")

        self.assertEqual(failure_class, "tests")
        self.assertEqual(signature, "test_foo")

    def test_genuinely_no_marker_still_returns_the_sentinel(self):
        # The sentinel must keep its meaning: widening the name class must not
        # make it unreachable, or the spin detector's sentinel check at
        # loop.py:1015 loses the case it exists for.
        self.assertEqual(
            parse_gate_failure_signature("chatter with no gate marker at all\n"),
            ("other", "no_gate_marker"))

    def test_a_passing_hyphenated_gate_is_not_treated_as_a_failure(self):
        self.assertEqual(
            parse_gate_failure_signature("### leak-scan: PASS\n```\nclean\n```\n"),
            ("other", "no_gate_marker"))


if __name__ == "__main__":
    unittest.main()
