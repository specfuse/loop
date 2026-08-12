#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Escalation message for a preexisting_gate_failure halt — FEAT-2026-0051/T03.

T01 halts pre-dispatch on a red baseline; T02 persists it. This WU turns that
minimal halt into a message a non-expert operator can act on without reading
driver source: which gate is red, its exact failure signature, proof (a
`git diff <integration-branch>...HEAD --stat`) that the base tree is
unchanged so no work unit caused it, and the only two v1 options (there is no
waiver yet — that is FEAT-2026-0052).
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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


FAILING_GATES = [{
    "gate": "tests",
    "failure_class": "test_failure",
    "failure_signature": "test_widget_render_fails",
}]


class TestFormatPreexistingGateFailure(unittest.TestCase):
    """format_preexisting_gate_failure: the rendered message, in isolation."""

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_message_names_gate_signature_and_proof(self):
        """Fails on HEAD before this WU's edits (function does not yet exist)."""
        with integration_workspace() as root:
            os.chdir(root)
            subprocess.run(["git", "-C", str(root), "checkout", "-q",
                            "-b", "feat/some-feature"], check=True)
            (root / "unrelated.txt").write_text("noop\n")
            subprocess.run(["git", "-C", str(root), "add", "unrelated.txt"],
                            check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "feature commit"], check=True)

            feat_fm = {"base": "main"}
            message = loop.format_preexisting_gate_failure(
                1, FAILING_GATES, feat_fm)

            self.assertIn("tests", message)
            self.assertIn("test_failure", message)
            self.assertIn("test_widget_render_fails", message)
            self.assertIn("git diff main...HEAD --stat", message)

    def test_states_no_wu_caused_it_and_zero_dispatched(self):
        feat_fm = {"base": "main"}
        message = loop.format_preexisting_gate_failure(1, FAILING_GATES, feat_fm)
        self.assertIn("No work unit caused this failure", message)
        self.assertIn("Zero work units were dispatched", message)

    def test_options_list_has_no_waiver_and_names_0052_as_future_work(self):
        feat_fm = {"base": "main"}
        message = loop.format_preexisting_gate_failure(1, FAILING_GATES, feat_fm)
        self.assertIn("fix", message.lower())
        self.assertIn("defer", message.lower())
        self.assertNotIn("--resume", message)
        self.assertNotIn("waiver.\n", message)  # no waiver instruction as a step
        self.assertIn("FEAT-2026-0052", message)
        self.assertIn("future work", message.lower())
        # No instruction implying a waiver already exists to invoke.
        self.assertNotIn("resume with", message.lower())
        self.assertNotIn("proceed anyway.\n", message.lower())

    def test_degrades_when_diffstat_unavailable(self):
        """A base ref that cannot be resolved by git (typo, unreachable, no
        such branch) must still render the gate/signature and an explicit
        unavailable line — evidence collection must never block the
        message."""
        with integration_workspace() as root:
            os.chdir(root)
            feat_fm = {"base": "does-not-exist-anywhere"}
            message = loop.format_preexisting_gate_failure(1, FAILING_GATES, feat_fm)
            self.assertIn("tests", message)
            self.assertIn("test_widget_render_fails", message)
            self.assertIn("base-tree comparison unavailable", message.lower())


class TestBaselineEvidenceDiffstat(unittest.TestCase):
    """baseline_evidence_diffstat: resolves the base through the existing
    FEAT-2026-0031 configuration mechanism, never a hardcoded 'main'."""

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_uses_configured_non_main_integration_branch(self):
        with integration_workspace() as root:
            os.chdir(root)
            subprocess.run(["git", "-C", str(root), "checkout", "-q",
                            "-b", "integration"], check=True)
            (root / "int-only.txt").write_text("on integration\n")
            subprocess.run(["git", "-C", str(root), "add", "int-only.txt"],
                            check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "integration-only commit"], check=True)
            subprocess.run(["git", "-C", str(root), "checkout", "-q",
                            "-b", "feat/child", "integration"], check=True)
            (root / "feature-file.txt").write_text("feature work\n")
            subprocess.run(["git", "-C", str(root), "add", "feature-file.txt"],
                            check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "feature commit"], check=True)

            feat_fm = {"base": "integration"}
            result = loop.baseline_evidence_diffstat(feat_fm)
            self.assertIsNotNone(result)
            self.assertIn("integration...HEAD", result)
            self.assertIn("feature-file.txt", result)
            self.assertNotIn("int-only.txt", result)

    def test_unresolvable_base_ref_returns_none(self):
        with integration_workspace() as root:
            os.chdir(root)
            result = loop.baseline_evidence_diffstat(
                {"base": "does-not-exist-anywhere"})
            self.assertIsNone(result)


