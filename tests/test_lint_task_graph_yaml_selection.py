#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Task-graph YAML block selection — regression for issue #21.

`lint_plan.py` used `re.search` against PLAN.md's body to find the task-graph
YAML block. The non-greedy regex matched the FIRST ```yaml fenced block —
which fails when PLAN.md includes a yaml example earlier in the document
(e.g. a frontmatter-schema illustration). The example block was parsed as
the task graph; the actual graph was ignored; WU planned-cost sums read 0
because no `work_units` were found in the example.

Regression test asserts the parser identifies the task-graph block by its
`gates:` key, regardless of preceding ```yaml fences.
"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


_PLAN_TWO_YAML_BLOCKS = textwrap.dedent("""\
    ---
    feature_id: FEAT-2026-9999
    title: Test two yaml blocks
    slug: test-two-yaml
    branch: feat/test-two-yaml
    roadmap_goal: Verify task-graph regex skips non-task-graph yaml blocks.
    status: planned
    planned_cost_usd: 2.50
    ---

    # Plan: example feature with a schema illustration before the graph

    ## Re-arm contract — WU frontmatter schema illustration

    Example shape (not the task graph; the task graph is below):

    ```yaml
    re_arm_count: 0
    re_arm_history: []
    cumulative_cost_usd: 0.0
    ```

    ## Task graph

    ```yaml
    gates:
      - gate: 1
        file: GATE-01.md
        work_units:
          - id: FEAT-2026-9999/T01
            file: WU-01-impl.md
            depends_on: []
          - id: FEAT-2026-9999/G1-CLOSE
            file: WU-90-close.md
            depends_on: [FEAT-2026-9999/T01]
    ```
    """)


_WU_BODY = (
    "**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)


def _make_feature(tmp: str) -> Path:
    repo = Path(tmp)
    specfuse = repo / ".specfuse"
    specfuse.mkdir()
    (specfuse / "roadmap.md").write_text(
        "---\nproject: test\n---\n\n# Roadmap\n\n"
        "| Feature ID | Title | Status | Folder | Detail |\n"
        "|------------|-------|--------|--------|--------|\n"
        "| FEAT-2026-9999 | Test | planned | — | — |\n"
    )
    feat = specfuse / "features" / "FEAT-2026-9999-test-two-yaml"
    feat.mkdir(parents=True)
    (feat / "PLAN.md").write_text(_PLAN_TWO_YAML_BLOCKS)
    (feat / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n")
    (feat / "WU-01-impl.md").write_text(
        "---\nid: FEAT-2026-9999/T01\ntype: implementation\nstatus: draft\n"
        "attempts: 0\nplanned_cost_usd: 1.00\n---\n\n# T01\n\n" + _WU_BODY
    )
    (feat / "WU-90-close.md").write_text(
        "---\nid: FEAT-2026-9999/G1-CLOSE\ntype: close\nstatus: draft\n"
        "attempts: 0\nplanned_cost_usd: 1.50\n---\n\n# Close\n\n" + _WU_BODY
    )
    return feat


class TestTaskGraphYamlSelection(unittest.TestCase):
    """`lint_plan.py` finds the task-graph block by its `gates:` key, not by
    position among yaml fences (issue #21)."""

    def test_two_yaml_blocks_lint_parses_graph_not_example(self):
        """PLAN.md with a yaml example BEFORE the task graph must lint clean.

        Sum of WU planned costs ($1.00 + $1.50 = $2.50) must match
        PLAN.md's `planned_cost_usd: 2.50`. Pre-fix: lint picks the schema
        example as the graph, sums zero WUs, fires "$2.50 differs from
        sum $0.00" WARN.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            feat = _make_feature(tmp)
            from io import StringIO
            from contextlib import redirect_stdout
            buf = StringIO()
            with redirect_stdout(buf):
                errs = lint_plan.lint(feat)
            output = buf.getvalue()

            self.assertEqual(
                errs, [],
                f"lint should return no errors; got:\n{errs}\nstdout:\n{output}"
            )
            self.assertNotIn(
                "$0.00", output,
                "WU planned-cost sum must NOT be $0.00 — the task-graph "
                "regex picked the schema example instead of the gates block"
            )
            self.assertNotIn(
                "delta 100%", output,
                "cost-delta WARN must not fire at 100% — the regex bug "
                "would compute sum=0 against plan=$2.50"
            )


if __name__ == "__main__":
    unittest.main()
