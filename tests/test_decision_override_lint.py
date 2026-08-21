#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A gate cannot arm while an override sits unsigned (FEAT-2026-0058/T03).

`decisions_format.parse_decisions` refuses to parse an entry whose override
provenance is incomplete — it lands in `ParseResult.errors`, not
`.entries`. Left there it is silently invisible to lint. This lint surfaces
that refusal as an ERROR, and additionally rejects a `signed_off_by` that
names a placeholder rather than a human.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint, REPO_ROOT

lint_plan = load_lint()

_GRAPH = (
    "```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
    "      - id: FEAT-2026-0099/T01\n        file: WU-01.md\n"
    "        depends_on: []\n```\n"
)


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
    decisions_text: str | None,
    plan_status: str = "planned",
    wu_status: str = "pending",
) -> Path:
    feat = tmp_path / "feat"
    feat.mkdir()
    (feat / "PLAN.md").write_text(_plan_fm(plan_status) + "\n" + _GRAPH)
    (feat / "WU-01.md").write_text(_wu_fm(status=wu_status) + "\n# WU\n")
    (feat / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
    if decisions_text is not None:
        (feat / "DECISIONS.md").write_text(decisions_text)
    return feat


def _entry(
    decision_id: str = "D1",
    *,
    status: str = "ratified",
    overridden_from: str | None = None,
    signed_off_by: str | None = None,
    signed_off_at: str | None = None,
) -> str:
    lines = [
        f"### {decision_id}",
        "",
        "- **statement:** Something this feature decided.",
        "- **owner:** platform-team",
        f"- **status:** `{status}`",
        "- **provenance:** PLAN.md D1",
    ]
    if overridden_from is not None:
        lines.append(f"- **overridden_from:** `{overridden_from}`")
    if signed_off_by is not None:
        lines.append(f"- **signed_off_by:** {signed_off_by}")
    if signed_off_at is not None:
        lines.append(f"- **signed_off_at:** {signed_off_at}")
    return "\n".join(lines) + "\n"


class TestOverrideSignoff(unittest.TestCase):

    def test_unsigned_override_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(status="overridden-pending-signoff"),
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("D1" in e and "override" in e for e in errs),
            f"expected unsigned-override error; errs={errs}",
        )

    def test_unsigned_override_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(status="overridden-pending-signoff"),
            )
            proc = subprocess.run(
                [sys.executable, "-m", "specfuse.loop.lint_plan", str(feat)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_ratified_from_override_without_signoff_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(
                    status="ratified",
                    overridden_from="overridden-pending-signoff",
                ),
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("D1" in e and "override" in e for e in errs),
            f"expected error for ratified-but-unsigned override; errs={errs}",
        )

    def test_fully_signed_override_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(
                    status="ratified",
                    overridden_from="overridden-pending-signoff",
                    signed_off_by="Jordan Blake",
                    signed_off_at="2026-08-20",
                ),
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "D1" in e and "override" in e.lower()],
            f"expected no override error once fully signed; errs={errs}",
        )

    def test_placeholder_signed_off_by_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(
                    status="ratified",
                    overridden_from="overridden-pending-signoff",
                    signed_off_by="TBD",
                    signed_off_at="2026-08-20",
                ),
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("D1" in e and "placeholder" in e for e in errs),
            f"expected placeholder signed_off_by to be rejected; errs={errs}",
        )

    def test_never_overridden_decision_needs_no_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(status="ratified"),
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "override" in e.lower() or "placeholder" in e],
            f"expected a never-overridden decision to need no provenance; "
            f"errs={errs}",
        )

    def test_feature_with_no_decisions_md_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), decisions_text=None)
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "override" in e.lower() or "placeholder" in e],
            f"expected no registry to mean opt-out; errs={errs}",
        )

    def test_done_feature_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(status="overridden-pending-signoff"),
                plan_status="done",
                wu_status="done",
            )
            errs = lint_plan.lint(feat)
        self.assertFalse(
            [e for e in errs if "override" in e.lower() or "placeholder" in e],
            f"expected done feature to be exempt; errs={errs}",
        )

    def test_error_names_decision_id_and_missing_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(
                Path(tmp),
                decisions_text=_entry(
                    decision_id="D7",
                    status="ratified",
                    overridden_from="overridden-pending-signoff",
                    signed_off_by="Jordan Blake",
                    # signed_off_at omitted
                ),
            )
            errs = lint_plan.lint(feat)
        self.assertTrue(
            any("D7" in e and "signed_off_at" in e for e in errs),
            f"expected error naming D7 and the missing signed_off_at field; "
            f"errs={errs}",
        )


class TestRealTreeCleanUnderThisCheck(unittest.TestCase):

    def test_this_feature_lints_clean(self):
        feat = REPO_ROOT / ".specfuse/features/FEAT-2026-0058-decision-registry"
        fm, _ = lint_plan.read_frontmatter(feat / "PLAN.md")
        errs = lint_plan.check_decision_override_signoff(feat, fm)
        self.assertEqual(errs, [], f"errs={errs}")


if __name__ == "__main__":
    unittest.main()
