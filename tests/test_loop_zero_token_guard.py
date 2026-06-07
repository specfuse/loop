#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Zero-token attempt guard — FEAT-2026-0008/T01.

Covers:
  (a) is_zero_token_attempt unit cases — True/False matrix per AC 5.
  (b) Integration via stubbed dispatch returning input_tokens=0 three times:
      the WU ends `blocked_human` with reason `all_attempts_zero_token`,
      no `task_completed` event was written, and no per-WU squash commit
      landed (only the `chore(loop)` bookkeeping commit).

The integration test mirrors test_driver_integration.py — stands up a real
git working tree, scaffolds a minimal feature, patches loop.dispatch at the
module level so run()'s un-injected call site sees the stub.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from tests._loop_loader import load_loop

loop = load_loop()

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD_SRC = REPO_ROOT / ".specfuse"


# --------------------------------------------------------------------------- #
# Unit tests for the helper                                                   #
# --------------------------------------------------------------------------- #


class TestIsZeroTokenAttempt(unittest.TestCase):

    def test_true_when_input_tokens_zero(self):
        self.assertTrue(loop.is_zero_token_attempt(
            {"input_tokens": 0, "output_tokens": 0}))

    def test_false_when_input_tokens_positive(self):
        self.assertFalse(loop.is_zero_token_attempt({"input_tokens": 1234}))

    def test_false_when_usage_is_none(self):
        # Cost tracking disabled — guard MUST NOT fire (AC 4).
        self.assertFalse(loop.is_zero_token_attempt(None))

    def test_false_when_input_tokens_missing(self):
        self.assertFalse(loop.is_zero_token_attempt({}))

    def test_false_when_only_output_tokens_present(self):
        self.assertFalse(loop.is_zero_token_attempt({"output_tokens": 0}))

    def test_false_for_non_dict(self):
        # Defensive — agent_reported_blocked-style tolerance.
        self.assertFalse(loop.is_zero_token_attempt("zero"))
        self.assertFalse(loop.is_zero_token_attempt(0))


# --------------------------------------------------------------------------- #
# Integration: three zero-token attempts -> blocked_human with new reason     #
# --------------------------------------------------------------------------- #


@contextmanager
def integration_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email",
                        "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"],
                       check=True)
        (root / "README.md").write_text("# fixture\n")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"],
                       check=True)
        shutil.copytree(SCAFFOLD_SRC / "scripts", root / ".specfuse/scripts")
        shutil.copytree(SCAFFOLD_SRC / "templates", root / ".specfuse/templates")
        shutil.copytree(SCAFFOLD_SRC / "rules", root / ".specfuse/rules")
        (root / ".specfuse/verification.yml").write_text(
            "code:\n  - name: noop\n    command: \"true\"\n"
            "doc:\n  - name: noop\n    command: \"true\"\n"
            "plannext:\n  - name: noop\n    command: \"true\"\n"
        )
        (root / ".specfuse/features").mkdir(parents=True)
        yield root


def write_minimal_feature(root: Path, feature_id: str, slug: str,
                          branch: str, wus: list) -> Path:
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
title: Zero-token guard fixture
slug: {slug}
branch: {branch}
roadmap_goal: exercise the zero-token guard under test
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
    for wu_id, wu_type, wu_status in all_wus:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wu_type}\nmodel: claude-haiku-4-5-20251001\n"
            f"status: {wu_status}\nattempts: 0\n---\n\n# {tnn}{body}"
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
                          capture_output=True, text=True, check=True).stdout.strip()


