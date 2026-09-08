#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The once-per-gate broad run — FEAT-2026-0109/T06.

T04 lets a `.specfuse/verification.yml` gate declare `tier: broad` to opt
itself OUT of the per-attempt (narrow) run. This unit is the other half: the
full `code` gate set runs exactly once, right before the gate's closing
sequence (a `close`/`close-intermediate` unit) is dispatched, and a red run
halts the gate for human review without counting against any work unit.

Harness for the e2e tests mirrors test_lifecycle_integration.py's single-gate
terminal scaffold (implementation WU + close WU, auto-close enabled by
default) with `_run_gate_set` patched instead of `verify` — the same
recording-boundary choice test_tiered_verification_e2e.py makes, so the real
per-attempt tier resolution AND the real gate_broad_run_check hook both run
for real; only subprocess execution is stubbed.
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


# --------------------------------------------------------------------------- #
# Scaffold                                                                     #
# --------------------------------------------------------------------------- #

_GITIGNORE = (
    ".specfuse/.loop.lock\n"
    ".specfuse/.scratch-*\n"
    ".specfuse/scripts/__pycache__/\n"
)

_RETRO_STUB = (
    "# Retrospective\n\n## Gate 1 — close ceremony\n\n"
    "Synthetic feature for the broad-run test.\n\n"
    "## Cost analysis\n\nOn plan.\n\n## Learnings\n\nNone.\n"
)


def _roadmap(feature_id: str, slug: str) -> str:
    return (
        "---\nproject: broad-run-test\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {feature_id} | Broad run test | active | {slug} | — |\n"
        f"\n## {feature_id} — Broad run test\n\nDetail section.\n"
    )


_ARCHIVE_SCAFFOLD = (
    "---\nproject: broad-run-test\n---\n\n# Archived feature details\n\n"
    "<!-- Archived sections appended below -->\n"
)


def scaffold_feature(root: Path, feature_id: str, slug: str, branch: str) -> Path:
    """Single terminal gate: one implementation WU, one close WU (auto-close
    enabled — the default), matching test_lifecycle_integration.py's shape."""
    (root / ".specfuse" / "roadmap.md").write_text(_roadmap(feature_id, slug))
    (root / ".specfuse" / "roadmap-archive.md").write_text(_ARCHIVE_SCAFFOLD)

    fdir = root / ".specfuse" / "features" / f"{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    plan = (
        "---\n"
        f"feature_id: {feature_id}\ntitle: Broad run test\nslug: {slug}\n"
        f"branch: {branch}\nroadmap_goal: exercise the once-per-gate broad run\n"
        "status: active\n---\n\n"
        f"# Plan: {slug}\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {feature_id}/T01\n        file: WU-T01.md\n"
        "        depends_on: []\n"
        f"      - id: {feature_id}/G1-CLOSE\n        file: WU-G1-CLOSE.md\n"
        f"        depends_on: [{feature_id}/T01]\n```\n"
    )
    (fdir / "PLAN.md").write_text(plan)
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {feature_id}/T01\ntype: implementation\n"
        f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"max_attempts: 1\n---\n\n# T01{body}")
    (fdir / "WU-G1-CLOSE.md").write_text(
        f"---\nid: {feature_id}/G1-CLOSE\ntype: close\n"
        f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"---\n\n# G1-CLOSE{body}")

    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".specfuse/.loop.lock" not in existing:
        gitignore.write_text(existing + _GITIGNORE)

    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold broad-run fixture"], check=True)
    return fdir


def _fake_dispatch(wu, failure_note, cost_tracking=True):
    if wu.type == "implementation":
        Path("src").mkdir(exist_ok=True)
        Path("src/feature.py").write_text("VALUE = 1\n")
        return ("```result\nstatus: complete\n"
                "files_changed:\n  - src/feature.py\n```\n")
    # Auto-close is expected to take the close WU before it ever reaches
    # dispatch; a stub result here is only a safety net.
    return "```result\nstatus: complete\n```\n"


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


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


class _CwdRestoringTestCase(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)


class _BroadRunTestCase(_CwdRestoringTestCase):

    def setUp(self):
        super().setUp()
        self._patches = []

    def tearDown(self):
        for name, original in self._patches:
            setattr(loop, name, original)
        super().tearDown()

    def _patch(self, name: str, replacement):
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    def _stub_agent(self, run_gate_set):
        self._patch("dispatch", _fake_dispatch)
        self._patch("_run_gate_set", run_gate_set)
        self._patch(
            "run_judge_session",
            lambda prompt, *, timeout=None: (
                "```result\nverdict: met\n```", None),
        )

    def _recording_gate_set_runner(self, failing_gate: "str | None" = None):
        calls = []

        def recording(gate_set, feature_dir, _capture_returncodes=None):
            calls.append(list(gate_set))
            return [
                {"name": g["name"],
                 "ok": g["name"] != failing_gate,
                 "report": (f"### {g['name']}: PASS\n```\n$ {g['command']}\n```"
                            if g["name"] != failing_gate else
                            f"### {g['name']}: FAIL\n```\n$ {g['command']}\n"
                            f"boom\n```")}
                for g in gate_set
            ]

        return calls, recording


