#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Terminal state-flip consolidation tests — FEAT-2026-0015/T06.

Covers:
  (a) fire_terminal_flips with met verdict flips gate, roadmap row, archives.
  (b) fire_terminal_flips is idempotent when gate already passed.
  (c) run() does NOT call fire_terminal_flips for met_locally verdict.
  (d) run() reverts PLAN.md→done when close WU has hedged verdict.
  (e) wrap-feature SKILL.md no longer lists gate-flip step instructions.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

REPO_ROOT = Path(__file__).resolve().parent.parent

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _make_repo_with_feature(
    root: Path,
    feature_id: str,
    gate_num: int = 2,
    gate_status: str = "awaiting_review",
    roadmap_row_status: str = "active",
) -> tuple[Path, Path]:
    """Write .specfuse scaffold + feature dir for fire_terminal_flips tests.

    Returns (feature_dir, repo_root).  No git repo needed — fire_terminal_flips
    only does file operations.
    """
    specfuse = root / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    feature_dir = specfuse / "features" / f"{feature_id}-test"
    feature_dir.mkdir(parents=True)

    gate_file = f"GATE-{gate_num:02d}.md"
    wu_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G{gate_num}-CLOSE"

    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nbranch: feat/test\n"
        f"roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n  - gate: {gate_num}\n    file: {gate_file}\n"
        f"    work_units:\n"
        f"      - id: {wu_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{wu_id}]\n```\n"
    )
    (feature_dir / gate_file).write_text(
        f"---\ngate: {gate_num}\nstatus: {gate_status}\n---\n\n# Gate {gate_num}\n"
    )
    (feature_dir / "WU-T01.md").write_text(
        f"---\nid: {wu_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: done\nattempts: 1\n---\n\n# T01{_WU_BODY}"
    )
    (feature_dir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: done\nattempts: 1\nverdict: met\n---\n\n# Close{_WU_BODY}"
    )

    (specfuse / "roadmap.md").write_text(
        f"---\nproject: test\n---\n\n# Roadmap\n\n"
        f"| Feature ID | Title | Status | Folder | Detail |\n"
        f"|------------|-------|--------|--------|--------|\n"
        f"| {feature_id} | Test feature | {roadmap_row_status} | — | — |\n\n"
        f"## {feature_id} — Test feature\n\nContent.\n"
    )
    (specfuse / "roadmap-archive.md").write_text(
        "---\nproject: test\n---\n\n# Archived\n\n"
        "<!-- Archived sections appended below -->\n"
    )

    return feature_dir, root


def _make_close_wu(feature_dir: Path, wu_id: str, verdict: str = "met") -> loop.WorkUnit:
    return loop.WorkUnit(
        wu_id=wu_id,
        file=feature_dir / "WU-close.md",
        depends_on=[],
        type="close",
        model="opus",
        effort="high",
        status="done",
        attempts=1,
        title="Close",
        body="",
        verdict=verdict,
    )


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


# --------------------------------------------------------------------------- #
# TestFireTerminalFlips — unit tests for the helper directly                  #
# --------------------------------------------------------------------------- #


