# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0085/T02: an auto-closed gate states what the driver's gates
# proved (which units passed, on which gate set, at what cost) instead of
# listing every acceptance criterion as deferred debt for a downstream close
# to reconcile. This replaces the FEAT-2026-0070 debt-enumeration stub.

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()
from specfuse.loop.gate_eval import AutoCloseDecision  # noqa: E402


def _decision(gate: int) -> AutoCloseDecision:
    return AutoCloseDecision(
        auto=True,
        reasons=[],
        metrics={"gate_total_cost": 1.23, "gate_budget": 5.0},
        gate_id=gate,
        feature_id="FEAT-TEST-0001",
        predicate_version="v1",
    )


def _write_plan(fd: Path, gate_number: int, wu_specs: list[dict]) -> None:
    wu_lines = "\n".join(
        f"      - id: FEAT-TEST-0001/{spec['sub_id']}\n"
        f"        file: {spec['file']}\n"
        f"        depends_on: []"
        for spec in wu_specs
    )
    (fd / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-TEST-0001\n"
        "status: active\n"
        "---\n\n"
        "# Plan\n\n"
        "```yaml\n"
        "gates:\n"
        f"  - gate: {gate_number}\n"
        f"    file: GATE-{gate_number:02d}.md\n"
        "    work_units:\n"
        f"{wu_lines}\n"
        "```\n"
    )


def _write_wu(fd: Path, spec: dict) -> None:
    ac_lines = "\n".join(f"{i}. {c}" for i, c in enumerate(spec["criteria"], start=1))
    (fd / spec["file"]).write_text(
        "---\n"
        f"id: FEAT-TEST-0001/{spec['sub_id']}\n"
        f"type: {spec.get('type', 'implementation')}\n"
        "status: done\n"
        "---\n\n"
        f"# {spec['sub_id']}\n\n"
        "**Acceptance criteria.**\n\n"
        f"{ac_lines}\n"
    )


