#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Six-part spin-out brief wired end to end — FEAT-2026-0104/T06.

Today the attempt-exhaustion halt prints one measured line and the
`human_escalation` payload carries `reason`/`attempts`/`attempts_usage` and
nothing a person can read. This is the gate's tracer bullet: a real
`loop.run()` driven to attempt exhaustion prints a six-part brief that
`escalation.validate_escalation_body` accepts, and the SAME text rides on the
`human_escalation` event's `message` field.

Harness reused from tests/test_lazy_baseline_e2e.py: a real git working tree,
a scaffolded feature, `loop.dispatch`/`loop.verify`/`loop.probe_baseline`
patched at module level, then `loop.run()`.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from specfuse.loop import escalation
from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()


def write_feature(root: Path, feature_id: str, slug: str, branch: str,
                   wus: list) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = [(wu_id, "implementation", extra) for wu_id, extra in wus] + [
        (f"{feature_id}/G1-RETRO", "retrospective", ""),
        (f"{feature_id}/G1-LESSONS", "lessons", ""),
        (f"{feature_id}/G1-DOCS", "docs", ""),
        (f"{feature_id}/G1-PLAN", "plan-next", ""),
    ]

    plan_wu_rows = []
    for i, (wu_id, _wu_type, _extra) in enumerate(all_wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i - 1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Spin-out brief fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the attempt-exhaustion spin-out brief
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
    for wu_id, wu_type, extra in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\n"
            f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
            f"{extra}---\n\n# {tnn}{body}"
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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


class SpinoutBriefEndToEnd(unittest.TestCase):

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

    def test_run_prints_a_conforming_brief_and_carries_it_on_the_event(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-8961", "spinout-brief",
                "feat/spinout-brief", [
                    ("FEAT-2026-8961/T01", "max_attempts: 3\n"),
                ])

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

            self.assertEqual(
                escalation.validate_escalation_body(stdout), [],
                "the printed brief must satisfy the escalation contract",
            )
            self.assertIn(
                "<!-- specfuse:escalation id=FEAT-2026-8961/T01 -->", stdout,
                "the marker's correlation id must be the WU id",
            )

            events = _read_events(fdir / "events.jsonl")
            escalations = [
                e for e in events
                if e["event_type"] == "human_escalation"
                and e["payload"].get("reason") == "spinning_detected"
            ]
            self.assertEqual(len(escalations), 1)
            message = escalations[0]["payload"].get("message", "")
            self.assertEqual(
                escalation.validate_escalation_body(message), [],
                "the event's carried brief must also satisfy the contract",
            )
            self.assertIn(message, stdout,
                           "the event must carry the SAME brief the run printed")

            self.assertIn(
                "re-plan fired", message.lower(),
                "part 1 must state that the automatic re-plan fired, since "
                "max_attempts=3 makes it eligible",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
