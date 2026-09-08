#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Lazy baseline attribution — FEAT-2026-0109/T01.

The gate-entry `code`-set probe (FEAT-2026-0051/T01) is gone: entering a gate
no longer runs the `code` set before dispatching its first unit. Instead, the
first time a unit's own verification fails, the driver runs `probe_baseline`
against the post-reset tree (`attribute_failure_to_baseline`) to decide
whether the failure pre-existed the unit's own work — a pre-existing failure
escalates `preexisting_gate_failure` and is not counted against the unit's
attempts; a genuine failure counts normally. Attribution is bounded to once
per gate via `gate_baseline_check`'s existing tree-sha dedup.

Harness reused from tests/test_baseline_probe.py: a real git working tree, a
scaffolded feature, `loop.dispatch`/`loop.verify`/`loop.probe_baseline`/
`loop._run_gate_set` patched at module level, then `loop.run()`.
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


def write_feature(root: Path, feature_id: str, slug: str, branch: str,
                   wus: list) -> Path:
    """Scaffold a feature folder with PLAN.md, GATE-01.md, and per-WU files.

    *wus* is a list of (wu_id, extra_frontmatter_lines) tuples for the
    substantive units; the closing sequence (retro/lessons/docs/plan-next) is
    appended automatically so `ready()` never sees an unmet cross-gate dep.
    """
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
title: Lazy baseline attribution fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise lazy failure-triggered baseline attribution
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


