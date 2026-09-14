#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""PROGRESS.md wired end to end — FEAT-2026-0106/T01.

`parse_result_block` already returns the agent's entire RESULT block,
`summary` included, on every attempt with well-formed output, and nothing
persisted it on the pass path. This is the gate's tracer bullet: a real
`loop.run()` driven through a gate of two units writes one `PROGRESS.md`
entry per dispatched unit, in dispatch order, and an attempt whose RESULT
block never parses still leaves a note.

Harness reused from tests/test_spinout_brief_end_to_end.py: a real git
working tree, a scaffolded feature, `loop.dispatch`/`loop.verify` patched at
module level, then `loop.run()`.
"""

from __future__ import annotations

import io
import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()


def write_feature(root: Path, feature_id: str, slug: str, branch: str,
                   wu_ids: list) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    plan_wu_rows = []
    for i, wu_id in enumerate(wu_ids):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{wu_ids[i - 1]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Progress lines fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the PROGRESS.md write path
status: active
---

# Plan: {slug}

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
{chr(10).join(plan_wu_rows)}
```
"""
    (fdir / "PLAN.md").write_text(plan)
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id in wu_ids:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: implementation\n"
            f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
            f"max_attempts: 1\n---\n\n# {tnn}{body}"
        )
    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".specfuse/.loop.lock" not in existing:
        gitignore.write_text(existing + ".specfuse/.loop.lock\n"
                             ".specfuse/.scratch-*\n"
                             ".specfuse/scripts/__pycache__/\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


class ProgressLinesEndToEndTest(unittest.TestCase):

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

    def test_one_progress_entry_per_dispatched_unit_in_dispatch_order(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-9412", "progress-lines",
                "feat/progress-lines",
                ["FEAT-2026-9412/T01", "FEAT-2026-9412/T02"],
            )

            summaries = {
                "FEAT-2026-9412/T01": "wired the first half",
                "FEAT-2026-9412/T02": None,  # no RESULT block at all
            }

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                summary = summaries[wu.wu_id]
                if summary is None:
                    return "no result block here, agent forgot the contract\n"
                return f"```result\nstatus: complete\nsummary: {summary}\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "OK"))

            captured = io.StringIO()
            with redirect_stdout(captured):
                rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 0, captured.getvalue())

            progress_path = fdir / "PROGRESS.md"
            self.assertTrue(progress_path.is_file(),
                            "PROGRESS.md must exist after the run")
            entries = [line for line in progress_path.read_text().splitlines()
                       if line.strip()]
            self.assertEqual(
                len(entries), 2,
                f"expected one entry per dispatched unit, got: {entries}",
            )
            self.assertIn("FEAT-2026-9412/T01", entries[0])
            self.assertIn("wired the first half", entries[0])
            self.assertIn("FEAT-2026-9412/T02", entries[1])
            self.assertNotIn("FEAT-2026-9412/T01", entries[1])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
