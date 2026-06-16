#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""End-to-end lifecycle integration test (FEAT-2026-0023/T02).

Drives a synthetic single-gate feature through the FULL lifecycle in one
``loop.run()`` against a real git repo in a tmp dir, stubbing ONLY the
``claude -p`` agent dispatch boundary (``loop.dispatch``/``loop.verify``).
Every other moving part is the real driver: ``ensure_feature_branch`` enters
the feature branch, the dispatch loop squashes per WU, the auto-close predicate
(``gate_eval.evaluate_auto_close``) decides the close path, ``fire_terminal_flips``
flips terminal state, and ``auto_archive_feature`` materializes the archive
anchor. This is the integration layer that would have caught #47, #48, #49.

The **terminal invariant** asserted at lifecycle end:
  - ``PLAN.md status: done``
  - terminal ``GATE-01.md status: passed``
  - roadmap row Status column ``done``
  - archive anchor ``<a id="feat-...">`` present in ``roadmap-archive.md``
  - ``RETROSPECTIVE.md`` present (stub for auto-close, full for dispatched)

Coverage map:
  - ``test_auto_close_lifecycle_terminal_invariant`` (AC1/AC4) — the RED anchor.
    Asserts ``PLAN.md == done`` after a terminal **auto-close**. The PLAN flip
    on the agent-less auto-close path is the T01 consolidation (closes #49):
    with T01 reverted ``fire_terminal_flips`` never touches PLAN.md, so it stays
    ``active`` and this assertion is RED; with T01 applied it is GREEN.
  - ``test_dispatched_close_lifecycle_terminal_invariant`` (AC3) — closes via a
    dispatched close WU passing with ``verdict: met``.
  - ``test_row_only_archive_anchor_materializes`` (AC5/#47) — a roadmap row with
    no inline detail section still gets its archive anchor; no
    ``archive_anchor_missing`` halt.
  - ``test_branch_seam_carries_pick_flips`` (AC6/#48) — a dirty-tree pick→branch
    handoff via ``ensure_feature_branch`` carries the /pick-feature flips onto
    the feature branch with no raw ``CalledProcessError`` escaping.

Escalation-trigger guard (escalation 1 — "stubbed too shallow"): the tests
exercise the REAL ``fire_terminal_flips`` / ``auto_archive_feature`` /
``ensure_feature_branch`` / auto-close predicate, not re-implementations. The
terminal invariant is checked by reading the files those functions write; a
regression in any of them leaves the invariant unsatisfied and the test RED.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


# --------------------------------------------------------------------------- #
# Synthetic-feature scaffold                                                  #
# --------------------------------------------------------------------------- #

_GITIGNORE = (
    ".specfuse/.loop.lock\n"
    ".specfuse/.scratch-*\n"
    ".specfuse/scripts/__pycache__/\n"
)

# Full close ceremony the dispatched-close stub writes. Satisfies every
# ``close``-type closing-deliverable guard: assert_retrospective_exists
# (non-empty), assert_learnings_appended_or_noop ("nothing generalizes"),
# assert_doc_or_roadmap_diff (RETROSPECTIVE.md in squash), and
# assert_cost_analysis_section_when_met (## Cost analysis, verdict=met).
_RETRO_FULL = (
    "# Retrospective\n\n"
    "## Gate 1 — close ceremony\n\n"
    "Full dispatched close for the synthetic lifecycle feature.\n\n"
    "## Cost analysis\n\n"
    "On plan; nothing to flag.\n\n"
    "## Learnings\n\n"
    "Nothing generalizes from this synthetic feature.\n"
)


def _roadmap(feature_id: str, slug: str, status: str,
             *, detail_section: bool) -> str:
    """A roadmap.md with the feature's row. Status column is the 3rd column
    (2nd after the ID) to match assert_terminal_flips_fired's positional regex
    and _parse_roadmap_row's header-name lookup."""
    text = (
        "---\n"
        "project: lifecycle-test\n"
        "---\n\n"
        "# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        f"| {feature_id} | Lifecycle test | {status} | {slug} | — |\n"
    )
    if detail_section:
        text += (
            f"\n## {feature_id} — Lifecycle test\n\n"
            "Inline detail section that auto_archive_feature moves to the "
            "archive.\n"
        )
    return text


_ARCHIVE_SCAFFOLD = (
    "---\n"
    "project: lifecycle-test\n"
    "---\n\n"
    "# Archived feature details\n\n"
    "<!-- Archived sections appended below -->\n"
)


def _scaffold_feature(root: Path, *, feature_id: str, slug: str, branch: str,
                      roadmap_status: str, plan_status: str,
                      detail_section: bool, auto_close_disabled: bool,
                      commit: bool = True) -> Path:
    """Build a synthetic single-gate feature: roadmap row + roadmap-archive +
    PLAN.md (gate 1 = terminal, one implementation WU + one close WU) + GATE
    file + per-WU files. Optionally commit so the tree is clean.

    Gate 1 is terminal (no gate 2), so the close WU drives the terminal close.
    """
    (root / ".specfuse" / "roadmap.md").write_text(
        _roadmap(feature_id, slug, roadmap_status, detail_section=detail_section))
    (root / ".specfuse" / "roadmap-archive.md").write_text(_ARCHIVE_SCAFFOLD)

    fdir = root / ".specfuse" / "features" / f"{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    disabled_line = "auto_close_disabled: true\n" if auto_close_disabled else ""
    plan = (
        "---\n"
        f"feature_id: {feature_id}\n"
        "title: Lifecycle test\n"
        f"slug: {slug}\n"
        f"branch: {branch}\n"
        "roadmap_goal: drive the full lifecycle end to end\n"
        f"status: {plan_status}\n"
        f"{disabled_line}"
        "---\n\n"
        f"# Plan: {slug}\n\n"
        "```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        f"      - id: {feature_id}/T01\n"
        "        file: WU-T01.md\n"
        "        depends_on: []\n"
        f"      - id: {feature_id}/G1-CLOSE\n"
        "        file: WU-G1-CLOSE.md\n"
        f"        depends_on: [{feature_id}/T01]\n"
        "```\n"
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
        f"---\n\n# T01{body}")
    # Close WU carries NO verdict field — so wu.verdict is None at load and the
    # auto-close / override branches fire (a preset verdict falls through to
    # normal dispatch by design).
    (fdir / "WU-G1-CLOSE.md").write_text(
        f"---\nid: {feature_id}/G1-CLOSE\ntype: close\n"
        f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
        f"---\n\n# G1-CLOSE{body}")

    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".specfuse/.loop.lock" not in existing:
        gitignore.write_text(existing + _GITIGNORE)

    if commit:
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "scaffold lifecycle fixture"], check=True)
    return fdir


# --------------------------------------------------------------------------- #
# Stubbed dispatch                                                            #
# --------------------------------------------------------------------------- #


def _fake_dispatch(wu, failure_note, cost_tracking=True):
    """Stub the agent boundary. The implementation WU writes a real deliverable;
    the close WU (dispatched-close path only) writes the full close ceremony and
    the verdict the close-deliverable guards demand. Auto-close never dispatches
    the close WU, so its branch is inert on that path."""
    if wu.type == "implementation":
        Path("src").mkdir(exist_ok=True)
        Path("src/feature.py").write_text("VALUE = 1\n")
        return ("```result\nstatus: complete\n"
                "files_changed:\n  - src/feature.py\n```\n")
    if wu.type == "close":
        (wu.file.parent / "RETROSPECTIVE.md").write_text(_RETRO_FULL)
        loop.write_frontmatter_field(wu.file, "verdict", "met")
        return "```result\nstatus: complete\n```\n"
    return "```result\nstatus: complete\n```\n"


# --------------------------------------------------------------------------- #
# Frontmatter / event readers                                                 #
# --------------------------------------------------------------------------- #


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


def _roadmap_row_status(root: Path, feature_id: str) -> str | None:
    """Read the feature row's Status column using the same positional regex
    assert_terminal_flips_fired uses (Status is group 2)."""
    text = (root / ".specfuse" / "roadmap.md").read_text()
    m = re.search(
        r"^\|\s*" + re.escape(feature_id) + r"\s*\|([^|]*)\|([^|]*)\|",
        text, re.MULTILINE,
    )
    return m.group(2).strip() if m else None


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _current_branch(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


# --------------------------------------------------------------------------- #
# Tests                                                                       #
# --------------------------------------------------------------------------- #


class LifecycleIntegrationTest(unittest.TestCase):
    """Drive loop.run() to a terminal outcome with the agent boundary stubbed."""

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

    def _stub_agent(self):
        self._patch("dispatch", _fake_dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

    def _assert_terminal_invariant(self, root: Path, feature_dir: Path,
                                   feature_id: str):
        """The terminal invariant the lifecycle must satisfy at close."""
        # PLAN.md status: done — the RED anchor (#49 / T01 consolidation).
        plan_fm = _read_frontmatter(feature_dir / "PLAN.md")
        self.assertEqual(
            plan_fm.get("status"), "done",
            "PLAN.md must be flipped to done by fire_terminal_flips (T01 "
            "consolidates this onto BOTH close paths; pre-T01 the auto-close "
            "path left it 'active' — issue #49)")
        # Terminal gate passed.
        gate_fm = _read_frontmatter(feature_dir / "GATE-01.md")
        self.assertEqual(gate_fm.get("status"), "passed",
                         "terminal gate must be flipped to passed")
        # Roadmap row done.
        self.assertEqual(_roadmap_row_status(root, feature_id), "done",
                         "roadmap row Status must be flipped to done")
        # Archive anchor present.
        archive = (root / ".specfuse" / "roadmap-archive.md").read_text()
        self.assertIn(f'<a id="{feature_id.lower()}"></a>', archive,
                      "auto_archive_feature must materialize the archive anchor")
        # RETROSPECTIVE.md present and non-empty.
        retro = feature_dir / "RETROSPECTIVE.md"
        self.assertTrue(retro.is_file() and retro.read_text().strip(),
                        "RETROSPECTIVE.md must be present and non-empty")

    def test_auto_close_lifecycle_terminal_invariant(self):
        """AC1/AC4 (RED anchor): a feature meeting the auto-close predicate closes
        via the agent-less auto path; the full terminal invariant — including
        PLAN.md == done — holds. RED against the pre-T01 driver: without the
        consolidated PLAN flip in fire_terminal_flips the auto-close path leaves
        PLAN.md 'active' (issue #49), so the PLAN.md==done assertion fails."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold_feature(
                root, feature_id="FEAT-2026-9001", slug="auto-close",
                branch="feat/FEAT-2026-9001-auto-close",
                roadmap_status="active", plan_status="active",
                detail_section=True, auto_close_disabled=False)
            self._stub_agent()

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0, "auto-close lifecycle must reach a clean "
                                    "terminal outcome (rc=0)")

            self._assert_terminal_invariant(root, feature_dir, "FEAT-2026-9001")

            # The auto-close path was actually taken (not a dispatched close):
            # the predicate emitted an auto_close_decision with auto=True.
            events = _read_events(feature_dir / "events.jsonl")
            auto_decisions = [
                e for e in events
                if e["event_type"] == "auto_close_decision"
                and e["payload"].get("auto") is True
            ]
            self.assertTrue(auto_decisions,
                            "expected an auto_close_decision(auto=True) event — "
                            "the auto-close predicate must have fired")
            # The close WU was marked auto-closed (verdict=met written by the
            # driver, not an agent).
            close_fm = _read_frontmatter(feature_dir / "WU-G1-CLOSE.md")
            self.assertEqual(close_fm.get("status"), "done")
            self.assertEqual(close_fm.get("verdict"), "met")
            self.assertIn(close_fm.get("auto_close"), ("true", "True"))

    def test_dispatched_close_lifecycle_terminal_invariant(self):
        """AC3: with auto-close disabled, the feature closes via a dispatched
        close WU passing with verdict: met; the full terminal invariant holds."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold_feature(
                root, feature_id="FEAT-2026-9002", slug="dispatched-close",
                branch="feat/FEAT-2026-9002-dispatched-close",
                roadmap_status="active", plan_status="active",
                detail_section=True, auto_close_disabled=True)
            self._stub_agent()

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0, "dispatched-close lifecycle must reach a "
                                    "clean terminal outcome (rc=0)")

            self._assert_terminal_invariant(root, feature_dir, "FEAT-2026-9002")

            # The close WU was actually DISPATCHED (auto-close refused via the
            # override): its passing attempt produced a task_completed event.
            events = _read_events(feature_dir / "events.jsonl")
            close_completed = [
                e for e in events
                if e["event_type"] == "task_completed"
                and e["correlation_id"] == "FEAT-2026-9002/G1-CLOSE"
            ]
            self.assertTrue(close_completed,
                            "expected the close WU to be dispatched and pass "
                            "(task_completed) — not auto-closed")
            close_fm = _read_frontmatter(feature_dir / "WU-G1-CLOSE.md")
            self.assertEqual(close_fm.get("verdict"), "met")
            self.assertNotIn(close_fm.get("auto_close"), ("true", "True"),
                             "dispatched close must not be marked auto_close")

    def test_row_only_archive_anchor_materializes(self):
        """AC5 (#47): a feature whose roadmap row has NO inline detail section
        still gets its archive anchor synthesized at close — the lifecycle does
        not halt on archive_anchor_missing."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_dir = _scaffold_feature(
                root, feature_id="FEAT-2026-9003", slug="row-only",
                branch="feat/FEAT-2026-9003-row-only",
                roadmap_status="active", plan_status="active",
                detail_section=False, auto_close_disabled=False)
            self._stub_agent()

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0, "row-only close must not halt on "
                                    "archive_anchor_missing")

            self._assert_terminal_invariant(root, feature_dir, "FEAT-2026-9003")

            # No post-pass invariant escalation fired (archive_anchor_missing
            # would surface as a human_escalation on the close WU).
            events = _read_events(feature_dir / "events.jsonl")
            escalations = [
                e for e in events
                if e["event_type"] == "human_escalation"
                and e["payload"].get("reason") == "post_pass_invariant_failed"
            ]
            self.assertFalse(escalations,
                             "row-only feature must not trip the post-pass "
                             "terminal-flip invariant")
            # The synthesized stub heading is in the archive (no inline section
            # existed to move).
            archive = (root / ".specfuse" / "roadmap-archive.md").read_text()
            self.assertIn("## FEAT-2026-9003 — Lifecycle test", archive)

    def test_branch_seam_carries_pick_flips(self):
        """AC6 (#48): a dirty-tree pick→branch handoff. The scaffold is committed
        on `main` with the row/PLAN still `planned`; the /pick-feature flips
        (roadmap.md + PLAN.md → active) are left UNCOMMITTED. ensure_feature_branch
        must create the feature branch carrying exactly those flips with no raw
        CalledProcessError escaping, and the lifecycle must still reach the clean
        terminal invariant (which is only satisfiable if the flips carried)."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9004"
            slug = "branch-seam"
            branch = "feat/FEAT-2026-9004-branch-seam"
            feature_dir = _scaffold_feature(
                root, feature_id=feature_id, slug=slug, branch=branch,
                roadmap_status="planned", plan_status="planned",
                detail_section=True, auto_close_disabled=False)

            # Simulate /pick-feature's flips, left uncommitted (the dirty tree
            # #48 used to crash on). Only roadmap.md + PLAN.md are touched — the
            # exact set ensure_feature_branch's _expected_flip_paths permits.
            (root / ".specfuse" / "roadmap.md").write_text(
                _roadmap(feature_id, slug, "active", detail_section=True))
            loop.write_frontmatter_field(
                feature_dir / "PLAN.md", "status", "active")

            self.assertEqual(_current_branch(root), "main")
            self._stub_agent()

            # Must not raise FeatureBranchError / CalledProcessError.
            try:
                rc = loop.run(None, dry_run=False)
            except subprocess.CalledProcessError as exc:  # pragma: no cover
                self.fail(f"raw CalledProcessError escaped the branch seam: {exc}")

            self.assertEqual(rc, 0, "dirty-tree pick→branch lifecycle must reach "
                                    "a clean terminal outcome (rc=0)")
            # The driver switched onto the feature branch (the pick flips rode
            # along on `git checkout -B`).
            self.assertEqual(_current_branch(root), branch,
                             "ensure_feature_branch must enter the feature branch")
            # The carried flips drove a clean terminal close: roadmap row could
            # only reach `done` if the carried `active` flip survived the branch
            # creation (fire_terminal_flips flips active→done).
            self._assert_terminal_invariant(root, feature_dir, feature_id)


if __name__ == "__main__":
    unittest.main()
