# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Every escalating provider path leaves a trace, or says why it doesn't (#1970).

An `ActionOutcome(status=STATUS_ESCALATED)` with neither an `escalation`
payload nor an `escalation_waived` reason records nothing anywhere: the run
summary mentions it once and the terminal scrolls. Nine such paths shipped
across three providers -- every one by omission rather than by decision, and
none of them visible without reading each `execute()` end to end.

Not every escalation deserves a GitHub record. An item that vanished from the
snapshot between `advertise` and `execute` is a benign race with nothing for a
human to decide, and filing a needs-human issue for it would be noise. Those
paths set `escalation_waived` instead, so "considered and declined" is
distinguishable from "forgotten" -- the same shape `NON_JUDGE_MODULES` and
`DEPENDENCY_MANIFEST_NAMED_UNCOVERED` already use.

This test enforces the choice, not either answer. A new escalating path must
carry one or the other; it cannot ship bare.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

from tests._loop_loader import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_PROVIDERS_DIR = REPO_ROOT / "specfuse" / "agent" / "providers"


def _is_none(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _is_empty_str(node) -> bool:
    return isinstance(node, ast.Constant) and node.value == ""


def _escalating_outcomes(path: Path) -> list:
    """Return (lineno, has_payload, has_waiver) for each escalating outcome."""
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "ActionOutcome"):
            continue
        kw = {k.arg: k.value for k in node.keywords}
        status = kw.get("status")
        if getattr(status, "id", "") != "STATUS_ESCALATED":
            continue
        payload = kw.get("escalation")
        waiver = kw.get("escalation_waived")
        found.append((
            node.lineno,
            payload is not None and not _is_none(payload),
            waiver is not None and not _is_empty_str(waiver),
        ))
    return found


class TestEveryEscalationLeavesATrace(unittest.TestCase):
    def test_no_escalating_path_is_bare(self):
        bare = []
        for path in sorted(_PROVIDERS_DIR.glob("*.py")):
            for lineno, has_payload, has_waiver in _escalating_outcomes(path):
                if not has_payload and not has_waiver:
                    bare.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")

        self.assertEqual(
            bare,
            [],
            "escalating ActionOutcome(s) with neither an `escalation` payload "
            "nor an `escalation_waived` reason. Such a path records nothing "
            "anywhere -- the run summary mentions it and the terminal "
            "scrolls. Give it a payload (with `target_issue` when it is about "
            "an issue), or state why it deliberately records nothing:\n  "
            + "\n  ".join(bare),
        )

    def test_a_path_does_not_claim_both(self):
        """A waiver next to a payload means one of them is a lie."""
        both = []
        for path in sorted(_PROVIDERS_DIR.glob("*.py")):
            for lineno, has_payload, has_waiver in _escalating_outcomes(path):
                if has_payload and has_waiver:
                    both.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")

        self.assertEqual(both, [])

    def test_the_sweep_actually_finds_paths(self):
        """Guard against the guard: a broken matcher would pass vacuously."""
        total = sum(
            len(_escalating_outcomes(p)) for p in sorted(_PROVIDERS_DIR.glob("*.py"))
        )

        self.assertGreaterEqual(
            total, 8, "AST sweep found almost no escalating outcomes — matcher is broken"
        )


class TestPayloadsTargetTheIssueTheyAreAbout(unittest.TestCase):
    """A payload about issue #N belongs on issue #N (#1937)."""

    def test_issue_shaped_providers_set_target_issue(self):
        for name in ("triage.py", "findings_diagnose.py", "findings_autofix.py", "bugs.py"):
            path = _PROVIDERS_DIR / name
            text = path.read_text()
            payload_count = text.count("EscalationPayload(")
            target_count = text.count("target_issue=")
            with self.subTest(provider=name):
                self.assertGreaterEqual(
                    target_count,
                    payload_count,
                    f"{name} builds {payload_count} payload(s) but sets "
                    f"target_issue {target_count} time(s). Every one of these "
                    f"providers works from a GitHub issue, so an escalation "
                    f"about it belongs on it rather than on a new issue.",
                )


if __name__ == "__main__":
    unittest.main()