class TestZeroTokenAllAttemptsIntegration(unittest.TestCase):
    """Three zero-token attempts in a row escalate to `blocked_human` with
    the distinguishable reason; no task_completed event; no squash commit."""

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

    def test_three_zero_token_attempts_block_human_with_new_reason(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9301", "zero-token-spin",
                                  "feat/test-zero-token", [
                                      ("FEAT-2026-9301/T01", "implementation",
                                       "pending"),
                                  ])

            # Stub dispatch: always returns a benign stdout (which would parse
            # as missing-block -> verify()) plus a usage dict with
            # input_tokens=0. The guard must fire BEFORE verify() runs.
            def fake_dispatch(wu, failure_note, cost_tracking=True):
                return ("(simulated empty agent output)\n",
                        {"input_tokens": 0, "output_tokens": 0,
                         "cost_usd": 0.0})

            # verify() must not be reached by the guarded path. If it is, the
            # WU would PASS and the test would catch it via the blocked
            # assertions below.
            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub — must not be called on zero-token path)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1,
                             "zero-token spin must exit 1 (blocked)")

            fdir = root / (".specfuse/features/FEAT-2026-9301-"
                           "zero-token-spin")
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "blocked_human",
                             "T01 must be blocked_human after 3 zero-token "
                             "attempts")

            events = _read_events(fdir / "events.jsonl")
            types = [e["event_type"] for e in events]
            self.assertNotIn("task_completed", types,
                             "no task_completed must be written on zero-token "
                             "spin")

            # Three attempt_outcome events with outcome=zero_token_skip.
            zero_events = [e for e in events
                           if e["event_type"] == "attempt_outcome"
                           and e["payload"].get("outcome") == "zero_token_skip"]
            self.assertEqual(len(zero_events), loop.MAX_ATTEMPTS,
                             "one attempt_outcome per zero-token attempt")
            self.assertEqual(sorted(e["payload"]["attempt"] for e in zero_events),
                             list(range(1, loop.MAX_ATTEMPTS + 1)))

            # human_escalation must carry the new reason.
            escalations = [e for e in events
                           if e["event_type"] == "human_escalation"]
            self.assertEqual(len(escalations), 1)
            self.assertEqual(escalations[0]["payload"]["reason"],
                             "all_attempts_zero_token",
                             "spinning reason must be the distinguishable one")
            self.assertEqual(escalations[0]["payload"]["attempts"],
                             loop.MAX_ATTEMPTS,
                             "all attempts must have been consumed")

            # No per-WU squash commit. The bookkeeping chore commit must
            # exist but it is NOT a squash commit (no `Feature: <wu_id>`
            # trailer for the squash — only the chore subject naming
            # blocked_human).
            log = _git(root, "log", "--format=%s", "feat/test-zero-token")
            self.assertNotIn("feat:", log,
                             "no feat() squash commit should land for the WU")
            self.assertNotIn("fix:", log,
                             "no fix() squash commit should land for the WU")
            self.assertIn("chore(loop): FEAT-2026-9301/T01 blocked_human", log)
            self.assertIn("all_attempts_zero_token", log,
                          "chore commit subject names the new reason")

    def test_cost_tracking_disabled_does_not_trigger_guard(self):
        """AC 4 regression: usage=None must NOT fire the guard. Stub dispatch
        returns a plain string (no usage dict), the agent stdout has no RESULT
        block, verify() returns True -> WU passes as today."""
        with integration_workspace() as root:
            os.chdir(root)
            write_minimal_feature(root, "FEAT-2026-9302", "cost-off",
                                  "feat/test-cost-off", [
                                      ("FEAT-2026-9302/T01", "implementation",
                                       "pending"),
                                  ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                # Plain string -> execute_unit_attempt treats usage as None.
                return "(simulated agent output, no usage dict)\n"

            def fake_verify(wu, feature_dir, cfg=None):
                return True, "(stub)"

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            # With T01 passing the gate proceeds into the closing sequence,
            # which the stubs also pass. Final rc is 0 (gate awaits review).
            self.assertEqual(rc, 0,
                             "cost-tracking-off path must behave as before "
                             "and not be tripped by the guard")
            fdir = root / ".specfuse/features/FEAT-2026-9302-cost-off"
            t01_fm = _read_frontmatter(fdir / "WU-T01.md")
            self.assertEqual(t01_fm.get("status"), "done",
                             "T01 must complete normally when usage is None")


if __name__ == "__main__":
    unittest.main()
