#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Planning-discipline section-presence lint (#201, second half).

WARN-only checks that the sections introduced by the FEAT-2026-0049
planning-discipline drop (PR #211) are present: PLAN.md carries
'Existing-mechanism search' and 'Escalation-predicate satisfiability'
(an explicit n/a line satisfies them — presence, not content), and each
non-passed gate file carries 'Arming discipline'. Sealed features
(plan status done/abandoned) are history and never warn.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

_SECTIONS = (
    "\n## Existing-mechanism search\n\nn/a — no enforcement designed\n"
    "\n## Escalation-predicate satisfiability\n\nn/a — no severity flip\n"
)


def _write_feature(tmpdir: str, *, plan_status: str = "active",
                   plan_sections: str = _SECTIONS,
                   gate_status: str = "open",
                   gate_body: str = "\n## Arming discipline\n\nprobe notes\n",
                   ) -> Path:
    feature = Path(tmpdir) / "feature"
    feature.mkdir(exist_ok=True)
    (feature / "PLAN.md").write_text(
        "---\nfeature_id: FEAT-2026-9998\ntitle: T\nbranch: feat/t\n"
        f"roadmap_goal: g\nstatus: {plan_status}\n"
        "planned_cost_usd: 10.00\n---\n\n# Plan\n\n"
        "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units:\n      - id: FEAT-2026-9998/T01\n"
        "        file: WU-01-impl.md\n        depends_on: []\n"
        "      - id: FEAT-2026-9998/G1-CLOSE\n        file: WU-90-close.md\n"
        "        depends_on: [FEAT-2026-9998/T01]\n```\n"
        f"{plan_sections}"
    )
    (feature / "GATE-01.md").write_text(
        f"---\ngate: 1\nstatus: {gate_status}\n---\n\n# Gate 1\n{gate_body}"
    )
    for fname, wid, wtype in (("WU-01-impl.md", "T01", "implementation"),
                              ("WU-90-close.md", "G1-CLOSE", "close")):
        (feature / fname).write_text(
            f"---\nid: FEAT-2026-9998/{wid}\ntype: {wtype}\nstatus: done\n"
            f"attempts: 1\nplanned_cost_usd: 5.0\n---\n\n# {wid}\n"
        )
    return feature


def _run_lint(feature: Path) -> tuple[list[str], str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        errs = lint_plan.lint(feature)
    return errs, buf.getvalue()


class TestPlanningSectionLint(unittest.TestCase):

    def test_silent_when_sections_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            errs, out = _run_lint(_write_feature(tmp))
            self.assertEqual(errs, [])
            self.assertNotIn("Existing-mechanism", out)
            self.assertNotIn("Arming discipline", out)

    def test_warns_on_missing_plan_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            errs, out = _run_lint(_write_feature(tmp, plan_sections=""))
            self.assertEqual(errs, [], "section presence is WARN-only")
            self.assertIn("missing 'Existing-mechanism search'", out)
            self.assertIn("missing 'Escalation-predicate satisfiability'", out)

    def test_na_line_satisfies_presence(self):
        """Presence, not content: the template's explicit n/a escape passes."""
        with tempfile.TemporaryDirectory() as tmp:
            _, out = _run_lint(_write_feature(tmp, plan_sections=_SECTIONS))
            self.assertNotIn("missing 'Existing-mechanism search'", out)

    def test_warns_on_gate_missing_arming_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            errs, out = _run_lint(_write_feature(tmp, gate_body=""))
            self.assertEqual(errs, [])
            self.assertIn("missing 'Arming discipline'", out)
            self.assertIn("GATE-01.md", out)

    def test_passed_gate_never_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out = _run_lint(_write_feature(tmp, gate_status="passed",
                                              gate_body=""))
            self.assertNotIn("missing 'Arming discipline'", out)

    def test_sealed_feature_never_warns(self):
        for status in ("done", "abandoned"):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    _, out = _run_lint(_write_feature(
                        tmp, plan_status=status, plan_sections="",
                        gate_body=""))
                    self.assertNotIn("missing 'Existing-mechanism search'", out)
                    self.assertNotIn("missing 'Arming discipline'", out)


if __name__ == "__main__":
    unittest.main()
