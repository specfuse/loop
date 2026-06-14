#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Type-keyed closing deliverable guard — FEAT-2026-0015/T07.

Covers:
  Unit tests (one class per assertion function, eight total):
    (1) assert_retrospective_exists
    (2) assert_learnings_appended_or_noop
    (3) assert_doc_or_roadmap_diff
    (4) assert_verdict_well_formed
    (5) assert_cost_analysis_section_when_met
    (6) assert_retrospective_gate_section
    (7) assert_gate_review_exists
    (8) assert_next_gate_drafted_or_terminal

  Integration tests (AC5 — test assert_closing_deliverables):
    (a) test_close_passes_when_all_assertions_hold
    (b) test_close_fails_when_retrospective_missing
    (c) test_close_intermediate_passes_when_gate_section_added
    (d) test_plan_next_fails_when_gate_review_missing

  Integration test (AC6 — test run() rollback):
    (e) test_run_rolls_back_on_closing_deliverable_missing
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

DUMMY_HEAD = "0000000000000000000000000000000000000000"


def _make_wu(
    file: Path = Path("FAKE-WU.md"),
    wu_id: str = "FEAT-9999/G1-CLOSE",
    wu_type: str = "close",
    verdict: str | None = "met",
    body: str = _WU_BODY,
) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=file,
        depends_on=[],
        type=wu_type,
        model="opus",
        status="pending",
        attempts=0,
        title="test WU",
        body=body,
        verdict=verdict,
    )


def _write_wu_file(wu: "loop.WorkUnit", on_disk_verdict: str | None | object = ...) -> None:
    """Materialize wu.file on disk with frontmatter.

    By default the on-disk verdict matches `wu.verdict`. Pass
    `on_disk_verdict=` explicitly (incl. `None`) to model the
    stale-in-memory-vs-fresh-on-disk scenario the post-issue-#12
    assertions must handle.
    """
    disk_verdict = wu.verdict if on_disk_verdict is ... else on_disk_verdict
    wu.file.parent.mkdir(parents=True, exist_ok=True)
    fm_lines = [
        f"id: {wu.wu_id}",
        f"type: {wu.type}",
        f"status: {wu.status}",
        f"attempts: {wu.attempts}",
    ]
    if disk_verdict is not None:
        fm_lines.append(f"verdict: {disk_verdict}")
    wu.file.write_text("---\n" + "\n".join(fm_lines) + "\n---\n\n" + wu.body)


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@test.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "commit.gpgSign", "false"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "gc.auto", "0"], check=True)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


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


# --------------------------------------------------------------------------- #
# (1) assert_retrospective_exists                                              #
# --------------------------------------------------------------------------- #


class TestAssertRetrospectiveExists(unittest.TestCase):

    def test_passes_when_retro_exists_and_nonempty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text("# Retro\n\nSome content.\n")
            wu = _make_wu(wu_type="close")
            ok, reason = loop.assert_retrospective_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertTrue(ok)
            self.assertEqual(reason, "")

    def test_fails_when_retro_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(wu_type="close")
            ok, reason = loop.assert_retrospective_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_retrospective_exists", reason)

    def test_fails_when_retro_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text("   \n")
            wu = _make_wu(wu_type="close")
            ok, reason = loop.assert_retrospective_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_retrospective_exists", reason)


# --------------------------------------------------------------------------- #
# (2) assert_learnings_appended_or_noop                                       #
# --------------------------------------------------------------------------- #


