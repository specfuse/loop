#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""FEAT-2026-0116/T02 — a repeat is the same failing set, not just a signature.

`detect_spinning_signature_repeat` used to compare only (failure_class,
failure_signature). Since T01 the signature is usually derived FROM the
failing test ids, so the two mostly move together — but when a runner's
output carries no per-test id line the signature falls back to the first
informative line, and two attempts that fail different tests can collapse
onto an identical generic line (an `AssertionError: mismatch` that says
nothing about which test). This pins both directions of the fix: the
`failing_tests` sets take precedence when both are non-empty, and an equal
`failure_excerpt` is required alongside (class, signature) when either set
is empty.
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

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _report(test_id: str) -> str:
    return (
        "### tests: FAIL\n"
        "```\n"
        "$ mvn test\n"
        f"[ERROR] {test_id}:10 expected: <x> but was: <y>\n"
        "[INFO] Tests run: 1, Failures: 1\n"
        "FAIL: Tests run: 1, Failures: 1, Errors: 0, Skipped: 0\n"
        "```\n"
    )


def _read_events(events_path: Path) -> list:
    if not events_path.exists():
        return []
    return [json.loads(ln) for ln in events_path.read_text().splitlines() if ln]


def _write_feature(root: Path, feature_id: str, slug: str) -> Path:
    fdir = root / f".specfuse/features/{feature_id}-{slug}"
    fdir.mkdir(parents=True)
    t_id = f"{feature_id}/T01"
    close_id = f"{feature_id}/G1-CLOSE"
    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Fixture\nslug: {slug}\n"
        f"branch: feat/{slug}\nroadmap_goal: test\nstatus: active\n---\n\n"
        f"# Plan\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        f"    work_units:\n"
        f"      - id: {t_id}\n        file: WU-T01.md\n        depends_on: []\n"
        f"      - id: {close_id}\n        file: WU-close.md\n"
        f"        depends_on: [{t_id}]\n```\n"
    )
    (fdir / "GATE-01.md").write_text(
        "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n"
    )
    (fdir / "WU-T01.md").write_text(
        f"---\nid: {t_id}\ntype: implementation\nmodel: sonnet\n"
        f"status: pending\nattempts: 0\nmax_attempts: 2\n"
        f"iterate_on_failure: true\n---\n\n# T01{_WU_BODY}"
    )
    (fdir / "WU-close.md").write_text(
        f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
        f"status: pending\nattempts: 0\n---\n\n# Close{_WU_BODY}"
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "scaffold"],
                   check=True)
    return fdir


class _IntegrationCase(unittest.TestCase):

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


class TestDifferentFailingTestsDoNotSpin(_IntegrationCase):

    def test_no_early_escalation_and_exhaustion_carries_last_attempt(self):
        """Attempt 1 fails TestAlpha.testFoo, attempt 2 fails
        TestBeta.testBar — different failing sets. No early
        spinning_signature_repeat after attempt 2; the unit instead
        exhausts its 2 attempts and the resulting spinning_detected
        escalation carries the last attempt's identity, none null."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_feature(root, "FEAT-2026-9971", "diffset")

            def fake_dispatch(wu, fn, ct=True):
                Path("src").mkdir(exist_ok=True)
                Path("src/impl.py").write_text("VALUE = 1\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - src/impl.py\n```\n")

            reports = [_report("TestAlpha.testFoo"), _report("TestBeta.testBar")]

            def fake_verify(wu, fd, cfg=None):
                return (False, reports.pop(0))

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", fake_verify)

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            events = _read_events(fdir / "events.jsonl")
            escalations = [e for e in events if e["event_type"] == "human_escalation"]

            spin_repeat = [e for e in escalations
                           if e["payload"]["reason"] == "spinning_signature_repeat"]
            self.assertEqual(spin_repeat, [],
                              "different failing tests must not spin-repeat")

            spin_detected = [e for e in escalations
                              if e["payload"]["reason"] == "spinning_detected"]
            self.assertEqual(len(spin_detected), 1)
            payload = spin_detected[0]["payload"]
            self.assertIsNotNone(payload["failure_class"])
            self.assertIsNotNone(payload["failure_signature"])
            self.assertIsNotNone(payload["failing_tests"])
            self.assertIn("TestBeta.testBar", payload["failing_tests"])


class TestSameFailingTestSpins(_IntegrationCase):

    def test_same_failing_test_escalates_with_failing_tests_named(self):
        """Both attempts fail the same test — a genuine repeat still
        escalates early, and the escalation payload names it."""
        with integration_workspace() as root:
            os.chdir(root)
            fdir = _write_feature(root, "FEAT-2026-9972", "sameset")

            def fake_dispatch(wu, fn, ct=True):
                Path("src").mkdir(exist_ok=True)
                Path("src/impl.py").write_text("VALUE = 1\n")
                return ("```result\nstatus: complete\n"
                        "files_changed:\n  - src/impl.py\n```\n")

            report = _report("TestAlpha.testFoo")

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, report))

            rc = loop.run(None, dry_run=False)
            self.assertEqual(rc, 1)

            events = _read_events(fdir / "events.jsonl")
            spin_repeat = [e for e in events
                           if e["event_type"] == "human_escalation"
                           and e["payload"]["reason"] == "spinning_signature_repeat"]
            self.assertEqual(len(spin_repeat), 1)
            self.assertIn("TestAlpha.testFoo", spin_repeat[0]["payload"]["failing_tests"])


class TestDetectSpinningSignatureRepeatFailingSetOverride(unittest.TestCase):
    """Unit-level pin: `failing_tests` sets take precedence over a stale or
    coincidental (class, signature) match once both sides are non-empty."""

    def test_different_failing_sets_override_an_identical_signature(self):
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", "same-signature"), ("tests", "same-signature"),
                ["TestA.testFoo"], ["TestB.testBar"],
            )
        )

    def test_equal_failing_sets_override_a_different_signature(self):
        self.assertTrue(
            loop.detect_spinning_signature_repeat(
                ("tests", "sig-one"), ("tests", "sig-two"),
                ["TestA.testFoo"], ["TestA.testFoo"],
            )
        )

    def test_equal_failing_sets_ignore_order(self):
        self.assertTrue(
            loop.detect_spinning_signature_repeat(
                ("tests", "x"), ("tests", "x"),
                ["TestA.testFoo", "TestB.testBar"],
                ["TestB.testBar", "TestA.testFoo"],
            )
        )

    def test_empty_sets_fall_back_to_signature_and_require_equal_excerpt(self):
        self.assertFalse(
            loop.detect_spinning_signature_repeat(
                ("tests", "same"), ("tests", "same"),
                [], [],
                "mentions test_a", "mentions test_b",
            )
        )
        self.assertTrue(
            loop.detect_spinning_signature_repeat(
                ("tests", "same"), ("tests", "same"),
                [], [],
                "mentions test_a", "mentions test_a",
            )
        )


if __name__ == "__main__":
    unittest.main()
