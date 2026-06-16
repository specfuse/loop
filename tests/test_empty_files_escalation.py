#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Empty-files escalation for implementation WUs (FEAT-2026-0022/T03).

A hard, ``produces:``-independent gate on the ``files_touched`` signal: an
``implementation`` WU that reports ``complete`` but whose squash diff names
only its own WU file and/or ``events.jsonl`` (or nothing) produced no
deliverable and MUST NOT reach ``done``. MAX_ATTEMPTS exhaustion escalates to
``blocked_human`` via the existing for-else machinery.

This closes the FEAT-2026-0020/T16 hollow pass (passed ``done`` having touched
zero files, ~$1.48) from the opposite side of ``verify_files_changed``: that
guard opts out when the agent claims nothing; this one fires regardless of
what the agent claimed.

The integration tests reuse the stubbed-dispatch harness shape from
``test_driver_integration``: a real git working tree, a scaffolded feature,
``loop.dispatch``/``loop.verify`` patched at module level, then ``loop.run()``.
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


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list) -> Path:
    """Scaffold a feature folder with PLAN.md, GATE-01.md, and per-WU files.

    `wus` is a list of (wu_id, type, status) tuples for the substantive WUs;
    the four closing-sequence WUs are appended so the structure is well-formed.
    """
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = list(wus) + [
        (f"{feature_id}/G1-RETRO", "retrospective", "pending"),
        (f"{feature_id}/G1-LESSONS", "lessons", "pending"),
        (f"{feature_id}/G1-DOCS", "docs", "pending"),
        (f"{feature_id}/G1-PLAN", "plan-next", "pending"),
    ]

    plan_wu_rows = []
    for i, (wu_id, _wu_type, _wu_status) in enumerate(all_wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i-1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Empty-files escalation fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the empty-files escalation guard
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
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
        )
    # Mirror production: init.sh gitignores the driver's runtime artifacts so
    # the lock file never enters a squash. Without this, the first WU's squash
    # sweeps in `.specfuse/.loop.lock` via `git add -A`, falsely looking like a
    # deliverable and masking the guard. events.jsonl is intentionally NOT
    # ignored — it is tracked driver state the filter strips by name.
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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _make_wu(wu_type: str, wu_id: str = "FEAT-2026-0022/T03",
             wu_file: str = "WU-T03.md") -> "loop.WorkUnit":
    """Construct a minimal WorkUnit for direct helper unit tests."""
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path(wu_file),
        depends_on=[],
        type=wu_type,
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title=wu_id,
        body="",
    )


class TestHelperUnit(unittest.TestCase):
    """Direct unit tests of assert_implementation_touched_files."""

    def test_close_wu_not_subject_to_empty_files_rule(self):
        """AC4: non-implementation types are exempt — closing/planning artifacts
        are gated by assert_closing_deliverables, not this rule."""
        for wu_type in ("close", "plan-next", "retrospective", "lessons",
                        "docs", "close-intermediate"):
            wu = _make_wu(wu_type)
            ok, summary = loop.assert_implementation_touched_files(wu, [])
            self.assertTrue(ok, f"{wu_type} must be exempt from the rule")
            self.assertEqual(summary, "")

    def test_only_wu_file_and_events_strip_to_no_deliverable(self):
        """AC5 (precision): the filter MUST strip the WU's own file and
        events.jsonl. If it did not, deliverables would be non-empty and the
        guard would never fire (escalation trigger 2)."""
        wu = _make_wu("implementation")
        touched = [
            ".specfuse/features/FEAT-2026-0022-x/WU-T03.md",
            ".specfuse/features/FEAT-2026-0022-x/events.jsonl",
        ]
        ok, summary = loop.assert_implementation_touched_files(wu, touched)
        self.assertFalse(ok, "WU-file + events.jsonl only must NOT pass")
        self.assertIn("no deliverable", summary.lower())

    def test_real_deliverable_passes_helper(self):
        wu = _make_wu("implementation")
        touched = [
            ".specfuse/features/FEAT-2026-0022-x/WU-T03.md",
            ".specfuse/features/FEAT-2026-0022-x/events.jsonl",
            ".specfuse/scripts/loop.py",
        ]
        ok, summary = loop.assert_implementation_touched_files(wu, touched)
        self.assertTrue(ok)
        self.assertEqual(summary, "")


