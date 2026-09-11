#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Re-plan is the spin-out brief's default option, recommend-only — T07.

Two things this file proves:

1. `replan_option_applies(reason)` is the single predicate the brief
   consults, and its verdict for all eleven `blocked_human` reasons matches
   the flag-scope table in `WU-07-replan-option-recommend-only.md`.
2. Driving a real `loop.run()` to `spinning_detected`, the printed brief's
   option 1 is the re-plan of the remaining gate (naming the units and the
   `/unblock-wu` command), part 6 recommends that same option by number, and
   part 1 states the automatic re-plan already ran and failed. Nothing on
   disk changes as a result — the brief recommends, it does not flip.

Harness reused from `tests/test_spinout_brief_end_to_end.py`.
"""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable
from tests.test_spinout_brief_end_to_end import write_feature, _read_events

loop = load_loop()

# The eleven `blocked_human` reasons named in `loop.py`'s flag-scope table
# (WU-07's own enumeration), each with the verdict the WU's table asserts.
EXPECTED_SCOPE = {
    "spinning_detected": True,
    "spinning_signature_repeat": True,
    "convergence_plateau": True,
    "replan_unchanged_body": True,
    "all_attempts_zero_token": False,
    "deterministic_refusal_repeat": False,
    "produces_shape_invalid": False,
    "spinning_reproduction_missing": False,
    "prep_halted": False,
    "agent_reported_blocked": False,
    "human_step_required": False,
}


class ReplanOptionAppliesTable(unittest.TestCase):

    def test_matches_the_flag_scope_table_for_all_eleven_reasons(self):
        self.assertEqual(len(EXPECTED_SCOPE), 11)
        for reason, expected in EXPECTED_SCOPE.items():
            with self.subTest(reason=reason):
                self.assertEqual(
                    loop.replan_option_applies(reason), expected,
                    f"{reason} should resolve to {expected}",
                )

    def test_unknown_reason_defaults_to_no_replan_option(self):
        self.assertFalse(loop.replan_option_applies("not_a_real_reason"))


class SpinoutBriefReplanOption(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_replan_is_option_one_and_recommended_recommend_only(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-8962", "spinout-brief-replan",
                "feat/spinout-brief-replan", [
                    ("FEAT-2026-8962/T01", "max_attempts: 3\n"),
                    ("FEAT-2026-8962/T02", ""),
                ])
            remaining_file = fdir / "WU-T02.md"
            before_fm, _ = loop.read_frontmatter(remaining_file)
            before_events = _read_events(fdir / "events.jsonl")

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "FAIL"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: [])

            captured = io.StringIO()
            with redirect_stdout(captured):
                rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 1)
            stdout = captured.getvalue()

            self.assertIn(
                "1. **Re-plan the remaining gate**", stdout,
                "option 1 must be the re-plan of the remaining gate",
            )
            self.assertIn(
                "/unblock-wu", stdout,
                "the option must name the command that performs the re-scope",
            )
            option_section = stdout.split(
                "1. **Re-plan the remaining gate**")[1][:600]
            self.assertIn(
                "FEAT-2026-8962/T01", option_section,
                "the option must name the spun-out unit",
            )
            self.assertIn(
                "FEAT-2026-8962/T02", option_section,
                "the option must name the remaining gate unit too",
            )

            self.assertIn("A recommendation", stdout)
            recommendation_section = stdout.split("## A recommendation")[1]
            recommendation_line = recommendation_section.strip().splitlines()[0]
            self.assertTrue(
                recommendation_line.startswith("Option 1."),
                f"part 6 must recommend option 1 by number, got: "
                f"{recommendation_line!r}",
            )

            part_1 = stdout.split("## What has been done so far")[1].split(
                "## What this issue is about")[0]
            self.assertIn(
                "already", part_1.lower(),
                "part 1 must state the automatic re-plan already ran",
            )
            self.assertIn(
                "did not pass", part_1,
                "part 1 must state that re-planned attempt already failed",
            )

            # Negative observation: nothing on disk was flipped by printing
            # the brief. The remaining unit's status/attempts are untouched,
            # and no second `replan` event was written beyond the automatic
            # trigger's own one.
            after_fm, _ = loop.read_frontmatter(remaining_file)
            self.assertEqual(before_fm.get("status"), after_fm.get("status"))
            self.assertEqual(
                before_fm.get("attempts"), after_fm.get("attempts"))

            after_events = _read_events(fdir / "events.jsonl")
            replan_events = [
                e for e in after_events if e["event_type"] == "replan"]
            self.assertEqual(
                len(replan_events), 1,
                "only the automatic trigger's own replan event may exist; "
                "the brief must not have caused a second one",
            )
            self.assertEqual(before_events, [],
                              "sanity: no events existed before the run")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class SpinoutBriefEveryPartHasContent(unittest.TestCase):
    """Every one of the six parts must SAY something (#3305).

    `validate_escalation_body` checks the headings are present, two numbered
    options exist and the correlation marker is there. It cannot check that a
    part says anything useful, so a part rendered as a placeholder satisfies
    it — which is how a hardcoded part 3 stub ("Full decision text is
    <work-unit-id>'s") shipped through a green gate whose oracle and whose
    close both read the brief and neither failed on it. These assertions are
    the missing half of that oracle.
    """

    def _render(self, *, replanned: bool, reason: str = "spinning_detected",
                remaining: list[str] | None = None) -> str:
        wu = loop.WorkUnit.__new__(loop.WorkUnit)
        object.__setattr__(wu, "wu_id", "FEAT-2026-8888/T01")
        object.__setattr__(wu, "title", "Do the thing")
        return loop.format_spinout_escalation_brief(
            wu, 1, ["FEAT-2026-8888/T00"],
            ["FEAT-2026-8888/T02"] if remaining is None else remaining,
            reason, 3, ["failed", "failed", "failed"], replanned,
            "specfuse run --feature FEAT-2026-8888")

    def _parts(self, brief: str) -> dict[str, str]:
        parts, current = {}, None
        for line in brief.splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                parts[current] = ""
            elif current:
                parts[current] += line + "\n"
        return parts

    def test_no_part_is_empty_or_a_placeholder(self):
        for replanned in (True, False):
            with self.subTest(replanned=replanned):
                parts = self._parts(self._render(replanned=replanned))
                self.assertEqual(len(parts), len(loop.ESCALATION_PART_HEADINGS))
                for heading, body in parts.items():
                    stripped = body.strip()
                    self.assertTrue(
                        len(stripped) >= 40,
                        f"part {heading!r} is {len(stripped)} chars — a part "
                        f"that cannot say 40 characters is a placeholder")

    def test_no_part_leaks_an_implementing_work_unit_id(self):
        # The brief describes the operator's feature, never the feature that
        # built the brief. `operator-escalation.md` forbids assuming the
        # reader has read the work unit; an internal FEAT/T-ID is exactly
        # that assumption, and #3305 shipped one in part 3.
        for replanned in (True, False):
            for reason in ("spinning_detected", "agent_reported_blocked"):
                with self.subTest(replanned=replanned, reason=reason):
                    brief = self._render(replanned=replanned, reason=reason)
                    self.assertNotIn("FEAT-2026-0104", brief)
                    self.assertNotIn(
                        "Full decision", brief,
                        "part 3 is deferring instead of stating the decision")

    def test_part_three_states_the_decision_and_why_it_is_needed(self):
        heading = loop.ESCALATION_PART_HEADINGS[2]
        for replanned in (True, False):
            with self.subTest(replanned=replanned):
                part3 = self._parts(self._render(replanned=replanned))[heading]
                self.assertIn("FEAT-2026-8888/T01", part3)
                # the "why": the driver has no remaining automatic move
                self.assertRegex(part3, r"(failed|exhaust|run out)")
                # the consequence of not deciding
                self.assertRegex(part3, r"(blocked|cannot close|nothing further)")
