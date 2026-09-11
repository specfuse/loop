#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Every per-unit `blocked_human` escalation carries the brief -- T10.

`format_spinout_escalation_brief` used to be called from exactly one site:
the attempt-exhaustion `for-else`. Every other `human_escalation` keyed on
`wu.wu_id` (or a close WU's own `wu_id`) emitted `reason`/`attempts`/
`attempts_usage`/`blocked_reason` and no `message` at all -- `GATE-02-REVIEW.md`
flagged that as a narrower reading of gate 2's definition of done than the
plan's own words.

The static check below enumerates every per-unit `human_escalation` site by
reading `loop.py`'s own AST rather than a hand-copied reason list, so a
reason added at a new site later fails this test instead of silently
shipping without a brief. A `human_escalation` keyed on `feature_id` (or a
derivative of `wu.wu_id`, e.g. `wu.wu_id.split("/")[0]`) is a gate-level
halt -- a different object with no single unit to brief about -- and is
asserted UNCHANGED, not widened.
"""

from __future__ import annotations

import ast
import io
import os
import unittest
from contextlib import redirect_stdout

from specfuse.loop import escalation
from tests._loop_loader import REPO_ROOT, load_loop
from tests._workspace import integration_workspace, write_stub_deliverable
from tests.test_spinout_brief_end_to_end import write_feature

LOOP_PY = REPO_ROOT / "specfuse" / "loop" / "loop.py"

loop = load_loop()


def _human_escalation_build_event_calls() -> list[ast.Call]:
    tree = ast.parse(LOOP_PY.read_text())
    calls = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "build_event"
                and len(node.args) >= 3
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "human_escalation"
            ):
                calls.append(node)
            self.generic_visit(node)

    Visitor().visit(tree)
    return calls


def _is_unit_keyed_subject(subject: ast.expr) -> bool:
    """True when *subject* is a work unit's own `.wu_id` attribute access.

    `wu.wu_id` / `close_wu.wu_id` -- a real per-unit identity. Anything else
    (`feature_id`, or a derivative like `wu.wu_id.split("/")[0]`) identifies
    the FEATURE, not a single unit, and is a gate-level halt out of scope for
    this brief.
    """
    return (
        isinstance(subject, ast.Attribute)
        and subject.attr == "wu_id"
        and isinstance(subject.value, ast.Name)
    )


def _dict_keys(payload: ast.Dict) -> list[str]:
    return [
        k.value for k in payload.keys
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    ]


def _reason_literal(payload: ast.Dict) -> str | None:
    for k, v in zip(payload.keys, payload.values, strict=False):
        if (
            isinstance(k, ast.Constant) and k.value == "reason"
            and isinstance(v, ast.Constant)
        ):
            return v.value
    return None


class EveryPerUnitEscalationSiteCarriesMessage(unittest.TestCase):

    def test_every_wu_id_keyed_human_escalation_dict_has_a_message_key(self):
        calls = _human_escalation_build_event_calls()
        unit_keyed = [
            c for c in calls if _is_unit_keyed_subject(c.args[1])
        ]
        # Roughly ten per-unit sites (WU-10's own count of the source at
        # authoring time). Pinned so a site added or removed is noticed --
        # not to forbid the count moving, but so it moves on purpose.
        self.assertGreaterEqual(
            len(unit_keyed), 8,
            "expected at least 8 per-unit (wu.wu_id-keyed) human_escalation "
            "sites in loop.py -- did a site get removed or reclassified?",
        )

        missing = []
        for call in unit_keyed:
            payload = call.args[2]
            if not isinstance(payload, ast.Dict):
                missing.append((call.lineno, "payload is not a literal dict"))
                continue
            reason = _reason_literal(payload)
            keys = _dict_keys(payload)
            if "message" not in keys:
                missing.append((call.lineno, reason))

        self.assertEqual(
            missing, [],
            "these per-unit human_escalation sites (line, reason) carry no "
            f"`message` key: {missing}",
        )


class GateLevelEscalationsUnchanged(unittest.TestCase):

    # Snapshot of today's four feature_id-keyed (gate-level) sites: reason ->
    # sorted payload keys. This unit does not touch these -- a gate-level
    # halt has no single unit to brief about -- so any diff here means a
    # gate-level site was accidentally widened or narrowed.
    EXPECTED = {
        "gate_budget_exceeded": [
            "budget_usd", "next_wu_id", "reason", "spent_usd",
        ],
        "gate_budget_exceeded_post_dispatch": [
            "budget_usd", "final_wu_id", "gate", "reason", "spent_usd",
        ],
        "broad_run_gate_failure": [
            "failing_gates", "gate", "message", "reason", "tree",
        ],
        "preexisting_gate_failure": [
            "attributed_to", "failing_gates", "gate", "message", "reason",
        ],
    }

    def test_four_feature_id_keyed_sites_with_their_original_reasons(self):
        calls = _human_escalation_build_event_calls()
        gate_level = [
            c for c in calls if not _is_unit_keyed_subject(c.args[1])
        ]
        self.assertEqual(
            len(gate_level), 4,
            "expected exactly four feature_id-keyed (gate-level) "
            "human_escalation sites",
        )

        found = {}
        for call in gate_level:
            payload = call.args[2]
            self.assertIsInstance(payload, ast.Dict)
            reason = _reason_literal(payload)
            found[reason] = sorted(_dict_keys(payload))

        self.assertEqual(found, self.EXPECTED)


class AgentReportedBlockedCarriesBriefEndToEnd(unittest.TestCase):
    """The reason the probe actually hit, driven through a real `loop.run()`.

    `agent_reported_blocked` is the corpus's most common per-unit escalation
    reason (22.2%) and, before T10, emitted no `message` at all. Harness
    reused from `tests/test_spinout_brief_end_to_end.py`.
    """

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

    def test_run_prints_a_conforming_brief_for_agent_reported_blocked(self):
        with integration_workspace() as root:
            os.chdir(root)
            write_feature(
                root, "FEAT-2026-8963", "agent-blocked-brief",
                "feat/agent-blocked-brief", [
                    ("FEAT-2026-8963/T01", "max_attempts: 3\n"),
                ])

            def fake_dispatch(wu, failure_note, cost_tracking=True):
                write_stub_deliverable(wu)
                return (
                    "```result\nstatus: blocked\n"
                    "blocked_reason: hit a real model boundary\n```\n"
                )

            self._patch("dispatch", fake_dispatch)
            self._patch("verify", lambda wu, fd, cfg=None: (False, "FAIL"))
            self._patch("probe_baseline", lambda feature_dir, cfg=None: [])

            captured = io.StringIO()
            with redirect_stdout(captured):
                rc = loop.run(None, dry_run=False)

            self.assertEqual(rc, 1)
            stdout = captured.getvalue()

            self.assertEqual(
                escalation.validate_escalation_body(stdout), [],
                "the printed brief must satisfy the escalation contract",
            )
            self.assertIn(
                "<!-- specfuse:escalation id=FEAT-2026-8963/T01 -->", stdout,
                "the marker's correlation id must be the WU id",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
