#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A verified attempt may drop a `produces:` path it did not need (FEAT-2026-0114/T01).

`produces_not_in_diff` refuses an unmatched `produces:` entry unless the
RESULT justifies it under `produces_unchanged:` (#3268,
`test_produces_justification.py`). That escape hatch is for a path that
already holds at HEAD. This unit adds the sibling escape hatch for the other
honest shape: a path the attempt never needed at all, because the unit's
work landed somewhere else. The RESULT drops it under `produces_amended:`
with a reason, the driver rewrites the unit's own `produces:` to match, and
the pass proceeds instead of refusing with `produces_not_in_diff`.

Integration tests reuse the stubbed-dispatch harness from
`test_produces_justification.py`.
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
        f"status: pending\nattempts: 0\nproduces:{produces_yaml}\n---\n\n"
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


class TestProducesAmendmentIntegration(unittest.TestCase):
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

    def _seed_repo(self, root: Path) -> None:
        Path("src").mkdir(exist_ok=True)
        Path("src/a.py").write_text("A = 1\n")
        Path("src/b.py").write_text("B = 1\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "pre-existing"], check=True)

    def _events(self, fdir: Path, wu_id: str) -> list:
        return [e for e in _read_events(fdir / "events.jsonl")
                if e["event_type"] == "attempt_outcome" and e["correlation_id"] == wu_id]

    def test_amended_path_is_dropped_and_pass_proceeds(self):
        """attempt 1 writes only src/a.py, drops src/b.py under
        `produces_amended:` with a reason: the pass proceeds on attempt 1,
        `produces:` on disk shrinks, `produces_dropped:` records why, and the
        passed attempt_outcome carries `produces_amended`."""
        with integration_workspace() as root:
            os.chdir(root)
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0114", "amended", "feat/amended",
                produces=["src/a.py", "src/b.py"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src/a.py").write_text("A = 2\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n  - src/a.py\n"
                        "produces_amended:\n"
                        "  - path: src/b.py\n"
                        "    reason: work landed entirely in src/a.py; src/b.py was never needed\n"
                        "```\n"
                    )
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            wu_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(wu_fm.get("status"), "done")
            wu_text = (fdir / "WU-T01.md").read_text()
            self.assertIn("produces:\n  - src/a.py\n", wu_text)
            self.assertNotIn("- src/b.py\n", wu_text.split("produces_dropped:")[0])
            self.assertIn("produces_dropped:", wu_text)
            self.assertIn("path: src/b.py", wu_text)
            self.assertIn("work landed entirely in src/a.py", wu_text)

            events = self._events(fdir, "FEAT-2026-0114/T01")
            outcomes = [e["payload"]["outcome"] for e in events]
            self.assertEqual(outcomes, ["passed"])
            amended = events[0]["payload"].get("produces_amended")
            self.assertEqual(len(amended), 1)
            self.assertEqual(amended[0]["path"], "src/b.py")
            self.assertIn("never needed", amended[0]["reason"])

    def test_dropping_every_declared_path_is_still_refused(self):
        """An amendment that would empty an implementation unit's `produces:`
        entirely is refused with the existing `produces_not_in_diff` outcome —
        this WU exists to let a real attempt narrow its deliverable, not to
        let it declare nothing at all."""
        with integration_workspace() as root:
            os.chdir(root)
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0140", "empty-amend", "feat/empty-amend",
                produces=["src/a.py"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("docs").mkdir(exist_ok=True)
                    Path("docs/notes.md").write_text("notes\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n  - docs/notes.md\n"
                        "produces_amended:\n"
                        "  - path: src/a.py\n"
                        "    reason: not needed after all\n"
                        "```\n"
                    )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)
            self.assertEqual(
                _read_frontmatter(fdir / "WU-T01.md").get("status"),
                "blocked_human")
            outcomes = [e["payload"]["outcome"]
                        for e in self._events(fdir, "FEAT-2026-0140/T01")]
            self.assertIn("produces_not_in_diff", outcomes)
            self.assertNotIn("passed", outcomes)

    def test_amendment_disabled_by_project_default_is_still_refused(self):
        """With `defaults: produces_amendable: false` in verification.yml,
        the same RESULT that would otherwise pass in
        test_amended_path_is_dropped_and_pass_proceeds is refused instead."""
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n  - name: noop\n    command: \"true\"\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
                "defaults:\n  produces_amendable: false\n"
            )
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0141", "disabled", "feat/disabled",
                produces=["src/a.py", "src/b.py"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src/a.py").write_text("A = 2\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n  - src/a.py\n"
                        "produces_amended:\n"
                        "  - path: src/b.py\n"
                        "    reason: work landed entirely in src/a.py\n"
                        "```\n"
                    )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)
            self.assertEqual(
                _read_frontmatter(fdir / "WU-T01.md").get("status"),
                "blocked_human")
            outcomes = [e["payload"]["outcome"]
                        for e in self._events(fdir, "FEAT-2026-0141/T01")]
            self.assertIn("produces_not_in_diff", outcomes)
            self.assertNotIn("passed", outcomes)


if __name__ == "__main__":
    unittest.main()
