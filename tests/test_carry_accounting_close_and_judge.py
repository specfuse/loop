#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0117/T03: the close states what it carried; the judge sees it.

Two surfaces read `carried_from_attempt` where a verdict gets decided: the
judge bundle (`judge.build_judge_bundle` / `render_judge_prompt`), which must
name a carried entry under its own heading with its `proved_at_sha` and
`covers`; and the closing registry's `close-o` requirement, which fails a
close whose `## Measurements` section is silent about what it inherited.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import closing_requirements as creq  # noqa: E402
from specfuse.loop import lint_closing  # noqa: E402
from specfuse.loop.criteria_state import CriterionStateEntry  # noqa: E402
from specfuse.loop.judge import build_judge_bundle, render_judge_prompt  # noqa: E402

GATE_MD = """\
---
gate: 1
status: open
---

# Gate 1 — a fixture gate

## Definition of done

- Everything the gate proved holds on this tree.
"""

CRITERIA_MD = """\
### T01#1

- **criterion:** the carried one
- **oracle:** python3 -m unittest tests.foo -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `abc1234`
- **attempt:** `1`
- **carried_from_attempt:** `1`
- **covers:** specfuse/loop/foo.py, tests/foo.py

### T02#1

- **criterion:** the re-measured one
- **oracle:** python3 -m unittest tests.bar -v -b
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `def5678`
- **attempt:** `2`
"""

RETRO_WITH_LINE = """\
# Retrospective

## Measurements

carried forward: 1 criteria, re-measured: 1

Both oracles above ran clean.
"""

RETRO_WITHOUT_LINE = """\
# Retrospective

## Measurements

Both oracles above ran clean.
"""


class TestJudgeBundleShowsCarriedEntries(unittest.TestCase):
    def _feature_dir(self, tmp: str) -> Path:
        d = Path(tmp)
        (d / "GATE-01.md").write_text(GATE_MD)
        (d / "GATE-01-CRITERIA.md").write_text(CRITERIA_MD)
        (d / "RETROSPECTIVE.md").write_text(RETRO_WITH_LINE)
        return d

    def test_carried_entry_named_under_its_own_heading_with_its_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._feature_dir(tmp)
            bundle = build_judge_bundle(d, 1, diff_text="", measurements=RETRO_WITH_LINE)
            prompt = render_judge_prompt(bundle)

        self.assertIn("Carried forward from a previous attempt", prompt)
        carried_idx = prompt.index("Carried forward from a previous attempt")
        # The carried criterion's sha appears under that heading.
        self.assertIn("T01#1", prompt[carried_idx:])
        self.assertIn("abc1234", prompt[carried_idx:])
        self.assertIn("specfuse/loop/foo.py", prompt[carried_idx:])
        # The re-measured entry is not listed under the carried heading.
        self.assertNotIn("T02#1", prompt[carried_idx:])
        # It is still visible in the main per-criterion state above.
        self.assertIn("T02#1", prompt[:carried_idx])
        self.assertIn("def5678", prompt[:carried_idx])

    def test_no_carried_heading_when_nothing_was_carried(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "GATE-01.md").write_text(GATE_MD)
            (d / "GATE-01-CRITERIA.md").write_text(
                "### T02#1\n\n"
                "- **criterion:** the only one\n"
                "- **oracle:** python3 -m unittest tests.bar -v -b\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                "- **proved_at_sha:** `def5678`\n"
                "- **attempt:** `1`\n"
            )
            (d / "RETROSPECTIVE.md").write_text(RETRO_WITHOUT_LINE)
            bundle = build_judge_bundle(d, 1, diff_text="", measurements=RETRO_WITHOUT_LINE)
            prompt = render_judge_prompt(bundle)

        self.assertNotIn("Carried forward from a previous attempt", prompt)