class TestTerminalStubHasNoDeferredLines(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_terminal_stub_has_no_deferred_lines(self):
        specs = [
            {
                "sub_id": "T01",
                "file": "WU-01-alpha.md",
                "type": "implementation",
                "criteria": ["Greppable criterion ALPHA-ONE must hold."],
            },
            {
                "sub_id": "T02",
                "file": "WU-02-beta.md",
                "type": "docs",
                "criteria": ["Greppable criterion BETA-ONE must hold."],
            },
        ]
        _write_plan(self.fd, 1, specs)
        for spec in specs:
            _write_wu(self.fd, spec)

        loop.write_stub_retrospective_terminal(self.fd, 1, _decision(1))
        retro = (self.fd / "RETROSPECTIVE.md").read_text()

        self.assertNotIn("deferred:", retro)
        self.assertNotIn("specfuse:autoclose-debt", retro)
        self.assertIn("FEAT-TEST-0001/T01", retro)
        self.assertIn("FEAT-TEST-0001/T02", retro)
        # one line per substantive unit naming its gate set
        self.assertIn("`code`", retro)
        self.assertIn("`doc`", retro)


# --------------------------------------------------------------------------- #
# terminal close after an auto-closed predecessor gate needs no deferral      #
# section — verified via the real assert_closing_deliverables /              #
# verify_post_pass_invariants guards, git-diff-based like theirs.             #
# --------------------------------------------------------------------------- #

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

DUMMY_HEAD = "0000000000000000000000000000000000000000"


def _init_git(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def _setup_substantive_commit(root: Path, extra_files: dict[str, str]) -> str:
    _init_git(root)
    (root / "README.md").write_text("# fixture\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True)
    head_before = _git(root, "rev-parse", "HEAD")
    for rel, content in extra_files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "squash"], check=True)
    return head_before


class TestTerminalCloseAfterAutoclosedGateNeedsNoDeferralSection(unittest.TestCase):

    def test_terminal_close_after_autoclosed_gate_needs_no_deferral_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature_dir = root / ".specfuse" / "features" / "FEAT-2026-8801-test"

            # Gate 1 auto-closed earlier: its retrospective section carries the
            # new pass summary, no deferral heading at all.
            gate1_summary = (
                "## Gate 1 — auto-closed (predicate=v1)\n\n"
                "On-plan close; full retrospective ceremony skipped per\n"
                "`evaluate_auto_close`.\n\n"
                "- **FEAT-2026-8801/T01** (`WU-01.md`): final attempt passed "
                "the `code` gate set\n\n"
                "- feature_id: FEAT-2026-8801\n"
                "- predicate_version: v1\n"
                "- gate_total_cost: $1.00\n"
                "- gate_budget: $5.00\n"
                "- reasons: [] (auto=True)\n"
            )
            retro_content = (
                f"{gate1_summary}\n\n"
                "## Gate 2\n\nClosed by dispatch. Nothing generalizes from "
                "this gate.\n\n"
                "## Cost analysis\n\nActual: $1.20 vs planned $1.50.\n"
            )
            gate_num = 2
            close_id = "FEAT-2026-8801/G2-CLOSE"

            head_before = _setup_substantive_commit(root, {
                ".specfuse/LEARNINGS.md": "# Learnings\n\nOld entry.\n\nNew entry.\n",
                ".specfuse/roadmap.md": (
                    "---\nproject: test\n---\n\n# Roadmap\n\n"
                    "| Feature ID | Title | Status | Folder | Detail |\n"
                    "|------------|-------|--------|--------|--------|\n"
                    "| FEAT-2026-8801 | Test feature | done | — | — |\n\n"
                    "## FEAT-2026-8801 — Test feature\n\nContent.\n"
                ),
                ".specfuse/roadmap-archive.md": (
                    "---\nproject: test\n---\n\n# Archived\n\n"
                    "<!-- Archived sections appended below -->\n"
                    '<a id="feat-2026-8801"></a>\n## FEAT-2026-8801 — Test feature\n'
                ),
                ".specfuse/features/FEAT-2026-8801-test/PLAN.md": (
                    "---\nfeature_id: FEAT-2026-8801\ntitle: Test\n"
                    "branch: feat/test\nroadmap_goal: test\nstatus: active\n"
                    "---\n\n# Plan\n\n```yaml\ngates:\n"
                    "  - gate: 1\n    file: GATE-01.md\n"
                    "    work_units:\n      - id: FEAT-2026-8801/T01\n"
                    "        file: WU-01.md\n        depends_on: []\n"
                    f"  - gate: {gate_num}\n    file: GATE-{gate_num:02d}.md\n"
                    f"    work_units:\n      - id: {close_id}\n"
                    "        file: WU-close.md\n        depends_on: []\n```\n"
                ),
                f".specfuse/features/FEAT-2026-8801-test/GATE-{gate_num:02d}.md": (
                    f"---\ngate: {gate_num}\nstatus: passed\n---\n\n# Gate {gate_num}\n"
                ),
                ".specfuse/features/FEAT-2026-8801-test/RETROSPECTIVE.md":
                    retro_content,
                ".specfuse/features/FEAT-2026-8801-test/WU-close.md": (
                    f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
                    "status: done\nattempts: 1\nverdict: met\n---\n\n"
                    f"# Close{_WU_BODY}"
                ),
            })

            self.assertNotIn(
                "What the loop did NOT verify",
                (feature_dir / "RETROSPECTIVE.md").read_text(),
            )

            wu = loop.WorkUnit(
                wu_id=close_id,
                file=feature_dir / "WU-close.md",
                depends_on=[],
                type="close",
                model="opus",
                status="done",
                attempts=1,
                title="Close",
                body=_WU_BODY,
                verdict="met",
            )

            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                ok, reason = loop.assert_closing_deliverables(
                    wu, feature_dir, root, head_before,
                )
                self.assertTrue(ok, f"assert_closing_deliverables failed: {reason!r}")

                ok, reason = loop.verify_post_pass_invariants(
                    wu, feature_dir, root, head_before,
                )
                self.assertTrue(ok, f"verify_post_pass_invariants failed: {reason!r}")
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
