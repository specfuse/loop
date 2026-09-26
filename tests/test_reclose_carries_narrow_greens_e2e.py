#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A re-armed close keeps the narrow greens the first close proved (FEAT-2026-0117/T01).

End-to-end: two `loop.run()` passes over the same gate, with a re-arm (attempts
reset to 0, status back to pending — what `/unblock-wu` does) between them.
The first close attempt fails once, then passes on its second internal
attempt, recording per-criterion state at `attempt: 2` — one `narrow`/`pass`
entry per acceptance criterion `T01#1`/`T01#2`, and one `broad`/`pass` entry
`T01#3`. After the re-arm, the second close's dispatch prompt must list the
two narrow entries under "Carried forward — do not re-verify" and count the
broad entry among those requiring re-verification (it has no oracle left to
group by — its per-attempt fields were cleared same as always — so it swells
the re-verify count without a named "### Re-verify" line of its own); on
disk, the narrow entries keep `state: pass` and their `proved_at_sha` and
gain `carried_from_attempt`, while the broad entry resets to `unverified` —
`close-discipline.md` §5's contract, `criteria_state.
reset_stale_criteria_entries` doing the work `_precreate_criteria_state_stub`
used to do unconditionally (#3279).

A second case sets `defaults: carry_forward_narrow_greens: false` and asserts
all three entries reset to `unverified` on the second dispatch — today's
behaviour, unchanged when the project opts out.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_T01_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.**\n\n"
    "1. the narrow thing works\n"
    "2. the other narrow thing works\n"
    "3. the whole suite still passes\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)
_CLOSE_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _write_feature(root: Path, feature_id: str, slug: str) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: feat/{slug}\nroadmap_goal: test\nstatus: active\n"
        f"judge_disabled: true\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\n---\n\n# T01{_T01_BODY}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close-intermediate\nmodel: opus\n"
        f"status: pending\nattempts: 0\nauto_close_disabled: true\n"
        f"---\n\n# Close{_CLOSE_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


def _head_sha(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


class _RearmCarryTestBase(unittest.TestCase):

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

    def _run_first_close_to_pass(self, root: Path, fdir: Path, close_id: str,
                                  feature_id: str):
        """T01 dispatches and passes immediately; the close fails its first
        internal attempt (nothing recorded survives that reset — #3279's own
        carve-out aside, an empty skeleton has nothing to lose), then passes
        its second, recording two narrow-pass entries and one broad-pass
        entry at `attempt: 1`."""
        criteria_path = fdir / "GATE-01-CRITERIA.md"
        close_calls = {"n": 0}

        def fake_dispatch(wu, failure_note, ct=True):
            if wu.wu_id.endswith("/T01"):
                Path("src").mkdir(exist_ok=True)
                Path("src/impl.py").write_text("VALUE = 1\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - src/impl.py\n```\n")
            close_calls["n"] += 1
            if close_calls["n"] == 1:
                return "```result\nstatus: complete\n```\n"
            sha = _head_sha(root)
            attempt = wu.attempts
            criteria_path.write_text(
                "# Gate 1 — per-criterion state\n\n"
                f"Written by `{close_id}`.\n\n"
                "### T01#1\n"
                "- **criterion:** the narrow thing works\n"
                "- **oracle:** `python3 -m unittest tests.test_narrow_one`\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                f"- **proved_at_sha:** `{sha}`\n"
                f"- **attempt:** `{attempt}`\n\n"
                "### T01#2\n"
                "- **criterion:** the other narrow thing works\n"
                "- **oracle:** `python3 -m unittest tests.test_narrow_two`\n"
                "- **kind:** `narrow`\n"
                "- **state:** `pass`\n"
                f"- **proved_at_sha:** `{sha}`\n"
                f"- **attempt:** `{attempt}`\n\n"
                "### T01#3\n"
                "- **criterion:** the whole suite still passes\n"
                "- **oracle:** `python3 -m unittest discover`\n"
                "- **kind:** `broad`\n"
                "- **state:** `pass`\n"
                f"- **proved_at_sha:** `{sha}`\n"
                f"- **attempt:** `{attempt}`\n"
            )
            (fdir / "RETROSPECTIVE.md").write_text(
                "# Retrospective\n\n## Gate 1\n\n## Measurements\n\nn/a\n\n"
                "nothing generalizes from this gate.\n"
            )
            return (
                "```result\nstatus: complete\nfiles_changed:\n"
                f"  - {criteria_path.relative_to(root)}\n"
                f"  - {(fdir / 'RETROSPECTIVE.md').relative_to(root)}\n```\n"
            )

        def fake_verify(wu, fd, cfg=None):
            if wu.wu_id.endswith("/G1-CLOSE") and close_calls["n"] < 2:
                return (False, "### tests: FAIL\nFAIL: test_boom")
            return (True, "(stub)")

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", fake_verify)

        loop.run(feature_id, dry_run=False)

        fm, _ = loop.read_frontmatter(fdir / "WU-close.md")
        self.assertEqual(fm.get("status"), "done",
                          "the close must complete before the re-arm this "
                          "test simulates")
        self.assertGreater(fm.get("attempts"), 0,
                            "the close's own retry must have consumed at "
                            "least one attempt before it passed, matching "
                            "#3279's recorded-attempt shape")
        return fm.get("attempts")

    def _rearm(self, root: Path, fdir: Path):
        """What `/unblock-wu` does: attempts back to 0, status back to pending."""
        loop.write_frontmatter_field(fdir / "WU-close.md", "status", "pending")
        loop.write_frontmatter_field(fdir / "WU-close.md", "attempts", 0)
        # The prior run's gate-broad-run log is untracked; commit it (and the
        # re-arm edits) so `require_feature_folder_committed` lets the next
        # `loop.run()` proceed.
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                         "chore: re-arm close"], check=True)

    def _dispatch_and_capture_second_close_prompt(self, root: Path, fdir: Path,
                                                   feature_id: str) -> str:
        captured = {}
        retro_path = fdir / "RETROSPECTIVE.md"

        def fake_dispatch(wu, failure_note, ct=True):
            if wu.wu_id.endswith("/G1-CLOSE") and "body" not in captured:
                captured["body"] = wu.body
            retro_path.write_text(
                retro_path.read_text() + "\n(re-verified on re-arm)\n")
            return (
                "```result\nstatus: complete\nfiles_changed:\n"
                f"  - {retro_path.relative_to(root)}\n```\n"
            )

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

        loop.run(feature_id, dry_run=False)
        return captured.get("body", "")