# --------------------------------------------------------------------------- #
# Ordering + once-per-gate                                                    #
# --------------------------------------------------------------------------- #

class TestBroadSetRunsBeforeClose(_BroadRunTestCase):

    def test_broad_set_runs_before_the_closing_sequence(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: tests\n    command: \"true\"\n"
                "  - name: security\n    command: \"true\"\n    tier: broad\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            scaffold_feature(root, "FEAT-2026-8401", "broad-order",
                              "feat/broad-order")

            calls, recording = self._recording_gate_set_runner()
            self._stub_agent(recording)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            # Exactly one call ran the full (per-gate-only-inclusive) set.
            full_set_calls = [c for c in calls
                               if {g["name"] for g in c} == {"tests", "security"}]
            self.assertEqual(
                len(full_set_calls), 1,
                "the per-gate-only ('tier: broad') gate must run exactly "
                "once, on the once-per-gate broad pass")

            narrow_calls = [c for c in calls
                            if {g["name"] for g in c} == {"tests"}]
            self.assertTrue(narrow_calls, "the implementation WU's own "
                            "per-attempt (narrow) run must have executed")

            self.assertLess(
                calls.index(narrow_calls[0]), calls.index(full_set_calls[0]),
                "the broad run must be ordered after the per-attempt run and "
                "before the gate's closing sequence completes")

            gate_fm = _read_frontmatter(root / ".specfuse/features/"
                                        "FEAT-2026-8401-broad-order/GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "passed")


# --------------------------------------------------------------------------- #
# Tree-keyed dedup                                                            #
# --------------------------------------------------------------------------- #

class TestBroadRunDedup(_CwdRestoringTestCase):

    def test_broad_run_does_not_repeat_at_an_unchanged_tree(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n  - name: tests\n    command: \"true\"\n"
            )
            fdir = scaffold_feature(root, "FEAT-2026-8402", "dedup-tree",
                                     "feat/dedup-tree")
            gate_file = fdir / "GATE-01.md"
            cfg = loop._miniyaml.parse(
                (root / ".specfuse/verification.yml").read_text())

            calls = []
            orig = loop._run_gate_set

            def counting(gate_set, feature_dir, _capture_returncodes=None):
                calls.append(list(gate_set))
                return orig(gate_set, feature_dir,
                           _capture_returncodes=_capture_returncodes)

            loop._run_gate_set = counting
            try:
                ok1, failing1, ran1 = loop.gate_broad_run_check(
                    gate_file, fdir, cfg)
                self.assertTrue(ok1)
                self.assertTrue(ran1)
                self.assertEqual(len(calls), 1)
                record1 = gate_file.read_text()

                ok2, failing2, ran2 = loop.gate_broad_run_check(
                    gate_file, fdir, cfg)
                self.assertTrue(ok2)
                self.assertFalse(
                    ran2, "a second entry at the same tree (the "
                    "driver-restart case) must not re-run the broad set")
                self.assertEqual(
                    len(calls), 1,
                    "zero further gate-set executions at an unchanged tree")
                self.assertEqual(
                    gate_file.read_text(), record1,
                    "the recorded broad_run: block must be unchanged")
            finally:
                loop._run_gate_set = orig

    def test_a_moved_tree_re_runs_the_broad_set(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n  - name: tests\n    command: \"true\"\n"
            )
            fdir = scaffold_feature(root, "FEAT-2026-8403", "moved-tree",
                                     "feat/moved-tree")
            gate_file = fdir / "GATE-01.md"
            cfg = loop._miniyaml.parse(
                (root / ".specfuse/verification.yml").read_text())

            calls = []
            orig = loop._run_gate_set

            def counting(gate_set, feature_dir, _capture_returncodes=None):
                calls.append(list(gate_set))
                return orig(gate_set, feature_dir,
                           _capture_returncodes=_capture_returncodes)

            loop._run_gate_set = counting
            try:
                loop.gate_broad_run_check(gate_file, fdir, cfg)
                self.assertEqual(len(calls), 1)

                # A real code change between the two entries.
                (root / "src").mkdir(exist_ok=True)
                (root / "src" / "new_file.py").write_text("X = 1\n")
                subprocess.run(["git", "-C", str(root), "add", "."], check=True)
                subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                                "a real change"], check=True)

                ok, failing, ran = loop.gate_broad_run_check(
                    gate_file, fdir, cfg)
                self.assertTrue(ran, "a moved tree must re-run the broad set")
                self.assertEqual(len(calls), 2)
            finally:
                loop._run_gate_set = orig


