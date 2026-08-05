#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The `prep:` fail-fast halt, observed against a real failing entry (#758).

FEAT-2026-0057 shipped `prep:` — a `verification.yml` set that runs **before
dispatch**, fail-fast: the first non-zero exit halts outright and no session
runs. Its unit-level half was tested (`execute_unit_attempt` returns
`"prep_halted"` and `dispatch_fn` is never called), but the operator-facing
half in `run()` had never executed against a real failing entry: the tree
reset, the `blocked_human` flip, the `attempt_outcome` carrying `halt_class`,
the `human_escalation`, the bookkeeping commit, and the `PREP HALT` line.

No work unit in this repository declares `prep:`, so nothing exercised it.

That surface is the entire value of the key. `prep` exists for environment
setup whose failure is a **setup problem, not a verdict** — the motivating case
was a stale consumer clone that cost a full close cycle because
`git reset --hard origin/main` lived in agent memory rather than in anything
enforced. What the operator sees when prep fails is the deliverable.

These tests drive the real `loop.run()` against a real git repo with a `prep`
set whose first entry exits non-zero, stubbing only the agent boundary — and
assert every condition #758 named, including that no session was spawned.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

from specfuse.loop.prerun import PREP_HALT_CLASS  # noqa: E402

_BODY = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
         "**Do not touch.** test\n\n**Verification.** test\n\n"
         "**Escalation triggers.** test\n")

_GITIGNORE = "\n.specfuse/.loop.lock\nwork/\n"

_ROADMAP = """# Roadmap

| Feature ID     | Title | Status | Folder | Detail |
|----------------|-------|--------|--------|--------|
| FEAT-2026-9500 | Prep halt fixture | active | — | — |

## Notes
"""


def _scaffold_prep_feature(root: Path, *, prep_value: str) -> Path:
    """A single-gate feature whose only substantive WU declares `prep:`."""
    (root / ".specfuse" / "roadmap.md").write_text(_ROADMAP)
    (root / ".specfuse" / "roadmap-archive.md").write_text("# Archive\n")

    fdir = root / ".specfuse" / "features" / "FEAT-2026-9500-prep-halt"
    fdir.mkdir(parents=True)

    (fdir / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9500\n"
        "title: Prep halt fixture\n"
        "slug: prep-halt\n"
        "branch: feat/FEAT-2026-9500-prep-halt\n"
        "roadmap_goal: observe the prep fail-fast halt\n"
        "status: active\n"
        "---\n\n"
        "# Plan: prep-halt\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9500/T01\n"
        "        file: WU-T01.md\n"
        "        depends_on: []\n"
        "      - id: FEAT-2026-9500/G1-CLOSE\n"
        "        file: WU-G1-CLOSE.md\n"
        "        depends_on: [FEAT-2026-9500/T01]\n"
        "```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        "---\nid: FEAT-2026-9500/T01\ntype: implementation\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"prep: {prep_value}\n"
        "---\n\n# T01" + _BODY)
    (fdir / "WU-G1-CLOSE.md").write_text(
        "---\nid: FEAT-2026-9500/G1-CLOSE\ntype: close\n"
        "model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        "---\n\n# G1-CLOSE" + _BODY)

    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    gitignore.write_text(existing + _GITIGNORE)

    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "prep fixture"],
                   check=True)
    subprocess.run(["git", "-C", str(root), "checkout", "-q", "-b",
                    "feat/FEAT-2026-9500-prep-halt"], check=True)
    return fdir


def _write_verification_with_prep(root: Path) -> None:
    """A `prep` set whose FIRST entry fails and whose second must never run.

    The second entry writes a sentinel file. Its absence after the run is the
    proof that fail-fast actually stopped at the first non-zero exit rather
    than running the set and ANDing the results.
    """
    (root / ".specfuse" / "verification.yml").write_text(
        "code:\n  - name: noop\n    command: \"true\"\n"
        "doc:\n  - name: noop\n    command: \"true\"\n"
        "plannext:\n  - name: noop\n    command: \"true\"\n"
        "prep-broken:\n"
        "  - name: failing-first\n"
        "    command: \"exit 3\"\n"
        "  - name: must-not-run\n"
        "    command: \"touch SECOND_PREP_ENTRY_RAN\"\n"
    )


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _read_frontmatter(path: Path) -> dict:
    fm, _ = loop.read_frontmatter(path)
    return fm


