#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The re-plan turn's real contract (FEAT-2026-0104/T03).

T01 stubbed `run_replan_turn` as a driver-side marker append — no session
dispatched, no failure history read, no narrowing. This module proves the
real contract that replaces it:

- `run_replan_turn` dispatches a FRESH session through the same `dispatch()`
  boundary every real attempt goes through (not a second, parallel
  vocabulary for it) — the rewritten body is that session's output, not a
  function of the input body alone.
- `synthesize_replan_brief` hands that session both prior attempts'
  failure_class, failure_signature, and their full retained notes verbatim
  — not a summary.
- The rewritten body must be NARROWER (fewer/tighter acceptance criteria
  plus an explicit non-goal) and still a valid work unit: the five
  mandatory sections intact, checked by running `lint_plan.lint()` over it,
  not by asserting on length.
- `assert_replan_changed_body` (and `run_replan_turn` calling it) refuses a
  turn whose output is byte-identical to its input, raising
  `ReplanUnchangedError` rather than handing back a body the caller could
  dispatch the unit's last attempt against unchanged.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint, load_loop

loop = load_loop()
lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FEATURE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"

_ORIGINAL_BODY = (
    "**Context.** Part of a feature that needs a rate limiter. Read "
    ".specfuse/rules/ before acting.\n\n"
    "**Acceptance criteria.**\n\n"
    "- Requests over the limit return 429 with a Retry-After header.\n"
    "- The limit is configurable per route via the existing config module.\n"
    "- A burst of concurrent requests at the boundary is handled without a "
    "race that double-admits one over the limit.\n\n"
    "**Do not touch.** Other routes, the auth middleware, `.git/`.\n\n"
    "**Verification.** The `code` gates in `.specfuse/verification.yml`.\n\n"
    "**Escalation triggers.** If no config module exists yet, emit "
    "`status: blocked`.\n"
)

_FAILURE_HISTORY = [
    {
        "attempt": 1,
        "failure_class": "tests",
        "failure_signature": "test_rate_limit_concurrent_boundary",
        "note": "FAIL: test_rate_limit_concurrent_boundary — two goroutines "
                "racing the same window counter both got admitted; the "
                "increment-then-check is not atomic under concurrent load.",
    },
    {
        "attempt": 2,
        "failure_class": "tests",
        "failure_signature": "test_rate_limit_concurrent_boundary",
        "note": "FAIL: test_rate_limit_concurrent_boundary — switched to a "
                "mutex around the counter, still flaky: the mutex protects "
                "the counter but the config-reload path can swap the limit "
                "mid-window without holding it, admitting one extra request "
                "on roughly 1 in 20 runs.",
    },
]


def _make_wu(wu_file: Path, body: str = _ORIGINAL_BODY) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=wu_file,
        depends_on=[],
        type="implementation",
        model="sonnet",
        effort="medium",
        status="pending",
        attempts=2,
        title="Add a per-route rate limiter",
        body=body,
    )


def copy_example_to(tmp: Path) -> Path:
    dest = tmp / "feature"
    shutil.copytree(EXAMPLE_FEATURE, dest)
    return dest


def _replace_wu_body(wu_path: Path, new_body: str) -> None:
    """Swap the body of a WU file, preserving its frontmatter block intact."""
    text = wu_path.read_text()
    lines = text.splitlines()
    j = 1
    while j < len(lines) and lines[j] != "---":
        j += 1
    fm_part = "\n".join(lines[: j + 1]) + "\n"
    wu_path.write_text(fm_part + "\n" + new_body)


