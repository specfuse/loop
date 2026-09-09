#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A justified, unchanged ``produces:`` path is not a refusal (#3268).

``result-contract.md`` closing obligation 1 has always said: every path in the
WU's ``produces:`` list must show a working-tree change, *or the RESULT must
justify each unchanged path with the command and output showing the
deliverable already holds*. The driver never read that justification —
``assert_produces_in_diff`` was diff-only — so an author's prediction of a
file the unit turned out not to need refused correct work: 20
``produces_not_in_diff`` outcomes in one consumer over twelve days, several
on attempts that had touched fifteen or more files.

The fix honours the contract: the RESULT block may carry

    produces_unchanged:
      - path: docs/VENDOR-EXTENSIONS.md
        justification: grep -c "## Vendor" docs/VENDOR-EXTENSIONS.md -> 1 ...

and an unmatched ``produces:`` entry that carries a non-empty justification is
accepted and recorded on the ``passed`` attempt_outcome as
``produces_justified``. A hollow attempt justifies nothing and is refused
exactly as before; an entry justified for the wrong path, or with an empty
justification, is still refused.

Integration tests reuse the stubbed-dispatch harness from
``test_produces_in_diff``.
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


def _make_wu(produces: list, wu_id: str = "FEAT-2026-0151/T03") -> "loop.WorkUnit":
    return loop.WorkUnit(
        wu_id=wu_id,
        file=Path("WU-T03.md"),
        depends_on=[],
        type="implementation",
        model="claude-haiku-4-5-20251001",
        status="pending",
        attempts=0,
        title=wu_id,
        body="",
        produces=produces,
    )


class TestProducesJustificationsParsing(unittest.TestCase):
    """``produces_justifications`` reads the optional RESULT field defensively:
    the agent's output is the least-trusted input in the system."""

    def test_none_and_missing_field_give_empty(self):
        self.assertEqual(loop.produces_justifications(None), {})
        self.assertEqual(loop.produces_justifications({"status": "complete"}), {})

    def test_well_formed_entries_are_keyed_by_normalized_path(self):
        block = {"produces_unchanged": [
            {"path": "./docs/X.md", "justification": "grep -c foo docs/X.md -> 3"},
            {"path": "src/y.py", "justification": "already present at HEAD; diff empty"},
        ]}
        self.assertEqual(loop.produces_justifications(block), {
            "docs/X.md": "grep -c foo docs/X.md -> 3",
            "src/y.py": "already present at HEAD; diff empty",
        })

    def test_malformed_entries_are_dropped_not_raised(self):
        block = {"produces_unchanged": [
            "docs/X.md",                                  # bare string, no justification
            {"path": "src/a.py"},                         # no justification
            {"path": "src/b.py", "justification": ""},    # empty justification
            {"path": "src/c.py", "justification": "   "}, # blank justification
            {"justification": "orphan"},                  # no path
            {"path": "src/d.py", "justification": "ran the check; holds"},
        ]}
        self.assertEqual(loop.produces_justifications(block), {"src/d.py": "ran the check; holds"})
        self.assertEqual(loop.produces_justifications({"produces_unchanged": "not a list"}), {})


class TestResolveProducesRefusal(unittest.TestCase):
    """``resolve_produces_refusal`` splits the unmatched entries into the ones
    the RESULT justified and the ones still refused."""

    def test_no_justification_refuses_every_unmatched_entry(self):
        wu = _make_wu(["src/rule.py", "docs/X.md"])
        remaining, accepted = loop.resolve_produces_refusal(wu, ["docs/notes.md"], None)
        self.assertEqual(remaining, ["src/rule.py", "docs/X.md"])
        self.assertEqual(accepted, [])

    def test_justified_entry_is_accepted_and_the_rest_still_refused(self):
        wu = _make_wu(["src/rule.py", "docs/X.md"])
        block = {"produces_unchanged": [
            {"path": "docs/X.md", "justification": "grep -c '## Vendor' docs/X.md -> 1"},
        ]}
        remaining, accepted = loop.resolve_produces_refusal(wu, ["src/other.py"], block)
        self.assertEqual(remaining, ["src/rule.py"])
        self.assertEqual(accepted, [
            {"path": "docs/X.md", "justification": "grep -c '## Vendor' docs/X.md -> 1"},
        ])

    def test_justification_for_a_touched_path_is_ignored(self):
        """Justifying a path that IS in the diff is noise, not a claim."""
        wu = _make_wu(["src/rule.py"])
        block = {"produces_unchanged": [{"path": "src/rule.py", "justification": "n/a"}]}
        remaining, accepted = loop.resolve_produces_refusal(wu, ["src/rule.py"], block)
        self.assertEqual((remaining, accepted), ([], []))

    def test_glob_entry_can_be_justified_by_its_own_spelling(self):
        wu = _make_wu(["src/test/expectations/python/**/*.py"])
        block = {"produces_unchanged": [
            {"path": "src/test/expectations/python/**/*.py",
             "justification": "expectations regenerated byte-identical; git diff --stat empty"},
        ]}
        remaining, accepted = loop.resolve_produces_refusal(wu, ["src/main/Gen.java"], block)
        self.assertEqual(remaining, [])
        self.assertEqual(accepted[0]["path"], "src/test/expectations/python/**/*.py")


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


