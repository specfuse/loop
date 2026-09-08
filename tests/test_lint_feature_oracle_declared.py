#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the feature-oracle-declared lint (FEAT-2026-0101/T03).

A gate carrying no `feature_oracle` is an ERROR when its feature is
`active`, a WARN when `planned`/`blocked`/`deferred`, and skipped when the
gate is `passed` or the feature is `done`/`abandoned`. Graduating by feature
status (not gate status alone) is the whole design — see the WU body.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _make_feature(
    tmpdir: str, feature_status: str, gate_status: str = "open",
    feature_oracle: "str | None" = None,
) -> Path:
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9998\n"
        "title: Feature-oracle-declared lint test\n"
        "branch: feat/feature-oracle-declared-test\n"
        "roadmap_goal: Verify feature-oracle-declared lint.\n"
        f"status: {feature_status}\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9998/T01\n"
        "        file: WU-01-x.md\n"
        "        depends_on: []\n"
        "```\n"
    )
    # Gate 1 carries a substantive unit, as a real single-gate feature does.
    # The fixture used `work_units: []` until #3262, which made the gate
    # indistinguishable from one `plan-next` has not drafted — the state the
    # rule must now skip. Without a real unit here these cases would assert
    # against a shape no dispatchable feature ever has.
    _wu(feature, "WU-01-x.md", "FEAT-2026-9998/T01", "implementation")

    gate_lines = ["---\n", "gate: 1\n", f"status: {gate_status}\n"]
    if feature_oracle is not None:
        gate_lines.append(f'feature_oracle: "{feature_oracle}"\n')
    gate_lines.append("---\n\n# Gate 1\n")
    (feature / "GATE-01.md").write_text("".join(gate_lines))

    return feature


def _wu(feature: Path, name: str, wu_id: str, wu_type: str) -> None:
    (feature / name).write_text(
        f"---\nid: {wu_id}\ntype: {wu_type}\nstatus: pending\nattempts: 0\n---\n\n# {wu_id}\n"
    )


def _make_multigate_feature(
    tmpdir: str, feature_status: str, gate1_oracle: "str | None" = None,
    gate2_drafted: bool = False,
) -> Path:
    """A three-gate feature shaped the way `/draft-feature` actually writes one.

    Gate 1 carries real substantive units. Gate 2 is skeletal (`work_units:
    []`) because `plan-next` has not drafted it. Gate 3 carries only the
    terminal `close` placeholder that lets the linter identify gate 1 as
    non-terminal. `gate2_drafted` promotes gate 2 to the state `plan-next`
    leaves it in, which is when its own oracle becomes due.
    """
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    gate2_units = (
        "      - id: FEAT-2026-9997/T02\n"
        "        file: WU-02-x.md\n"
        "        depends_on: []\n"
        if gate2_drafted
        else ""
    )
    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9997\n"
        "title: Multi-gate oracle lint test\n"
        "branch: feat/multigate-oracle-test\n"
        "roadmap_goal: Verify skeletal later gates carry no oracle requirement.\n"
        f"status: {feature_status}\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n"
        "  - gate: 1\n"
        "    file: GATE-01.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9997/T01\n"
        "        file: WU-01-x.md\n"
        "        depends_on: []\n"
        "  - gate: 2\n"
        "    file: GATE-02.md\n"
        f"    work_units:{'' if gate2_drafted else ' []'}\n"
        f"{gate2_units}"
        "  - gate: 3\n"
        "    file: GATE-03.md\n"
        "    work_units:\n"
        "      - id: FEAT-2026-9997/G3-CLOSE\n"
        "        file: WU-90-gate-3-close.md\n"
        "        depends_on: []\n"
        "```\n"
    )

    _wu(feature, "WU-01-x.md", "FEAT-2026-9997/T01", "implementation")
    _wu(feature, "WU-90-gate-3-close.md", "FEAT-2026-9997/G3-CLOSE", "close")
    if gate2_drafted:
        _wu(feature, "WU-02-x.md", "FEAT-2026-9997/T02", "implementation")

    g1 = ["---\n", "gate: 1\n", "status: open\n"]
    if gate1_oracle is not None:
        g1.append(f'feature_oracle: "{gate1_oracle}"\n')
    g1.append("---\n\n# Gate 1\n")
    (feature / "GATE-01.md").write_text("".join(g1))
    (feature / "GATE-02.md").write_text("---\ngate: 2\nstatus: open\n---\n\n# Gate 2\n")
    (feature / "GATE-03.md").write_text("---\ngate: 3\nstatus: open\n---\n\n# Gate 3\n")

    return feature