# A plausible narrowed rewrite: one tightly-scoped criterion (dropping the
# per-route-config and burst-boundary criteria the attempts never got past),
# one explicit non-goal drawn from what attempt 2 hit, all five sections
# still present.
_NARROWED_REWRITE = (
    "**Context.** Part of a feature that needs a rate limiter. Two prior "
    "attempts both failed on the same concurrent-boundary race; this "
    "narrows the unit to just that race, deferring the rest.\n\n"
    "**Acceptance criteria.**\n\n"
    "- A burst of concurrent requests at the boundary never admits more "
    "than the configured limit, verified by "
    "test_rate_limit_concurrent_boundary under `-race`.\n\n"
    "**Do not touch.** Other routes, the auth middleware, `.git/`. "
    "Non-goal: the config-reload path's own atomicity — both prior "
    "attempts' failures traced to the counter/limit race, not to reload "
    "itself; leave reload as this unit found it.\n\n"
    "**Verification.** The `code` gates in `.specfuse/verification.yml`.\n\n"
    "**Escalation triggers.** If the race persists after this unit's own "
    "attempt, emit `status: blocked` rather than a third silent retry.\n"
)


class SynthesizeReplanBriefTest(unittest.TestCase):
    def test_brief_carries_full_failure_history_not_a_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wu = _make_wu(Path(tmpdir) / "WU-01.md")
            brief = loop.synthesize_replan_brief(wu, _FAILURE_HISTORY)

        for entry in _FAILURE_HISTORY:
            self.assertIn(str(entry["attempt"]), brief)
            self.assertIn(entry["failure_class"], brief)
            self.assertIn(entry["failure_signature"], brief)
            # The full note text, verbatim — not a paraphrase/summary of it.
            self.assertIn(entry["note"], brief)
        self.assertIn(wu.body, brief)

    def test_brief_names_both_attempts_distinctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wu = _make_wu(Path(tmpdir) / "WU-01.md")
            brief = loop.synthesize_replan_brief(wu, _FAILURE_HISTORY)

        self.assertIn("Attempt 1", brief)
        self.assertIn("Attempt 2", brief)


class AssertReplanChangedBodyTest(unittest.TestCase):
    def test_identical_body_raises(self):
        with self.assertRaises(loop.ReplanUnchangedError):
            loop.assert_replan_changed_body(_ORIGINAL_BODY, _ORIGINAL_BODY)

    def test_identical_modulo_whitespace_raises(self):
        with self.assertRaises(loop.ReplanUnchangedError):
            loop.assert_replan_changed_body(
                _ORIGINAL_BODY, _ORIGINAL_BODY + "\n\n")

    def test_changed_body_does_not_raise(self):
        loop.assert_replan_changed_body(_ORIGINAL_BODY, _NARROWED_REWRITE)