class TestFireTerminalFlips(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_fire_terminal_flips_met_verdict_flips_all_three(self):
        """met verdict: gate flipped to passed, roadmap row to done, archive written."""
        feature_id = "FEAT-2026-9991"
        feature_dir, repo_root = _make_repo_with_feature(
            self.root, feature_id, gate_num=2, gate_status="awaiting_review",
            roadmap_row_status="active",
        )
        wu = _make_close_wu(feature_dir, f"{feature_id}/G2-CLOSE", verdict="met")

        modified = loop.fire_terminal_flips(wu, feature_dir, repo_root)

        # Gate flipped to passed
        gate_fm = _read_frontmatter(feature_dir / "GATE-02.md")
        self.assertEqual(gate_fm.get("status"), "passed",
                         "terminal gate must be flipped to passed")

        # Roadmap row flipped to done
        roadmap_text = (repo_root / ".specfuse" / "roadmap.md").read_text()
        self.assertIn(f"| {feature_id} | Test feature | done |", roadmap_text,
                      "roadmap row must be flipped to done")

        # Auto-archive ran — archive file has section
        archive_text = (repo_root / ".specfuse" / "roadmap-archive.md").read_text()
        self.assertIn(f"## {feature_id} — Test feature", archive_text,
                      "feature section must appear in roadmap-archive.md")

        # modified list is non-empty
        self.assertTrue(modified, "fire_terminal_flips must return non-empty modified list")

    def test_fire_terminal_flips_skips_when_already_passed(self):
        """Re-firing when gate is already passed: gate left untouched (idempotent)."""
        feature_id = "FEAT-2026-9992"
        feature_dir, repo_root = _make_repo_with_feature(
            self.root, feature_id, gate_num=2, gate_status="passed",
            roadmap_row_status="active",
        )
        wu = _make_close_wu(feature_dir, f"{feature_id}/G2-CLOSE", verdict="met")

        # First call — gate already passed, but roadmap still active
        loop.fire_terminal_flips(wu, feature_dir, repo_root)

        # Gate stays passed (was passed before, skipped by helper)
        gate_fm = _read_frontmatter(feature_dir / "GATE-02.md")
        self.assertEqual(gate_fm.get("status"), "passed",
                         "gate must remain passed after skip")

        # Second call — now everything already archived too
        gate_before = (feature_dir / "GATE-02.md").read_bytes()
        loop.fire_terminal_flips(wu, feature_dir, repo_root)
        gate_after = (feature_dir / "GATE-02.md").read_bytes()
        self.assertEqual(gate_before, gate_after,
                         "second call must not modify an already-passed gate file")


# --------------------------------------------------------------------------- #
# TestRunTerminalFlipIntegration — integration tests through loop.run()       #
# --------------------------------------------------------------------------- #


class TestRunTerminalFlipIntegration(unittest.TestCase):

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

    def _write_feature(
        self,
        root: Path,
        feature_id: str,
        close_verdict: str,
        plan_status: str = "active",
    ) -> Path:
        fdir = root / f".specfuse/features/{feature_id}-test"
        fdir.mkdir(parents=True)
        close_id = f"{feature_id}/G1-CLOSE"

        (fdir / "PLAN.md").write_text(
            f"---\nfeature_id: {feature_id}\ntitle: Test\nslug: test\n"
            f"branch: feat/{feature_id.lower()}-test\n"
            f"roadmap_goal: test\nstatus: {plan_status}\n---\n\n# Plan\n\n"
            f"```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
            f"    work_units:\n      - id: {close_id}\n        file: WU-close.md\n"
            f"        depends_on: []\n```\n"
        )
        (fdir / "GATE-01.md").write_text(
            "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
        )
        (fdir / "WU-close.md").write_text(
            f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
            f"status: pending\nattempts: 0\nverdict: {close_verdict}\n---\n\n"
            f"# Close{_WU_BODY}"
        )
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "scaffold"], check=True)
        return fdir

    def test_run_does_not_flip_on_met_locally_verdict(self):
        """met_locally verdict: GATE-01.md stays awaiting_review, roadmap row stays active."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9993"
            fdir = self._write_feature(root, feature_id, close_verdict="met_locally")

            specfuse = root / ".specfuse"
            (specfuse / "roadmap.md").write_text(
                f"---\nproject: test\n---\n\n# Roadmap\n\n"
                f"| Feature ID | Title | Status | Folder | Detail |\n"
                f"|------------|-------|--------|--------|--------|\n"
                f"| {feature_id} | Test | active | — | — |\n\n"
                f"## {feature_id} — Test\n\nContent.\n"
            )
            (specfuse / "roadmap-archive.md").write_text(
                "---\nproject: test\n---\n\n# Archived\n\n"
                "<!-- Archived sections appended below -->\n"
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "roadmap"], check=True)

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # Simulate a real close-WU agent: write RETROSPECTIVE.md with
                # the "nothing generalizes" sentinel so closing-deliverable
                # assertions pass. Required since the diff-only-touches-wu
                # bypass was removed (FEAT-2026-0017/G1-CLOSE-attempt-3 fix).
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                return ("", {"input_tokens": 10, "output_tokens": 5, "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            loop.run(None, dry_run=False)

            # Gate must be awaiting_review (normal gate-complete), NOT passed
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review",
                             "met_locally verdict must leave gate at awaiting_review")

            # Roadmap row must still be active
            roadmap_text = (specfuse / "roadmap.md").read_text()
            self.assertIn(f"| {feature_id} | Test | active |", roadmap_text,
                          "met_locally verdict must leave roadmap row active")

    def test_run_reverts_plan_status_on_hedged_verdict(self):
        """Hedged verdict: if close WU body wrote PLAN.md→done, driver reverts to active."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9994"
            fdir = self._write_feature(root, feature_id, close_verdict="partially_met")
            plan_path = fdir / "PLAN.md"

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # Simulate agent body flipping PLAN.md to done
                loop.write_frontmatter_field(plan_path, "status", "done")
                return ("", {"input_tokens": 10, "output_tokens": 5, "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            loop.run(None, dry_run=False)

            plan_fm = _read_frontmatter(plan_path)
            self.assertEqual(plan_fm.get("status"), "active",
                             "driver must revert PLAN.md to active on hedged verdict")


# --------------------------------------------------------------------------- #
# TestWrapFeatureSkillGateFliPreRemoved                                       #
# --------------------------------------------------------------------------- #


class TestWrapFeatureSkillGateFlipRemoved(unittest.TestCase):

    def test_wrap_feature_skill_no_longer_lists_gate_flip(self):
        """wrap-feature/SKILL.md must not contain gate-flip step instructions."""
        skill_path = (REPO_ROOT / ".specfuse" / "skills" / "wrap-feature" / "SKILL.md")
        self.assertTrue(skill_path.exists(), f"SKILL.md not found at {skill_path}")
        content = skill_path.read_text()
        # Must not have the old cosmetic-flip step as an instruction
        self.assertNotIn(
            "GATE-NN.md status` is `awaiting_review`, flip to `passed`",
            content,
            "gate-flip step must have been removed from wrap-feature SKILL.md",
        )
        # Must contain the transfer note
        self.assertIn(
            "FEAT-2026-0015/T06",
            content,
            "SKILL.md must reference the T06 transfer",
        )
        self.assertIn(
            "fire_terminal_flips",
            content,
            "SKILL.md must name fire_terminal_flips as the new owner",
        )


if __name__ == "__main__":
    unittest.main()
