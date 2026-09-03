#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The verdict is binary: `met` or `not_met` — FEAT-2026-0085/T01.

Across 273 features, 48% of verdict-bearing closes ended `met_locally` or
`partially_met`, and 59 of those were later flipped to `met` by
`/accept-hedged-close` with nothing re-run. The two soft-success values are
retired here. What they leave behind is deliberately asymmetric:

- **Writing one is rejected.** `assert_verdict_well_formed` runs at outcome
  time on the close just dispatched, so a close written from now on cannot
  record a hedge. The rejection names the two legal values and the migration
  note, because "not in VERDICT_VALUES" alone does not tell the operator of a
  standing hedged feature what to do.
- **Reading one still works.** 42 hedged closes are `done` on disk across the
  corpus. `load_wu` and `recheck_terminal_verdict` must parse them without
  crashing — `LEGACY_VERDICT_VALUES` is what keeps that readable — and the
  re-check refuses the flips with a reason that says `legacy` rather than
  presenting the value as merely unrecognised.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

from specfuse.loop import closing_requirements as creq  # noqa: E402

DUMMY_HEAD = "0" * 40

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _write_close_wu(
    feature_dir: Path, wu_id: str, verdict: str | None, status: str = "pending",
) -> Path:
    """A close WU on disk. `assert_verdict_well_formed` re-reads from the file,
    never from the in-memory WorkUnit, so the frontmatter here is what counts."""
    path = feature_dir / "WU-close.md"
    verdict_line = f"verdict: {verdict}\n" if verdict is not None else ""
    path.write_text(
        f"---\nid: {wu_id}\ntype: close\nmodel: opus\n"
        f"status: {status}\nattempts: 1\n{verdict_line}---\n\n# Close{_WU_BODY}"
    )
    return path


def _close_work_unit(path: Path, wu_id: str, verdict: str | None) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=path,
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


def _make_repo_with_feature(
    root: Path,
    feature_id: str,
    close_verdict: str | None,
    gate_num: int = 2,
) -> tuple[Path, Path]:
    """`.specfuse` scaffold with one terminal gate whose close WU is `done`.

    No git repo: `recheck_terminal_verdict` and `fire_terminal_flips` only do
    file operations.
    """
    specfuse = root / ".specfuse"
    specfuse.mkdir(parents=True, exist_ok=True)
    feature_dir = specfuse / "features" / f"{feature_id}-test"
    feature_dir.mkdir(parents=True)

    gate_file = f"GATE-{gate_num:02d}.md"
    close_id = f"{feature_id}/G{gate_num}-CLOSE"

    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Test\nbranch: feat/test\n"
        f"roadmap_goal: test\nstatus: active\n---\n\n# Plan\n\n```yaml\n"
        f"gates:\n  - gate: {gate_num}\n    file: {gate_file}\n"
        f"    work_units:\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: []\n```\n"
    )
    (feature_dir / gate_file).write_text(
        f"---\ngate: {gate_num}\nstatus: awaiting_review\n---\n\n# Gate {gate_num}\n"
    )
    _write_close_wu(feature_dir, close_id, close_verdict, status="done")

    (specfuse / "roadmap.md").write_text(
        f"---\nproject: test\n---\n\n# Roadmap\n\n"
        f"| Feature ID | Title | Status | Folder | Detail |\n"
        f"|------------|-------|--------|--------|--------|\n"
        f"| {feature_id} | Test feature | active | — | — |\n\n"
        f"## {feature_id} — Test feature\n\nContent.\n"
    )
    (specfuse / "roadmap-archive.md").write_text(
        "---\nproject: test\n---\n\n# Archived\n\n"
        "<!-- Archived sections appended below -->\n"
    )
    return feature_dir, root


def _read_frontmatter(path: Path) -> dict:
    fm, _ = loop.read_frontmatter(path)
    return fm


