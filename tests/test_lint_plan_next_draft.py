#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for lint_plan_next_draft() — focused plan-next-draft lint pass.

Covers AC5 cases from FEAT-2026-0018/T07:
  - clean draft cohort → empty list
  - missing planned_cost_usd → one WARN naming the WU
  - implementation WU with loop.py body + empty produces_driver_helper → one WARN
  - empty section (heading present, body empty) → one WARN
  - non-implementation type (docs) without driver-wiring → no WARN regardless of pdh
  - terminal gate (no gate N+1) → empty list, no crash
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_VALID_BODY = """\
**Context.**
Part of feature FEAT-2026-9999.

**Acceptance criteria.**
The code works.

**Do not touch.**
No generated files.

**Verification.**
code gates.

**Escalation triggers.**
Emit blocked if anything is wrong.
"""

_VALID_WU_BASE_FM = (
    "---\n"
    "id: FEAT-2026-9999/T01\n"
    "type: implementation\n"
    "status: draft\n"
    "attempts: 0\n"
    "planned_cost_usd: 0.50\n"
)

_PLAN_TEMPLATE = """\
---
feature_id: FEAT-2026-9999
title: lint_plan_next_draft test fixture
branch: feat/pnd-test
roadmap_goal: verify lint_plan_next_draft
status: active
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9999/G1-CLOSE-INTERMEDIATE
        file: WU-90-ci.md
        depends_on: []
      - id: FEAT-2026-9999/G1-PLAN
        file: WU-91-plan.md
        depends_on: [FEAT-2026-9999/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-9999/T01
        file: WU-01-impl.md
        depends_on: []
```
"""

_PLAN_TERMINAL = """\
---
feature_id: FEAT-2026-9999
title: lint_plan_next_draft terminal test
branch: feat/pnd-test
roadmap_goal: verify lint_plan_next_draft terminal gate
status: active
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9999/G1-CLOSE
        file: WU-90-close.md
        depends_on: []
```
"""


