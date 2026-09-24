#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The bug lane picks its model from what is known about the issue (#3391).

Every bug the lane dispatched got one Sonnet session at medium effort, whether
it was a one-line template fix or a change whose direction has architectural
consequences -- `build_invocation`'s defaults, never overridden at the call
site.

The issue proposed two signals. The first, a `effort=` field triage guesses
from issue text in ~8 seconds, is **not** what this implements: the issue's own
caveat argues against it, and the case it cites is decisive -- the issue that
read as most mechanical ("a test fake fabricates a Guid instead of using the
seed") was the one whose correct fix required knowing where the seed value
comes from. Effort is a property of the codebase, not of the report.

The second is what shipped: `fix_scope`, which `/diagnose-issue` already emits
as a validated field of `specfuse.monitor.diagnosis.Diagnosis`. It rests on
something a tool produced rather than a classification made in eight seconds,
and it needed no new vocabulary -- `FIX_SCOPES` has been shipped since
FEAT-2026-0041.

An issue with no diagnosis keeps the previous default exactly, so the lane's
behaviour is unchanged wherever this signal does not exist.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from specfuse.loop.agent_policy import (
    DEFAULT_MODEL_BY_FIX_SCOPE,
    resolve_model_by_fix_scope,
)
from specfuse.monitor.diagnosis import FIX_SCOPES


class TheDefaultMapping(unittest.TestCase):

    def test_every_fix_scope_has_an_entry(self):
        # A scope with no entry would silently fall back, which is the shape
        # that made this invisible in the first place.
        for scope in FIX_SCOPES:
            self.assertIn(scope, DEFAULT_MODEL_BY_FIX_SCOPE)

    def test_a_small_fix_keeps_the_previous_default(self):
        self.assertEqual(("sonnet", "medium"), DEFAULT_MODEL_BY_FIX_SCOPE["small"])

    def test_a_large_fix_gets_more(self):
        model, effort = DEFAULT_MODEL_BY_FIX_SCOPE["large"]
        self.assertEqual("opus", model)
        self.assertEqual("high", effort)


class ResolvingFromPolicy(unittest.TestCase):

    def _policy(self, text: str) -> Path:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "agent-policy.yml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_absent_policy_is_the_shipped_default(self):
        self.assertEqual(DEFAULT_MODEL_BY_FIX_SCOPE, resolve_model_by_fix_scope(None))

    def test_an_operator_can_choose_what_large_costs_them(self):
        path = self._policy(
            "rules:\n  bugs:\n    model_by_fix_scope:\n"
            "      large: [sonnet, high]\n"
        )

        resolved = resolve_model_by_fix_scope(path)

        self.assertEqual(("sonnet", "high"), resolved["large"])
        self.assertEqual(
            DEFAULT_MODEL_BY_FIX_SCOPE["small"], resolved["small"],
            "an entry the operator did not name keeps its shipped value",
        )

    def test_a_malformed_entry_falls_back_rather_than_raising(self):
        path = self._policy(
            "rules:\n  bugs:\n    model_by_fix_scope:\n      large: nonsense\n"
        )

        self.assertEqual(
            DEFAULT_MODEL_BY_FIX_SCOPE["large"],
            resolve_model_by_fix_scope(path)["large"],
        )

    def test_an_unknown_scope_name_is_ignored(self):
        path = self._policy(
            "rules:\n  bugs:\n    model_by_fix_scope:\n      enormous: [opus, high]\n"
        )

        self.assertEqual(DEFAULT_MODEL_BY_FIX_SCOPE, resolve_model_by_fix_scope(path))


class ReadingTheScopeFromTheIssue(unittest.TestCase):

    def _runner(self, comments):
        def runner(argv, check=False):
            if argv[:3] == ["gh", "issue", "view"]:
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "body": "A bug.", "comments": comments,
                }), stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return runner

    def _marker(self, scope: str) -> str:
        # Rendered by the real renderer, not a hand-written marker: `parse`
        # requires the prose sections too, and a fixture that skipped them
        # would pass here while every real diagnosis fell back to the default.
        from specfuse.monitor.diagnosis import Diagnosis, render

        return render(Diagnosis(
            root_cause="The guard never validates the discriminator.",
            evidence="Exhaustive switch falls through a case.",
            candidate_fix="Validate at the boundary.",
            confidence=0.9,
            fix_scope=scope,
        ))

    def test_a_diagnosed_large_fix_reads_as_large(self):
        from specfuse.loop.bug_lane_run import dispatch_profile_for

        model, effort, source = dispatch_profile_for(
            self._runner([{"body": self._marker("large")}]), "acme/widget", 7)

        self.assertEqual(("opus", "high"), (model, effort))
        self.assertEqual("diagnosis:large", source)

    def test_no_diagnosis_keeps_the_previous_default(self):
        from specfuse.loop.bug_lane_run import dispatch_profile_for

        model, effort, source = dispatch_profile_for(
            self._runner([{"body": "just a comment"}]), "acme/widget", 7)

        self.assertEqual(("sonnet", "medium"), (model, effort))
        self.assertEqual("default", source)

    def test_an_unreadable_issue_keeps_the_previous_default(self):
        from specfuse.loop.bug_lane_run import dispatch_profile_for

        def runner(argv, check=False):
            return SimpleNamespace(returncode=1, stdout="", stderr="boom")

        model, effort, source = dispatch_profile_for(runner, "acme/widget", 7)

        self.assertEqual(("sonnet", "medium"), (model, effort))
        self.assertEqual("default", source)

    def test_a_malformed_diagnosis_marker_does_not_raise(self):
        from specfuse.loop.bug_lane_run import dispatch_profile_for

        model, effort, _source = dispatch_profile_for(
            self._runner([{"body": "<!-- specfuse:diagnosis oops"}]),
            "acme/widget", 7)

        self.assertEqual(("sonnet", "medium"), (model, effort))


