#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Post-pass driver-state invariant guard — FEAT-2026-0017/T01.

Covers:
  Unit tests on `assert_terminal_flips_fired` / `verify_post_pass_invariants`:
    (a) test_close_with_verdict_met_passes_when_flips_fire
    (b) test_close_with_verdict_met_fails_when_gate_unflipped
    (c) test_close_with_verdict_met_fails_when_row_active
    (d) test_close_with_verdict_met_fails_when_archive_anchor_absent
    (e) test_close_with_hedged_verdict_skips_guard
    (f) test_feat_2026_0015_t06_regression  (canary for the wu.verdict
        re-read race: simulates fire_terminal_flips never running)

  Unit tests on `assert_autoclose_debt_reconciled` (FEAT-2026-0070/T07):
    TestAutoCloseDebtReconciled — marker-gated predecessor-debt guard.

assert_terminal_flips_fired is pure file-state; no tempdir-git repo is
required. The WU body's gpgSign-false mandate applies to tests that DO
create tempdir git repos — these tests do not.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()


_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

DUMMY_HEAD = "0000000000000000000000000000000000000000"


def _make_close_wu(
    feature_dir: Path,
    feature_id: str = "FEAT-2026-9999",
    gate_num: int = 2,
    verdict: str | None = "met",
) -> "loop.WorkUnit":
    """Build a WorkUnit instance pointing at the close-WU file in feature_dir."""
    close_id = f"{feature_id}/G{gate_num}-CLOSE"
    return loop.WorkUnit(
        wu_id=close_id,
        file=feature_dir / "WU-close.md",
        depends_on=[],
        type="close",
        model="opus",
        status="done",
        attempts=1,
        title="Close",
        body=_WU_BODY,
        verdict=verdict,
    )


def _write_feature_scaffold(
    repo_root: Path,
    feature_id: str = "FEAT-2026-9999",
    gate_num: int = 2,
    gate_status: str = "passed",
    roadmap_row_status: str = "done",
    archive_anchor_present: bool = True,
    wu_verdict: str = "met",
    roadmap_priority_column: bool = False,
) -> Path:
    """Write a .specfuse scaffold matching the requested post-flip state.

    Returns the feature_dir. Defaults represent the "all flips fired" state
    so individual tests can flip one knob to negative.
    """
    specfuse = repo_root / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    feature_dir = specfuse / "features" / f"{feature_id}-test"
    feature_dir.mkdir(parents=True)

    gate_file_name = f"GATE-{gate_num:02d}.md"
    close_id = f"{feature_id}/G{gate_num}-CLOSE"

    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nbranch: feat/test\n"
        f"roadmap_goal: test\nstatus: done\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n  - gate: {gate_num}\n    file: {gate_file_name}\n"
        f"    work_units:\n      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: []\n```\n"
    )
    (feature_dir / gate_file_name).write_text(
        f"---\ngate: {gate_num}\nstatus: {gate_status}\n---\n\n# Gate {gate_num}\n"
    )
    (feature_dir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: done\nattempts: 1\nverdict: {wu_verdict}\n---\n\n# Close{_WU_BODY}"
    )

    if roadmap_priority_column:
        # Non-canonical shape: a Priority column sits BEFORE Status, shifting
        # Status from column 3 to column 4. Exercises header-name parsing.
        roadmap_table = (
            f"| Feature ID | Title | Priority | Status | Folder |\n"
            f"|------------|-------|----------|--------|--------|\n"
            f"| {feature_id} | Test feature | P2 | {roadmap_row_status} | — |\n\n"
        )
    else:
        roadmap_table = (
            f"| Feature ID | Title | Status | Folder | Detail |\n"
            f"|------------|-------|--------|--------|--------|\n"
            f"| {feature_id} | Test feature | {roadmap_row_status} | — | — |\n\n"
        )
    (specfuse / "roadmap.md").write_text(
        f"---\nproject: test\n---\n\n# Roadmap\n\n"
        f"{roadmap_table}"
        f"## {feature_id} — Test feature\n\nContent.\n"
    )

    anchor_line = (
        f'<a id="{feature_id.lower()}"></a>\n## {feature_id} — Test feature\n'
        if archive_anchor_present
        else ""
    )
    (specfuse / "roadmap-archive.md").write_text(
        "---\nproject: test\n---\n\n# Archived\n\n"
        "<!-- Archived sections appended below -->\n"
        f"{anchor_line}"
    )

    return feature_dir


# --------------------------------------------------------------------------- #
# assert_terminal_flips_fired                                                  #
# --------------------------------------------------------------------------- #