class TestVerdictVocabulary(unittest.TestCase):
    """The two sets, spelled once, imported everywhere."""

    def test_verdict_values_is_binary(self):
        self.assertEqual(creq.VERDICT_VALUES, frozenset({"met", "not_met"}))

    def test_legacy_values_are_named_and_disjoint(self):
        self.assertEqual(
            creq.LEGACY_VERDICT_VALUES, frozenset({"met_locally", "partially_met"})
        )
        self.assertFalse(
            creq.VERDICT_VALUES & creq.LEGACY_VERDICT_VALUES,
            "a value cannot be both legal and retired",
        )

    def test_loop_re_exports_both_sets(self):
        # lint_plan.py imports VERDICT_VALUES from loop.py, and the guards read
        # both through the same module. Re-exporting one but not the other is
        # how the two spellings drift apart.
        self.assertEqual(loop.VERDICT_VALUES, creq.VERDICT_VALUES)
        self.assertEqual(loop.LEGACY_VERDICT_VALUES, creq.LEGACY_VERDICT_VALUES)


class TestVerdictRejectedAtOutcome(unittest.TestCase):
    """`assert_verdict_well_formed` (close-d) on a close dispatched now."""

    def test_met_locally_is_rejected_at_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu_id = "FEAT-2026-9990/G1-CLOSE"
            path = _write_close_wu(fdir, wu_id, "met_locally")
            wu = _close_work_unit(path, wu_id, verdict=None)

            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)

            self.assertFalse(ok, "met_locally must not pass close-d")
            self.assertIn("'met'", reason, f"reason must name `met`; got {reason!r}")
            self.assertIn(
                "'not_met'", reason, f"reason must name `not_met`; got {reason!r}"
            )

    def test_partially_met_is_rejected_at_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu_id = "FEAT-2026-9990/G1-CLOSE"
            path = _write_close_wu(fdir, wu_id, "partially_met")
            wu = _close_work_unit(path, wu_id, verdict=None)

            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)

            self.assertFalse(ok)
            self.assertIn("'met'", reason)
            self.assertIn("'not_met'", reason)

    def test_legacy_rejection_points_at_the_migration_note(self):
        # An operator hitting this is mid-migration, not typo-ing a verdict.
        # "not in VERDICT_VALUES" alone leaves them nowhere to go.
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu_id = "FEAT-2026-9990/G1-CLOSE"
            path = _write_close_wu(fdir, wu_id, "met_locally")
            wu = _close_work_unit(path, wu_id, verdict=None)

            _ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)

            self.assertIn("docs/methodology.md", reason)
            self.assertIn("Migrating a hedged close", reason)

    def test_both_legal_values_pass(self):
        for verdict in ("met", "not_met"):
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as tmp:
                fdir = Path(tmp)
                wu_id = "FEAT-2026-9990/G1-CLOSE"
                path = _write_close_wu(fdir, wu_id, verdict)
                wu = _close_work_unit(path, wu_id, verdict=None)

                ok, reason = loop.assert_verdict_well_formed(
                    wu, fdir, fdir, DUMMY_HEAD
                )

                self.assertTrue(ok, reason)
                self.assertEqual(wu.verdict, verdict, "guard updates wu.verdict")

    def test_an_unrecognised_value_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu_id = "FEAT-2026-9990/G1-CLOSE"
            path = _write_close_wu(fdir, wu_id, "beautifully_done")
            wu = _close_work_unit(path, wu_id, verdict=None)

            ok, reason = loop.assert_verdict_well_formed(wu, fdir, fdir, DUMMY_HEAD)

            self.assertFalse(ok)
            self.assertIn("beautifully_done", reason)


