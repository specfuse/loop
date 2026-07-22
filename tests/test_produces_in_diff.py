#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Produces-vs-squash-diff cross-check (#198).

The deliverable-presence gate (FEAT-2026-0022/T02) is presence-only, so a WU
whose ``produces:`` paths are pre-existing files it was supposed to MODIFY
passes it without touching them — the FEAT-2026-0049/T06 done-without-
delivering shape. ``assert_produces_in_diff`` requires every ``produces:``
entry to match at least one path in the WU's actual squash diff (literal or
glob); an unmatched entry refuses the pass with outcome
``produces_not_in_diff``, rolls back the squash, and retries within budget.

Integration tests reuse the stubbed-dispatch harness shape from
``test_deliverable_presence_gate``.
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


def _make_wu(produces: list, wu_type: str = "implementation",
             wu_id: str = "FEAT-2026-0049/T06",
             wu_file: str = "WU-T06.md") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path(wu_file),
        depends_on=[],
        type=wu_type,
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title=wu_id,
        body="",
        produces=produces,
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


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


class TestAssertProducesInDiffUnit(unittest.TestCase):
    """Direct unit tests of assert_produces_in_diff."""

    def test_empty_produces_opts_out(self):
        ok, summary = loop.assert_produces_in_diff(_make_wu([]), [])
        self.assertTrue(ok)
        self.assertEqual(summary, "")

    def test_literal_match_passes(self):
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src/rule.py"]), ["src/rule.py", "docs/GATE-02.md"])
        self.assertTrue(ok)
        self.assertEqual(summary, "")

    def test_glob_match_passes(self):
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src/*.py"]), ["src/rule.py"])
        self.assertTrue(ok)
        self.assertEqual(summary, "")

    def test_untouched_entry_reported(self):
        """The T06 shape: produces names an existing file, the diff touches
        only gate docs — the entry must be named in the refusal."""
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src/rule.py"]), ["docs/GATE-02.md"])
        self.assertFalse(ok)
        self.assertIn("src/rule.py", summary)

    def test_all_unmatched_entries_named(self):
        ok, summary = loop.assert_produces_in_diff(
            _make_wu(["src/rule.py", "src/flags.py"]), ["docs/GATE-02.md"])
        self.assertFalse(ok)
        self.assertIn("src/rule.py", summary)
        self.assertIn("src/flags.py", summary)


def _write_minimal_feature(root: Path, feature_id: str, slug: str,
                           branch: str, produces: list) -> Path:
    """One implementation WU with `produces`, plus the close-type WU."""
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
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    produces_yaml = "".join(f"\n  - {p}" for p in produces)
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\nproduces:{produces_yaml}\n---\n\n"
        f"# T01{body}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{body}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


class TestProducesInDiffIntegration(unittest.TestCase):
    """End-to-end: loop.run() with stubbed dispatch in a temp git repo."""

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

    def _outcomes(self, events_path: Path, wu_id: str) -> list:
        return [e["payload"]["outcome"] for e in _read_events(events_path)
                if e["event_type"] == "attempt_outcome"
                and e["correlation_id"] == wu_id]

    def test_preexisting_untouched_produces_blocks(self):
        """A WU declaring a pre-existing file in produces: that touches only
        an unrelated file must NOT reach done — presence passes, diff
        cross-check refuses with produces_not_in_diff."""
        with integration_workspace() as root:
            os.chdir(root)
            # Pre-existing deliverable, committed before the feature runs —
            # presence-only checking is green over it from the start.
            Path("src").mkdir(exist_ok=True)
            Path("src/rule.py").write_text("SEVERITY = 'WARNING'\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "pre-existing rule"], check=True)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0049", "t06-shape", "feat/t06-shape",
                produces=["src/rule.py"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    # Agent touches only an unrelated doc — never the
                    # declared deliverable.
                    Path("docs").mkdir(exist_ok=True)
                    Path("docs/notes.md").write_text("notes\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - docs/notes.md\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1, "untouched-produces WU must escalate")

            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertNotEqual(t01_fm.get("status"), "done",
                                "WU whose produces path is absent from its "
                                "squash diff must NOT reach done")
            self.assertEqual(t01_fm.get("status"), "blocked_human")

            outcomes = self._outcomes(fdir / "events.jsonl",
                                      "FEAT-2026-0049/T01")
            self.assertIn("produces_not_in_diff", outcomes)
            self.assertNotIn("passed", outcomes)

            # The rejection is diagnosable (#182 family): class + signature
            # + excerpt populated on the produces_not_in_diff outcome.
            for e in _read_events(fdir / "events.jsonl"):
                if (e["event_type"] == "attempt_outcome"
                        and e["payload"]["outcome"] == "produces_not_in_diff"):
                    self.assertEqual(e["payload"]["failure_class"],
                                     "produces_not_in_diff")
                    self.assertIn("rule.py", e["payload"]["failure_signature"])
                    self.assertTrue(e["payload"]["failure_excerpt"])

    def test_touched_produces_passes(self):
        """A WU that actually modifies its declared pre-existing deliverable
        reaches done — the cross-check must not fire on an honest pass."""
        with integration_workspace() as root:
            os.chdir(root)
            Path("src").mkdir(exist_ok=True)
            Path("src/rule.py").write_text("SEVERITY = 'WARNING'\n")
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "pre-existing rule"], check=True)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0050", "honest", "feat/honest",
                produces=["src/rule.py"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src/rule.py").write_text("SEVERITY = 'ERROR'\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - src/rule.py\n```\n")
                # Close WU: satisfy the closing-deliverable guard.
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n"
                )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done",
                             "an honestly-delivered produces path must pass")
            outcomes = self._outcomes(fdir / "events.jsonl",
                                      "FEAT-2026-0050/T01")
            self.assertIn("passed", outcomes)
            self.assertNotIn("produces_not_in_diff", outcomes)


if __name__ == "__main__":
    unittest.main()