class TestAssertLearningsAppendedOrNoop(unittest.TestCase):

    def test_passes_when_nothing_generalizes_in_retro(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retro\n\nNothing generalizes from this gate.\n"
            )
            wu = _make_wu(wu_type="close")
            # head_before is dummy; git will return empty diff (non-git dir)
            ok, reason = loop.assert_learnings_appended_or_noop(wu, fdir, fdir, DUMMY_HEAD)
            self.assertTrue(ok)
            self.assertEqual(reason, "")

    def test_fails_when_no_learnings_and_no_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            # No RETROSPECTIVE.md at all → noop check fails
            wu = _make_wu(wu_type="close")
            ok, reason = loop.assert_learnings_appended_or_noop(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_learnings_appended_or_noop", reason)

    def test_passes_when_learnings_diff_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            specfuse = root / ".specfuse"
            specfuse.mkdir(parents=True)
            (specfuse / "LEARNINGS.md").write_text("# Learnings\n\nOld entry.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            (specfuse / "LEARNINGS.md").write_text(
                "# Learnings\n\nOld entry.\n\n## New section\n\nNew content.\n"
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "add learnings"], check=True)

            fdir = root / ".specfuse/features/test"
            fdir.mkdir(parents=True)
            wu = _make_wu(wu_type="close")
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_learnings_appended_or_noop(
                    wu, fdir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok)


# --------------------------------------------------------------------------- #
# (3) assert_doc_or_roadmap_diff                                              #
# --------------------------------------------------------------------------- #


class TestAssertDocOrRoadmapDiff(unittest.TestCase):

    def test_passes_for_intermediate_when_no_doc_in_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(
                wu_type="close-intermediate",
                wu_id="FEAT-9999/G1-CLOSE-INTERMEDIATE",
                body="body with no docs or roadmap mention",
                verdict=None,
            )
            ok, reason = loop.assert_doc_or_roadmap_diff(wu, fdir, fdir, DUMMY_HEAD)
            self.assertTrue(ok)

    def test_fails_for_close_when_no_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(wu_type="close")
            ok, reason = loop.assert_doc_or_roadmap_diff(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_doc_or_roadmap_diff", reason)

    def test_passes_when_roadmap_in_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            specfuse = root / ".specfuse"
            specfuse.mkdir(parents=True)
            (specfuse / "roadmap.md").write_text("# Roadmap\n\nContent.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
            head_before = _git(root, "rev-parse", "HEAD")

            (specfuse / "roadmap.md").write_text("# Roadmap\n\nUpdated.\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "update roadmap"], check=True)

            fdir = root / ".specfuse/features/test"
            fdir.mkdir(parents=True)
            wu = _make_wu(wu_type="close")
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_doc_or_roadmap_diff(wu, fdir, root, head_before)
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok)


# --------------------------------------------------------------------------- #
# (4) assert_verdict_well_formed                                              #
# --------------------------------------------------------------------------- #


class TestAssertVerdictWellFormed(unittest.TestCase):

    def test_passes_with_valid_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            for verdict in loop.VERDICT_VALUES:
                wu = _make_wu(file=fdir / "WU.md", verdict=verdict)
                _write_wu_file(wu)
                ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)
                self.assertTrue(ok, f"Expected pass for verdict={verdict!r}")

    def test_fails_with_none_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(file=fdir / "WU.md", verdict=None)
            _write_wu_file(wu)
            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_verdict_well_formed", reason)

    def test_fails_with_invalid_verdict_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(file=fdir / "WU.md", verdict="definitely_not_valid")
            _write_wu_file(wu)
            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_verdict_well_formed", reason)

    def test_reads_fresh_verdict_from_disk_not_stale_memory(self):
        """Issue #12 regression: in-memory wu.verdict is the placeholder set by
        load_wu at gate start; the agent writes the real verdict to the WU file
        during dispatch. Assertion MUST read fresh from disk, else every close
        spins to MAX_ATTEMPTS and rolls back all artifacts.

        Surfaced in resto-manager-iac FEAT-2026-0019 ($14.70 sunk over 6
        attempts) and FEAT-2026-0017/G1-CLOSE (5 attempts).
        """
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(file=fdir / "WU.md", verdict="not_set")
            _write_wu_file(wu, on_disk_verdict="met")
            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)
            self.assertTrue(
                ok,
                f"Assertion must read fresh from disk; got reason: {reason!r}",
            )
            self.assertEqual(
                wu.verdict, "met",
                "Assertion must update in-memory wu.verdict so downstream "
                "checks (verdict_permits_terminal_flips, cost analysis) see "
                "the post-squash value.",
            )

    def test_reads_fresh_when_disk_verdict_none(self):
        """Companion to the regression test: when in-memory is 'met' (carried
        from prior gate) but disk has no verdict (agent failed to write),
        assertion must fail — not accept the stale in-memory value."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(file=fdir / "WU.md", verdict="met")
            _write_wu_file(wu, on_disk_verdict=None)
            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_verdict_well_formed", reason)


# --------------------------------------------------------------------------- #
# (5) assert_cost_analysis_section_when_met                                   #
# --------------------------------------------------------------------------- #


class TestAssertCostAnalysisSectionWhenMet(unittest.TestCase):

    def test_skips_when_verdict_not_met(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            for v in ("met_locally", "partially_met", "not_met"):
                wu = _make_wu(file=fdir / "WU.md", verdict=v)
                _write_wu_file(wu)
                ok, reason = loop.assert_cost_analysis_section_when_met(
                    wu, fdir, fdir, DUMMY_HEAD,
                )
                self.assertTrue(ok, f"Expected skip for verdict={v!r}")

    def test_passes_when_met_and_section_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retro\n\nSome content.\n\n## Cost analysis\n\nCost details.\n"
            )
            wu = _make_wu(file=fdir / "WU.md", verdict="met")
            _write_wu_file(wu)
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok)

    def test_fails_when_met_and_section_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text("# Retro\n\nSome content.\n")
            wu = _make_wu(file=fdir / "WU.md", verdict="met")
            _write_wu_file(wu)
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_cost_analysis_section_when_met", reason)

    def test_reads_fresh_verdict_from_disk_not_stale_memory(self):
        """Issue #12 regression (close-e variant): in-memory verdict='not_set',
        disk verdict='met', RETROSPECTIVE.md has '## Cost analysis' section.
        Pre-patch the assertion read stale `wu.verdict` and treated this as
        the not-met skip path, masking missing cost sections in real runs."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retro\n\n## Cost analysis\n\nCost details.\n"
            )
            wu = _make_wu(file=fdir / "WU.md", verdict="not_set")
            _write_wu_file(wu, on_disk_verdict="met")
            ok, reason = loop.assert_cost_analysis_section_when_met(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok, f"Expected pass; got: {reason!r}")


