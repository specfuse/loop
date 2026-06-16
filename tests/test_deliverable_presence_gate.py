#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Deliverable-presence gate (FEAT-2026-0022/T02).

Before the driver accepts a WU's pass, every path the WU declared in
``produces:`` must exist on disk and be non-empty (``test -s`` semantics:
``Path(p).exists()`` and ``Path(p).stat().st_size > 0``). An absent or
zero-length declared deliverable refuses the pass — the attempt records
``deliverable_missing``, the squash is rolled back, and MAX_ATTEMPTS exhaustion
escalates to ``blocked_human`` via the existing for-else machinery.

This catches the partial-bundle hollow pass (FEAT-2026-0020/T12: SECURITY.md
present, bundled CODE_OF_CONDUCT.md absent), made executable as issue #41
point 3. The opt-out is preserved: a WU with empty ``produces:`` never fires the
gate, so every current WU is unchanged.

The integration tests reuse the stubbed-dispatch harness shape from
``test_empty_files_escalation``: a real git working tree, a scaffolded feature,
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

    `wus` is a list of (wu_id, type, status, produces) tuples for the
    substantive WUs, where `produces` is a list of declared paths (possibly
    empty); the four closing-sequence WUs are appended so the structure is
    well-formed.
    """
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = list(wus) + [
        (f"{feature_id}/G1-RETRO", "retrospective", "pending", []),
        (f"{feature_id}/G1-LESSONS", "lessons", "pending", []),
        (f"{feature_id}/G1-DOCS", "docs", "pending", []),
        (f"{feature_id}/G1-PLAN", "plan-next", "pending", []),
    ]

    plan_wu_rows = []
    for i, (wu_id, _t, _s, _p) in enumerate(all_wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i-1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Deliverable-presence gate fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the deliverable-presence gate
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
    for wu_id, wu_type, wu_status, produces in all_wus:
        tnn = wu_id.split("/")[-1]
        produces_line = (
            f"produces: [{', '.join(json.dumps(p) for p in produces)}]\n"
            if produces else ""
        )
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n{produces_line}---\n\n# {tnn}{body}"
        )
    # Mirror production: init.sh gitignores the driver's runtime artifacts so
    # the lock file never enters a squash and masks a guard. events.jsonl is
    # intentionally NOT ignored — it is tracked driver state stripped by name.
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


def _make_wu(produces: list, wu_type: str = "implementation",
             wu_id: str = "FEAT-2026-0022/T02",
             wu_file: str = "WU-T02.md") -> "loop.WorkUnit":
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
        produces=produces,
    )


class TestHelperUnit(unittest.TestCase):
    """Direct unit tests of assert_declared_deliverables."""

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        # integration_workspace() removes the temp dir on exit; restore cwd so a
        # later test's os.getcwd() in setUp does not hit a deleted directory.
        os.chdir(self._cwd)

    def test_empty_produces_opts_out(self):
        """AC2/AC4: an empty produces list returns (True, "") — no gate."""
        ok, summary = loop.assert_declared_deliverables(_make_wu([]))
        self.assertTrue(ok)
        self.assertEqual(summary, "")

    def test_present_nonempty_passes(self):
        """AC2: every declared path present and non-empty → (True, "")."""
        with integration_workspace() as root:
            os.chdir(root)
            (root / "X.md").write_text("content\n")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["X.md"]))
            self.assertTrue(ok)
            self.assertEqual(summary, "")

    def test_absent_path_reported(self):
        """AC2: an absent declared path → (False, summary) naming it as absent."""
        with integration_workspace() as root:
            os.chdir(root)
            ok, summary = loop.assert_declared_deliverables(_make_wu(["GONE.md"]))
            self.assertFalse(ok)
            self.assertIn("GONE.md", summary)
            self.assertIn("absent", summary)

    def test_zero_length_path_reported(self):
        """AC2/AC6: a zero-length declared path is treated as missing (empty)."""
        with integration_workspace() as root:
            os.chdir(root)
            (root / "EMPTY.md").write_text("")
            ok, summary = loop.assert_declared_deliverables(_make_wu(["EMPTY.md"]))
            self.assertFalse(ok)
            self.assertIn("EMPTY.md", summary)
            self.assertIn("empty", summary)

    def test_first_offender_named(self):
        """AC5: the partial bundle names the FIRST offending path."""
        with integration_workspace() as root:
            os.chdir(root)
            (root / "SECURITY.md").write_text("present\n")
            ok, summary = loop.assert_declared_deliverables(
                _make_wu(["SECURITY.md", "CODE_OF_CONDUCT.md"]))
            self.assertFalse(ok)
            self.assertIn("CODE_OF_CONDUCT.md", summary)


class TestDeliverablePresenceGate(unittest.TestCase):
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

    def _outcomes(self, events_path: Path, wu_id: str) -> list:
        return [e["payload"]["outcome"] for e in _read_events(events_path)
                if e["event_type"] == "attempt_outcome"
                and e["correlation_id"] == wu_id]

    def test_declared_deliverable_absent_blocks(self):
        """AC1: an implementation WU declaring produces: ["DELIVERABLE.md"] that
        reports complete without creating the file does NOT reach done — it
        records deliverable_missing and escalates to blocked_human after
        MAX_ATTEMPTS. Fails on HEAD (no gate exists; the WU reaches done)."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0022", "deliv-absent",
                                  "feat/deliv-absent", [
                                      ("FEAT-2026-0022/T02", "implementation",
                                       "pending", ["DELIVERABLE.md"]),
                                  ])

            # complete RESULT, but DELIVERABLE.md is never created.
            self._patch("dispatch", lambda wu, fn, ct=True:
                        "```result\nstatus: complete\n```\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "missing-deliverable WU must escalate")

            fdir = root / ".specfuse/features/FEAT-2026-0022-deliv-absent"
            t02_fm = _read_frontmatter(fdir / "WU-T02.md")
            self.assertNotEqual(t02_fm.get("status"), "done",
                                "WU with an absent declared deliverable must "
                                "NOT reach done")
            self.assertEqual(t02_fm.get("status"), "blocked_human")

            outcomes = self._outcomes(fdir / "events.jsonl", "FEAT-2026-0022/T02")
            self.assertIn("deliverable_missing", outcomes)
            self.assertNotIn("passed", outcomes)

    def test_no_produces_passes_unchanged(self):
        """AC4: a WU with no produces: declared is unaffected by the gate — it
        reaches done on a real deliverable, exactly as before."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0025", "no-produces",
                                  "feat/no-produces", [
                                      ("FEAT-2026-0025/T02", "implementation",
                                       "pending", []),
                                  ])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T02"):
                    Path("src").mkdir(exist_ok=True)
                    Path("src/feature.py").write_text("VALUE = 1\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/feature.py\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            fdir = root / ".specfuse/features/FEAT-2026-0025-no-produces"
            t02_fm = _read_frontmatter(fdir / "WU-T02.md")
            self.assertEqual(t02_fm.get("status"), "done",
                             "undeclared-produces WU must be unaffected")

            outcomes = self._outcomes(fdir / "events.jsonl", "FEAT-2026-0025/T02")
            self.assertIn("passed", outcomes)
            self.assertNotIn("deliverable_missing", outcomes)

    def test_partial_bundle_blocks(self):
        """AC5: a WU declaring two deliverables that creates only one records
        deliverable_missing naming the absent one and does not reach done.
        (The FEAT-2026-0020/T12 partial-bundle shape.)"""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0026", "partial-bundle",
                                  "feat/partial-bundle", [
                                      ("FEAT-2026-0026/T02", "implementation",
                                       "pending",
                                       ["SECURITY.md", "CODE_OF_CONDUCT.md"]),
                                  ])

            # Only SECURITY.md is written; CODE_OF_CONDUCT.md is omitted.
            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T02"):
                    Path("SECURITY.md").write_text("policy\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - SECURITY.md\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            fdir = root / ".specfuse/features/FEAT-2026-0026-partial-bundle"
            t02_fm = _read_frontmatter(fdir / "WU-T02.md")
            self.assertNotEqual(t02_fm.get("status"), "done")

            events = _read_events(fdir / "events.jsonl")
            missing_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["correlation_id"] == "FEAT-2026-0026/T02"
                and e["payload"]["outcome"] == "deliverable_missing"
            ]
            self.assertTrue(missing_events, "expected a deliverable_missing event")
            self.assertIn(
                "CODE_OF_CONDUCT.md",
                missing_events[0]["payload"].get("summary", ""),
            )

    def test_empty_deliverable_blocks(self):
        """AC6: a declared path created but zero-length records
        deliverable_missing (an empty deliverable is a hollow deliverable)."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0027", "empty-deliv",
                                  "feat/empty-deliv", [
                                      ("FEAT-2026-0027/T02", "implementation",
                                       "pending", ["REPORT.md"]),
                                  ])

            # REPORT.md is created but left zero-length.
            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T02"):
                    Path("REPORT.md").write_text("")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - REPORT.md\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            fdir = root / ".specfuse/features/FEAT-2026-0027-empty-deliv"
            t02_fm = _read_frontmatter(fdir / "WU-T02.md")
            self.assertNotEqual(t02_fm.get("status"), "done")

            outcomes = self._outcomes(fdir / "events.jsonl", "FEAT-2026-0027/T02")
            self.assertIn("deliverable_missing", outcomes)

    def test_all_deliverables_present_passes(self):
        """AC7: a WU declaring produces: ["X.md"] that creates a non-empty X.md
        reaches done and records passed — the gate does not over-fire."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-0028", "green-path",
                                  "feat/green-path", [
                                      ("FEAT-2026-0028/T02", "implementation",
                                       "pending", ["X.md"]),
                                  ])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T02"):
                    Path("X.md").write_text("real content\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - X.md\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            fdir = root / ".specfuse/features/FEAT-2026-0028-green-path"
            t02_fm = _read_frontmatter(fdir / "WU-T02.md")
            self.assertEqual(t02_fm.get("status"), "done",
                             "WU with all deliverables present must reach done")

            outcomes = self._outcomes(fdir / "events.jsonl", "FEAT-2026-0028/T02")
            self.assertIn("passed", outcomes)
            self.assertNotIn("deliverable_missing", outcomes)


if __name__ == "__main__":
    unittest.main()
