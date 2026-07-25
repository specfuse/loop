#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Baseline persistence, re-probe policy, and kill-switch — FEAT-2026-0051/T02.

T01 (`probe_baseline`) runs a full `code`-set gate probe at every gate entry.
This WU stops that from being a per-resume cost: the result is written into
`GATE-NN.md` frontmatter's `baseline:` block, and the next entry skips the
probe when the recorded sha matches the sha it is about to dispatch into.
`--no-baseline-probe` and a `verification.yml` `baseline_probe: false` key
disable the probe outright, resolved in one place by `baseline_probe_enabled`.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace, write_stub_deliverable

loop = load_loop()


class TestFrontmatterBlockWriter(unittest.TestCase):
    """write_frontmatter_block: multi-line value, no reflow of sibling keys."""

    def _gate_file(self, tmp_path: Path, body_extra: str = "") -> Path:
        p = tmp_path / "GATE-01.md"
        p.write_text(
            f"---\ngate: 1\nstatus: open\ncost_budget_usd: 12.5{body_extra}\n"
            f"---\n\n# Gate 1\n"
        )
        return p

    def test_insert_new_block_leaves_other_keys_untouched(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            before = gf.read_text()
            loop.write_frontmatter_block(
                gf, "baseline",
                ["baseline:", "  sha: abc123", "  probed_at: 2026-01-01T00:00:00+00:00",
                 "  failing: []"],
            )
            after = gf.read_text()
            self.assertIn("gate: 1", after)
            self.assertIn("status: open", after)
            self.assertIn("cost_budget_usd: 12.5", after)
            self.assertIn("baseline:", after)
            self.assertIn("  sha: abc123", after)
            self.assertNotEqual(before, after)

    def test_replace_existing_block_does_not_duplicate(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            loop.write_frontmatter_block(
                gf, "baseline",
                ["baseline:", "  sha: sha-one", "  probed_at: t1", "  failing: []"],
            )
            loop.write_frontmatter_block(
                gf, "baseline",
                ["baseline:", "  sha: sha-two", "  probed_at: t2", "  failing: []"],
            )
            text = gf.read_text()
            self.assertEqual(text.count("baseline:"), 1)
            self.assertIn("sha: sha-two", text)
            self.assertNotIn("sha-one", text)
            self.assertIn("cost_budget_usd: 12.5", text)


class TestGateBaselineReadWrite(unittest.TestCase):
    """read_gate_baseline / write_gate_baseline round trip and malformed input."""

    def _gate_file(self, tmp_path: Path) -> Path:
        p = tmp_path / "GATE-01.md"
        p.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        return p

    def test_absent_baseline_key_returns_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            self.assertIsNone(loop.read_gate_baseline(gf))

    def test_green_probe_round_trips_as_empty_list_not_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            loop.write_gate_baseline(gf, "deadbeef", "2026-01-01T00:00:00+00:00", [])
            record = loop.read_gate_baseline(gf)
            self.assertIsNotNone(
                record, "an empty failing: list must not be treated as absent")
            self.assertEqual(record["sha"], "deadbeef")
            self.assertEqual(record["failing"], [])

    def test_red_probe_round_trips_failing_entries(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            failing = [{"gate": "tests", "failure_class": "test_failure",
                        "failure_signature": "sig_abc"}]
            loop.write_gate_baseline(gf, "cafef00d", "2026-01-01T00:00:00+00:00", failing)
            record = loop.read_gate_baseline(gf)
            self.assertEqual(record["sha"], "cafef00d")
            self.assertEqual(record["failing"], failing)

    def test_missing_sha_treated_as_absent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            # Half-written block: probed_at present, sha never landed.
            gf.write_text(
                "---\ngate: 1\nstatus: open\nbaseline:\n"
                "  probed_at: 2026-01-01T00:00:00+00:00\n  failing: []\n---\n\n# Gate 1\n"
            )
            self.assertIsNone(loop.read_gate_baseline(gf))

    def test_unparseable_baseline_block_treated_as_absent_not_crashed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            # Mixed/inconsistent indentation under _miniyaml's documented
            # subset raises MiniYAMLError — must degrade to "absent", not raise.
            gf.write_text(
                "---\ngate: 1\nstatus: open\nbaseline:\n"
                "  sha: abc\n   probed_at: bad-indent\n---\n\n# Gate 1\n"
            )
            self.assertIsNone(loop.read_gate_baseline(gf))

    def test_non_dict_baseline_treated_as_absent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            gf.write_text(
                "---\ngate: 1\nstatus: open\nbaseline: not-a-mapping\n---\n\n# Gate 1\n"
            )
            self.assertIsNone(loop.read_gate_baseline(gf))


class TestGateBaselineCheck(unittest.TestCase):
    """gate_baseline_check: the re-probe policy in isolation, no run()."""

    def _gate_file(self, tmp_path: Path) -> Path:
        p = tmp_path / "GATE-01.md"
        p.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        return p

    def test_second_entry_skips_probe_when_sha_unchanged(self):
        """Fails on HEAD before this WU's edits (gate_baseline_check absent)."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            probe_calls = []

            def counting_probe(feature_dir, cfg=None):
                probe_calls.append(1)
                return []

            orig = loop.probe_baseline
            loop.probe_baseline = counting_probe
            try:
                cfg = {"code": []}
                loop.gate_baseline_check(gf, Path(td), cfg, "same-sha",
                                          probed_at="t1")
                loop.gate_baseline_check(gf, Path(td), cfg, "same-sha",
                                          probed_at="t2")
            finally:
                loop.probe_baseline = orig

            self.assertEqual(len(probe_calls), 1,
                              "probe must run exactly once across two gate "
                              "entries against an unchanged sha")

    def test_moved_sha_reprobes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            probe_calls = []

            def counting_probe(feature_dir, cfg=None):
                probe_calls.append(1)
                return []

            orig = loop.probe_baseline
            loop.probe_baseline = counting_probe
            try:
                cfg = {"code": []}
                loop.gate_baseline_check(gf, Path(td), cfg, "sha-one",
                                          probed_at="t1")
                loop.gate_baseline_check(gf, Path(td), cfg, "sha-two",
                                          probed_at="t2")
            finally:
                loop.probe_baseline = orig

            self.assertEqual(len(probe_calls), 2,
                              "a changed sha must run the probe a second time")

    def test_skip_uses_recorded_failing_set(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            gf = self._gate_file(Path(td))
            calls = {"n": 0}

            def red_then_crash_probe(feature_dir, cfg=None):
                calls["n"] += 1
                if calls["n"] > 1:
                    raise AssertionError("probe must not re-run on unchanged sha")
                return [{"gate": "tests", "failure_class": "test_failure",
                          "failure_signature": "sig"}]

            orig = loop.probe_baseline
            loop.probe_baseline = red_then_crash_probe
            try:
                cfg = {"code": []}
                first, freshly = loop.gate_baseline_check(
                    gf, Path(td), cfg, "same-sha", probed_at="t1")
                second, freshly2 = loop.gate_baseline_check(
                    gf, Path(td), cfg, "same-sha", probed_at="t2")
            finally:
                loop.probe_baseline = orig

            self.assertTrue(freshly)
            self.assertFalse(freshly2)
            self.assertEqual(first, second)
            self.assertEqual(first[0]["gate"], "tests")


class TestBaselineProbeEnabled(unittest.TestCase):
    """baseline_probe_enabled: single precedence resolution point."""

    def test_default_enabled(self):
        self.assertTrue(loop.baseline_probe_enabled(False, {}))

    def test_config_key_disables(self):
        self.assertFalse(
            loop.baseline_probe_enabled(False, {"baseline_probe": False}))

    def test_cli_flag_disables_even_with_config_enabled(self):
        self.assertFalse(
            loop.baseline_probe_enabled(True, {"baseline_probe": True}))

    def test_cli_flag_beats_config_key(self):
        # CLI flag wins even when the config key would have allowed the probe.
        self.assertFalse(
            loop.baseline_probe_enabled(True, {"baseline_probe": True}))
        # And CLI flag NOT set still respects a config key that disables it.
        self.assertFalse(
            loop.baseline_probe_enabled(False, {"baseline_probe": False}))


class TestBaselinePersistenceIntegration(unittest.TestCase):
    """End-to-end: run() writes + commits the baseline, --no-baseline-probe
    and the verification.yml key both disable the probe outright."""

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

    def _scaffold(self, root: Path, feature_id: str, slug: str, branch: str,
                   wu_status: str = "pending") -> Path:
        fdir = root / f".specfuse/features/{feature_id}-{slug}"
        fdir.mkdir(parents=True)
        wus = [
            (f"{feature_id}/T01", "implementation", wu_status),
            (f"{feature_id}/G1-RETRO", "retrospective", "pending"),
            (f"{feature_id}/G1-LESSONS", "lessons", "pending"),
            (f"{feature_id}/G1-DOCS", "docs", "pending"),
            (f"{feature_id}/G1-PLAN", "plan-next", "pending"),
        ]
        plan_wu_rows = []
        for i, (wu_id, _t, _s) in enumerate(wus):
            tnn = wu_id.split("/")[-1]
            wu_file = f"WU-{tnn}.md"
            deps = "[]" if i == 0 else f"[{wus[i - 1][0]}]"
            plan_wu_rows.append(
                f"      - id: {wu_id}\n        file: {wu_file}\n        "
                f"depends_on: {deps}"
            )
        plan = f"""---
feature_id: {feature_id}
title: Baseline persistence fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise baseline persistence and the kill-switch
status: active
---

# Plan: {slug}

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
{chr(10).join(plan_wu_rows)}
```
"""
        (fdir / "PLAN.md").write_text(plan)
        (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
        body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
                "**Do not touch.** test\n\n**Verification.** test\n\n"
                "**Escalation triggers.** test\n")
        for wu_id, wu_type, wu_status_ in wus:
            tnn = wu_id.split("/")[-1]
            (fdir / f"WU-{tnn}.md").write_text(
                f"---\nid: {wu_id}\ntype: {wu_type}\n"
                f"model: claude-haiku-4-5-20251001\nstatus: {wu_status_}\n"
                f"attempts: 0\n---\n\n# {tnn}{body}"
            )
        gitignore = root / ".gitignore"
        existing = gitignore.read_text() if gitignore.exists() else ""
        if ".specfuse/.loop.lock" not in existing:
            gitignore.write_text(existing + ".specfuse/.loop.lock\n"
                                 ".specfuse/.scratch-*\n"
                                 ".specfuse/scripts/__pycache__/\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "scaffold fixture"], check=True)
        return fdir

    def test_green_baseline_is_written_and_committed_alongside_gate_file(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._scaffold(root, "FEAT-2026-8901", "green-persist",
                                   "feat/green-persist")

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: [])

            loop.run(None, dry_run=False)

            gate_text = (fdir / "GATE-01.md").read_text()
            self.assertIn("baseline:", gate_text)
            self.assertIn("failing: []", gate_text)

            status = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain"],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertNotIn("GATE-01.md", status,
                              "baseline write must be committed, not left dirty")

    def test_no_baseline_probe_flag_skips_probe_entirely(self):
        with integration_workspace() as root:
            os.chdir(root)
            self._scaffold(root, "FEAT-2026-8902", "killswitch-cli",
                            "feat/killswitch-cli")

            probe_calls = []

            def fake_probe(feature_dir, cfg=None):
                probe_calls.append(1)
                raise AssertionError("probe_baseline must not run with "
                                     "--no-baseline-probe")

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("probe_baseline", fake_probe)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False, no_baseline_probe=True)
            self.assertEqual(probe_calls, [])

    def test_verification_yml_opt_out_key_disables_probe(self):
        with integration_workspace() as root:
            os.chdir(root)
            self._scaffold(root, "FEAT-2026-8903", "killswitch-config",
                            "feat/killswitch-config")

            verification_path = root / ".specfuse/verification.yml"
            text = verification_path.read_text()
            verification_path.write_text("baseline_probe: false\n" + text)
            subprocess.run(["git", "-C", str(root), "add",
                           ".specfuse/verification.yml"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                            "disable baseline probe"], check=True)

            probe_calls = []

            def fake_probe(feature_dir, cfg=None):
                probe_calls.append(1)
                raise AssertionError("probe_baseline must not run when "
                                     "verification.yml sets baseline_probe: false")

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return "```result\nstatus: complete\n```\n"

            self._patch("probe_baseline", fake_probe)
            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (True, "(stub)"))

            loop.run(None, dry_run=False)
            self.assertEqual(probe_calls, [])


if __name__ == "__main__":
    unittest.main()