class LazyBaselineIntegration(unittest.TestCase):
    """End-to-end: drive loop.run() with stubbed dispatch/verify in a temp
    git repo, and an injected gate-set runner that records what it was asked
    to run."""

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

    def test_green_gate_entry_runs_no_gate_set(self):
        """Entering a gate and dispatching its first unit executes no
        `code`-set command — proven by an injected gate-set runner that
        records what it was asked to run, not by a probe_baseline mock."""
        with integration_workspace() as root:
            os.chdir(root)
            write_feature(
                root, "FEAT-2026-8951", "green-entry",
                "feat/green-entry", [("FEAT-2026-8951/T01", "")])

            gate_set_calls = []

            def recording_run_gate_set(gate_set, feature_dir,
                                        _capture_returncodes=None):
                gate_set_calls.append(gate_set)
                raise AssertionError(
                    "no code-set command should run on the green path")

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("_run_gate_set", recording_run_gate_set)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)
            self.assertEqual(gate_set_calls, [],
                              "the injected gate-set runner must never be "
                              "invoked on an all-green gate")

    def test_first_failure_triggers_attribution(self):
        """A unit whose verification fails causes probe_baseline to run once
        against the post-reset tree, and the resulting record names the unit
        that triggered it."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-8952", "first-failure",
                "feat/first-failure", [
                    ("FEAT-2026-8952/T01", "max_attempts: 1\n"),
                ])

            probe_calls = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            def fake_probe(feature_dir, cfg=None):
                probe_calls.append(1)
                return []  # tree was clean — the unit's own failure

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "FAIL"))
            self._patch("probe_baseline", fake_probe)

            loop.run(None, dry_run=False)

            self.assertEqual(len(probe_calls), 1,
                              "attribution must run probe_baseline exactly "
                              "once for the first failure")
            events = _read_events(fdir / "events.jsonl")
            attributions = [e for e in events
                             if e["event_type"] == "baseline_attribution"]
            self.assertEqual(len(attributions), 1)
            self.assertEqual(
                attributions[0]["payload"]["attributed_to"],
                "FEAT-2026-8952/T01",
                "the record must name the unit that triggered attribution")

    def test_preexisting_failure_does_not_consume_an_attempt(self):
        """When attribution finds the tree was already red, the escalation
        is preexisting_gate_failure and the unit's attempts is unchanged."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-8953", "preexisting",
                "feat/preexisting", [
                    ("FEAT-2026-8953/T01", "max_attempts: 3\n"),
                ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "FAIL"))
            self._patch(
                "probe_baseline",
                lambda feature_dir, cfg=None: [{
                    "gate": "tests",
                    "failure_class": "tests",
                    "failure_signature": "test_preexisting_thing",
                }],
            )

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review")

            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(
                wu_fm.get("attempts"), "0",
                "a pre-existing failure must not consume an attempt")

            events = _read_events(fdir / "events.jsonl")
            escalations = [e for e in events
                           if e["event_type"] == "human_escalation"
                           and e["payload"].get("reason")
                           == "preexisting_gate_failure"]
            self.assertEqual(len(escalations), 1)

    def test_genuine_failure_counts_normally(self):
        """When attribution finds the tree was green, the unit's attempt is
        counted and it retries (here: exhausts its budget) as today."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-8954", "genuine-failure",
                "feat/genuine-failure", [
                    ("FEAT-2026-8954/T01", "max_attempts: 1\n"),
                ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "FAIL"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: [])

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(wu_fm.get("status"), "blocked_human")

            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertNotEqual(gate_fm.get("status"), "awaiting_review",
                                 "a genuine failure is a per-unit escalation, "
                                 "not a preexisting_gate_failure gate halt")

            # The frontmatter `attempts` field is reverted by the failed
            # attempt's own `git reset --hard` (a pre-existing, out-of-scope
            # quirk — the exhaustion path never rewrites it after that reset);
            # events.jsonl is the ground truth for "was this attempt counted".
            events = _read_events(fdir / "events.jsonl")
            escalations = [e for e in events
                           if e["event_type"] == "human_escalation"
                           and e["payload"].get("reason") == "spinning_detected"]
            self.assertEqual(len(escalations), 1)
            self.assertEqual(
                escalations[0]["payload"]["attempts"], 1,
                "a genuine failure counts against the unit's attempt budget "
                "exactly as it does today")

    def test_no_baseline_probe_flag_still_honoured(self):
        """--no-baseline-probe suppresses attribution too."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = write_feature(
                root, "FEAT-2026-8955", "killswitch",
                "feat/killswitch", [
                    ("FEAT-2026-8955/T01", "max_attempts: 1\n"),
                ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            def fake_probe(feature_dir, cfg=None):
                raise AssertionError(
                    "probe_baseline must not run with --no-baseline-probe")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "FAIL"))
            self._patch("probe_baseline", fake_probe)

            rc = loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(rc, 1)

            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(wu_fm.get("status"), "blocked_human")

            events = _read_events(fdir / "events.jsonl")
            self.assertEqual(
                [e for e in events if e["event_type"] == "baseline_attribution"],
                [], "--no-baseline-probe must suppress attribution too")
            escalations = [e for e in events
                           if e["event_type"] == "human_escalation"
                           and e["payload"].get("reason") == "spinning_detected"]
            self.assertEqual(len(escalations), 1)
            self.assertEqual(
                escalations[0]["payload"]["attempts"], 1,
                "with attribution suppressed, a failure counts normally "
                "exactly as it does today")


class AttributionDedup(unittest.TestCase):
    """attribute_failure_to_baseline: the once-per-gate bound, in isolation —
    two attributions at the same tree must not re-run probe_baseline."""

    def test_attribution_runs_at_most_once_per_gate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = Path(td) / "GATE-01.md"
            gf.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
            cfg = {"code": [{"name": "tests", "command": "true"}]}

            calls = []
            orig = loop.probe_baseline

            def counting_probe(feature_dir, cfg=None):
                calls.append(1)
                return orig(feature_dir, cfg)

            loop.probe_baseline = counting_probe
            try:
                first, first_fresh = loop.attribute_failure_to_baseline(
                    gf, Path(td), cfg, "same-sha", "FEAT-X/T01")
                second, second_fresh = loop.attribute_failure_to_baseline(
                    gf, Path(td), cfg, "same-sha", "FEAT-X/T02")
            finally:
                loop.probe_baseline = orig

            self.assertEqual(len(calls), 1,
                              "a second failing unit at the same tree must "
                              "not trigger a second probe")
            self.assertTrue(first_fresh)
            self.assertFalse(second_fresh)
            self.assertEqual(first, second)
            self.assertEqual(first, [])


if __name__ == "__main__":
    unittest.main()
