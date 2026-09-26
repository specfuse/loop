#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A `produces_not_in_diff` refusal shows both escape hatches (FEAT-2026-0114/T02).

Nine repair attempts across six units in the 2026-09-10..26 window changed
nothing and never used `produces_unchanged:` (PLAN.md). The retry note named
the key but never showed its shape. This unit adds a worked example — one
`produces_unchanged:` entry and one `produces_amended:` entry, both naming
the attempt's own first unmatched path — to the note the next attempt reads,
and records the refusal into `refusal_history` so a second identical refusal
on an untouched tree ends the unit via `detect_deterministic_refusal_repeat`
instead of paying for a third attempt.

Integration test reuses the stubbed-dispatch harness from
`test_produces_amendment_e2e.py`.
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


def _write_minimal_feature(root: Path, feature_id: str, slug: str,
                           branch: str, produces: list) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: {branch}\nroadmap_goal: test\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    produces_yaml = "".join(f"\n  - {p}" for p in produces)
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\nmax_attempts: 3\n"
        f"produces:{produces_yaml}\n---\n\n"
        f"# T01{body}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{body}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"], check=True)
    return fdir


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    end = text.find("\n---\n", 4)
    out = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


class TestProducesRepairNoteIntegration(unittest.TestCase):
    """End-to-end: loop.run() with a dispatch stub that never repairs."""

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

    def _seed_repo(self, root: Path) -> None:
        Path("src").mkdir(exist_ok=True)
        Path("src/a.py").write_text("A = 1\n")
        Path("src/b.py").write_text("B = 1\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "pre-existing"], check=True)

    def _events(self, fdir: Path, wu_id: str) -> list:
        return [e for e in _read_events(fdir / "events.jsonl")
                if e["event_type"] == "attempt_outcome" and e["correlation_id"] == wu_id]

    def test_second_identical_refusal_ends_the_unit_and_shows_both_hatches(self):
        with integration_workspace() as root:
            os.chdir(root)
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0150", "repair-note", "feat/repair-note",
                produces=["src/a.py", "src/b.py"])

            failure_notes: list = []

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                if wu.wu_id.endswith("/T01"):
                    failure_notes.append(failure_note)
                    # Only touches src/a.py every attempt; src/b.py stays
                    # unmatched and unjustified — the refusal repeats exactly.
                    Path("src/a.py").write_text(
                        f"A = {len(failure_notes) + 1}\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n  - src/a.py\n"
                        "```\n"
                    )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            # Attempt 2's prompt (failure_note from attempt 1) shows both
            # escape hatches, naming the unmatched path.
            self.assertEqual(len(failure_notes), 2)
            attempt_2_note = failure_notes[1]
            self.assertIn("```result", attempt_2_note)
            self.assertIn("produces_unchanged:", attempt_2_note)
            self.assertIn("produces_amended:", attempt_2_note)
            self.assertIn("src/b.py", attempt_2_note)

            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(wu_fm.get("status"), "blocked_human")
            self.assertEqual(
                wu_fm.get("escalation_reason"), "deterministic_refusal_repeat")

            events = self._events(fdir, "FEAT-2026-0150/T01")
            self.assertEqual(len(events), 2)
            self.assertEqual(
                [e["payload"]["outcome"] for e in events],
                ["produces_not_in_diff", "produces_not_in_diff"])


if __name__ == "__main__":
    unittest.main()
