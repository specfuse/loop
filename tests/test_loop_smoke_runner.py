#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Smoke-import runner — FEAT-2026-0008/T03.

Covers:
  (a) extract_smoke_imports finds two import-form lines in mixed content;
      ignores non-matching `python3 -c` lines and prose.
  (b) run_smoke_imports returns (True, "") on a successful import.
  (c) run_smoke_imports returns (False, summary) on a failing import.
  (d) Integration: a WU whose body declares a FAILING smoke check spins
      to blocked_human — squash rollback, smoke_import_failed events,
      no `done` flip on disk, no `task_completed` event.
  (e) Integration: a WU whose body declares NO smoke check completes
      end-to-end as today — no new event types, no rollback, status=done.
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


# --------------------------------------------------------------------------- #
# Unit tests for extract_smoke_imports                                        #
# --------------------------------------------------------------------------- #


class TestExtractSmokeImports(unittest.TestCase):

    def test_mixed_body_returns_only_matching_lines(self):
        body = (
            "# WU body\n"
            "Some prose explaining the work.\n"
            "\n"
            "**Verification.**\n"
            '  python3 -c "from foo import bar"\n'
            'python -c "from baz.qux import frobnicate"\n'
            '  python3 -c "import sys"\n'              # not match: no `from`
            '  python3 -c "print(\\"hi\\")"\n'         # not match: free-form
            "random non-Python prose line\n"
            "  python3 some_script.py\n"               # not match: no -c
        )
        out = loop.extract_smoke_imports(body)
        self.assertEqual(out, [
            'python3 -c "from foo import bar"',
            'python -c "from baz.qux import frobnicate"',
        ])

    def test_single_quote_form_matches(self):
        body = "python3 -c 'from sys import version'\n"
        self.assertEqual(
            loop.extract_smoke_imports(body),
            ["python3 -c 'from sys import version'"],
        )

    def test_empty_body_returns_empty(self):
        self.assertEqual(loop.extract_smoke_imports(""), [])

    def test_no_matches_returns_empty(self):
        body = (
            "no Python at all\n"
            "echo hello\n"
            'python3 -c "import os; print(os.getcwd())"\n'  # free-form, no `from`
        )
        self.assertEqual(loop.extract_smoke_imports(body), [])


# --------------------------------------------------------------------------- #
# Unit tests for run_smoke_imports                                            #
# --------------------------------------------------------------------------- #


