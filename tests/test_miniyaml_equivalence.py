#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Positive equivalence: _miniyaml.parse must produce structurally-identical
output to yaml.safe_load on every real YAML input in this repo.

This is the strongest "no behavior change on valid files" check — for the
canonical inputs the loop reads in production (frontmatter, the PLAN graph,
verification.yml, and the agent's RESULT block fixtures), the two parsers
must return the same dict / list / scalar tree.

PyYAML is a DEV dependency only; this test file requires it to run, but
production code (loop.py, lint_plan.py) does not.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml  # dev-only — see pyproject.toml [project.optional-dependencies] dev

from tests._loop_loader import load_miniyaml

miniyaml = load_miniyaml()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"


def frontmatter_of(path: Path) -> str:
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        i += 1
    return "\n".join(lines[1:i])


def plan_graph_block(path: Path) -> str:
    text = path.read_text()
    m = re.search(r"```ya?ml\s*\n(.*?)\n```", text, re.DOTALL)
    if not m:
        return ""
    return m.group(1)


class TestParserEquivalenceOnRealFiles(unittest.TestCase):
    """For every real YAML input in the repo, miniyaml.parse == yaml.safe_load."""

    def _assert_equivalent(self, label: str, text: str):
        actual = miniyaml.parse(text)
        expected = yaml.safe_load(text)
        self.assertEqual(actual, expected,
                         f"miniyaml/pyyaml mismatch on {label}\n"
                         f"  miniyaml: {actual!r}\n"
                         f"  pyyaml:   {expected!r}")

    def test_plan_md_frontmatter(self):
        self._assert_equivalent("PLAN.md frontmatter",
                                frontmatter_of(EXAMPLE / "PLAN.md"))

    def test_plan_md_graph_block(self):
        self._assert_equivalent("PLAN.md graph block",
                                plan_graph_block(EXAMPLE / "PLAN.md"))

    def test_gate_01_md_frontmatter(self):
        self._assert_equivalent("GATE-01.md frontmatter",
                                frontmatter_of(EXAMPLE / "GATE-01.md"))

    def test_gate_02_md_frontmatter(self):
        self._assert_equivalent("GATE-02.md frontmatter",
                                frontmatter_of(EXAMPLE / "GATE-02.md"))

    def test_every_wu_file_frontmatter(self):
        wu_files = sorted(EXAMPLE.glob("WU-*.md"))
        self.assertGreater(len(wu_files), 0, "expected WU files in the example")
        for p in wu_files:
            with self.subTest(file=p.name):
                self._assert_equivalent(f"{p.name} frontmatter", frontmatter_of(p))

    def test_verification_yml_example(self):
        path = REPO_ROOT / ".specfuse/verification.yml.example"
        self._assert_equivalent("verification.yml.example", path.read_text())

    def test_this_repos_verification_yml(self):
        path = REPO_ROOT / ".specfuse/verification.yml"
        self._assert_equivalent("verification.yml (this repo's actual)",
                                path.read_text())


# --- Result-block fixtures from test_result_block.py ---------------------- #

# We re-define the well-formed fixtures here to avoid a cross-test-module
# import cycle. The malformed-by-design fixture is correctly NOT included in
# the equivalence suite — it is asserted in test_miniyaml_negative.

_BLOCKED = """\
status: blocked
summary: cannot add a route because no router module exists
files_changed: []
acceptance_criteria:
  - text: GET /health responds 200
    met: false
    evidence: router module not present
blocked_reason: no router module exists at the path the WU references
"""

_COMPLETE = """\
status: complete
summary: added GET /health returning {status, version}
files_changed:
  - src/routes/health.py
acceptance_criteria:
  - text: GET /health responds 200
    met: true
    evidence: pytest tests/test_health.py::test_status_ok passed
"""


class TestParserEquivalenceOnResultBlocks(unittest.TestCase):

    def test_blocked_result_block(self):
        self.assertEqual(miniyaml.parse(_BLOCKED), yaml.safe_load(_BLOCKED))

    def test_complete_result_block(self):
        self.assertEqual(miniyaml.parse(_COMPLETE), yaml.safe_load(_COMPLETE))


if __name__ == "__main__":
    unittest.main()