class PrepHaltOperatorSurfaceTest(unittest.TestCase):
    """#758 — drive the real run() into the prep-halt branch."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches = []
        self.dispatched = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _stub_agent(self):
        def _recording_dispatch(wu, failure_note, cost_tracking=True):
            # Records every dispatch so "no session was spawned" is an
            # assertion about observed behaviour, not an inference from cost.
            self.dispatched.append(wu.wu_id)
            if wu.type == "implementation":
                # Write a real deliverable: a stub that touches nothing trips
                # the deliverable-presence guard, which would couple these
                # tests to machinery they are not about.
                Path("src").mkdir(exist_ok=True)
                Path("src/feature.py").write_text("VALUE = 1\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - src/feature.py\n```\n")
            return "```result\nstatus: complete\n```\n"
        self._patch("dispatch", _recording_dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

    def test_failing_prep_halts_before_dispatch_with_the_full_operator_surface(self):
        with integration_workspace() as root:
            os.chdir(root)
            # Written BEFORE the scaffold so its own commit carries it;
            # the driver refuses to start on an uncommitted feature folder.
            _write_verification_with_prep(root)
            fdir = _scaffold_prep_feature(root, prep_value="[prep-broken]")
            self._stub_agent()

            loop.run(None, dry_run=False, no_baseline_probe=True)

            # (4) No session was spawned — the whole point of a PRE-dispatch halt.
            self.assertNotIn(
                "FEAT-2026-9500/T01", self.dispatched,
                "a failing prep must halt BEFORE the agent session is spawned")

            # (5) Fail-fast: the second prep entry never ran.
            self.assertFalse(
                (root / "SECOND_PREP_ENTRY_RAN").exists(),
                "prep must stop at the first non-zero exit, not run the whole "
                "set and AND the results")

            # (1) The work unit is parked for a human.
            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(
                wu_fm.get("status"), "blocked_human",
                "a prep failure is a setup problem the operator must fix")

            events = _read_events(fdir / "events.jsonl")

            # (2) attempt_outcome carries the outcome and the halt class.
            outcomes = [e for e in events
                        if e.get("event_type") == "attempt_outcome"
                        and e.get("payload", {}).get("outcome") == "prep_halted"]
            self.assertTrue(
                outcomes, "expected an attempt_outcome with outcome=prep_halted; "
                          f"saw {[e.get('payload', {}).get('outcome') for e in events if e.get('event_type') == 'attempt_outcome']}")
            self.assertEqual(
                outcomes[0]["payload"].get("halt_class"), PREP_HALT_CLASS,
                "the halt class distinguishes a setup failure from a verdict")

            # (3) human_escalation names the reason.
            escalations = [e for e in events
                           if e.get("event_type") == "human_escalation"
                           and e.get("payload", {}).get("reason") == "prep_halted"]
            self.assertTrue(
                escalations,
                "expected a human_escalation with reason=prep_halted; saw "
                f"{[e.get('payload', {}).get('reason') for e in events if e.get('event_type') == 'human_escalation']}")

    def test_a_wu_declaring_no_prep_is_unaffected(self):
        """The opt-in guarantee: the halt path must not fire on the common case."""
        with integration_workspace() as root:
            os.chdir(root)
            # Written BEFORE the scaffold so its own commit carries it;
            # the driver refuses to start on an uncommitted feature folder.
            _write_verification_with_prep(root)
            fdir = _scaffold_prep_feature(root, prep_value="[]")
            self._stub_agent()

            loop.run(None, dry_run=False, no_baseline_probe=True)

            self.assertIn(
                "FEAT-2026-9500/T01", self.dispatched,
                "a work unit declaring no prep must dispatch normally")
            events = _read_events(fdir / "events.jsonl")
            self.assertEqual(
                [e for e in events
                 if e.get("payload", {}).get("outcome") == "prep_halted"], [],
                "no prep declared means no prep halt")
            self.assertFalse((root / "SECOND_PREP_ENTRY_RAN").exists())


if __name__ == "__main__":
    unittest.main()