def _make_base_feature(tmpdir: str, plan_text: str = _PLAN_TEMPLATE) -> Path:
    """Write a minimal two-gate feature folder with gate-1 closing WUs."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()
    (feature / "PLAN.md").write_text(plan_text)
    (feature / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
    (feature / "GATE-02.md").write_text("---\nstatus: open\n---\n\n# Gate 2\n")
    # Gate-1 closing WUs (not draft — must not be linted by this pass)
    (feature / "WU-90-ci.md").write_text(
        "---\nid: FEAT-2026-9999/G1-CLOSE-INTERMEDIATE\n"
        "type: close-intermediate\nstatus: done\nattempts: 1\n---\n\n# CI\n"
    )
    (feature / "WU-91-plan.md").write_text(
        "---\nid: FEAT-2026-9999/G1-PLAN\n"
        "type: plan-next\nstatus: done\nattempts: 1\n---\n\n# Plan\n"
    )
    return feature


def _write_wu(feature: Path, body: str = _VALID_BODY, fm_extra: str = "") -> Path:
    """Write WU-01-impl.md; fm_extra goes inside the frontmatter block."""
    wu = feature / "WU-01-impl.md"
    wu.write_text(_VALID_WU_BASE_FM + fm_extra + "---\n\n" + body)
    return wu


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLintPlanNextDraftClean(unittest.TestCase):
    """Clean draft cohort → empty warn list."""

    def test_clean_draft_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp)
            _write_wu(feature)
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            self.assertEqual(warns, [], f"expected no warns; got {warns}")


class TestLintPlanNextDraftMissingCost(unittest.TestCase):
    """Missing planned_cost_usd → one WARN naming the WU file."""

    def test_missing_cost_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp)
            wu = feature / "WU-01-impl.md"
            wu.write_text(
                "---\n"
                "id: FEAT-2026-9999/T01\n"
                "type: implementation\n"
                "status: draft\n"
                "attempts: 0\n"
                "---\n\n"
                + _VALID_BODY
            )
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            cost_warns = [w for w in warns if "planned_cost_usd" in w]
            self.assertEqual(len(cost_warns), 1, f"expected 1 cost warn; got {warns}")
            self.assertIn("WU-01-impl.md", cost_warns[0])


class TestLintPlanNextDraftDriverWiring(unittest.TestCase):
    """Implementation WU with loop.py in body + empty produces_driver_helper → one WARN."""

    def test_driver_wiring_warns_when_pdh_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp)
            body = _VALID_BODY + "\nThis WU edits loop.py directly.\n"
            _write_wu(feature, body=body)
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            wiring_warns = [w for w in warns if "produces_driver_helper" in w]
            self.assertEqual(len(wiring_warns), 1, f"expected 1 wiring warn; got {warns}")

    def test_driver_wiring_no_warn_when_pdh_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp)
            body = _VALID_BODY + "\nThis WU edits loop.py directly.\n"
            _write_wu(feature, body=body, fm_extra="produces_driver_helper: my_hook\n")
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            wiring_warns = [w for w in warns if "produces_driver_helper" in w]
            self.assertEqual(wiring_warns, [], f"pdh set → no warn; got {warns}")


class TestLintPlanNextDraftEmptySection(unittest.TestCase):
    """Section heading present but body empty → one WARN."""

    def test_empty_section_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp)
            body = (
                "**Context.**\n"
                "Part of feature FEAT-2026-9999.\n\n"
                "**Acceptance criteria.**\n"
                "The code works.\n\n"
                "**Do not touch.**\n"
                "No generated files.\n\n"
                "**Verification.**\n\n"          # empty — heading only
                "**Escalation triggers.**\n"
                "Emit blocked.\n"
            )
            _write_wu(feature, body=body)
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            empty_warns = [w for w in warns if "empty" in w and "Verification" in w]
            self.assertEqual(len(empty_warns), 1, f"expected 1 empty-section warn; got {warns}")


class TestLintPlanNextDraftNonImplType(unittest.TestCase):
    """Non-implementation type (docs) → no driver-wiring WARN regardless of pdh."""

    def test_docs_type_no_wiring_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp)
            wu = feature / "WU-01-impl.md"
            wu.write_text(
                "---\n"
                "id: FEAT-2026-9999/T01\n"
                "type: docs\n"
                "status: draft\n"
                "attempts: 0\n"
                "planned_cost_usd: 0.10\n"
                "---\n\n"
                "**Context.**\n"
                "Part of feature FEAT-2026-9999.\n\n"
                "**Acceptance criteria.**\n"
                "Docs updated.\n\n"
                "**Do not touch.**\n"
                "Nothing.\n\n"
                "**Verification.**\n"
                "doc gates.\n\n"
                "**Escalation triggers.**\n"
                "Emit blocked.\n\n"
                "This docs WU mentions loop.py for context only.\n"
            )
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            wiring_warns = [w for w in warns if "produces_driver_helper" in w]
            self.assertEqual(wiring_warns, [], f"docs type → no wiring warn; got {warns}")


class TestLintPlanNextDraftTerminalGate(unittest.TestCase):
    """Terminal gate (no N+1) → returns empty list, no crash."""

    def test_terminal_gate_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            (feature / "PLAN.md").write_text(_PLAN_TERMINAL)
            (feature / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
            (feature / "WU-90-close.md").write_text(
                "---\nid: FEAT-2026-9999/G1-CLOSE\n"
                "type: close\nstatus: done\nattempts: 1\n---\n\n# Close\n"
            )
            # Gate 1 is the terminal gate; just_closed_gate=1 means we look for gate 2
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            self.assertEqual(warns, [], f"terminal gate → empty list; got {warns}")

    def test_missing_plan_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "feature"
            feature.mkdir()
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            self.assertEqual(warns, [])


if __name__ == "__main__":
    unittest.main()