class TestRearmCarriesNarrowGreensByDefault(_RearmCarryTestBase):

    def test_carried_forward_and_reverify_partition_and_persist(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_feature(root, "FEAT-2026-9990", "carry-default")
            close_id = "FEAT-2026-9990/G1-CLOSE"

            recorded_attempt = self._run_first_close_to_pass(
                root, fdir, close_id, "FEAT-2026-9990")
            self._rearm(root, fdir)

            prompt = self._dispatch_and_capture_second_close_prompt(
                root, fdir, "FEAT-2026-9990")

            self.assertIn("### Carried forward", prompt)
            carried_section = prompt.split("### Carried forward", 1)[1]
            self.assertIn("T01#1", carried_section)
            self.assertIn("T01#2", carried_section)
            self.assertNotIn("T01#3", carried_section)
            self.assertIn(
                "1 require re-verification this attempt", prompt,
                "the reset broad entry has no oracle to group by (its "
                "per-attempt fields were cleared), so it counts toward "
                "re-verification without a '### Re-verify' oracle listing")

            text = (fdir / "GATE-01-CRITERIA.md").read_text()
            narrow_one = text.split("### T01#1", 1)[1].split("### T01#2", 1)[0]
            narrow_two = text.split("### T01#2", 1)[1].split("### T01#3", 1)[0]
            broad = text.split("### T01#3", 1)[1]

            for block in (narrow_one, narrow_two):
                self.assertIn("**state:** `pass`", block)
                self.assertIn(
                    f"**carried_from_attempt:** `{recorded_attempt}`", block)
                self.assertIn("**proved_at_sha:**", block)

            self.assertIn("**state:** `unverified`", broad)
            self.assertNotIn("**carried_from_attempt:**", broad)


class TestRearmCarryCanBeDisabled(_RearmCarryTestBase):

    def test_carry_forward_narrow_greens_false_resets_everything(self):
        with integration_workspace() as root:
            (root / ".specfuse/verification.yml").write_text(
                "defaults:\n  carry_forward_narrow_greens: false\n"
                "code:\n  - name: noop\n    command: \"true\"\n"
                "doc:\n  - name: noop\n    command: \"true\"\n"
                "plannext:\n  - name: noop\n    command: \"true\"\n"
            )
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                             "opt out of carry-forward"], check=True)
            os.chdir(root)
            fdir = _write_feature(root, "FEAT-2026-9991", "carry-disabled")
            close_id = "FEAT-2026-9991/G1-CLOSE"

            self._run_first_close_to_pass(root, fdir, close_id, "FEAT-2026-9991")
            self._rearm(root, fdir)
            self._dispatch_and_capture_second_close_prompt(
                root, fdir, "FEAT-2026-9991")

            text = (fdir / "GATE-01-CRITERIA.md").read_text()
            for entry_id in ("T01#1", "T01#2", "T01#3"):
                self.assertIn(f"### {entry_id}", text)
            for block in (
                text.split("### T01#1", 1)[1].split("### T01#2", 1)[0],
                text.split("### T01#2", 1)[1].split("### T01#3", 1)[0],
                text.split("### T01#3", 1)[1],
            ):
                self.assertIn("**state:** `unverified`", block)
                self.assertNotIn("**carried_from_attempt:**", block)


if __name__ == "__main__":
    unittest.main()