class TestEmptyFilesEscalation(unittest.TestCase):
    """End-to-end: drive loop.run() with stubbed dispatch in a temp git repo."""

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

    def test_implementation_zero_files_blocks(self):
        """AC1: an implementation WU that reports complete but writes no file
        does NOT reach done — it records no_deliverable_files and escalates to
        blocked_human after MAX_ATTEMPTS. Fails on HEAD (reaches done today)."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0022", "zero-files",
                                  "feat/zero-files", [
                                      ("FEAT-2026-0022/T03", "implementation",
                                       "pending"),
                                  ])

            # complete RESULT, but the agent writes nothing — the T16 shape.
            def fake_dispatch(wu, failure_note, cost_tracking=True):
                return ("```result\nstatus: complete\n"
                        "summary: did nothing\n```\n")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "zero-deliverable WU must escalate (exit 1)")

            fdir = root / ".specfuse/features/FEAT-2026-0022-zero-files"
            t03_fm = _read_frontmatter(fdir / "WU-T03.md")
            self.assertNotEqual(t03_fm.get("status"), "done",
                                "implementation WU touching zero files must "
                                "NOT reach done")
            self.assertEqual(t03_fm.get("status"), "blocked_human")

            events = _read_events(fdir / "events.jsonl")
            outcomes = [e["payload"]["outcome"] for e in events
                        if e["event_type"] == "attempt_outcome"
                        and e["correlation_id"] == "FEAT-2026-0022/T03"]
            self.assertIn("no_deliverable_files", outcomes)
            self.assertNotIn("passed", outcomes)

    def test_only_wu_file_touched_blocks(self):
        """AC5: the exact T16 shape — diff is solely the WU file + events.jsonl
        (the status flip the driver itself writes) — records
        no_deliverable_files and does not reach done."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0023", "wu-file-only",
                                  "feat/wu-file-only", [
                                      ("FEAT-2026-0023/T03", "implementation",
                                       "pending"),
                                  ])

            # No file write — the only diff at squash time is the driver's own
            # status flip on the WU file plus the events.jsonl append.
            self._patch("dispatch", lambda wu, fn, ct=True:
                        "```result\nstatus: complete\n```\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            fdir = root / ".specfuse/features/FEAT-2026-0023-wu-file-only"
            t03_fm = _read_frontmatter(fdir / "WU-T03.md")
            self.assertNotEqual(t03_fm.get("status"), "done")

            events = _read_events(fdir / "events.jsonl")
            outcomes = [e["payload"]["outcome"] for e in events
                        if e["event_type"] == "attempt_outcome"
                        and e["correlation_id"] == "FEAT-2026-0023/T03"]
            self.assertIn("no_deliverable_files", outcomes)

    def test_implementation_with_real_file_passes(self):
        """AC6: an implementation WU that writes a real source/test file reaches
        done — the guard does not over-fire."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0024", "real-file",
                                  "feat/real-file", [
                                      ("FEAT-2026-0024/T03", "implementation",
                                       "pending"),
                                  ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                if wu.wu_id.endswith("/T03"):
                    # Write a genuine deliverable into the working tree; squash
                    # picks it up via `git add -A`.
                    src = Path("src")
                    src.mkdir(exist_ok=True)
                    (src / "feature.py").write_text("VALUE = 1\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/feature.py\n```\n")
                # Closing WUs write nothing; their own guards will halt the loop
                # after T03 has already committed — that is fine for this test.
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            fdir = root / ".specfuse/features/FEAT-2026-0024-real-file"
            t03_fm = _read_frontmatter(fdir / "WU-T03.md")
            self.assertEqual(t03_fm.get("status"), "done",
                             "implementation WU with a real deliverable must "
                             "reach done")

            events = _read_events(fdir / "events.jsonl")
            t03_outcomes = [e["payload"]["outcome"] for e in events
                            if e["event_type"] == "attempt_outcome"
                            and e["correlation_id"] == "FEAT-2026-0024/T03"]
            self.assertIn("passed", t03_outcomes)
            self.assertNotIn("no_deliverable_files", t03_outcomes)


if __name__ == "__main__":
    unittest.main()
