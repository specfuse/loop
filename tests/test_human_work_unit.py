#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A `type: human` work unit the driver halts on (FEAT-2026-0085/T04).

Sixteen hedged features in the corpus needed a person to reply, click, sign,
or run something interactively, and recorded that as a softened verdict after
the fact. `human` is a work-unit type the driver never dispatches: when one is
ready, the driver prints the six-part operator brief, flips the unit to
`blocked_human`, and halts. The operator performs the step, marks the unit
`done` with `evidence:`, and the run resumes.

These tests drive the real outcome path (`loop.run()`) with a stubbed
dispatcher rather than asserting on `halt_for_human_unit` in isolation: the
property under test is that no session is ever spawned for a `human` unit,
and only the run loop can show that.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import unittest
from pathlib import Path

from specfuse.loop import lint_plan
from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, with_deliverable

loop = load_loop()

_FULL_BODY = (
    "\n\n**Objective.** Reply to the vendor on issue #12 so the contract "
    "question is settled.\n\n"
    "**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
# A `human` unit carries only Objective / Context / Acceptance criteria.
_HUMAN_BODY = (
    "\n\n**Objective.** Reply to the vendor on issue #12 so the contract "
    "question is settled.\n\n"
    "**Context.** The vendor asked which SKU the integration targets; only a "
    "person with the account can answer.\n\n"
    "**Acceptance criteria.** A reply is posted on issue #12 naming the SKU.\n"
)


def _wu_filename(wu_id: str) -> str:
    tail = wu_id.split("/")[-1]
    return "WU-close.md" if tail.endswith("CLOSE") else f"WU-{tail}.md"


def _write_feature(root: Path, feature_id: str, slug: str,
                   human_status: str = "pending",
                   human_extra: str = "") -> Path:
    """Single gate: T01 (`human`) -> T02 (implementation) -> close."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    wu_ids = [f"{feature_id}/T01", f"{feature_id}/T02", f"{feature_id}/G1-CLOSE"]

    rows = []
    for i, wu_id in enumerate(wu_ids):
        dep = f"[{wu_ids[i - 1]}]" if i > 0 else "[]"
        rows.append(f"      - id: {wu_id}\n        file: {_wu_filename(wu_id)}\n"
                    f"        depends_on: {dep}\n")
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: feat/{slug}\nroadmap_goal: test\nstatus: active\n"
        f"auto_close_disabled: true\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n" + "".join(rows) + "```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

    (fdir / "WU-T01.md").write_text(
        f"---\nid: {wu_ids[0]}\ntype: human\nstatus: {human_status}\n"
        f"attempts: 0\n{human_extra}---\n\n# Reply to the vendor{_HUMAN_BODY}"
    )
    (fdir / "WU-T02.md").write_text(
        f"---\nid: {wu_ids[1]}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n---\n\n# {wu_ids[1]}{_FULL_BODY}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {wu_ids[2]}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# {wu_ids[2]}{_FULL_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


def _read_events(fdir: Path) -> list:
    path = fdir / "events.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


class TestHumanWorkUnitHalt(unittest.TestCase):
    """End-to-end: loop.run() with a stubbed dispatcher in a temp git repo."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def test_ready_human_unit_halts_without_dispatch(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9601"
            fdir = _write_feature(root, feature_id, "human-halt")

            dispatched = []

            def fake_dispatch(wu, fn, ct=True):
                dispatched.append(wu.wu_id)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", with_deliverable(fake_dispatch))
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = loop.run(None, dry_run=False)
            output = buf.getvalue()

            self.assertEqual(rc, 1)
            # No session was spawned at all — not for the human unit, and not
            # for the units behind it.
            self.assertEqual(dispatched, [])

            escalations = [
                e for e in _read_events(fdir)
                if e["event_type"] == "human_escalation"
                and e["payload"].get("reason") == loop.HALT_REASON_HUMAN_STEP
            ]
            self.assertEqual(len(escalations), 1, _read_events(fdir))
            self.assertEqual(escalations[0]["correlation_id"],
                             f"{feature_id}/T01")

            for heading in loop.ESCALATION_PART_HEADINGS:
                self.assertIn(heading, output)

            fm, _ = loop.read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(fm["status"], "blocked_human")
            self.assertEqual(int(fm["attempts"]), 0)

    def test_done_human_unit_with_evidence_lets_next_unit_dispatch(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9602"
            fdir = _write_feature(
                root, feature_id, "human-done",
                human_status="done",
                human_extra='evidence: "replied on issue #12"\n',
            )

            units = [loop.load_wu(fdir, ref)
                     for ref in loop.load_graph(fdir)[1][0].refs]
            human_unit = units[0]
            self.assertEqual(human_unit.type, "human")
            self.assertEqual(human_unit.evidence, "replied on issue #12")

            # `ready()` hands back the next unit, not the human one.
            frontier = loop.ready(units, {f"{feature_id}/T01"})
            self.assertEqual([u.wu_id for u in frontier], [f"{feature_id}/T02"])

            dispatched = []

            def fake_dispatch(wu, fn, ct=True):
                dispatched.append(wu.wu_id)
                if wu.type == "close":
                    (fdir / "RETROSPECTIVE.md").write_text(
                        "# Retrospective\n\nNothing generalizes from this gate.\n")
                    loop.write_frontmatter_field(wu.file, "verdict", "met")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", with_deliverable(fake_dispatch))
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                loop.run(None, dry_run=False)

            self.assertIn(f"{feature_id}/T02", dispatched)
            self.assertNotIn(f"{feature_id}/T01", dispatched)


class TestHumanWorkUnitLint(unittest.TestCase):
    """`lint_plan` knows the type, its three sections, and its evidence rule."""

    def test_lint_accepts_human_unit_with_three_sections(self):
        with integration_workspace() as root:
            fdir = _write_feature(root, "FEAT-2026-9603", "human-lint-ok")
            errs = lint_plan.lint(fdir)
            self.assertEqual(errs, [], errs)

    def test_lint_rejects_done_human_without_evidence(self):
        with integration_workspace() as root:
            fdir = _write_feature(root, "FEAT-2026-9604", "human-lint-bad",
                                  human_status="done")
            errs = lint_plan.lint(fdir)
            offending = [e for e in errs if "WU-T01.md" in e and "evidence" in e]
            self.assertEqual(len(offending), 1, errs)

            # Same unit, same status, with evidence: no finding.
            loop.write_frontmatter_field(
                fdir / "WU-T01.md", "evidence", "replied on issue #12")
            self.assertEqual(
                [e for e in lint_plan.lint(fdir)
                 if "WU-T01.md" in e and "evidence" in e],
                [],
            )


if __name__ == "__main__":
    unittest.main()
