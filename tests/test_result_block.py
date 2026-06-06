#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Fix 1 — the agent's RESULT block parse + decision.

Covers parse_result_block(), agent_reported_blocked(), and the integration into
execute_unit_attempt() so the short-circuit on `status: blocked` is exercised
without spawning a real agent.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


def make_wu(wu_type: str = "implementation"):
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=Path("/tmp/does-not-matter.md"),
        depends_on=[],
        type=wu_type,
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title="test fixture",
        body="(body unused in these tests)",
    )


BLOCKED_STDOUT = """\
I attempted the work but discovered the router module does not exist in this
repo yet, which is an escalation trigger named in the WU.

```result
status: blocked
summary: cannot add a route because no router module exists
files_changed: []
acceptance_criteria:
  - text: GET /health responds 200
    met: false
    evidence: router module not present
blocked_reason: no router module exists at the path the WU references
```
"""

COMPLETE_STDOUT = """\
Added the route and verified.

```result
status: complete
summary: added GET /health returning {status, version}
files_changed:
  - src/routes/health.py
acceptance_criteria:
  - text: GET /health responds 200
    met: true
    evidence: pytest tests/test_health.py::test_status_ok passed
```
"""

NO_BLOCK_STDOUT = """\
I made some edits. I think they look right.

(no fenced result block here — agent forgot to emit one)
"""

MALFORMED_BLOCK_STDOUT = """\
```result
this is not yaml: it is just text
  - and: this: looks: nested: but: isnt
   weirdly indented: : :
```
"""

# Agent writes the discussion in a result-look-alike, then the real block at the end.
MULTIPLE_BLOCKS_STDOUT = """\
```result
status: complete
summary: first (stale) attempt
```

Wait — actually on re-reading, the router module is missing.

```result
status: blocked
blocked_reason: the real, last block — router module missing
```
"""


class TestParseResultBlock(unittest.TestCase):

    def test_parses_blocked(self):
        parsed = loop.parse_result_block(BLOCKED_STDOUT)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["status"], "blocked")
        self.assertIn("router module", parsed["blocked_reason"])

    def test_parses_complete(self):
        parsed = loop.parse_result_block(COMPLETE_STDOUT)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["status"], "complete")

    def test_no_block_returns_none(self):
        self.assertIsNone(loop.parse_result_block(NO_BLOCK_STDOUT))

    def test_empty_stdout_returns_none(self):
        self.assertIsNone(loop.parse_result_block(""))

    def test_malformed_block_returns_none(self):
        # Forgiving parse: malformed YAML must not crash, must return None so the
        # caller falls back to verify().
        self.assertIsNone(loop.parse_result_block(MALFORMED_BLOCK_STDOUT))

    def test_returns_last_block_when_multiple(self):
        parsed = loop.parse_result_block(MULTIPLE_BLOCKS_STDOUT)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["status"], "blocked")
        self.assertIn("real, last block", parsed["blocked_reason"])


class TestAgentReportedBlocked(unittest.TestCase):

    def test_blocked_returns_true_with_reason(self):
        is_blocked, reason = loop.agent_reported_blocked(BLOCKED_STDOUT)
        self.assertTrue(is_blocked)
        self.assertIn("router module", reason)

    def test_complete_returns_false(self):
        is_blocked, reason = loop.agent_reported_blocked(COMPLETE_STDOUT)
        self.assertFalse(is_blocked)
        self.assertIsNone(reason)

    def test_missing_block_returns_false(self):
        is_blocked, reason = loop.agent_reported_blocked(NO_BLOCK_STDOUT)
        self.assertFalse(is_blocked)
        self.assertIsNone(reason)

    def test_malformed_block_returns_false(self):
        # Malformed must not block — degrade to "verify decides."
        is_blocked, reason = loop.agent_reported_blocked(MALFORMED_BLOCK_STDOUT)
        self.assertFalse(is_blocked)
        self.assertIsNone(reason)


