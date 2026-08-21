#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A gate cannot arm while an artifact cites a decision ID absent from
`DECISIONS.md`, or restates a decision's statement instead of citing its ID
(FEAT-2026-0058/T02).

Two mechanical checks, deliberately never contradiction detection (`PLAN.md`
D1): **reference integrity** — every cited decision ID must exist in the
feature's registry — and **non-restatement** — an artifact that reproduces a
decision's statement text, rather than citing its ID, is an error. The
second is the load-bearing half: if artifacts may only cite, there is no
second copy of the statement to drift, which is the defect shape
FEAT-2026-0066 shipped (a four-row operator contract table transcribed as
three).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint, REPO_ROOT

lint_plan = load_lint()

FEATURES_DIR = REPO_ROOT / ".specfuse/features"

_GRAPH = (
    "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
    "      - id: FEAT-2026-0099/T01\n        file: WU-01.md\n"
    "        depends_on: []\n```\n"
)

_DECISIONS_D1_D2 = """\
### D1

- **statement:** Widgets ship blue by default, never red, because the brand
  guide fixed that in 2024 and no later decision reopened it.
- **owner:** platform-team
- **status:** `ratified`
- **provenance:** PLAN.md D1

### D2

- **statement:** The API returns 404 for a missing widget, 410 for a
  deleted one, 403 for one the caller cannot see, and 401 when unauthenticated.
- **owner:** platform-team
- **status:** `ratified`
- **provenance:** PLAN.md D2
"""


def _plan_fm(status: str = "planned") -> str:
    return (
        "---\n"
        "feature_id: FEAT-2026-0099\n"
        "title: Test Feature\n"
        "branch: feat/test\n"
        "roadmap_goal: Test goal\n"
        f"status: {status}\n"
        "---\n"
    )


def _wu_fm(wid: str = "FEAT-2026-0099/T01", status: str = "pending") -> str:
    return f"---\nid: {wid}\ntype: implementation\nstatus: {status}\n---\n"


def _build_feature(
    tmp_path: Path,
    *,
    decisions_text: str | None = _DECISIONS_D1_D2,
    plan_status: str = "planned",
    plan_body_extra: str = "",
    wu_body_extra: str = "",
    wu_status: str = "pending",
) -> Path:
    feat = tmp_path / "feat"
    feat.mkdir()
    (feat / "PLAN.md").write_text(
        _plan_fm(plan_status) + "\n" + plan_body_extra + "\n" + _GRAPH
    )
    (feat / "WU-01.md").write_text(
        _wu_fm(status=wu_status) + "\n# WU\n\n" + wu_body_extra + "\n"
    )
    (feat / "GATE-01.md").write_text(
        "---\nstatus: open\n---\n\n# Gate 1\n"
    )
    if decisions_text is not None:
        (feat / "DECISIONS.md").write_text(decisions_text)
    return feat


class TestCitationIntegrity(unittest.TestCase):

    def test_dangling_decision_id_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra="This unit implements the behavior from D9, "
                "which does not exist in the registry.",
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("cites decision" in e and "D9" in e for e in errs),
            f"expected dangling-citation error; errs={errs}",
        )

    def test_dangling_decision_id_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra="See D9 for the rationale.",
            )
            proc = subprocess.run(
                [sys.executable, "-m", "specfuse.loop.lint_plan", str(feat)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_valid_citation_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra="This unit implements the behavior decided in "
                "D1 and D2.",
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "cites decision" in e or "reproduces decision" in e],
            f"expected no citation/restatement errors; errs={errs}",
        )

    def test_restatement_with_one_clause_altered_is_caught(self):
        # FEAT-2026-0066's dropped-row shape: a four-row contract transcribed
        # as three. Here, D2's four-status-code statement is restated with the
        # 403 clause dropped, and the WU never cites D2's ID.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra=(
                    "The API returns 404 for a missing widget, 410 for a "
                    "deleted one, and 401 when unauthenticated."
                ),
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("reproduces decision" in e and "D2" in e for e in errs),
            f"expected restatement error for D2; errs={errs}",
        )

    def test_legitimate_quotation_with_citation_is_not_a_false_positive(self):
        # A close WU quoting a decision's statement while also citing its ID
        # is legitimate — not the restatement this check exists to catch.
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                wu_body_extra=(
                    "Per D1: widgets ship blue by default, never red, because "
                    "the brand guide fixed that in 2024 and no later decision "
                    "reopened it."
                ),
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "reproduces decision" in e],
            f"expected no restatement error when the ID is also cited; "
            f"errs={errs}",
        )

    def test_done_feature_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                plan_status="done",
                wu_status="done",
                wu_body_extra="See D9 for the rationale.",
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "cites decision" in e or "reproduces decision" in e],
            f"expected done feature to be exempt; errs={errs}",
        )

    def test_abandoned_feature_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                plan_status="abandoned",
                wu_status="done",
                wu_body_extra="See D9 for the rationale.",
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "cites decision" in e or "reproduces decision" in e],
            f"expected abandoned feature to be exempt; errs={errs}",
        )

    def test_feature_with_no_decisions_md_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=None,
                wu_body_extra="See D9 for the rationale, whatever that is.",
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "cites decision" in e or "reproduces decision" in e],
            f"expected no registry to mean opt-out; errs={errs}",
        )

    def test_check_runs_clean_over_this_repository(self):
        """FEAT-2026-0058's own D2: the satisfiability claim is falsifiable,
        not assumed. Every feature folder that carries a `DECISIONS.md` in
        this repository's real tree must show zero citation/restatement
        errors (the FEAT-2026-0050 repair precondition from `PLAN.md` D2 and
        `GATE-01.md`).
        """
        self.assertTrue(FEATURES_DIR.is_dir())
        offenders = []
        for feature_dir in sorted(FEATURES_DIR.iterdir()):
            if not feature_dir.is_dir():
                continue
            if not (feature_dir / "PLAN.md").is_file():
                continue
            errs = lint_plan.lint(feature_dir)
            bad = [
                e for e in errs
                if "cites decision" in e or "reproduces decision" in e
            ]
            if bad:
                offenders.append((feature_dir.name, bad))
        self.assertEqual(
            offenders, [], f"expected zero citation/restatement errors; "
            f"offenders={offenders}"
        )


if __name__ == "__main__":
    unittest.main()
