#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""End-to-end tracer bullet for re-plan-after-two-failures (FEAT-2026-0104/T01).

`run()`'s `units = [load_wu(feature_dir, ref) for ref in gate.refs]` snapshots
every unit's body once, before the `while True:` dispatch loop starts, and
never calls `load_wu` again — so a unit whose body is rewritten mid-gate (a
re-plan turn) is invisible to the rest of the gate unless something re-reads
it. This test drives a real `loop.run()` against a synthetic single-WU feature
in a temp git repo, stubbing only the `claude -p` boundary (`loop.dispatch` /
`loop.verify`, same seam as `tests/test_lifecycle_integration.py`), and proves
the reload point end to end:

- the unit's second-to-last permitted attempt fails, the re-plan tracer
  trigger fires (opt-in via `replan_stub_trigger: true`, inert for every
  other unit in the suite), and the body dispatched on the LAST attempt
  differs from the one the failing attempt received;
- the re-planned unit's last attempt then PASSES, and the unit reaches
  `status: done` with the gate running to completion (not stranded) — the
  reconciliation the first (reverted) attempt at this WU got wrong: it
  reloaded the object but left the gate's own `units` list pointing at the
  stale one, so a passed unit was reported "never became ready".
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_FEATURE_ID = "FEAT-TEST-0104"
_SLUG = "replan-fixture"
_BRANCH = f"feat/{_FEATURE_ID}-{_SLUG}"
_ORIGINAL_BODY_MARKER = "ORIGINAL BODY — the pre-replan prompt.\n"


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


def _scaffold(root: Path) -> Path:
    """A single-gate, single-WU feature: no close WU, so the reload's effect
    on `ready()`/`stranded` is exercised as directly as possible."""
    fdir = root / ".specfuse" / "features" / f"{_FEATURE_ID}-{_SLUG}"
    fdir.mkdir(parents=True)
    (root / ".specfuse" / "roadmap.md").write_text(
        "---\nproject: replan-fixture\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {_FEATURE_ID} | Replan fixture | active | {_SLUG} | — |\n"
    )
    (fdir / "PLAN.md").write_text(
        "---\n"
        f"feature_id: {_FEATURE_ID}\n"
        "title: Replan fixture\n"
        f"slug: {_SLUG}\n"
        f"branch: {_BRANCH}\n"
        "roadmap_goal: exercise the replan reload path end to end\n"
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
        "max_attempts: 3\nreplan_stub_trigger: true\n"
        f"---\n\n# T01\n\n{_ORIGINAL_BODY_MARKER}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold replan fixture"], check=True)
    return fdir


class ReplanEndToEndTest(unittest.TestCase):
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

    def test_replan_reload_reaches_done_with_a_rewritten_body(self):
        dispatched_bodies: list[str] = []

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            dispatched_bodies.append(wu.body)
            return "```result\nstatus: complete\n```\n"

        verify_calls = {"n": 0}

        def fake_verify(wu, feature_dir, gate_file=None):
            verify_calls["n"] += 1
            # max_attempts=3: attempts 1 and 2 fail; the second failure (the
            # unit's second-to-last permitted attempt) fires the re-plan
            # tracer trigger, so attempt 3 dispatches a rewritten body and
            # passes.
            if verify_calls["n"] < 3:
                return False, "synthetic failure for the replan tracer test"
            return True, "(stub)"

        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold(root)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0,
                             "the gate must run to completion, not halt")
            self.assertEqual(verify_calls["n"], 3,
                             "expected exactly 3 attempts (max_attempts=3)")
            self.assertEqual(len(dispatched_bodies), 3)

            # The first two attempts (before any re-plan fired) saw the
            # identical, un-replanned body.
            self.assertEqual(
                dispatched_bodies[0], dispatched_bodies[1],
                "the first two attempts must dispatch the same body — the "
                "re-plan trigger only fires AFTER the second attempt fails")
            self.assertIn(_ORIGINAL_BODY_MARKER.strip(), dispatched_bodies[1])

            # AC: the next dispatch (the last permitted attempt) receives a
            # body that DIFFERS from the one the prior (second-to-last)
            # attempt received — asserted on the dispatched prompt itself,
            # not the file on disk.
            self.assertNotEqual(
                dispatched_bodies[1], dispatched_bodies[2],
                "the last attempt must dispatch the re-planned body, not the "
                "one the failing second-to-last attempt received")

            # The re-planned unit that then passed reaches `done`.
            wu_fm = _read_frontmatter(feature_dir / "WU-T01.md")
            self.assertEqual(
                wu_fm.get("status"), "done",
                "a re-planned unit that then passes must reach status: done")

            # The gate ran to completion — not stranded by a reload that left
            # the gate's bookkeeping pointing at the stale (pre-replan) unit.
            gate_fm = _read_frontmatter(feature_dir / "GATE-01.md")
            self.assertEqual(
                gate_fm.get("status"), "awaiting_review",
                "the gate must reach its normal end-of-gate state, not be "
                "reported as having stranded work units")

            # The rewritten body landed on disk too (the reload's source),
            # even though the assertions above are keyed to the dispatched
            # prompt, per the WU's own instruction not to assert on the file.
            on_disk_body = (feature_dir / "WU-T01.md").read_text()
            self.assertIn("re-planned after a failed attempt", on_disk_body)


if __name__ == "__main__":
    unittest.main()