class TestRunSmokeImports(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_successful_import_returns_true_empty(self):
        ok, summary = loop.run_smoke_imports(
            ['python3 -c "from sys import version"'], self.cwd,
        )
        self.assertTrue(ok)
        self.assertEqual(summary, "")

    def test_failing_import_returns_false_with_summary(self):
        cmd = 'python3 -c "from nonexistent_module_xyz import nothing"'
        ok, summary = loop.run_smoke_imports([cmd], self.cwd)
        self.assertFalse(ok)
        self.assertIn(cmd, summary)
        # ModuleNotFoundError surfaces in stderr — the summary must carry it.
        self.assertIn("nonexistent_module_xyz", summary)

    def test_empty_command_list_returns_true(self):
        ok, summary = loop.run_smoke_imports([], self.cwd)
        self.assertTrue(ok)
        self.assertEqual(summary, "")

    def test_short_circuits_on_first_failure(self):
        # Second command would create a sentinel file IF run. Verifying it
        # is NOT created proves the runner stopped after the first failure.
        sentinel = self.cwd / "should_not_exist.txt"
        bad = 'python3 -c "from nonexistent_module_xyz import nothing"'
        good = f'python3 -c "open({str(sentinel)!r}, \\"w\\").write(\\"x\\")"'
        ok, _ = loop.run_smoke_imports([bad, good], self.cwd)
        self.assertFalse(ok)
        self.assertFalse(sentinel.exists(),
                         "runner must short-circuit on first failure")


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list,
                          t01_body_extra: str = "") -> Path:
    """Scaffold a single-gate feature. `t01_body_extra` is appended to
    T01's WU body verbatim — used to inject a smoke-import line."""
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    all_wus = list(wus) + [
        (f"{feature_id}/G1-RETRO", "retrospective", "pending"),
        (f"{feature_id}/G1-LESSONS", "lessons", "pending"),
        (f"{feature_id}/G1-DOCS", "docs", "pending"),
        (f"{feature_id}/G1-PLAN", "plan-next", "pending"),
    ]

    plan_wu_rows = []
    for i, (wu_id, _wu_type, _wu_status) in enumerate(all_wus):
        tnn = wu_id.split("/")[-1]
        wu_file = f"WU-{tnn}.md"
        deps = "[]" if i == 0 else f"[{all_wus[i-1][0]}]"
        plan_wu_rows.append(
            f"      - id: {wu_id}\n        file: {wu_file}\n        "
            f"depends_on: {deps}"
        )

    plan = f"""---
feature_id: {feature_id}
title: smoke runner fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the smoke-import runner under test
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
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )

    body_base = ("\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
                 "**Do not touch.** test\n\n**Verification.** test\n\n"
                 "**Escalation triggers.** test\n")
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        extra = t01_body_extra if tnn == "T01" else ""
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\n"
            f"model: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body_base}{extra}"
        )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                    "scaffold fixture"], check=True)
    return fdir


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


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=True
                          ).stdout.strip()


# --------------------------------------------------------------------------- #
# Integration: failing smoke check spins to blocked_human                     #
# --------------------------------------------------------------------------- #


class TestSmokeFailureSpinsIntegration(unittest.TestCase):

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

    def test_failing_smoke_check_spins_to_blocked_human(self):
        with integration_workspace() as root:
            os.chdir(root)
            # T01's body carries a guaranteed-failing smoke import line.
            smoke = (
                "\n**Existence check.**\n"
                'python3 -c "from nonexistent_module_xyz import nothing"\n'
            )
            write_minimal_feature(
                root, "FEAT-2026-9501", "smoke-fail",
                "feat/test-smoke-fail",
                [("FEAT-2026-9501/T01", "implementation", "pending")],
                t01_body_extra=smoke,
            )

            # Stub: agent emits a complete RESULT, writes a sentinel file
            # so squash_commit has something to commit, then verify() PASSes.
            # The smoke runner fires AFTER squash and MUST reject.
            result_block = (
                "```result\n"
                "status: complete\n"
                "summary: edits applied\n"
                "```\n"
            )

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # Create a real diff so squash_commit produces a sha (it
                # short-circuits to None on an empty tree).
                (root / f"agent-edit-{wu.attempts}.txt").write_text("x\n")
                return (result_block, {"input_tokens": 100,
                                       "output_tokens": 50,
                                       "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1,
                             "3 smoke failures must escalate (blocked_human, "
                             "rc=1)")

            fdir = (root / ".specfuse/features"
                         / "FEAT-2026-9501-smoke-fail")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "blocked_human",
                             "T01 must be blocked_human after 3 smoke fails")

            events = _read_events(fdir / "events.jsonl")
            smoke_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["payload"].get("outcome") == "smoke_import_failed"
            ]
            self.assertEqual(len(smoke_events), loop.MAX_ATTEMPTS,
                             "one attempt_outcome per failed smoke attempt")
            for ev in smoke_events:
                self.assertIn("nonexistent_module_xyz",
                              ev["payload"]["summary"])

            types = [e["event_type"] for e in events]
            self.assertNotIn("task_completed", types,
                             "no task_completed when smoke fired every "
                             "attempt")

            log = _git(root, "log", "--format=%s", "feat/test-smoke-fail")
            self.assertNotIn("feat: T01", log,
                             "rolled-back squash must NOT remain in history")
            self.assertIn("chore(loop): FEAT-2026-9501/T01 blocked_human", log)


# --------------------------------------------------------------------------- #
# Integration: WU without a smoke check completes as today                    #
# --------------------------------------------------------------------------- #


class TestNoSmokeCheckPassesIntegration(unittest.TestCase):

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

    def test_no_smoke_check_in_body_runs_squash_as_today(self):
        with integration_workspace() as root:
            os.chdir(root)
            # T01 body has NO smoke-import line. The runner must be a
            # no-op — pre-T03 behavior preserved.
            write_minimal_feature(
                root, "FEAT-2026-9502", "no-smoke",
                "feat/test-no-smoke",
                [("FEAT-2026-9502/T01", "implementation", "pending")],
            )

            result_block = (
                "```result\n"
                "status: complete\n"
                "summary: nothing fancy\n"
                "```\n"
            )

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                (root / f"agent-edit-{wu.wu_id.split('/')[-1]}.txt"
                 ).write_text("x\n")
                return (result_block, {"input_tokens": 100,
                                       "output_tokens": 50,
                                       "cost_usd": 0.001})

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub verify pass)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 0,
                             "gate must complete normally when no smoke "
                             "check is declared")

            fdir = (root / ".specfuse/features"
                         / "FEAT-2026-9502-no-smoke")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done",
                             "T01 must flip to done when no smoke check")

            events = _read_events(fdir / "events.jsonl")
            smoke_events = [
                e for e in events
                if e["event_type"] == "attempt_outcome"
                and e["payload"].get("outcome") == "smoke_import_failed"
            ]
            self.assertEqual(smoke_events, [],
                             "smoke runner must not log when body declares "
                             "no smoke check")

            types = [e["event_type"] for e in events]
            self.assertIn("task_completed", types,
                          "task_completed must be present on normal pass")


if __name__ == "__main__":
    unittest.main()
