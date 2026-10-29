#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Feature oracle for FEAT-LOOP-2026-0248 gate 1 — `ids migrate --all` keeps a repo valid."""

import tempfile
import unittest
from pathlib import Path

from specfuse.loop import agent_policy
from tests.test_ids_migrate_all import _git, _make, _run

_REAL = Path(__file__).resolve().parent.parent / ".specfuse" / "agent-policy.yml"


def _policy(entry="FEAT-2026-0042"):
    lines = _REAL.read_text().splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("queue:"))
    end = next(i for i, ln in enumerate(lines) if i > start and ln.startswith("rules:"))
    return "\n".join(lines[:start] + ["queue:", f"  - {entry}", ""] + lines[end:]) + "\n"


def _commit_policy(root, text=None):
    text = _policy() if text is None else text
    (root / ".specfuse" / "agent-policy.yml").write_text(text)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "policy")


class Clause1PolicyResolvesOldIds(unittest.TestCase):
    def test_queue_with_old_id_validates_after_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            _commit_policy(root)
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertTrue((root / ".specfuse" / "id-aliases.yml").is_file())
            findings = agent_policy.validate_agent_policy(
                root / ".specfuse" / "agent-policy.yml", repo_root=root
            )
            self.assertEqual([f for f in findings if f.startswith("ERROR")], [])

    def test_unknown_queue_entry_still_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            _commit_policy(root, _policy("FEAT-2026-0999"))
            _run(root, "--apply")
            findings = agent_policy.validate_agent_policy(
                root / ".specfuse" / "agent-policy.yml", repo_root=root
            )
            self.assertTrue(any("has no row in roadmap.md" in f for f in findings), findings)


class Clause2ApplyValidatesResult(unittest.TestCase):
    def test_clean_fixture_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            _commit_policy(root)
            code, out, err = _run(root, "--apply")
            self.assertEqual(code, 0, out + err)
            self.assertIn("validated", out)

    def test_lint_plan_error_exits_nonzero_with_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make(tmp)
            plan = root / ".specfuse" / "features" / "FEAT-2026-0042-live" / "PLAN.md"
            plan.write_text(plan.read_text().replace("feature_id:", "feature_idx:", 1))
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "break plan")
            code, out, _ = _run(root, "--apply")
            self.assertNotEqual(code, 0)
            self.assertIn("ERROR", out)
            self.assertIn("FEAT-ACME-2026-0042-live", out)
            self.assertIn("git checkout -- . && git clean -fd .specfuse/features", out)


@unittest.skip("T02 owns rewrite classification")
class Clause3RewriteClassification(unittest.TestCase):
    def test_pending(self):
        pass


@unittest.skip("T03 owns prose scoping")
class Clause4ProseScoping(unittest.TestCase):
    def test_pending(self):
        pass


@unittest.skip("T04 owns --rehearse")
class Clause5Rehearse(unittest.TestCase):
    def test_pending(self):
        pass


if __name__ == "__main__":
    unittest.main()
