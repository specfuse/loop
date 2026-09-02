#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the gate-proportionality lint (FEAT-2026-0084/T04).

A feature whose planned substantive WU count (types implementation,
qa_authoring, qa_execution, qa_curation) is at most the ceremony-
proportionality threshold should draft as a single gate
(docs/methodology.md §6 "Ceremony proportionality"). This WARN-only check
flags a small feature that was drafted across more than one gate.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()


def _write_wu(feature: Path, filename: str, wid: str, wu_type: str) -> None:
    (feature / filename).write_text(
        "---\n"
        f"id: {wid}\n"
        f"type: {wu_type}\n"
        "status: draft\n"
        "attempts: 0\n"
        "---\n\n# Title\n"
    )


def _make_feature(tmpdir: str, gates_units: list[list[str]]) -> Path:
    """Build a feature with gates_units[i] a list of WU types for gate i+1."""
    feature = Path(tmpdir) / "feature"
    feature.mkdir()

    gate_blocks = []
    wu_counter = 1
    for gate_idx, types in enumerate(gates_units, start=1):
        wu_lines = []
        for wu_type in types:
            wid = f"FEAT-2026-9997/T{wu_counter:02d}"
            wfile = f"WU-{wu_counter:02d}-{wu_type}.md"
            _write_wu(feature, wfile, wid, wu_type)
            wu_lines.append(
                f"      - id: {wid}\n"
                f"        file: {wfile}\n"
                f"        depends_on: []\n"
            )
            wu_counter += 1
        gate_blocks.append(
            f"  - gate: {gate_idx}\n"
            f"    file: GATE-{gate_idx:02d}.md\n"
            f"    work_units:\n" + "".join(wu_lines)
        )

    (feature / "PLAN.md").write_text(
        "---\n"
        "feature_id: FEAT-2026-9997\n"
        "title: Gate proportionality lint test\n"
        "branch: feat/gate-proportionality-test\n"
        "roadmap_goal: Verify gate-proportionality lint.\n"
        "status: active\n"
        "---\n\n# Plan\n\n```yaml\n"
        "gates:\n" + "".join(gate_blocks) + "```\n"
    )

    return feature


class TestLintGateProportionality(unittest.TestCase):

    def _run(self, feature: Path) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            fm, body = lint_plan.read_frontmatter(feature / "PLAN.md")
            graph = lint_plan._find_task_graph_block(body)
            lint_plan.lint_gate_proportionality(feature, graph["gates"])
        return buf.getvalue()

    def test_small_feature_two_gates_warns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                [
                    ["implementation", "implementation", "qa_authoring"],
                    ["qa_execution", "implementation", "qa_curation"],
                ],
            )
            out = self._run(feature)
            warns = [
                line for line in out.splitlines()
                if "WARN" in line and "planned substantive WU count" in line
            ]
            self.assertEqual(len(warns), 1, f"out={out!r}")
            self.assertIn("6", warns[0])
            self.assertIn("8", warns[0])

    def test_small_feature_one_gate_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                [
                    ["implementation", "implementation", "qa_authoring",
                     "qa_execution", "implementation", "qa_curation"],
                ],
            )
            out = self._run(feature)
            self.assertNotIn("WARN", out)

    def test_nine_units_two_gates_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = _make_feature(
                tmpdir,
                [
                    ["implementation"] * 5,
                    ["implementation"] * 4,
                ],
            )
            out = self._run(feature)
            self.assertNotIn("WARN", out)


if __name__ == "__main__":
    unittest.main()
