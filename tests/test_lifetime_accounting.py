#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Lifetime attempts/cost accounting across re-arms (#199).

WU frontmatter `attempts`/`cost_usd` are per-dispatch-cycle values that reset
on re-arm, but consumers read them as lifetime totals (FEAT-2026-0049/WU-06:
frontmatter said 1 attempt / $2.75; events.jsonl said 9 attempts / $30.29).

Covers:
  - fold_cumulative_on_rearm maintains cumulative_attempts from
    re_arm_history[].prior_attempts (recompute — idempotent).
  - gate_spent_usd sums cost_usd + cumulative_cost_usd (lifetime, not cycle).
  - task_completed carries type, re_arm_count, cost_usd, cumulative_cost_usd,
    attempts_lifetime, planned_cost_usd.
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


def _make_wu(wu_file: Path) -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id="FEAT-2026-9999/T01",
        file=wu_file,
        depends_on=[],
        type="implementation",
        model="sonnet",
        status="pending",
        attempts=0,
        title="T01",
        body="",
    )


class TestCumulativeAttemptsFold(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_wu(self, history_yaml: str = "") -> Path:
        wu_file = self._root / "WU-T01.md"
        wu_file.write_text(
            "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
            "model: sonnet\nstatus: pending\nattempts: 0\n"
            "re_arm_count: 2\ncost_usd: 5.0\ninput_tokens: 10\n"
            f"output_tokens: 5\n{history_yaml}---\n\n# T01{_WU_BODY}"
        )
        return wu_file

    def test_fold_accumulates_attempts_from_history(self):
        wu_file = self._write_wu(
            "re_arm_history:\n"
            "  - at: 2026-07-01T00:00:00Z\n"
            "    reason: \"first re-arm\"\n"
            "    prior_attempts: 3\n"
            "  - at: 2026-07-02T00:00:00Z\n"
            "    reason: \"second re-arm\"\n"
            "    prior_attempts: 2\n"
        )
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), loop.Backend())
        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(int(fm.get("cumulative_attempts", -1)), 5,
                         "cumulative_attempts must sum prior_attempts across "
                         "all re_arm_history entries")

    def test_fold_attempts_recompute_is_idempotent(self):
        wu_file = self._write_wu(
            "re_arm_history:\n"
            "  - at: 2026-07-01T00:00:00Z\n"
            "    reason: \"re-arm\"\n"
            "    prior_attempts: 3\n"
        )
        backend = loop.Backend()
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), backend)
        # Second fold (re-entry with cost already zeroed): recompute, not add.
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), backend)
        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(int(fm.get("cumulative_attempts", -1)), 3,
                         "recompute must not double-count on re-entry")

    def test_fold_missing_history_defaults_zero(self):
        wu_file = self._write_wu()
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), loop.Backend())
        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(int(fm.get("cumulative_attempts", -1)), 0)

    def test_fold_entries_without_prior_attempts_contribute_zero(self):
        wu_file = self._write_wu(
            "re_arm_history:\n"
            "  - at: 2026-07-01T00:00:00Z\n"
            "    reason: \"pre-#199 entry\"\n"
        )
        loop.fold_cumulative_on_rearm(_make_wu(wu_file), loop.Backend())
        fm, _ = loop.read_frontmatter(wu_file)
        self.assertEqual(int(fm.get("cumulative_attempts", -1)), 0)


class TestGateSpentIncludesCumulative(unittest.TestCase):

    def test_gate_spent_sums_cycle_plus_cumulative(self):
        """A re-armed done WU: cost_usd holds the final cycle, prior cycles
        live in cumulative_cost_usd — spent must be the sum of both."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp)
            (feature / "WU-T01.md").write_text(
                "---\nid: FEAT-2026-9701/T01\ntype: implementation\n"
                "model: sonnet\nstatus: done\nattempts: 1\n"
                "cost_usd: 2.75\ncumulative_cost_usd: 27.54\n---\n\n# T01\n"
            )
            gate = {
                "file": "GATE-01.md",
                "work_units": [
                    {"id": "FEAT-2026-9701/T01", "file": "WU-T01.md"},
                ],
            }
            self.assertAlmostEqual(
                loop.gate_spent_usd({}, gate, feature), 30.29, places=6)


class TestTaskCompletedLifetimeFields(unittest.TestCase):
    """task_completed must carry the per-WU lifetime/telemetry fields (#199)."""

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

    def test_task_completed_carries_lifetime_fields(self):
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9997"
            fdir = root / f".specfuse/features/{feature_id}-lifetime"
            fdir.mkdir(parents=True)
            t_id = f"{feature_id}/T01"
            close_id = f"{feature_id}/G1-CLOSE"
            (fdir / "PLAN.md").write_text(
                f"---\nfeature_id: {feature_id}\ntitle: Fixture\n"
                f"slug: lifetime\nbranch: feat/lifetime\nroadmap_goal: test\n"
                f"status: active\n---\n\n# Plan\n\n```yaml\ngates:\n"
                f"  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
                f"      - id: {t_id}\n        file: WU-T01.md\n"
                f"        depends_on: []\n"
                f"      - id: {close_id}\n        file: WU-close.md\n"
                f"        depends_on: [{t_id}]\n```\n"
            )
            (fdir / "GATE-01.md").write_text(
                "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
            )
            # A re-armed WU: prior cycle folded (cumulative_* populated by an
            # earlier fold), planned cost declared.
            (fdir / "WU-T01.md").write_text(
                f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
                f"status: pending\nattempts: 0\nplanned_cost_usd: 2.0\n"
                f"re_arm_count: 1\ncumulative_cost_usd: 27.54\n"
                f"cumulative_attempts: 6\ncost_usd: 0.0\n"
                f"re_arm_history:\n"
                f"  - at: 2026-07-01T00:00:00Z\n"
                f"    reason: \"re-arm\"\n"
                f"    prior_attempts: 6\n"
                f"---\n\n# T01{_WU_BODY}"
            )
            (fdir / "WU-close.md").write_text(
                f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
                f"status: pending\nattempts: 0\n---\n\n# Close{_WU_BODY}"
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "scaffold"], check=True)

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src").mkdir(exist_ok=True)
                    Path("src/impl.py").write_text("VALUE = 1\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/impl.py\n```\n",
                            {"input_tokens": 10, "output_tokens": 5,
                             "cost_usd": 1.5})
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                return ("```result\nstatus: complete\n```\n",
                        {"input_tokens": 10, "output_tokens": 5,
                         "cost_usd": 0.1})

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            events = [json.loads(ln) for ln in
                      (fdir / "events.jsonl").read_text().splitlines() if ln]
            completed = [e for e in events
                         if e["event_type"] == "task_completed"
                         and e["correlation_id"] == t_id]
            self.assertEqual(len(completed), 1)
            payload = completed[0]["payload"]
            self.assertEqual(payload["type"], "implementation")
            self.assertEqual(payload["re_arm_count"], 1)
            self.assertEqual(payload["attempts"], 1)
            self.assertEqual(payload["attempts_lifetime"], 7,
                             "6 folded prior attempts + 1 this cycle")
            self.assertAlmostEqual(payload["cost_usd"], 1.5, places=6)
            self.assertAlmostEqual(payload["cumulative_cost_usd"],
                                   29.04, places=6)
            self.assertAlmostEqual(payload["planned_cost_usd"], 2.0, places=6)


if __name__ == "__main__":
    unittest.main()