# --------------------------------------------------------------------------- #
# Red halt                                                                     #
# --------------------------------------------------------------------------- #

class TestRedBroadRunHalts(_BroadRunTestCase):

    def test_a_red_broad_run_halts_the_gate_before_the_close(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: tests\n    command: \"true\"\n"
                "  - name: security\n    command: \"true\"\n    tier: broad\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            fdir = scaffold_feature(root, "FEAT-2026-8404", "red-broad",
                                     "feat/red-broad")

            calls, recording = self._recording_gate_set_runner(
                failing_gate="security")
            self._stub_agent(recording)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "a red broad run must halt the gate")

            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review")

            close_fm = _read_frontmatter(fdir / "WU-G1-CLOSE.md")
            self.assertNotEqual(
                close_fm.get("status"), "done",
                "the close unit must never be dispatched (nor auto-closed) "
                "once the broad run is red")

            events = _read_events(fdir / "events.jsonl")
            escalations = [e for e in events
                          if e.get("event_type") == "human_escalation"
                          and e["payload"].get("reason")
                          == "broad_run_gate_failure"]
            self.assertTrue(escalations, "expected a "
                            "broad_run_gate_failure human_escalation event")
            self.assertIn("security", escalations[0]["payload"]["message"])

    def test_a_red_broad_run_counts_against_no_unit(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: tests\n    command: \"true\"\n"
                "  - name: security\n    command: \"true\"\n    tier: broad\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            fdir = scaffold_feature(root, "FEAT-2026-8405", "red-no-blame",
                                     "feat/red-no-blame")

            calls, recording = self._recording_gate_set_runner(
                failing_gate="security")
            self._stub_agent(recording)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(
                t01_fm.get("attempts"), "1",
                "the implementation unit's own successful attempt is the "
                "only charge — the broad-run halt must add none")

            close_fm = _read_frontmatter(fdir / "WU-G1-CLOSE.md")
            self.assertEqual(
                close_fm.get("attempts", "0"), "0",
                "the close unit was never dispatched, so its attempts must "
                "stay at zero")

            events = _read_events(fdir / "events.jsonl")
            self.assertFalse(
                [e for e in events if e.get("event_type") == "attempt_outcome"
                 and e.get("correlation_id") == f"{fdir.name.split('-', 2)[0]}"
                 "-2026-8405/G1-CLOSE"],
                "no attempt_outcome may be emitted for the halted close unit")
            close_outcomes = [
                e for e in events
                if e.get("event_type") == "attempt_outcome"
                and "G1-CLOSE" in e.get("correlation_id", "")
            ]
            self.assertEqual(
                close_outcomes, [],
                "no unit's attempt_outcome may be emitted for a broad-run halt")


# --------------------------------------------------------------------------- #
# Frontmatter no-reflow write                                                 #
# --------------------------------------------------------------------------- #

class TestBroadRunWriteLeavesFrontmatterAlone(_CwdRestoringTestCase):

    def test_broad_run_write_leaves_other_frontmatter_byte_identical(self):
        with integration_workspace() as root:
            os.chdir(root)
            gate_file = root / "GATE-01.md"
            gate_file.write_text(
                "---\n"
                "gate: 1\n"
                "status: open\n"
                "feature_oracle: \"python3 -m unittest tests.test_x -v -b\"\n"
                "baseline:\n"
                "  sha: abc123\n"
                "  probed_at: '2026-01-01T00:00:00+00:00'\n"
                "  failing: []\n"
                "---\n\n# Gate 1\n"
            )
            before = gate_file.read_text()
            before_lines = [
                ln for ln in before.splitlines()
                if ln.startswith("feature_oracle:") or ln.startswith("  sha:")
                or ln.startswith("  probed_at:") or ln.startswith("baseline:")
            ]

            loop.write_gate_broad_run(
                gate_file, "abc:def", "2026-01-02T00:00:00+00:00", True, [])

            after = gate_file.read_text()
            after_lines = [
                ln for ln in after.splitlines()
                if ln.startswith("feature_oracle:") or ln.startswith("  sha:")
                or ln.startswith("  probed_at:") or ln.startswith("baseline:")
            ]
            self.assertEqual(
                before_lines, after_lines,
                "feature_oracle and baseline: lines must survive the "
                "broad_run: write byte-identical")
            self.assertIn("broad_run:", after)


if __name__ == "__main__":
    unittest.main()