class TestRenderCarrySummary(unittest.TestCase):
    def test_counts_carried_and_remeasured(self):
        entries = [
            CriterionStateEntry(
                criterion_id="T01#1", criterion=None, oracle=None, kind="narrow",
                state="pass", proved_at_sha="abc1234", attempt="1",
                carried_from_attempt="1",
            ),
            CriterionStateEntry(
                criterion_id="T02#1", criterion=None, oracle=None, kind="narrow",
                state="pass", proved_at_sha="def5678", attempt="2",
            ),
        ]
        self.assertEqual(
            creq.render_carry_summary(entries),
            "carried forward: 1 criteria, re-measured: 1",
        )

    def test_required_only_when_something_was_carried(self):
        carried = [
            CriterionStateEntry(
                criterion_id="T01#1", criterion=None, oracle=None, kind="narrow",
                state="pass", proved_at_sha="abc1234", attempt="1",
                carried_from_attempt="1",
            ),
        ]
        none_carried = [
            CriterionStateEntry(
                criterion_id="T02#1", criterion=None, oracle=None, kind="narrow",
                state="pass", proved_at_sha="def5678", attempt="1",
            ),
        ]
        self.assertTrue(creq.carry_summary_is_required(carried))
        self.assertFalse(creq.carry_summary_is_required(none_carried))


class TestCloseORegistryCheck(unittest.TestCase):
    def test_registry_has_close_o_requirement(self):
        req = next(
            r for r in creq.CLOSING_REQUIREMENTS["close"] if r.id == "close-o"
        )
        self.assertEqual(req.enforced_by, "check_carry_summary_recorded")
        self.assertTrue(hasattr(lint_closing, req.enforced_by))

    def _ctx(self, fdir: Path) -> "lint_closing.ClosingContext":
        return lint_closing.ClosingContext(
            feature_dir=fdir, repo_root=fdir.parent, plan_fm={}, gates=[],
            wu_id="FEAT-2026-9999/G1-CLOSE", wu_type="close", gate_num=1,
            wfm={"verdict": "met"}, wbody="",
        )

    def test_fails_when_measurements_lacks_the_carry_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / "feature"
            fdir.mkdir()
            (fdir / "GATE-01-CRITERIA.md").write_text(CRITERIA_MD)
            (fdir / "RETROSPECTIVE.md").write_text(RETRO_WITHOUT_LINE)
            req = next(
                r for r in creq.CLOSING_REQUIREMENTS["close"] if r.id == "close-o"
            )
            ok, reason = lint_closing.check_carry_summary_recorded(req, self._ctx(fdir))
            self.assertFalse(ok)
            self.assertIn("carried forward: 1 criteria, re-measured: 1", reason)

    def test_passes_when_measurements_has_the_carry_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / "feature"
            fdir.mkdir()
            (fdir / "GATE-01-CRITERIA.md").write_text(CRITERIA_MD)
            (fdir / "RETROSPECTIVE.md").write_text(RETRO_WITH_LINE)
            req = next(
                r for r in creq.CLOSING_REQUIREMENTS["close"] if r.id == "close-o"
            )
            ok, reason = lint_closing.check_carry_summary_recorded(req, self._ctx(fdir))
            self.assertTrue(ok, reason)

    def test_passes_with_no_line_when_nothing_was_carried(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp) / "feature"
            fdir.mkdir()
            (fdir / "GATE-01-CRITERIA.md").write_text(
                "### T02#1\n\n"
                "- **criterion:** the only one\n"
                "- **oracle:** python3 -m unittest tests.bar -v -b\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                "- **proved_at_sha:** `def5678`\n"
                "- **attempt:** `1`\n"
            )
            (fdir / "RETROSPECTIVE.md").write_text(RETRO_WITHOUT_LINE)
            req = next(
                r for r in creq.CLOSING_REQUIREMENTS["close"] if r.id == "close-o"
            )
            ok, reason = lint_closing.check_carry_summary_recorded(req, self._ctx(fdir))
            self.assertTrue(ok, reason)


if __name__ == "__main__":
    unittest.main()