# --------------------------------------------------------------------------- #
# (6) assert_retrospective_gate_section                                       #
# --------------------------------------------------------------------------- #


class TestAssertRetrospectiveGateSection(unittest.TestCase):

    def test_passes_when_gate_section_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retro\n\n## Gate 1\n\nSome observations.\n"
            )
            wu = _make_wu(
                wu_type="close-intermediate",
                wu_id="FEAT-9999/G1-CLOSE-INTERMEDIATE",
                verdict=None,
            )
            ok, reason = loop.assert_retrospective_gate_section(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok)

    def test_passes_with_triple_hash_gate_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retro\n\n### Gate 2\n\nSome observations.\n"
            )
            wu = _make_wu(
                wu_type="close-intermediate",
                wu_id="FEAT-9999/G2-CLOSE-INTERMEDIATE",
                verdict=None,
            )
            ok, reason = loop.assert_retrospective_gate_section(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok)

    def test_fails_when_gate_section_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retro\n\n## Gate 2\n\nOnly gate 2 here.\n"
            )
            wu = _make_wu(
                wu_type="close-intermediate",
                wu_id="FEAT-9999/G1-CLOSE-INTERMEDIATE",
                verdict=None,
            )
            ok, reason = loop.assert_retrospective_gate_section(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_retrospective_gate_section", reason)

    def test_fails_when_retro_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu = _make_wu(
                wu_type="close-intermediate",
                wu_id="FEAT-9999/G1-CLOSE-INTERMEDIATE",
                verdict=None,
            )
            ok, reason = loop.assert_retrospective_gate_section(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_retrospective_gate_section", reason)


# --------------------------------------------------------------------------- #
# (7) assert_gate_review_exists                                               #
# --------------------------------------------------------------------------- #


class TestAssertGateReviewExists(unittest.TestCase):

    def _write_two_gate_plan(self, fdir: Path, feature_id: str) -> None:
        (fdir / "PLAN.md").write_text(
            f"---\nfeature_id: {feature_id}\ntitle: Test\n"
            f"branch: feat/test\nroadmap_goal: test\nstatus: active\n---\n\n"
            f"# Plan\n\n```yaml\ngates:\n"
            f"  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
            f"      - id: {feature_id}/G1-PLAN\n        file: WU-plan.md\n"
            f"        depends_on: []\n"
            f"  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
            f"      - id: {feature_id}/T01\n        file: WU-T01.md\n"
            f"        depends_on: []\n```\n"
        )

    def test_passes_when_review_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            self._write_two_gate_plan(fdir, "FEAT-9999")
            (fdir / "GATE-02-REVIEW.md").write_text("# Gate 2 Review\n\nFindings.\n")
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_gate_review_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertTrue(ok)

    def test_fails_when_review_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            self._write_two_gate_plan(fdir, "FEAT-9999")
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_gate_review_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertFalse(ok)
            self.assertIn("assert_gate_review_exists", reason)

    def test_passes_for_terminal_single_gate_feature(self):
        """Single-gate feature: no next gate defined → terminal → review not expected."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\ntitle: Test\n"
                "branch: feat/test\nroadmap_goal: test\nstatus: active\n---\n\n"
                "# Plan\n\n```yaml\ngates:\n"
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n```\n"
            )
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_gate_review_exists(wu, fdir, fdir, DUMMY_HEAD)
            self.assertTrue(ok)


# --------------------------------------------------------------------------- #
# (8) assert_next_gate_drafted_or_terminal                                    #
# --------------------------------------------------------------------------- #


class TestAssertNextGateDraftedOrTerminal(unittest.TestCase):

    def test_passes_when_plan_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\ntitle: Test\n"
                "branch: feat/test\nroadmap_goal: test\nstatus: done\n---\n\n"
                "# Plan\n\n```yaml\ngates:\n"
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n```\n"
            )
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_next_gate_drafted_or_terminal(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok)

    def test_passes_when_next_gate_has_work_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\ntitle: Test\n"
                "branch: feat/test\nroadmap_goal: test\nstatus: active\n---\n\n"
                "# Plan\n\n```yaml\ngates:\n"
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
                "      - id: FEAT-9999/T01\n        file: WU-T01.md\n"
                "        depends_on: []\n```\n"
            )
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_next_gate_drafted_or_terminal(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertTrue(ok)

    def test_fails_when_next_gate_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\ntitle: Test\n"
                "branch: feat/test\nroadmap_goal: test\nstatus: active\n---\n\n"
                "# Plan\n\n```yaml\ngates:\n"
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units: []\n```\n"
            )
            wu = _make_wu(wu_type="plan-next", wu_id="FEAT-9999/G1-PLAN", verdict=None)
            ok, reason = loop.assert_next_gate_drafted_or_terminal(
                wu, fdir, fdir, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("assert_next_gate_drafted_or_terminal", reason)


# --------------------------------------------------------------------------- #
# Integration tests — assert_closing_deliverables (AC5)                      #
# --------------------------------------------------------------------------- #


def _setup_substantive_commit(root: Path, extra_files: dict[str, str]) -> str:
    """Commit initial state, then commit extra_files; return head_before (initial SHA)."""
    _init_git(root)
    (root / "README.md").write_text("# fixture\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
    head_before = _git(root, "rev-parse", "HEAD")
    for rel, content in extra_files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "squash"], check=True)
    return head_before


class TestCloseAssertions(unittest.TestCase):

    def test_close_passes_when_all_assertions_hold(self):
        """close: all assertions pass with full fixture."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retro_content = (
                "# Retrospective\n\nNothing generalizes from this gate.\n\n"
                "## Cost analysis\n\nActual: $1.20 vs planned $1.50.\n"
            )
            head_before = _setup_substantive_commit(root, {
                ".specfuse/LEARNINGS.md": "# Learnings\n\nOld entry.\n\nNew entry.\n",
                ".specfuse/roadmap.md": "# Roadmap\n\nUpdated.\n",
                "feature/RETROSPECTIVE.md": retro_content,
                "feature/WU-close.md": (
                    "---\nid: FEAT-9999/G1-CLOSE\ntype: close\n"
                    "status: done\nattempts: 1\nverdict: met\n---\n\n"
                    "# Close ceremony\n"
                ),
            })
            fdir = root / "feature"
            fdir.mkdir(exist_ok=True)
            wu = _make_wu(
                file=root / "feature/WU-close.md",
                wu_type="close",
                verdict="met",
            )
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(
                    wu, fdir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok, f"Expected pass; got reason: {reason!r}")
            self.assertEqual(reason, "")

    def test_close_fails_when_diff_only_touches_wu_file(self):
        """FEAT-2026-0017/G1-CLOSE attempt-3 regression: a close-type WU whose
        squash diff contains ONLY the WU's own frontmatter (driver bookkeeping)
        must NOT silently pass; an earlier 'diff-is-empty' bypass made hollow
        close ceremonies look successful. Guard must fall through to the typed
        assertions, which fail because no RETROSPECTIVE.md was written."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _init_git(root)
            (root / "feature").mkdir()
            wu_rel = "feature/WU-close.md"
            (root / wu_rel).write_text(
                "---\nid: FEAT-9999/G1-CLOSE\nstatus: pending\nattempts: 0\n---\n"
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True,
            )
            head_before = _git(root, "rev-parse", "HEAD")
            # Hollow squash: only the WU file gets modified (driver bookkeeping shape).
            (root / wu_rel).write_text(
                "---\nid: FEAT-9999/G1-CLOSE\nstatus: done\nattempts: 3\n---\n"
            )
            subprocess.run(["git", "-C", str(root), "add", wu_rel], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "squash"], check=True,
            )
            fdir = root / "feature"
            wu = _make_wu(
                file=root / wu_rel,
                wu_type="close",
                verdict="not_set",
            )
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(
                    wu, fdir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertFalse(ok, "diff-only-touches-wu hollow pass must NOT pass")
            self.assertIn("assert_retrospective_exists", reason)

    def test_close_fails_when_retrospective_missing(self):
        """close: fails immediately when RETROSPECTIVE.md absent."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            head_before = _setup_substantive_commit(root, {
                "feature/agent-output.txt": "some output\n",
            })
            fdir = root / "feature"
            fdir.mkdir(exist_ok=True)
            wu = _make_wu(
                file=root / "feature/WU-close.md",
                wu_type="close",
                verdict="met",
            )
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(
                    wu, fdir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertFalse(ok)
            self.assertIn("assert_retrospective_exists", reason)

    def test_close_intermediate_passes_when_gate_section_added(self):
        """close-intermediate: passes when RETROSPECTIVE.md has Gate 1 section."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retro_content = (
                "# Retrospective\n\n## Gate 1\n\nObservations.\n\n"
                "Nothing generalizes from this gate.\n"
            )
            head_before = _setup_substantive_commit(root, {
                "feature/RETROSPECTIVE.md": retro_content,
                "feature/agent-output.txt": "some output\n",
            })
            fdir = root / "feature"
            fdir.mkdir(exist_ok=True)
            wu = _make_wu(
                file=root / "feature/WU-ci.md",
                wu_type="close-intermediate",
                wu_id="FEAT-9999/G1-CLOSE-INTERMEDIATE",
                verdict=None,
                body="body with no doc mention",
            )
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(
                    wu, fdir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertTrue(ok, f"Expected pass; got: {reason!r}")

    def test_plan_next_fails_when_gate_review_missing(self):
        """plan-next: fails when GATE-02-REVIEW.md absent in a 2-gate feature."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            head_before = _setup_substantive_commit(root, {
                "feature/agent-output.txt": "drafted gate 2 WUs\n",
            })
            fdir = root / "feature"
            fdir.mkdir(exist_ok=True)
            # Two-gate PLAN.md: gate 2 exists but no GATE-02-REVIEW.md
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-9999\ntitle: Test\n"
                "branch: feat/test\nroadmap_goal: test\nstatus: active\n---\n\n"
                "# Plan\n\n```yaml\ngates:\n"
                "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                "      - id: FEAT-9999/G1-PLAN\n        file: WU-plan.md\n"
                "        depends_on: []\n"
                "  - gate: 2\n    file: GATE-02.md\n    work_units:\n"
                "      - id: FEAT-9999/T01\n        file: WU-T01.md\n"
                "        depends_on: []\n```\n"
            )
            wu = _make_wu(
                file=root / "feature/WU-plan.md",
                wu_type="plan-next",
                wu_id="FEAT-9999/G1-PLAN",
                verdict=None,
            )
            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(
                    wu, fdir, root, head_before,
                )
            finally:
                os.chdir(old_cwd)
            self.assertFalse(ok)
            self.assertIn("assert_gate_review_exists", reason)


