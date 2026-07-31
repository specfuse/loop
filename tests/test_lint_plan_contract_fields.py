#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the plan-next contract fields lint (FEAT-2026-0053/T02).

Covers `open_questions:` presence/shape on the just-armed gate's
GATE-{N+1}-REVIEW.md, via lint_plan_next_draft. Warn-only — no ERROR path.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

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

_PLAN_TEMPLATE = """\
---
feature_id: FEAT-2026-9999
title: contract-fields lint test fixture
branch: feat/pcf-test
roadmap_goal: verify plan-next contract fields lint
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


def _make_base_feature(tmpdir: str, review_text: str | None) -> Path:
    feature = Path(tmpdir) / "feature"
    feature.mkdir()
    (feature / "PLAN.md").write_text(_PLAN_TEMPLATE)
    (feature / "GATE-01.md").write_text("---\nstatus: open\n---\n\n# Gate 1\n")
    (feature / "GATE-02.md").write_text("---\nstatus: open\n---\n\n# Gate 2\n")
    (feature / "WU-90-ci.md").write_text(
        "---\nid: FEAT-2026-9999/G1-CLOSE-INTERMEDIATE\n"
        "type: close-intermediate\nstatus: done\nattempts: 1\n---\n\n# CI\n"
    )
    (feature / "WU-91-plan.md").write_text(
        "---\nid: FEAT-2026-9999/G1-PLAN\n"
        "type: plan-next\nstatus: done\nattempts: 1\n---\n\n# Plan\n"
    )
    (feature / "WU-01-impl.md").write_text(
        "---\n"
        "id: FEAT-2026-9999/T01\n"
        "type: implementation\n"
        "status: draft\n"
        "attempts: 0\n"
        "planned_cost_usd: 0.50\n"
        "---\n\n" + _VALID_BODY
    )
    if review_text is not None:
        (feature / "GATE-02-REVIEW.md").write_text(review_text)
    return feature


class TestContractFields(unittest.TestCase):
    def test_review_missing_open_questions_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(
                tmp,
                "# Gate 2 review\n\nNo frontmatter here at all.\n",
            )
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            oq_warns = [w for w in warns if "open_questions" in w]
            self.assertEqual(
                len(oq_warns), 1, f"expected 1 open_questions warn; got {warns}"
            )
            self.assertIn("GATE-02-REVIEW.md", oq_warns[0])

    def test_review_present_empty_open_questions_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(
                tmp,
                "---\nopen_questions: []\n---\n\n# Gate 2 review\n",
            )
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            oq_warns = [w for w in warns if "open_questions" in w]
            self.assertEqual(oq_warns, [], f"expected no warns; got {warns}")

    def test_review_present_nonempty_open_questions_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(
                tmp,
                "---\nopen_questions:\n  - is X in scope?\n---\n\n# Gate 2 review\n",
            )
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            oq_warns = [w for w in warns if "open_questions" in w]
            self.assertEqual(oq_warns, [], f"expected no warns; got {warns}")

    def test_review_missing_file_no_open_questions_warn(self):
        # No GATE-02-REVIEW.md at all — a different check's problem (assert_gate_review_exists);
        # this lint must not pile on with a spurious open_questions warn.
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(tmp, None)
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            oq_warns = [w for w in warns if "open_questions" in w]
            self.assertEqual(oq_warns, [], f"expected no warns; got {warns}")

    def test_wu_human_only_and_provenance_no_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = _make_base_feature(
                tmp,
                "---\nopen_questions: []\n---\n\n# Gate 2 review\n",
            )
            wu = feature / "WU-01-impl.md"
            wu.write_text(
                "---\n"
                "id: FEAT-2026-9999/T01\n"
                "type: implementation\n"
                "status: draft\n"
                "attempts: 0\n"
                "planned_cost_usd: 0.50\n"
                "human_only: true\n"
                "provenance: retrospective item #3\n"
                "---\n\n" + _VALID_BODY
            )
            warns = lint_plan.lint_plan_next_draft(feature, 1)
            self.assertEqual(warns, [], f"expected no warns; got {warns}")


if __name__ == "__main__":
    unittest.main()