class TestAssertTerminalFlipsFired(unittest.TestCase):

    def test_close_with_verdict_met_passes_when_flips_fire(self):
        """All three side-effects present → guard returns (True, "")."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(root)
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_close_with_verdict_met_fails_when_gate_unflipped(self):
        """Gate stayed `awaiting_review`: guard names terminal_gate_not_passed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(
                root, gate_status="awaiting_review",
            )
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertTrue(
                reason.startswith("terminal_gate_not_passed:"),
                msg=f"unexpected reason: {reason!r}",
            )
            self.assertIn("awaiting_review", reason)

    def test_close_with_verdict_met_fails_when_row_active(self):
        """Gate passed but roadmap row still active: roadmap_row_not_done."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(
                root, roadmap_row_status="active",
            )
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertTrue(
                reason.startswith("roadmap_row_not_done:"),
                msg=f"unexpected reason: {reason!r}",
            )
            self.assertIn("active", reason)

    def test_close_row_missing_names_the_fix(self):
        """#127: when the roadmap row was dropped before dispatch, the reason
        must point at the recovery (restore + re-commit, dispatch via
        --prepare), not just report 'not found'."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(root)
            # Drop the row: a header-only roadmap with no row for the feature.
            (root / ".specfuse" / "roadmap.md").write_text(
                "---\nproject: test\n---\n\n# Roadmap\n\n"
                "| Feature ID | Title | Status | Folder | Detail |\n"
                "|------------|-------|--------|--------|--------|\n"
            )
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertTrue(
                reason.startswith("roadmap_row_not_done:"),
                msg=f"unexpected reason: {reason!r}",
            )
            self.assertIn("--prepare", reason)

    def test_close_passes_with_priority_column_roadmap(self):
        """Issue #104: roadmap with a Priority column before Status.

        Positional parsing read the Priority cell ('P2') as the status and
        false-escalated roadmap_row_not_done. Header-name parsing must find
        the real Status column and pass.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(
                root, roadmap_priority_column=True,
            )
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_close_fails_with_priority_column_when_row_active(self):
        """Priority-column table, row genuinely active → still flagged, and the
        reason reports the real Status cell, not the Priority token."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(
                root, roadmap_priority_column=True,
                roadmap_row_status="active",
            )
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertTrue(
                reason.startswith("roadmap_row_not_done:"),
                msg=f"unexpected reason: {reason!r}",
            )
            self.assertIn("active", reason)
            self.assertNotIn("P2", reason)

    def test_close_with_verdict_met_fails_when_archive_anchor_absent(self):
        """Gate + row done but archive missing the lower-cased anchor."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(
                root, archive_anchor_present=False,
            )
            wu = _make_close_wu(feature_dir)
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertTrue(
                reason.startswith("archive_anchor_missing:"),
                msg=f"unexpected reason: {reason!r}",
            )
            self.assertIn("feat-2026-9999", reason)

    def test_close_with_hedged_verdict_skips_guard(self):
        """verdict=met_locally → guard returns (True, "") without checks.

        Asserts the short-circuit: even if every flip is missing, the guard
        passes when the on-disk verdict is hedged. The hedge says "no
        terminal flips are expected" — demanding them would be wrong.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(
                root,
                gate_status="awaiting_review",
                roadmap_row_status="active",
                archive_anchor_present=False,
                wu_verdict="met_locally",
            )
            wu = _make_close_wu(feature_dir, verdict="met_locally")
            ok, reason = loop.assert_terminal_flips_fired(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail for hedged verdict: {reason!r}")
            self.assertEqual(reason, "")


# --------------------------------------------------------------------------- #
# verify_post_pass_invariants — dispatcher behavior                            #
# --------------------------------------------------------------------------- #


class TestVerifyPostPassInvariants(unittest.TestCase):

    def test_returns_true_for_implementation_type(self):
        """No invariants registered for `implementation` → (True, "")."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = _write_feature_scaffold(root)
            wu = loop.WorkUnit(
                wu_id="FEAT-2026-9999/T01",
                file=feature_dir / "WU-close.md",
                depends_on=[],
                type="implementation",
                model="sonnet",
                status="done",
                attempts=1,
                title="T01",
                body=_WU_BODY,
            )
            ok, reason = loop.verify_post_pass_invariants(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok)
            self.assertEqual(reason, "")

    def test_close_key_registered(self):
        """`close` key is populated in POST_PASS_INVARIANTS_BY_TYPE."""
        self.assertIn("close", loop.POST_PASS_INVARIANTS_BY_TYPE)
        self.assertTrue(
            loop.POST_PASS_INVARIANTS_BY_TYPE["close"],
            "close key must hold at least one assertion callable",
        )
        self.assertIn(
            loop.assert_terminal_flips_fired,
            loop.POST_PASS_INVARIANTS_BY_TYPE["close"],
        )


# --------------------------------------------------------------------------- #
# FEAT-2026-0015/T06 regression canary                                         #
# --------------------------------------------------------------------------- #


class TestFeat20260015T06Regression(unittest.TestCase):
    """Reproduces the FEAT-2026-0015/T06 wiring-race bug shape.

    Scenario: close WU writes `verdict: met` to its frontmatter. In a
    regressed driver, `fire_terminal_flips` would never run (e.g. because
    the in-memory `wu.verdict` was loaded BEFORE dispatch, leaving the
    close-path check oblivious to the agent's just-written value). The
    on-disk state thus shows verdict=met but gate=awaiting_review, row=active,
    archive anchor absent. The post-pass guard MUST surface this.

    This test is the canary: if a future change re-introduces the race —
    OR neutralizes the post-pass check — this assertion fails and the WU
    cannot ship hollow.
    """

    def test_feat_2026_0015_t06_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Simulate the post-pass driver state when fire_terminal_flips
            # was never invoked: WU verdict=met on disk, but none of the
            # three flips fired.
            feature_dir = _write_feature_scaffold(
                root,
                gate_status="awaiting_review",
                roadmap_row_status="active",
                archive_anchor_present=False,
                wu_verdict="met",
            )
            wu = _make_close_wu(feature_dir, verdict="met")

            ok, reason = loop.verify_post_pass_invariants(
                wu, feature_dir, root, DUMMY_HEAD,
            )

            self.assertFalse(
                ok,
                "post-pass guard MUST flag the T06 wiring-race state "
                "(verdict=met on disk, flips absent). If this assertion "
                "passes, the guard is neutralized.",
            )
            # The first assertion in POST_PASS_INVARIANTS_BY_TYPE['close']
            # surfaces the gate-not-passed condition (others would too).
            self.assertTrue(
                reason.startswith("terminal_gate_not_passed:"),
                msg=f"unexpected reason: {reason!r}",
            )


# --------------------------------------------------------------------------- #
# assert_autoclose_debt_reconciled (FEAT-2026-0070/T07)                       #
# --------------------------------------------------------------------------- #


_DEBT_MARKER = (
    "<!-- specfuse:autoclose-debt gate=1 wus=T01 criteria=1 predicate=v1 -->"
)


def _write_two_gate_scaffold(
    repo_root: Path,
    feature_id: str = "FEAT-2026-8888",
    retro_text: str = "",
    terminal_auto_close: bool = False,
) -> Path:
    """Feature dir with gate 1 (auto-closed) and gate 2 (terminal, close WU).

    `load_graph(feature_dir).gates[-1].number == 2`, so gate 1 is always a
    predecessor of the terminal gate. RETROSPECTIVE.md is written verbatim
    from `retro_text` so tests fully control the debt marker and the
    deferral-section content.
    """
    specfuse = repo_root / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    feature_dir = specfuse / "features" / f"{feature_id}-test"
    feature_dir.mkdir(parents=True)

    close_id = f"{feature_id}/G2-CLOSE"
    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nbranch: feat/test\n"
        f"roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n"
        f"  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n      - id: {feature_id}/T01\n        file: WU-01.md\n"
        f"        depends_on: []\n"
        f"  - gate: 2\n    file: GATE-02.md\n"
        f"    work_units:\n      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: []\n```\n"
    )
    (feature_dir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\nstatus: done\n"
        f"attempts: 1\nverdict: met\n"
        f"auto_close: {'true' if terminal_auto_close else 'false'}\n"
        f"---\n\n# Close{_WU_BODY}"
    )
    (feature_dir / "RETROSPECTIVE.md").write_text(retro_text)
    return feature_dir


class TestAutoCloseDebtReconciled(unittest.TestCase):

    def test_marked_predecessor_debt_unmentioned_fails(self):
        """Gate 1 auto-closed with T06's marker; terminal deferral section
        never names gate 1 -> (False, reason) with autoclose_debt_unreconciled."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retro = (
                f"## Gate 1 — auto-closed (predicate=v1)\n\n"
                f"## What the loop did NOT verify (gate 1)\n\n"
                f"{_DEBT_MARKER}\n\n- **T01** (`WU-01.md`)\n  - deferred: x\n\n"
                f"## Cost analysis\n\nn/a\n\n"
                f"## What the loop did NOT verify\n\n"
                f"Nothing outstanding for this close.\n"
            )
            feature_dir = _write_two_gate_scaffold(root, retro_text=retro)
            wu = _make_close_wu(
                feature_dir, feature_id="FEAT-2026-8888", gate_num=2,
            )
            ok, reason = loop.assert_autoclose_debt_reconciled(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertFalse(ok)
            self.assertIn("autoclose_debt_unreconciled", reason)
            self.assertIn("1", reason)

    def test_marked_predecessor_debt_mentioned_passes(self):
        """Identical fixture, but the terminal deferral section DOES name
        gate 1 -> (True, "")."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retro = (
                f"## Gate 1 — auto-closed (predicate=v1)\n\n"
                f"## What the loop did NOT verify (gate 1)\n\n"
                f"{_DEBT_MARKER}\n\n- **T01** (`WU-01.md`)\n  - deferred: x\n\n"
                f"## Cost analysis\n\nn/a\n\n"
                f"## What the loop did NOT verify\n\n"
                f"gate 1's deferred criterion was walked and verified here.\n"
            )
            feature_dir = _write_two_gate_scaffold(root, retro_text=retro)
            wu = _make_close_wu(
                feature_dir, feature_id="FEAT-2026-8888", gate_num=2,
            )
            ok, reason = loop.assert_autoclose_debt_reconciled(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_unmarked_autoclose_is_not_debt_and_does_not_fire(self):
        """Same shape, marker comment removed -> (True, ""): the marker is
        the satisfiability gate. This is what keeps the invariant off every
        feature that closed before T06 shipped (GATE-02-REVIEW.md)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retro = (
                "## Gate 1 — auto-closed (predicate=v1)\n\n"
                "## What the loop did NOT verify (gate 1)\n\n"
                "- **T01** (`WU-01.md`)\n  - deferred: x\n\n"
                "## Cost analysis\n\nn/a\n\n"
                "## What the loop did NOT verify\n\n"
                "Nothing outstanding for this close.\n"
            )
            feature_dir = _write_two_gate_scaffold(root, retro_text=retro)
            wu = _make_close_wu(
                feature_dir, feature_id="FEAT-2026-8888", gate_num=2,
            )
            ok, reason = loop.assert_autoclose_debt_reconciled(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_terminal_auto_close_short_circuits(self):
        """The terminal close WU itself is auto_close: true -> (True, "")
        even though gate 1 carries an unreconciled marker: no session ran, so
        there is no one to hold responsible."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            retro = (
                f"## Gate 1 — auto-closed (predicate=v1)\n\n"
                f"## What the loop did NOT verify (gate 1)\n\n"
                f"{_DEBT_MARKER}\n\n- **T01** (`WU-01.md`)\n  - deferred: x\n"
            )
            feature_dir = _write_two_gate_scaffold(
                root, retro_text=retro, terminal_auto_close=True,
            )
            wu = _make_close_wu(
                feature_dir, feature_id="FEAT-2026-8888", gate_num=2,
            )
            ok, reason = loop.assert_autoclose_debt_reconciled(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_marker_for_terminal_gate_itself_is_not_a_predecessor(self):
        """A debt marker naming the terminal gate (2) itself must not fire —
        only markers for gates earlier than the terminal one are predecessors."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            terminal_marker = (
                "<!-- specfuse:autoclose-debt gate=2 wus=T01 criteria=1 "
                "predicate=v1 -->"
            )
            retro = (
                f"## What the loop did NOT verify (gate 2)\n\n"
                f"{terminal_marker}\n\n- **T01** (`WU-01.md`)\n  - deferred: x\n"
            )
            feature_dir = _write_two_gate_scaffold(root, retro_text=retro)
            wu = _make_close_wu(
                feature_dir, feature_id="FEAT-2026-8888", gate_num=2,
            )
            ok, reason = loop.assert_autoclose_debt_reconciled(
                wu, feature_dir, root, DUMMY_HEAD,
            )
            self.assertTrue(ok, msg=f"unexpected fail: {reason!r}")
            self.assertEqual(reason, "")

    def test_registered_after_terminal_flips_fired(self):
        """AC7: registration order — assert_terminal_flips_fired fires first,
        the more fundamental finding (verify_post_pass_invariants returns on
        first failure)."""
        registered = loop.POST_PASS_INVARIANTS_BY_TYPE["close"]
        self.assertIn(loop.assert_terminal_flips_fired, registered)
        self.assertIn(loop.assert_autoclose_debt_reconciled, registered)
        self.assertLess(
            registered.index(loop.assert_terminal_flips_fired),
            registered.index(loop.assert_autoclose_debt_reconciled),
            "assert_terminal_flips_fired must fire before "
            "assert_autoclose_debt_reconciled",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