# --------------------------------------------------------------------------- #
# Integration test — run() rollback on closing_deliverable_missing (AC6)     #
# --------------------------------------------------------------------------- #


def _write_close_feature(root: Path, feature_id: str) -> Path:
    """Scaffold a single-gate feature with one `close` WU pending."""
    slug = "close-guard-test"
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    close_id = f"{feature_id}/G1-CLOSE"

    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nslug: {slug}\n"
        f"branch: feat/{feature_id.lower()}-{slug}\n"
        f"roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n"
        f"```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: []\n```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\nverdict: met\n---\n\n"
        f"# Close ceremony{_WU_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"], check=True)
    return fdir


class TestRunRollbackOnClosingDeliverableMissing(unittest.TestCase):

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

    def test_run_rolls_back_on_closing_deliverable_missing(self):
        """close WU with agent output but no RETROSPECTIVE.md spins to blocked_human."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9511"
            fdir = _write_close_feature(root, feature_id)

            result_block = (
                "```result\n"
                "status: complete\n"
                "summary: close ceremony done\n"
                "```\n"
            )

            attempt_counter = {"n": 0}

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                attempt_counter["n"] += 1
                # Create a substantive file so the closing guard fires,
                # but deliberately omit RETROSPECTIVE.md.
                (root / f"agent-output-{attempt_counter['n']}.txt").write_text(
                    "some output\n"
                )
                return (result_block, {"input_tokens": 100,
                                       "output_tokens": 50,
                                       "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1,
                             "3 closing guard failures must escalate (rc=1)")

            # WU must be blocked_human after 3 failed closing-guard attempts.
            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            self.assertEqual(wu_fm.get("status"), "blocked_human",
                             "close WU must be blocked_human after 3 guard failures")

            # Each attempt must emit a closing_deliverable_missing event.
            events = _read_events(fdir / "events.jsonl")
            guard_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["payload"].get("outcome") == "closing_deliverable_missing"
            ]
            self.assertEqual(len(guard_events), loop.MAX_ATTEMPTS,
                             "one closing_deliverable_missing event per attempt")
            for ev in guard_events:
                self.assertEqual(ev["payload"]["assertion"],
                                 "assert_retrospective_exists",
                                 "failing assertion must be named in the event")

            # No task_completed event — WU never successfully completed.
            event_types = [e["event_type"] for e in events]
            self.assertNotIn("task_completed", event_types,
                             "task_completed must not fire when guard failed")

            # Squash commits must have been rolled back (not in final git log).
            git_log = subprocess.run(
                ["git", "log", "--format=%s",
                 f"feat/{feature_id.lower()}-close-guard-test"],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertNotIn("feat: Close ceremony", git_log,
                             "rolled-back squash must not remain in history")


if __name__ == "__main__":
    unittest.main()