class TestLegacyVerdictStaysReadable(unittest.TestCase):
    """42 hedged closes are `done` on disk. Reading them must not crash."""

    def test_load_wu_still_parses_a_legacy_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            fdir = Path(tmp)
            wu_id = "FEAT-2026-9991/G1-CLOSE"
            _write_close_wu(fdir, wu_id, "met_locally", status="done")
            ref = {"id": wu_id, "file": "WU-close.md", "depends_on": []}

            wu = loop.load_wu(fdir, ref)

            self.assertEqual(wu.verdict, "met_locally")

    def test_recheck_refuses_legacy_verdict_with_migration_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir, repo_root = _make_repo_with_feature(
                Path(tmp), "FEAT-2026-9992", close_verdict="met_locally",
            )

            result = loop.recheck_terminal_verdict(feature_dir, repo_root)

            self.assertFalse(result["fired"])
            self.assertIn(
                "legacy", result["reason"],
                f"a retired value is not merely unrecognised; got "
                f"{result['reason']!r}",
            )
            self.assertEqual(result["modified"], [])
            # And it touched nothing.
            self.assertEqual(
                _read_frontmatter(feature_dir / "GATE-02.md").get("status"),
                "awaiting_review",
            )
            self.assertEqual(
                _read_frontmatter(feature_dir / "PLAN.md").get("status"), "active",
            )

    def test_recheck_refuses_partially_met_the_same_way(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir, repo_root = _make_repo_with_feature(
                Path(tmp), "FEAT-2026-9993", close_verdict="partially_met",
            )

            result = loop.recheck_terminal_verdict(feature_dir, repo_root)

            self.assertFalse(result["fired"])
            self.assertIn("legacy", result["reason"])

    def test_recheck_still_fires_on_a_migrated_met_verdict(self):
        # The migration route: an operator rewrites the on-disk verdict to
        # `met`, and --recheck-verdict fires the flips through their one owner.
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir, repo_root = _make_repo_with_feature(
                Path(tmp), "FEAT-2026-9994", close_verdict="met",
            )

            result = loop.recheck_terminal_verdict(feature_dir, repo_root)

            self.assertTrue(result["fired"], result["reason"])
            self.assertEqual(
                _read_frontmatter(feature_dir / "PLAN.md").get("status"), "done",
            )

    def test_recheck_on_not_met_does_not_say_legacy(self):
        # `not_met` is a live verdict that withholds the flips, not a retired
        # one. Reporting it as legacy would send the operator to a migration
        # note that has nothing to say about it.
        with tempfile.TemporaryDirectory() as tmp:
            feature_dir, repo_root = _make_repo_with_feature(
                Path(tmp), "FEAT-2026-9995", close_verdict="not_met",
            )

            result = loop.recheck_terminal_verdict(feature_dir, repo_root)

            self.assertFalse(result["fired"])
            self.assertNotIn("legacy", result["reason"])


class TestTerminalGateMessageNotMet(unittest.TestCase):
    """The `not_met` branch replaces the hedged one (#1416 stays fixed)."""

    def _msg(self, verdict):
        return loop.terminal_gate_message(1, verdict)

    def test_not_met_points_at_the_followups_artifact(self):
        message = self._msg("not_met")
        self.assertIn("FOLLOW-UPS.md", message)

    def test_not_met_is_not_reported_as_an_inconsistency(self):
        # Withholding the flips on `not_met` is the verdict-coupling rule
        # working. Telling the operator to hand-flip PLAN.md is advice to
        # violate the contract `fire_terminal_flips` just enforced.
        message = self._msg("not_met")
        self.assertNotIn("Inconsistency", message)
        self.assertNotIn("active -> done", message)
        self.assertNotIn("status: done", message)

    def test_met_without_the_flips_is_still_an_inconsistency(self):
        self.assertIn("Inconsistency", self._msg("met"))

    def test_legacy_verdict_gets_the_migration_pointer(self):
        for verdict in ("met_locally", "partially_met"):
            with self.subTest(verdict=verdict):
                message = self._msg(verdict)
                self.assertIn(verdict, message)
                self.assertIn("docs/methodology.md", message)
                self.assertNotIn("active -> done", message)

    def test_absent_or_unrecognised_verdict_is_still_an_inconsistency(self):
        for verdict in (None, "", "garbage"):
            with self.subTest(verdict=verdict):
                self.assertIn("Inconsistency", self._msg(verdict))


if __name__ == "__main__":
    unittest.main()
