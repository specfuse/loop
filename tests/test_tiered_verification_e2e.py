#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The per-attempt tier — FEAT-2026-0109/T04, this gate's `feature_oracle`.

A gate in `.specfuse/verification.yml`'s `code:` list may declare `tier:
broad` to opt itself OUT of the per-attempt run; an entry declaring no tier
runs in both the per-attempt (narrow) run and the once-per-gate broad run
(T06's own code path, not exercised here) — the absent-key default that keeps
a `verification.yml` with no tier keys anywhere byte-identical to today. A
gate may also declare `narrow_command`, a template carrying
`{selected_test_modules}`, to run a cheaper command scoped to the dispatched
unit's own declared test paths (its `produces:` entries under `tests/`) per
attempt while `command` still runs whole. An empty selection falls back to
the gate's full `command` — fail safe, never open.

Harness reused from tests/test_lazy_baseline_e2e.py: a real git working tree,
a scaffolded feature, `loop.dispatch`/`loop._run_gate_set` patched at module
level, then `loop.run()`. `verify` itself is NOT patched — the whole point is
to exercise its real per-attempt tier resolution.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()


def write_feature(root: Path, feature_id: str, slug: str, branch: str,
                   wu_id: str, produces_extra: str = "") -> Path:
    """Scaffold a feature folder with PLAN.md, GATE-01.md, and one
    implementation WU plus the closing sequence (so `ready()` never sees an
    unmet cross-gate dep)."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = [(wu_id, "implementation", f"max_attempts: 1\n{produces_extra}")] + [
        (f"{feature_id}/G1-RETRO", "retrospective", ""),
        (f"{feature_id}/G1-LESSONS", "lessons", ""),
        (f"{feature_id}/G1-DOCS", "docs", ""),
        (f"{feature_id}/G1-PLAN", "plan-next", ""),
    ]

    plan_wu_rows = []
    for i, (wid, _wu_type, _extra) in enumerate(all_wus):
        tnn = wid.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i - 1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wid}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: Tiered verification fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the per-attempt tier
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
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

    body = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
            "**Do not touch.** test\n\n**Verification.** test\n\n"
            "**Escalation triggers.** test\n")
    for wid, wu_type, extra in all_wus:
        tnn = wid.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wid}\ntype: {wu_type}\n"
            f"model: claude-haiku-4-5-20251001\nstatus: pending\nattempts: 0\n"
            f"{extra}---\n\n# {tnn}{body}"
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


class TieredVerificationIntegration(unittest.TestCase):
    """End-to-end: drive loop.run() with a stubbed dispatch and an injected
    `_run_gate_set` that records what the real, unpatched `verify()` asked it
    to run — `verify()`'s own per-attempt tier resolution is exercised for
    real, only the subprocess execution is stubbed."""

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

    def _recording_gate_set_runner(self):
        calls = []

        def recording_run_gate_set(gate_set, feature_dir,
                                    _capture_returncodes=None):
            calls.append(list(gate_set))
            return [{"name": g["name"], "ok": True, "report": "ok"}
                    for g in gate_set]

        return calls, recording_run_gate_set

    def _fake_dispatch(self):
        def fake_dispatch(wu, failure_note, cost_tracking=True):
            if wu.produces:
                # A WU declaring `produces:` must actually deliver every
                # path it names — the presence gate rejects a stub that
                # writes something else as a hollow pass.
                for rel in wu.produces:
                    p = Path(rel)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(f"# stub deliverable for {wu.wu_id}\n")
            else:
                from tests._workspace import write_stub_deliverable
                write_stub_deliverable(wu)
            return "```result\nstatus: complete\n```\n"
        return fake_dispatch

    def test_per_attempt_run_executes_only_the_narrow_tier(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: tests\n"
                "    command: \"true\"\n"
                "    narrow_command: \"true\"\n"
                "  - name: lint\n"
                "    command: \"true\"\n"
                "  - name: security\n"
                "    command: \"true\"\n"
                "    tier: broad\n"
                "  - name: coverage\n"
                "    needs: [tests]\n"
                "    command: \"true\"\n"
                "    tier: broad\n"
                "doc:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
                "plannext:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
            )
            write_feature(root, "FEAT-2026-7401", "narrow-tier",
                          "feat/narrow-tier", "FEAT-2026-7401/T01")

            calls, recording = self._recording_gate_set_runner()
            self._patch("_run_gate_set", recording)
            self._patch("dispatch", self._fake_dispatch())

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertGreaterEqual(
                len(calls), 1,
                "the implementation WU's own attempt must have run at "
                "least one gate set")
            executed_names = {g["name"] for g in calls[0]}
            self.assertEqual(
                executed_names, {"tests", "lint"},
                "gates declared tier: broad must be absent from the "
                "per-attempt run, and the narrow ones must be present")

    def test_untiered_gate_still_runs_every_attempt(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: misc\n"
                "    command: \"true\"\n"
                "  - name: heavy\n"
                "    command: \"true\"\n"
                "    tier: broad\n"
                "doc:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
                "plannext:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
            )
            write_feature(root, "FEAT-2026-7402", "untiered-gate",
                          "feat/untiered-gate", "FEAT-2026-7402/T01")

            calls, recording = self._recording_gate_set_runner()
            self._patch("_run_gate_set", recording)
            self._patch("dispatch", self._fake_dispatch())

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertGreaterEqual(
                len(calls), 1,
                "the implementation WU's own attempt must have run at "
                "least one gate set")
            executed_names = {g["name"] for g in calls[0]}
            self.assertIn(
                "misc", executed_names,
                "an entry declaring no tier must still run per attempt — "
                "the absent-key default")
            self.assertNotIn("heavy", executed_names)

    def test_a_config_with_no_tier_keys_is_byte_identical_to_today(self):
        with integration_workspace() as root:
            os.chdir(root)
            cfg_text = (
                "code:\n"
                "  - name: a\n"
                "    command: \"true\"\n"
                "  - name: b\n"
                "    needs: [a]\n"
                "    command: \"true\"\n"
                "  - name: c\n"
                "    command: \"true\"\n"
                "doc:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
                "plannext:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
            )
            (root / ".specfuse/verification.yml").write_text(cfg_text)
            write_feature(root, "FEAT-2026-7403", "no-tier-keys",
                          "feat/no-tier-keys", "FEAT-2026-7403/T01")

            calls, recording = self._recording_gate_set_runner()
            self._patch("_run_gate_set", recording)
            self._patch("dispatch", self._fake_dispatch())

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertGreaterEqual(
                len(calls), 1,
                "the implementation WU's own attempt must have run at "
                "least one gate set")
            actual = [(g["name"], g["command"]) for g in calls[0]]

            parsed = loop._miniyaml.parse(cfg_text)
            expected_ordered = loop.order_gate_set(list(parsed["code"]))
            expected = [(g["name"], g["command"]) for g in expected_ordered]

            self.assertEqual(
                actual, expected,
                "a verification.yml with no tier keys anywhere must produce "
                "the same executed gate list order_gate_set alone produces")

    def test_selection_falls_back_to_the_full_command_when_empty(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: tests\n"
                "    command: \"FULLCMD\"\n"
                "    narrow_command: \"python3 -m unittest "
                "{selected_test_modules} -v -b\"\n"
                "doc:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
                "plannext:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
            )
            write_feature(
                root, "FEAT-2026-7404", "empty-selection",
                "feat/empty-selection", "FEAT-2026-7404/T01",
                produces_extra="produces:\n  - src/foo.py\n")

            calls, recording = self._recording_gate_set_runner()
            self._patch("_run_gate_set", recording)
            self._patch("dispatch", self._fake_dispatch())

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertGreaterEqual(
                len(calls), 1,
                "the implementation WU's own attempt must have run at "
                "least one gate set")
            tests_gate = next(g for g in calls[0] if g["name"] == "tests")
            self.assertEqual(
                tests_gate["command"], "FULLCMD",
                "a produces: naming no path under tests/ must fall back to "
                "the gate's full command, not an empty or skipped run")

    def test_declared_test_paths_are_selected(self):
        with integration_workspace() as root:
            os.chdir(root)
            (root / ".specfuse/verification.yml").write_text(
                "code:\n"
                "  - name: tests\n"
                "    command: \"FULLCMD\"\n"
                "    narrow_command: \"python3 -m unittest "
                "{selected_test_modules} -v -b\"\n"
                "doc:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
                "plannext:\n"
                "  - name: noop\n"
                "    command: \"true\"\n"
            )
            write_feature(
                root, "FEAT-2026-7405", "declared-paths",
                "feat/declared-paths", "FEAT-2026-7405/T01",
                produces_extra=(
                    "produces:\n"
                    "  - tests/test_a.py\n"
                    "  - tests/test_b.py\n"
                ))

            calls, recording = self._recording_gate_set_runner()
            self._patch("_run_gate_set", recording)
            self._patch("dispatch", self._fake_dispatch())

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0)

            self.assertGreaterEqual(
                len(calls), 1,
                "the implementation WU's own attempt must have run at "
                "least one gate set")
            tests_gate = next(g for g in calls[0] if g["name"] == "tests")
            self.assertEqual(
                tests_gate["command"],
                "python3 -m unittest tests.test_a tests.test_b -v -b")
            all_commands = [g["command"] for g in calls[0]]
            self.assertNotIn(
                "FULLCMD", all_commands,
                "the full command must not appear once the declared test "
                "paths select a non-empty narrow run")


if __name__ == "__main__":
    unittest.main()
