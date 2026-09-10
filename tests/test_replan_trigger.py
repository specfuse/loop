#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The real re-plan trigger predicate (FEAT-2026-0104/T02).

`should_replan_instead_of_retry` replaces T01's `replan_stub_trigger` opt-in
tracer with a predicate every unit is subject to: a unit re-plans when its
NEXT attempt would be its last permitted one (ceiling-relative, not a hard
count of two — see `resolve_max_attempts`, #2651), unless it declared
`iterate_on_failure` (#2650).

This module also proves the loop terminates whether or not a re-plan fires —
a previous attempt at this trigger rewound the attempt counter on re-plan and
hung the whole suite — and that a `detect_deterministic_refusal_repeat`
escalation owns its outcome instead of racing the re-plan trigger for it.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def _wu(**overrides) -> "loop.WorkUnit":
    defaults = dict(
        wu_id="FEAT-TEST-0104/T01",
        file=Path("WU-T01.md"),
        depends_on=[],
        type="implementation",
        model="sonnet",
        status="in_progress",
        attempts=0,
        title="T01",
        body="body",
    )
    defaults.update(overrides)
    return loop.WorkUnit(**defaults)


class ShouldReplanInsteadOfRetryTest(unittest.TestCase):
    """Pure predicate — no dispatch, no I/O."""

    def test_default_ceiling_fires_after_second_failure(self):
        wu = _wu()
        self.assertFalse(loop.should_replan_instead_of_retry(wu, 1, 3),
                          "must not fire after the 1st failure")
        self.assertTrue(loop.should_replan_instead_of_retry(wu, 2, 3),
                         "must fire after the 2nd failure at the default "
                         "ceiling of 3 — the unit's next attempt (3) is its "
                         "last permitted one")

    def test_declared_ceiling_of_ten_fires_after_ninth_not_second(self):
        wu = _wu()
        self.assertFalse(loop.should_replan_instead_of_retry(wu, 2, 10),
                          "a unit that declared max_attempts: 10 must not "
                          "re-plan at the point a default-ceiling unit would")
        self.assertTrue(loop.should_replan_instead_of_retry(wu, 9, 10),
                         "must fire after the 9th failure — attempt 10 is "
                         "the last permitted one")

    def test_ceiling_of_one_never_fires(self):
        wu = _wu()
        for attempt in range(1, 4):
            self.assertFalse(
                loop.should_replan_instead_of_retry(wu, attempt, 1),
                f"max_attempts: 1 has no second-to-last attempt to re-plan "
                f"from (checked at attempt={attempt})")

    def test_iterate_on_failure_never_fires_at_any_ceiling(self):
        wu = _wu(iterate_on_failure=True)
        for ceiling in (2, 3, 10):
            self.assertFalse(
                loop.should_replan_instead_of_retry(wu, ceiling - 1, ceiling),
                f"iterate_on_failure units are exempt outright "
                f"(ceiling={ceiling})")


_FEATURE_ID = "FEAT-TEST-0104B"
_SLUG = "replan-terminates"
_BRANCH = f"feat/{_FEATURE_ID}-{_SLUG}"
_DISPATCH_CEILING = 10


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def _scaffold(root: Path, wu_body_extra: str = "") -> Path:
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: replan-terminates\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Replan terminates | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Replan terminates\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: prove the unit loop terminates whether or not a "
        "re-plan fires\n"
        "status: active\n"
        "---\n\n"
        f"# Plan: {_SLUG}\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {_FEATURE_ID}/T01\n"
        "        file: WU-T01.md\n"
        "        depends_on: []\n"
        "```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {_FEATURE_ID}/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "max_attempts: 3\n"
        f"---\n\n# T01\n\n{wu_body_extra}Body.\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold replan-terminates fixture"], check=True)
    return fdir


class ReplanTerminatesTest(unittest.TestCase):
    """AC: a unit that fails every attempt and re-plans still terminates."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_all_attempts_failing_reaches_blocked_human_within_dispatch_ceiling(self):
        dispatch_count = {"n": 0}

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            dispatch_count["n"] += 1
            if dispatch_count["n"] > _DISPATCH_CEILING:
                self.fail(
                    f"dispatched more than {_DISPATCH_CEILING} times — the "
                    f"unit loop is spinning instead of terminating (a "
                    f"re-plan must spend the remaining attempt slot, not "
                    f"buy a new budget)")
            return "```result\nstatus: complete\n```\n"

        def fake_verify(wu, feature_dir, gate_file=None):
            return False, "synthetic failure for every attempt"

        with integration_workspace() as root:
            os.chdir(root)
            _scaffold(root)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 1, "an all-failing unit halts the gate")
            self.assertEqual(
                dispatch_count["n"], 3,
                "max_attempts: 3 must terminate at exactly 3 dispatches — a "
                "re-plan on attempt 2 spends the last attempt slot (3), it "
                "does not reset the counter and buy a fresh budget")

            fdir = (root / ".specfuse" / "features" /
                    f"{_FEATURE_ID}-{_SLUG}")
            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(wu_fm.get("status"), "blocked_human",
                              "an exhausted, still-failing unit must reach "
                              "a terminal state, not hang")


class RefusalRepeatOwnsOutcomeTest(unittest.TestCase):
    """AC: a deterministic-refusal-repeat escalation owns the outcome; the
    re-plan trigger must not also fire at the same attempt boundary."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_refusal_repeat_escalates_and_the_replanned_attempt_never_dispatches(self):
        # verify() PASSES on every attempt, but dispatch writes no
        # deliverable file — so `assert_implementation_touched_files` refuses
        # the pass identically every time ("no_deliverable_files"), which
        # appends to `refusal_history` with empty `files_touched`. That is a
        # guard refusal, a structurally distinct code path from a real
        # verify() failure: `should_replan_instead_of_retry` is only ever
        # consulted on the "outcome == failed" path, so it is never reached
        # here at all — the refusal-repeat check owns the outcome outright.
        # `detect_deterministic_refusal_repeat` fires at the top of attempt 3
        # once 2 identical refusals (from attempts 1 and 2) exist, blocking
        # BEFORE attempt 3 is ever dispatched: proven directly by
        # dispatch_count staying at 2, not 3.
        dispatch_count = {"n": 0}

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            dispatch_count["n"] += 1
            return "```result\nstatus: complete\nfiles_changed: []\n```\n"

        def fake_verify(wu, feature_dir, gate_file=None):
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            _scaffold(root)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 1)
            fdir = (root / ".specfuse" / "features" /
                    f"{_FEATURE_ID}-{_SLUG}")
            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(wu_fm.get("status"), "blocked_human")
            self.assertEqual(
                wu_fm.get("escalation_reason"), "deterministic_refusal_repeat",
                "the repeated guard refusal must own the escalation")
            self.assertEqual(
                dispatch_count["n"], 2,
                "the refusal-repeat check must block attempt 3 before it is "
                "dispatched — the re-plan that fired at the end of attempt "
                "2 must never reach dispatch")


if __name__ == "__main__":
    unittest.main()