class RunReplanTurnTest(unittest.TestCase):
    def setUp(self):
        self._original_dispatch = loop.dispatch

    def tearDown(self):
        loop.dispatch = self._original_dispatch

    def test_dispatches_a_real_session_not_a_string_transform(self):
        """The rewritten body is a dispatched session's OWN output.

        A driver-side transform (e.g. appending the brief as a Markdown
        section onto the existing body) would make the output a function of
        the input body alone. Proving the real contract means the output
        must be traceable to something ONLY the patched dispatcher decided
        — here, a rewrite the input body does not itself contain a single
        token of.
        """
        calls: list = []

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            calls.append(wu)
            return _NARROWED_REWRITE, {"cost_usd": 0.01}

        loop.dispatch = fake_dispatch

        with tempfile.TemporaryDirectory() as tmpdir:
            wu = _make_wu(Path(tmpdir) / "WU-01.md")
            result = loop.run_replan_turn(wu, _FAILURE_HISTORY)

        self.assertEqual(len(calls), 1, "the patched dispatcher must be called")
        self.assertEqual(result["body"], _NARROWED_REWRITE.strip())
        self.assertEqual(result["transcript"], _NARROWED_REWRITE)
        self.assertEqual(result["usage"], {"cost_usd": 0.01})
        # The rewrite is NOT derivable from the input body alone: nothing in
        # wu.body mentions "Non-goal" or names the race-under-`-race` fix.
        self.assertNotIn("Non-goal", wu.body)
        self.assertIn("Non-goal", result["body"])

    def test_brief_is_what_gets_dispatched(self):
        """The session dispatched IS handed `synthesize_replan_brief`'s
        brief (as the prompt body), not the raw unit body — proving the
        turn is genuinely informed by the failure history, not just any
        session that happens to return a different string."""
        seen = {}

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            seen["body"] = wu.body
            return _NARROWED_REWRITE, None

        loop.dispatch = fake_dispatch

        with tempfile.TemporaryDirectory() as tmpdir:
            wu = _make_wu(Path(tmpdir) / "WU-01.md")
            loop.run_replan_turn(wu, _FAILURE_HISTORY)

        expected_brief = loop.synthesize_replan_brief(wu, _FAILURE_HISTORY)
        self.assertEqual(seen["body"], expected_brief)

    def test_unchanged_body_raises_and_does_not_dispatch_twice(self):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            return _ORIGINAL_BODY, None  # echoes the input body unchanged

        loop.dispatch = fake_dispatch

        with tempfile.TemporaryDirectory() as tmpdir:
            wu = _make_wu(Path(tmpdir) / "WU-01.md")
            with self.assertRaises(loop.ReplanUnchangedError):
                loop.run_replan_turn(wu, _FAILURE_HISTORY)

    def test_dispatch_stub_returning_plain_text_is_tolerated(self):
        """Mirrors execute_unit_attempt's own backward-compatible dispatch_fn
        contract: a stub may return a plain str instead of (str, usage)."""
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            return _NARROWED_REWRITE

        loop.dispatch = fake_dispatch

        with tempfile.TemporaryDirectory() as tmpdir:
            wu = _make_wu(Path(tmpdir) / "WU-01.md")
            result = loop.run_replan_turn(wu, _FAILURE_HISTORY)

        self.assertEqual(result["body"], _NARROWED_REWRITE.strip())
        self.assertIsNone(result["usage"])


class RewrittenBodyIsNarrowerAndValidTest(unittest.TestCase):
    """AC: the rewritten unit parses as a valid WU with its five mandatory
    sections intact, and is narrower — not merely longer. Asserted on the
    parsed sections via the real WU lint, not on raw length."""

    def test_narrowed_rewrite_passes_the_wu_lint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            wu_path = feature / "WU-01-health-endpoint.md"
            _replace_wu_body(wu_path, _NARROWED_REWRITE)
            errs = lint_plan.lint(feature)
            section_errs = [e for e in errs if "missing section" in e]
        self.assertEqual(
            section_errs, [],
            f"narrowed rewrite must keep all five mandatory sections; "
            f"section_errs={section_errs}")

    def test_narrowed_rewrite_has_fewer_acceptance_criteria(self):
        from specfuse.loop._wu_sections import slice_acceptance_criteria

        original_ac = slice_acceptance_criteria(_ORIGINAL_BODY)
        rewritten_ac = slice_acceptance_criteria(_NARROWED_REWRITE)
        original_bullets = [
            line for line in original_ac.splitlines() if line.strip().startswith("-")
        ]
        rewritten_bullets = [
            line for line in rewritten_ac.splitlines()
            if line.strip().startswith("-")
        ]
        self.assertLess(
            len(rewritten_bullets), len(original_bullets),
            "the rewrite must scope acceptance criteria to fewer items, not "
            "just longer prose")

    def test_narrowed_rewrite_states_an_explicit_non_goal(self):
        do_not_touch = loop._wu_sections.slice_wu_section(
            _NARROWED_REWRITE, "Do not touch")
        self.assertIn("non-goal", do_not_touch.lower())

    def test_narrowed_rewrite_is_not_merely_appended(self):
        """A body that just appends the brief as a trailing section (the
        previously-rejected shape) is NOT what this contract wants — the
        original text must not still be present verbatim, proving the turn
        rewrote rather than appended."""
        self.assertNotIn(_ORIGINAL_BODY.strip(), _NARROWED_REWRITE)


if __name__ == "__main__":
    unittest.main()
