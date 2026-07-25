#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Pre-flight baseline gate probe — FEAT-2026-0051/T01.

`probe_baseline()` runs the `code` gate set once at gate entry, before any WU
is dispatched. A red result halts the run with `preexisting_gate_failure`
(same mechanics as the per-gate budget brake: set_gate(awaiting_review) ->
human_escalation event -> commit_bookkeeping -> return 1) so zero work units
are dispatched against a failure they did not cause. A green result leaves
dispatch behavior unchanged.

The integration tests reuse the stubbed-dispatch harness shape from
`test_empty_files_escalation`: a real git working tree, a scaffolded feature,
`loop.dispatch`/`loop.verify`/`loop.probe_baseline` patched at module level,
then `loop.run()`.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list, *,
                          gate_status: str = "open") -> Path:
    """Scaffold a feature folder with PLAN.md, GATE-01.md, and per-WU files."""
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
title: Baseline probe fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the pre-flight baseline gate probe
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
        f"---\ngate: 1\nstatus: {gate_status}\n---\n\n# Gate 1\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
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


class TestProbeBaselineHelper(unittest.TestCase):
    """Direct unit tests of probe_baseline() against a stub cfg — no run()."""

    def test_green_baseline_returns_empty_list(self):
        cfg = {"code": [{"name": "tests", "command": "true"}]}
        result = loop.probe_baseline(Path("."), cfg=cfg)
        self.assertEqual(result, [],
                          "all-passing code set must return the empty list, "
                          "not None — a probe that ran and found nothing must "
                          "be distinguishable from a probe that never ran")
        self.assertIsInstance(result, list)

    def test_red_baseline_returns_failing_gate_entries(self):
        cfg = {"code": [{"name": "tests", "command": "false"}]}
        result = loop.probe_baseline(Path("."), cfg=cfg)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["gate"], "tests")
        self.assertIn("failure_class", result[0])
        self.assertIn("failure_signature", result[0])

    def test_only_code_set_is_probed_not_doc(self):
        """A configured-but-failing `doc` gate must not appear in the result —
        the probe measures the `code` set specifically."""
        cfg = {
            "code": [{"name": "tests", "command": "true"}],
            "doc": [{"name": "doc_lint", "command": "false"}],
        }
        result = loop.probe_baseline(Path("."), cfg=cfg)
        self.assertEqual(result, [])


class TestBaselineProbeIntegration(unittest.TestCase):
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

    def test_red_baseline_halts_before_any_dispatch(self):
        """A red probe halts before the frontier loop — dispatch is called
        exactly zero times. Fails on HEAD before this WU's edits (module does
        not yet exist / probe_baseline is absent)."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_minimal_feature(
                root, "FEAT-2026-8801", "red-baseline",
                "feat/red-baseline", [
                    ("FEAT-2026-8801/T01", "implementation", "pending"),
                ])

            dispatch_calls = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                dispatch_calls.append(wu.wu_id)
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            self._patch(
                "probe_baseline",
                lambda feature_dir, cfg=None: [{
                    "gate": "tests",
                    "failure_class": "tests",
                    "failure_signature": "test_something",
                }],
            )

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "red baseline must halt the run (exit 1)")
            self.assertEqual(dispatch_calls, [],
                              "dispatch must be called exactly zero times "
                              "when the baseline probe is red")

            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review")

            events = _read_events(fdir / "events.jsonl")
            escalations = [e for e in events
                           if e["event_type"] == "human_escalation"]
            self.assertEqual(len(escalations), 1)
            self.assertEqual(
                escalations[0]["payload"]["reason"], "preexisting_gate_failure")
            self.assertEqual(escalations[0]["payload"]["gate"], 1)
            self.assertEqual(
                escalations[0]["payload"]["failing_gates"],
                [{"gate": "tests", "failure_class": "tests",
                  "failure_signature": "test_something"}],
            )

            # The status flip must be COMMITTED, not just written to disk — an
            # uncommitted flip silently reverts on the next `git reset --hard`.
            log = subprocess.run(
                ["git", "-C", str(root), "log", "--oneline", "-1"],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertIn("preexisting gate failure", log)
            status = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain"],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertNotIn("GATE-01.md", status,
                              "gate status flip must be committed, not left "
                              "dirty in the working tree")

    def test_green_baseline_dispatches_normally(self):
        """A green probe leaves dispatch behavior byte-identical to today —
        the WU dispatches and reaches done."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_minimal_feature(
                root, "FEAT-2026-8802", "green-baseline",
                "feat/green-baseline", [
                    ("FEAT-2026-8802/T01", "implementation", "pending"),
                ])

            dispatch_calls = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                dispatch_calls.append(wu.wu_id)
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: [])

            loop.run(None, dry_run=False)

            self.assertIn("FEAT-2026-8802/T01", dispatch_calls,
                          "green baseline must not block dispatch")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done")

    def test_probe_skipped_when_dry_run(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(
                root, "FEAT-2026-8803", "dry-run-skip",
                "feat/dry-run-skip", [
                    ("FEAT-2026-8803/T01", "implementation", "pending"),
                ])

            probe_calls = []

            def fake_probe(feature_dir, cfg=None):
                probe_calls.append(feature_dir)
                raise AssertionError("probe_baseline must not run in dry_run")

            self._patch("probe_baseline", fake_probe)

            loop.run(None, dry_run=True)
            self.assertEqual(probe_calls, [],
                              "probe_baseline must be skipped when dry_run is set")

    def test_probe_skipped_when_gate_already_awaiting_review(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(
                root, "FEAT-2026-8804", "already-awaiting",
                "feat/already-awaiting", [
                    ("FEAT-2026-8804/T01", "implementation", "done"),
                ],
                gate_status="awaiting_review",
            )

            probe_calls = []

            def fake_probe(feature_dir, cfg=None):
                probe_calls.append(feature_dir)
                raise AssertionError(
                    "probe_baseline must not run when the gate is already "
                    "awaiting_review")

            self._patch("probe_baseline", fake_probe)
            self._patch("dispatch", lambda wu, fn, ct=True:
                        "```result\nstatus: complete\n```\n")
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)
            self.assertEqual(probe_calls, [],
                              "probe_baseline must be skipped when the gate "
                              "is already awaiting_review")


if __name__ == "__main__":
    unittest.main()