class TestEscalationEventCarriesMessage(unittest.TestCase):
    """The rendered message text is also written into the human_escalation
    event payload, so the audit log carries what the operator saw."""

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

    def _scaffold(self, root: Path, feature_id: str, slug: str,
                   branch: str) -> Path:
        fdir = root / f".specfuse/features/{feature_id}-{slug}"
        fdir.mkdir(parents=True)
        wus = [
            (f"{feature_id}/T01", "implementation", "pending"),
            (f"{feature_id}/G1-RETRO", "retrospective", "pending"),
            (f"{feature_id}/G1-LESSONS", "lessons", "pending"),
            (f"{feature_id}/G1-DOCS", "docs", "pending"),
            (f"{feature_id}/G1-PLAN", "plan-next", "pending"),
        ]
        plan_wu_rows = []
        for i, (wu_id, _t, _s) in enumerate(wus):
            tnn = wu_id.split("/")[-1]
            wu_file = f"WU-{tnn}.md"
            deps = "[]" if i == 0 else f"[{wus[i - 1][0]}]"
            plan_wu_rows.append(
                f"      - id: {wu_id}\n        file: {wu_file}\n        "
                f"depends_on: {deps}"
            )
        plan = f"""---
feature_id: {feature_id}
title: Escalation message fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the preexisting_gate_failure escalation message
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
        for wu_id, wu_type, wu_status in wus:
            tnn = wu_id.split("/")[-1]
            (fdir / f"WU-{tnn}.md").write_text(
                f"---\nid: {wu_id}\ntype: {wu_type}\n"
                f"model: claude-haiku-4-5-20251001\nstatus: {wu_status}\n"
                f"attempts: 0\n---\n\n# {tnn}{body}"
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

    def test_human_escalation_payload_carries_rendered_message(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._scaffold(root, "FEAT-2026-8910", "escalation-message",
                                   "feat/escalation-message")

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: FAILING_GATES)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            events = _read_events(fdir / "events.jsonl")
            escalations = [e for e in events
                           if e["event_type"] == "human_escalation"]
            self.assertEqual(len(escalations), 1)
            message = escalations[0]["payload"]["message"]
            self.assertIn("tests", message)
            self.assertIn("test_widget_render_fails", message)
            self.assertIn("No work unit caused this failure", message)
            self.assertIn("Zero work units were dispatched", message)
            self.assertIn("FEAT-2026-0052", message)


if __name__ == "__main__":
    unittest.main()


class TestResumedGateAttribution(unittest.TestCase):
    """Issue #360 — a RESUMED gate's baseline includes the feature's own work.

    The probe runs before dispatch, so on a fresh gate "these checks were
    already failing before this feature touched any file" is true. On a
    resumed gate — some work units already `done` and committed — it is false,
    and the `git diff base...HEAD` printed as "proof the feature's tree matches
    its integration branch" is the feature's whole changeset, refuting the
    sentence above it.

    Observed on FEAT-2026-0042 gate 1: four units done, the fifth halted, and
    the failing signature named a test T03 had added two commits earlier.
    """

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    _FAILING = [{"gate": "tests", "failure_class": "tests",
                 "failure_signature": "test_added_by_this_feature"}]

    def test_resumed_gate_does_not_blame_the_integration_branch(self):
        msg = loop.format_preexisting_gate_failure(
            1, self._FAILING, {}, done_unit_ids=["FEAT-2026-0042/T01",
                                                 "FEAT-2026-0042/T03"])
        self.assertNotIn("before this feature touched any file", msg)
        self.assertNotIn("No work unit caused this failure", msg)

    def test_resumed_gate_names_the_landed_units(self):
        msg = loop.format_preexisting_gate_failure(
            1, self._FAILING, {}, done_unit_ids=["FEAT-2026-0042/T01",
                                                 "FEAT-2026-0042/T03"])
        self.assertIn("FEAT-2026-0042/T01", msg)
        self.assertIn("FEAT-2026-0042/T03", msg)

    def test_resumed_gate_points_remediation_at_the_branch_not_main(self):
        msg = loop.format_preexisting_gate_failure(
            1, self._FAILING, {}, done_unit_ids=["FEAT-2026-0042/T01"])
        self.assertNotIn(
            "Fix the failing check(s) on the integration branch", msg,
            "a resumed gate's defect lives on the feature branch; sending the "
            "operator to /fix-bug against main is the wrong repair")

    def test_fresh_gate_message_is_unchanged(self):
        """No done units — every original claim is true and must survive."""
        msg = loop.format_preexisting_gate_failure(1, self._FAILING, {})
        self.assertIn("before this feature touched any file", msg)
        self.assertIn("No work unit caused this failure", msg)
        self.assertIn("Fix the failing check(s) on the integration branch", msg)

    def test_fresh_gate_with_empty_done_list_is_still_fresh(self):
        msg = loop.format_preexisting_gate_failure(
            1, self._FAILING, {}, done_unit_ids=[])
        self.assertIn("before this feature touched any file", msg)

    def test_fresh_gate_diffstat_header_does_not_overstate_a_matching_tree(self):
        """Issue #240: a fresh gate almost always has a non-empty diffstat --
        the feature's own plan/scaffold files -- so a header claiming "the
        feature's tree matches its integration branch" is self-refuting the
        moment the diffstat below it lists changed files."""
        with integration_workspace() as root:
            os.chdir(root)
            subprocess.run(["git", "-C", str(root), "checkout", "-q",
                            "-b", "feat/some-feature"], check=True)
            (root / "PLAN.md").write_text("plan scaffold\n")
            subprocess.run(["git", "-C", str(root), "add", "PLAN.md"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "feat: scaffold plan"], check=True)
            msg = loop.format_preexisting_gate_failure(1, self._FAILING, {})

        self.assertNotIn(
            "Proof the feature's tree matches its integration branch", msg,
            "the diffstat below the header lists PLAN.md as changed -- "
            "claiming the tree 'matches' the integration branch while "
            "showing it doesn't is the contradiction issue #240 reports")

    def test_resumed_gate_never_calls_its_diff_proof_of_a_matching_tree(self):
        with integration_workspace() as root:
            os.chdir(root)
            subprocess.run(["git", "-C", str(root), "checkout", "-q",
                            "-b", "feat/resumed"], check=True)
            (root / "landed.txt").write_text("work from a done unit\n")
            subprocess.run(["git", "-C", str(root), "add", "landed.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "feat: a work unit that already landed"], check=True)
            msg = loop.format_preexisting_gate_failure(
                1, self._FAILING, {}, done_unit_ids=["FEAT-2026-0001/T01"])

        self.assertNotIn("Proof the feature's tree matches its integration branch", msg,
                         "the diff shows the feature's own changeset; calling it "
                         "proof of a matching tree is self-refuting")