class TestParseResultBlockForgivesAnyParserError(unittest.TestCase):
    """parse_result_block must NOT crash on arbitrary parser exceptions.

    MiniYAMLError covers documented-subset violations, but the parser is
    hand-rolled and could in principle raise something else (IndexError,
    ValueError, etc.) on a sufficiently weird agent input. The forgiving
    contract is that ANY parser failure on this least-trusted input
    degrades to `verify() decides`, not a driver crash.
    """

    def test_non_miniyaml_exception_is_swallowed_to_None(self):
        # Inject a generic exception type from the parser to prove the catch
        # is broad, not MiniYAMLError-specific.
        stdout = "blah blah\n```result\nstatus: complete\n```\n"
        original = loop._miniyaml.parse
        loop._miniyaml.parse = lambda body: (_ for _ in ()).throw(
            ValueError("simulated arbitrary parser failure"))
        try:
            self.assertIsNone(loop.parse_result_block(stdout))
        finally:
            loop._miniyaml.parse = original

    def test_indexerror_from_parser_is_swallowed(self):
        # Same shape with a different exception type — proves broadness, not
        # an accidental tuple-of-types catch.
        stdout = "noise\n```result\nstatus: complete\n```\n"
        original = loop._miniyaml.parse
        loop._miniyaml.parse = lambda body: (_ for _ in ()).throw(
            IndexError("simulated index bug"))
        try:
            self.assertIsNone(loop.parse_result_block(stdout))
        finally:
            loop._miniyaml.parse = original

    def test_agent_reported_blocked_also_swallows_non_miniyaml(self):
        # The decision wrapper builds on parse_result_block; the forgiveness
        # should propagate — neither layer crashes on a parser bug.
        stdout = "anything\n```result\nstatus: blocked\n```\n"
        original = loop._miniyaml.parse
        loop._miniyaml.parse = lambda body: (_ for _ in ()).throw(
            RuntimeError("simulated parser bug"))
        try:
            is_blocked, reason = loop.agent_reported_blocked(stdout)
            self.assertFalse(is_blocked)
            self.assertIsNone(reason)
        finally:
            loop._miniyaml.parse = original


class TestExecuteUnitAttemptShortCircuits(unittest.TestCase):
    """Integration: when the agent emits status: blocked, execute_unit_attempt
    must NOT call verify(). This is what guarantees 'no further attempts.'"""

    def setUp(self):
        self.verify_calls = 0

        def fake_verify(wu, feature_dir, *args, **kwargs):
            self.verify_calls += 1
            return True, "(verify was called)"

        self.fake_verify = fake_verify

    def test_blocked_stdout_skips_verify(self):
        wu = make_wu()
        outcome, payload, _usage = loop.execute_unit_attempt(
            wu, Path("/tmp/feat"), None,
            dispatch_fn=lambda w, n: BLOCKED_STDOUT,
            verify_fn=self.fake_verify,
        )
        self.assertEqual(outcome, "blocked")
        self.assertIn("router module", payload)
        self.assertEqual(self.verify_calls, 0,
                         "verify must NOT be called when agent reports blocked")

    def test_complete_stdout_calls_verify(self):
        wu = make_wu()
        outcome, payload, _usage = loop.execute_unit_attempt(
            wu, Path("/tmp/feat"), None,
            dispatch_fn=lambda w, n: COMPLETE_STDOUT,
            verify_fn=self.fake_verify,
        )
        self.assertEqual(outcome, "passed")
        self.assertEqual(self.verify_calls, 1,
                         "verify must run when agent reports complete")

    def test_no_block_falls_through_to_verify(self):
        wu = make_wu()
        # verify reports failure here so we can confirm fall-through doesn't
        # spuriously block.
        def failing_verify(w, fd, *a, **kw):
            self.verify_calls += 1
            return False, "(simulated gate failure)"
        outcome, payload, _usage = loop.execute_unit_attempt(
            wu, Path("/tmp/feat"), None,
            dispatch_fn=lambda w, n: NO_BLOCK_STDOUT,
            verify_fn=failing_verify,
        )
        self.assertEqual(outcome, "failed")
        self.assertIn("simulated gate failure", payload)
        self.assertEqual(self.verify_calls, 1,
                         "missing result block must fall through to verify")

    def test_malformed_block_falls_through_to_verify(self):
        wu = make_wu()
        outcome, payload, _usage = loop.execute_unit_attempt(
            wu, Path("/tmp/feat"), None,
            dispatch_fn=lambda w, n: MALFORMED_BLOCK_STDOUT,
            verify_fn=self.fake_verify,
        )
        # verify reported True in setUp; malformed must NOT spuriously block.
        self.assertEqual(outcome, "passed")
        self.assertEqual(self.verify_calls, 1)


if __name__ == "__main__":
    unittest.main()