class TestLintFeatureOracleDeclared(unittest.TestCase):

    def _run(self, feature: Path) -> tuple[list[str], str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            fm, _ = lint_plan.read_frontmatter(feature / "PLAN.md")
            errs = lint_plan.lint_feature_oracle_declared(feature, fm)
        return errs, buf.getvalue()

    def test_active_feature_missing_oracle_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "active")
            errs, out = self._run(feature)
            self.assertEqual(len(errs), 1, f"errs={errs!r}")
            self.assertIn("GATE-01", errs[0])
            self.assertIn("ERROR", errs[0])
            self.assertNotIn("WARN", out)

    def test_planned_feature_missing_oracle_is_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "planned")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertIn("WARN", out)
            self.assertIn("GATE-01", out)

    def test_blocked_feature_missing_oracle_is_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "blocked")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertIn("WARN", out)

    def test_deferred_feature_missing_oracle_is_warn(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "deferred")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertIn("WARN", out)

    def test_passed_gate_and_done_feature_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "active", gate_status="passed")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("WARN", out)

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "done")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("WARN", out)

        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(tmpdir, "abandoned")
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("WARN", out)

    def test_declared_oracle_reports_nothing(self):
        for status in ("active", "planned", "blocked", "deferred", "done", "abandoned"):
            with tempfile.TemporaryDirectory() as tmpdir:
                feature = _make_feature(
                    tmpdir, status, feature_oracle="python3 -m unittest -q"
                )
                errs, out = self._run(feature)
                self.assertEqual(errs, [], f"status={status} errs={errs!r}")
                self.assertNotIn("WARN", out, f"status={status} out={out!r}")


class TestSkeletalLaterGatesAreSkipped(unittest.TestCase):
    """A gate `plan-next` has not drafted yet carries no oracle requirement (#3262).

    Later gates are deliberately skeletal at feature-planning time: the
    methodology details only as far as the next gate, and each later gate's
    oracle is authored by the prior gate's `plan-next` along with its work
    units. Requiring one before the gate is designed makes every multi-gate
    feature un-draftable while `active`, and reintroduces at gate level the
    exact problem that put the key on `GATE-NN.md` instead of `PLAN.md`.
    """

    def _run(self, feature: Path) -> tuple[list[str], str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            fm, _ = lint_plan.read_frontmatter(feature / "PLAN.md")
            errs = lint_plan.lint_feature_oracle_declared(feature, fm)
        return errs, buf.getvalue()

    def test_skeletal_and_placeholder_gates_are_skipped_while_gate_one_is_required(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_multigate_feature(tmpdir, "active", gate1_oracle=None)
            errs, _ = self._run(feature)
            # Gate 1 has substantive units and no oracle: still an ERROR.
            self.assertEqual(len(errs), 1, f"errs={errs!r}")
            self.assertIn("GATE-01", errs[0])
            # Gate 2 (no work units) and gate 3 (terminal close placeholder
            # only) are not drafted yet — neither may be reported.
            joined = " ".join(errs)
            self.assertNotIn("GATE-02", joined)
            self.assertNotIn("GATE-03", joined)

    def test_multigate_feature_with_gate_one_oracle_is_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_multigate_feature(
                tmpdir, "active", gate1_oracle="python3 -m unittest -q"
            )
            errs, out = self._run(feature)
            self.assertEqual(errs, [], f"errs={errs!r}")
            self.assertNotIn("WARN", out, f"out={out!r}")

    def test_later_gate_that_has_been_drafted_is_required_again(self):
        # Once `plan-next` gives gate 2 substantive units, its oracle is due.
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_multigate_feature(
                tmpdir, "active", gate1_oracle="python3 -m unittest -q",
                gate2_drafted=True,
            )
            errs, _ = self._run(feature)
            self.assertEqual(len(errs), 1, f"errs={errs!r}")
            self.assertIn("GATE-02", errs[0])

    def test_skeletal_gates_are_skipped_on_a_planned_feature_too(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_multigate_feature(
                tmpdir, "planned", gate1_oracle="python3 -m unittest -q"
            )
            errs, out = self._run(feature)
            self.assertEqual(errs, [])
            self.assertNotIn("GATE-02", out)
            self.assertNotIn("GATE-03", out)


if __name__ == "__main__":
    unittest.main()