class TheRunSaysWhatItDispatchedWith(unittest.TestCase):
    """The proposal's closing point: without this the dial is unmeasurable."""

    def _note(self, profile):
        from specfuse.agent.providers.bugs import _dispatch_profile_note
        return _dispatch_profile_note(profile)

    def test_it_names_the_model_the_effort_and_the_source(self):
        note = self._note(("opus", "high", "diagnosis:large"))

        self.assertIn("opus", note)
        self.assertIn("high", note)
        self.assertIn("diagnosis:large", note)

    def test_a_default_dispatch_says_so_rather_than_staying_silent(self):
        # Silence would be indistinguishable from "this run predates the dial".
        note = self._note(("sonnet", "medium", "default"))

        self.assertIn("default", note)

    def test_an_absent_profile_renders_nothing(self):
        self.assertEqual("", self._note(()))
        self.assertEqual("", self._note(None))


class EveryReturnPathCarriesTheProfile(unittest.TestCase):
    """A profile recorded on some paths and not others makes the run log
    silently partial, which is the shape that hides a regression."""

    def test_every_result_run_bug_lane_returns_names_the_profile(self):
        import inspect
        import re

        from specfuse.loop import bug_lane_run

        src = inspect.getsource(bug_lane_run.run_bug_lane)
        # Results built here, plus the one delegated to `_declined`, which
        # takes the profile as a keyword and sets it on the result it builds.
        built = len(re.findall(r"BugLaneResult\(", src))
        delegated = len(re.findall(r"return _declined\(", src))
        carried = len(re.findall(r"dispatch_profile=_profile", src))

        self.assertEqual(
            built + delegated, carried,
            f"{built} BugLaneResult(s) built and {delegated} delegated to "
            f"_declined, but only {carried} pass dispatch_profile — a return "
            f"path that omits it reports no model for that item",
        )

    def test__declined_sets_it_on_the_result_it_builds(self):
        import inspect

        from specfuse.loop import bug_lane_run

        src = inspect.getsource(bug_lane_run._declined)
        self.assertIn("dispatch_profile=dispatch_profile", src)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