class TestProducesJustificationIntegration(unittest.TestCase):
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
        """A pre-existing source file (the real deliverable) and a pre-existing
        doc the author predicted the unit would need to touch."""
        Path("src").mkdir(exist_ok=True)
        Path("docs").mkdir(exist_ok=True)
        Path("src/rule.py").write_text("SEVERITY = 'WARNING'\n")
        Path("docs/VENDOR-EXTENSIONS.md").write_text("## Vendor extensions\n\n- x-acme\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "pre-existing"], check=True)

    def _events(self, fdir: Path, wu_id: str) -> list:
        return [e for e in _read_events(fdir / "events.jsonl")
                if e["event_type"] == "attempt_outcome" and e["correlation_id"] == wu_id]

    def test_justified_unchanged_path_passes_and_is_recorded(self):
        """The FEAT-2026-0151/T03 shape done right: the source deliverable is
        changed, the predicted doc is not, and the RESULT says why with the
        command and output. The attempt passes and the justification lands on
        the passed event."""
        with integration_workspace() as root:
            os.chdir(root)
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0151", "justified", "feat/justified",
                produces=["src/rule.py", "docs/VENDOR-EXTENSIONS.md"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src/rule.py").write_text("SEVERITY = 'ERROR'\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n  - src/rule.py\n"
                        "produces_unchanged:\n"
                        "  - path: docs/VENDOR-EXTENSIONS.md\n"
                        "    justification: grep -c '## Vendor extensions' docs/VENDOR-EXTENSIONS.md -> 1; the section this unit documents already exists at HEAD\n"
                        "```\n"
                    )
                (fdir / "RETROSPECTIVE.md").write_text(
                    "# Retrospective\n\nNothing generalizes from this gate.\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            self.assertEqual(_read_frontmatter(fdir / "WU-T01.md").get("status"), "done")
            events = self._events(fdir, "FEAT-2026-0151/T01")
            outcomes = [e["payload"]["outcome"] for e in events]
            self.assertEqual(outcomes, ["passed"])
            justified = events[0]["payload"].get("produces_justified")
            self.assertEqual(len(justified), 1)
            self.assertEqual(justified[0]["path"], "docs/VENDOR-EXTENSIONS.md")
            self.assertIn("grep -c", justified[0]["justification"])

    def test_hollow_attempt_with_no_justification_is_still_refused(self):
        """The guard's reason to exist is unchanged: touch nothing declared,
        justify nothing, and the attempt is refused."""
        with integration_workspace() as root:
            os.chdir(root)
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0049", "hollow", "feat/hollow",
                produces=["src/rule.py"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("docs/notes.md").write_text("notes\n")
                    return ("```result\nstatus: complete\n"
                            "files_changed:\n  - docs/notes.md\n```\n")
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)
            self.assertEqual(_read_frontmatter(fdir / "WU-T01.md").get("status"), "blocked_human")
            outcomes = [e["payload"]["outcome"] for e in self._events(fdir, "FEAT-2026-0049/T01")]
            self.assertIn("produces_not_in_diff", outcomes)
            self.assertNotIn("passed", outcomes)

    def test_justifying_the_wrong_path_or_nothing_useful_is_still_refused(self):
        """A justification for a path the diff already covers, or an empty
        one for the path that matters, buys nothing: the refusal names the
        still-unjustified entry and the retry note tells the agent both
        ways out."""
        with integration_workspace() as root:
            os.chdir(root)
            self._seed_repo(root)
            fdir = _write_minimal_feature(
                root, "FEAT-2026-0139", "wrong-path", "feat/wrong-path",
                produces=["src/rule.py", "docs/VENDOR-EXTENSIONS.md"])

            def fake_dispatch(wu, fn, ct=True):
                if wu.wu_id.endswith("/T01"):
                    Path("src/rule.py").write_text("SEVERITY = 'ERROR'\n")
                    return (
                        "```result\nstatus: complete\n"
                        "files_changed:\n  - src/rule.py\n"
                        "produces_unchanged:\n"
                        "  - path: src/rule.py\n"
                        "    justification: irrelevant, it was changed\n"
                        "  - path: docs/VENDOR-EXTENSIONS.md\n"
                        "    justification: \"\"\n"
                        "```\n"
                    )
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)

            self.assertNotEqual(_read_frontmatter(fdir / "WU-T01.md").get("status"), "done")
            events = self._events(fdir, "FEAT-2026-0139/T01")
            refusals = [e for e in events if e["payload"]["outcome"] == "produces_not_in_diff"]
            self.assertTrue(refusals)
            self.assertIn("VENDOR-EXTENSIONS.md", refusals[0]["payload"]["failure_signature"])
            self.assertNotIn("rule.py", refusals[0]["payload"]["failure_signature"])
            self.assertIn("produces_unchanged", refusals[0]["payload"]["failure_excerpt"] + refusals[0]["payload"].get("summary", ""))


if __name__ == "__main__":
    unittest.main()
