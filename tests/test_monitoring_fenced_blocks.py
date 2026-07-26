#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Drift guard: every fenced `yaml` block in monitoring prose must validate.

Gate 1 shipped one validated example, `.specfuse/monitoring.yml.example`,
guarded by the `monitoring-example-lint` gate. Gate 2 adds several more
examples, but they live inside markdown prose where no gate looks. This
module extracts every fenced ```yaml block from the declared surfaces below
and runs each through `validate_monitoring`, so a prose example cannot
silently drift from gate 1's schema.

Declared surfaces (the explicit scope — not inferred from a glob):
  - plugins/specfuse/skills/derive-monitoring/SKILL.md
  - plugins/specfuse/skills/derive-monitoring/PROMPT.md
  - .specfuse/skills/derive-monitoring/SKILL.md
  - .specfuse/skills/derive-monitoring/PROMPT.md
  - .specfuse/monitoring-secrets-checklist.md

Not covered, and why:
  - `.specfuse/monitoring.overrides.yml.example` — a YAML file, not prose;
    already validated directly by T06's tests.
  - `docs/concepts/monitoring-schema.md`'s `## Example` section — it has no
    inline fenced example; it points readers at
    `.specfuse/monitoring.yml.example`, which gate 1's
    `monitoring-example-lint` gate already validates on every run.

Fragment convention: a fenced ```yaml block that is a deliberate partial
snippet (not a complete config) carries `# lint-monitoring: fragment` as its
first line. This extractor skips it. The count of such blocks is asserted
explicitly below so the escape hatch cannot quietly become the norm.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from specfuse.loop.lint_monitoring import validate_monitoring

_REPO_ROOT = Path(__file__).resolve().parent.parent

_DECLARED_SURFACES = (
    _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring" / "SKILL.md",
    _REPO_ROOT / "plugins" / "specfuse" / "skills" / "derive-monitoring" / "PROMPT.md",
    _REPO_ROOT / ".specfuse" / "skills" / "derive-monitoring" / "SKILL.md",
    _REPO_ROOT / ".specfuse" / "skills" / "derive-monitoring" / "PROMPT.md",
    _REPO_ROOT / ".specfuse" / "monitoring-secrets-checklist.md",
)

_EXPECTED_BLOCK_COUNT = 4
_EXPECTED_FRAGMENT_COUNT = 0

_FRAGMENT_MARKER = "# lint-monitoring: fragment"

_YAML_FENCE_RE = re.compile(r"```yaml\n(.*?)```", re.DOTALL)


class _Block:
    def __init__(self, source: Path, line_no: int, body: str):
        self.source = source
        self.line_no = line_no
        self.body = body
        first_line = body.splitlines()[0] if body.splitlines() else ""
        self.is_fragment = first_line.strip() == _FRAGMENT_MARKER

    def where(self) -> str:
        return f"{self.source}:{self.line_no}"


def _extract_blocks(text: str, source: Path) -> list[_Block]:
    blocks = []
    for match in _YAML_FENCE_RE.finditer(text):
        line_no = text[: match.start()].count("\n") + 1
        blocks.append(_Block(source, line_no, match.group(1)))
    return blocks


def _all_blocks() -> list[_Block]:
    blocks: list[_Block] = []
    for path in _DECLARED_SURFACES:
        blocks.extend(_extract_blocks(path.read_text(), path))
    return blocks


class MonitoringFencedBlockTests(unittest.TestCase):
    def test_declared_surfaces_all_exist(self):
        for path in _DECLARED_SURFACES:
            self.assertTrue(path.is_file(), f"declared surface missing: {path}")

    def test_extractor_finds_the_expected_block_count(self):
        blocks = _all_blocks()
        self.assertGreaterEqual(len(blocks), 1, "no fenced yaml blocks found at all")
        self.assertEqual(
            len(blocks),
            _EXPECTED_BLOCK_COUNT,
            f"expected {_EXPECTED_BLOCK_COUNT} fenced yaml blocks across "
            f"declared surfaces, found {len(blocks)}: "
            f"{[b.where() for b in blocks]}",
        )

    def test_fragment_markers_are_bounded(self):
        blocks = _all_blocks()
        fragments = [b for b in blocks if b.is_fragment]
        for block in fragments:
            first_line = block.body.splitlines()[0] if block.body.splitlines() else ""
            self.assertEqual(
                first_line.strip(),
                _FRAGMENT_MARKER,
                f"{block.where()}: fragment marker must be the block's first line",
            )
        self.assertEqual(
            len(fragments),
            _EXPECTED_FRAGMENT_COUNT,
            f"expected {_EXPECTED_FRAGMENT_COUNT} fragment-marked blocks, "
            f"found {len(fragments)}: {[b.where() for b in fragments]}",
        )

    def test_every_yaml_block_validates_clean(self):
        blocks = [b for b in _all_blocks() if not b.is_fragment]
        for block in blocks:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / "monitoring.yml"
                tmp_path.write_text(block.body)
                findings = validate_monitoring(tmp_path)
            self.assertEqual(
                findings,
                [],
                f"{block.where()}: fenced yaml block failed validation: {findings}",
            )

    def test_extractor_catches_a_broken_block(self):
        markdown = """
Some prose introducing an example.

```yaml
environments:
  staging:
    telemetry:
      provider: acme-telemetry
      credentials:
        api_key: ACME_TELEMETRY_STAGING_API_KEY
    broker:
      provider: acme-broker
      credentials:
        connection_string: ACME_BROKER_STAGING_CONNECTION_STRING

components:
  - name: acme-web-api
    type: http-service
    runner: not-a-real-runner
    diagnose: manual
    autofix: "off"
    checks:
      - type: heartbeat
```

More prose after the example.
"""
        blocks = _extract_blocks(markdown, Path("<inline>"))
        self.assertEqual(len(blocks), 1)

        all_findings: list[str] = []
        for block in blocks:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / "monitoring.yml"
                tmp_path.write_text(block.body)
                all_findings.extend(validate_monitoring(tmp_path))

        self.assertEqual(len(all_findings), 1, all_findings)
        self.assertIn("runner", all_findings[0])


if __name__ == "__main__":
    unittest.main()
