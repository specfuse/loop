#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Spinning re-arm reproduction gate (#200).

After a spinning_signature_repeat escalation, the driver used to re-dispatch
a re-armed WU with no evidence the escalated failure was ever reproduced —
FEAT-2026-0049/WU-06 was re-armed twice on test-subset diagnoses; the third
re-arm (first full reproduction) found the real defect immediately.

Covers:
  - the spinning escalation stamps escalation_reason/class/signature into
    WU frontmatter (the dispatch path cannot read events.jsonl);
  - rearm_reproduction_gate unit behaviour (opt-outs, match, mismatch,
    override, unrecorded signature);
  - integration: a re-armed spinning WU without reproduction evidence is
    refused (re_arm_rejected, back to blocked_human, dispatch never runs);
    with reproduced_signature it dispatches.
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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


class TestRearmReproductionGateUnit(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_wu(self, extra: str = "") -> Path:
        wu_file = self._root / "WU-T01.md"
        wu_file.write_text(
            "---\nid: FEAT-2026-9999/T01\ntype: implementation\n"
            "model: sonnet\nstatus: pending\nattempts: 0\n"
            f"{extra}---\n\n# T01{_WU_BODY}"
        )
        return wu_file

    def test_never_escalated_passes(self):
        ok, reason = loop.rearm_reproduction_gate(_make_wu(self._write_wu()))
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_escalated_but_not_rearmed_passes(self):
        """escalation fields present but re_arm_count 0/absent: not a re-arm
        dispatch — the gate must not fire."""
        wu_file = self._write_wu(
            "escalation_reason: spinning_signature_repeat\n"
            "escalation_failure_signature: test_foo\n"
        )
        ok, _ = loop.rearm_reproduction_gate(_make_wu(wu_file))
        self.assertTrue(ok)

    def test_rearmed_without_evidence_refused(self):
        wu_file = self._write_wu(
            "escalation_reason: spinning_signature_repeat\n"
            "escalation_failure_signature: test_foo\n"
            "re_arm_count: 1\n"
        )
        ok, reason = loop.rearm_reproduction_gate(_make_wu(wu_file))
        self.assertFalse(ok)
        self.assertIn("test_foo", reason)
        self.assertIn("reproduced_signature", reason)

    def test_matching_reproduction_passes(self):
        wu_file = self._write_wu(
            "escalation_reason: spinning_signature_repeat\n"
            "escalation_failure_signature: test_foo\n"
            "re_arm_count: 1\n"
            "reproduced_signature: test_foo\n"
        )
        ok, _ = loop.rearm_reproduction_gate(_make_wu(wu_file))
        self.assertTrue(ok)

    def test_mismatched_reproduction_refused(self):
        """A stale reproduced_signature from an earlier escalation must not
        satisfy a NEW signature."""
        wu_file = self._write_wu(
            "escalation_reason: spinning_signature_repeat\n"
            "escalation_failure_signature: test_bar\n"
            "re_arm_count: 2\n"
            "reproduced_signature: test_foo\n"
        )
        ok, reason = loop.rearm_reproduction_gate(_make_wu(wu_file))
        self.assertFalse(ok)
        self.assertIn("test_bar", reason)

    def test_override_passes(self):
        wu_file = self._write_wu(
            "escalation_reason: spinning_signature_repeat\n"
            "escalation_failure_signature: test_foo\n"
            "re_arm_count: 1\n"
            "re_arm_override: true\n"
        )
        ok, _ = loop.rearm_reproduction_gate(_make_wu(wu_file))
        self.assertTrue(ok)

    def test_unrecorded_signature_requires_override(self):
        """Empty escalation_failure_signature: nothing to match against —
        only the explicit override may pass."""
        wu_file = self._write_wu(
            "escalation_reason: spinning_signature_repeat\n"
            "escalation_failure_signature: \"\"\n"
            "re_arm_count: 1\n"
            "reproduced_signature: whatever\n"
        )
        ok, reason = loop.rearm_reproduction_gate(_make_wu(wu_file))
        self.assertFalse(ok)
        self.assertIn("re_arm_override", reason)


def _write_feature(root: Path, feature_id: str, slug: str,
                   t01_extra_fm: str = "") -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: feat/{slug}\nroadmap_goal: test\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n{t01_extra_fm}---\n\n# T01{_WU_BODY}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{_WU_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


class TestSpinningRearmIntegration(unittest.TestCase):

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

    def test_spinning_escalation_stamps_frontmatter(self):
        """Two identical failure signatures → spinning escalation → the
        escalation identity lands in WU frontmatter."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_feature(root, "FEAT-2026-9981", "stamp")

            def fake_dispatch(wu, fn, ct=True):
                Path("src").mkdir(exist_ok=True)
                Path("src/impl.py").write_text("VALUE = 1\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - src/impl.py\n```\n")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None:
                        (False, "### tests: FAIL\nFAIL: test_foo"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            fm, _ = loop.read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(fm.get("status"), "blocked_human")
            self.assertEqual(fm.get("escalation_reason"),
                             "spinning_signature_repeat")
            self.assertEqual(fm.get("escalation_failure_class"), "tests")
            self.assertEqual(fm.get("escalation_failure_signature"),
                             "test_foo")

    def test_rearm_without_reproduction_rejected(self):
        """A re-armed spinning WU with no reproduction evidence: dispatch
        never runs, WU back to blocked_human, re_arm_rejected recorded."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_feature(
                root, "FEAT-2026-9982", "rejected",
                t01_extra_fm=(
                    "escalation_reason: spinning_signature_repeat\n"
                    "escalation_failure_class: tests\n"
                    "escalation_failure_signature: test_foo\n"
                    "re_arm_count: 1\n"
                ),
            )
            dispatched = []

            def fake_dispatch(wu, fn, ct=True):
                dispatched.append(wu.wu_id)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "gate must halt on the rejected re-arm")
            self.assertNotIn("FEAT-2026-9982/T01", dispatched,
                             "the WU must never reach dispatch")

            fm, _ = loop.read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(fm.get("status"), "blocked_human")

            events = _read_events(fdir / "events.jsonl")
            rejected = [e for e in events
                        if e["event_type"] == "re_arm_rejected"
                        and e["correlation_id"] == "FEAT-2026-9982/T01"]
            self.assertEqual(len(rejected), 1)
            self.assertEqual(rejected[0]["payload"]["reason"],
                             "spinning_reproduction_missing")

    def test_rearm_with_reproduction_dispatches(self):
        """reproduced_signature matching the escalated signature: the WU
        dispatches normally and passes."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_feature(
                root, "FEAT-2026-9983", "reproduced",
                t01_extra_fm=(
                    "escalation_reason: spinning_signature_repeat\n"
                    "escalation_failure_class: tests\n"
                    "escalation_failure_signature: test_foo\n"
                    "re_arm_count: 1\n"
                    "reproduced_signature: test_foo\n"
                ),
            )
            dispatched = []

            def fake_dispatch(wu, fn, ct=True):
                dispatched.append(wu.wu_id)
                if wu.wu_id.endswith("/T01"):
                    Path("src").mkdir(exist_ok=True)
                    Path("src/impl.py").write_text("VALUE = 1\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/impl.py\n```\n")
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            self.assertIn("FEAT-2026-9983/T01", dispatched)
            fm, _ = loop.read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(fm.get("status"), "done")


if __name__ == "__main__":
    unittest.main()
