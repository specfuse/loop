#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for check_produces_satisfiability (FEAT-2026-0055/T01).

WARN when a dispatchable WU's `produces:` path exactly matches a `done` WU's
`produces:` entry in the same feature.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

_VALID_FM = """\
---
feature_id: FEAT-2026-0099
title: Test Feature
branch: feat/test
roadmap_goal: Test goal
status: active
---
"""

_BODY_SECTIONS = """
## Context
Test context.

## Acceptance criteria
- something.

## Do not touch
- nothing.

## Verification
- run tests.

## Escalation triggers
- if stuck.
"""


def _wu_text(
    wid: str,
    wu_type: str,
    status: str,
    produces=None,
    produces_incremental=None,
    extra: str = "",
) -> str:
    lines = ["---", f"id: {wid}", f"type: {wu_type}", f"status: {status}"]
    if produces is not None:
        if isinstance(produces, list):
            lines.append("produces:")
            for p in produces:
                lines.append(f"  - {p}")
        else:
            lines.append(f"produces: {produces}")
    if produces_incremental is not None:
        if isinstance(produces_incremental, list):
            lines.append("produces_incremental:")
            for p in produces_incremental:
                lines.append(f"  - {p}")
        else:
            lines.append(f"produces_incremental: {produces_incremental}")
    if extra:
        lines.append(extra)
    lines.append("---")
    return "\n".join(lines) + "\n" + _BODY_SECTIONS


def _make_graph(work_units: list[dict]) -> str:
    parts = ["```yaml", "gates:", "  - gate: 1", "    work_units:"]
    for wu in work_units:
        parts.append(f"      - id: {wu['id']}")
        parts.append(f"        file: {wu['file']}")
        parts.append("        depends_on: []")
    parts.append("```")
    return "\n".join(parts)


def _build_feature(tmp_path: Path, wus: list[dict]) -> Path:
    feat = tmp_path / "feat"
    feat.mkdir()
    (feat / "PLAN.md").write_text(
        _VALID_FM + "\n" + _make_graph([{"id": w["id"], "file": w["file"]} for w in wus]) + "\n"
    )
    for w in wus:
        (feat / w["file"]).write_text(
            _wu_text(
                w["id"], w["type"], w["status"],
                produces=w.get("produces"),
                produces_incremental=w.get("produces_incremental"),
            )
        )
    return feat


def _lint_stdout(feat: Path) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        lint_plan.lint(feat)
    return buf.getvalue()


class TestProducesSatisfiability(unittest.TestCase):

    def test_warns_when_done_wu_already_declared_path(self):
        """T04-shape: a dispatchable WU's produces path was already delivered
        in full by a done WU. WARN names both WUs and the shared path."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [
                {
                    "id": "FEAT-2026-0099/T03", "file": "WU-03.md",
                    "type": "implementation", "status": "done",
                    "produces": "src/widget.py",
                },
                {
                    "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                    "type": "implementation", "status": "pending",
                    "produces": "src/widget.py",
                },
            ])
            out = _lint_stdout(feat)
        self.assertIn("WARN", out)
        self.assertIn("FEAT-2026-0099/T04", out)
        self.assertIn("FEAT-2026-0099/T03", out)
        self.assertIn("src/widget.py", out)
        self.assertIn("Drop the path, declare it under produces_incremental:", out)

    def test_incremental_edit_chain_still_warns(self):
        """0066 T03->T05 shape: a later WU incrementally edits a path an
        earlier done WU already produced. Still WARNs — the message's
        'state the incremental edit' branch is the correct outcome here,
        asserted on message content (not silence)."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [
                {
                    "id": "FEAT-2026-0099/T03", "file": "WU-03.md",
                    "type": "implementation", "status": "done",
                    "produces": "src/shared.py",
                },
                {
                    "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                    "type": "implementation", "status": "done",
                    "produces": "src/other.py",
                },
                {
                    "id": "FEAT-2026-0099/T05", "file": "WU-05.md",
                    "type": "implementation", "status": "ready",
                    "produces": "src/shared.py",
                },
            ])
            out = _lint_stdout(feat)
        self.assertIn("WARN", out)
        self.assertIn("FEAT-2026-0099/T05", out)
        self.assertIn("FEAT-2026-0099/T03", out)
        self.assertIn("src/shared.py", out)
        self.assertIn("incremental edit this WU makes to it in the body", out)

    def test_clean_feature_no_warn(self):
        """Distinct produces paths across WUs never clash — no WARN."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [
                {
                    "id": "FEAT-2026-0099/T01", "file": "WU-01.md",
                    "type": "implementation", "status": "done",
                    "produces": "src/a.py",
                },
                {
                    "id": "FEAT-2026-0099/T02", "file": "WU-02.md",
                    "type": "implementation", "status": "pending",
                    "produces": "src/b.py",
                },
            ])
            out = _lint_stdout(feat)
        self.assertNotIn("already delivered it", out)

    def test_no_warn_when_earlier_wu_not_done(self):
        """Parallel drafts legitimately sharing a surface: earlier WU is not
        `done` (e.g. still `pending`) -> no WARN."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [
                {
                    "id": "FEAT-2026-0099/T01", "file": "WU-01.md",
                    "type": "implementation", "status": "pending",
                    "produces": "src/shared.py",
                },
                {
                    "id": "FEAT-2026-0099/T02", "file": "WU-02.md",
                    "type": "implementation", "status": "draft",
                    "produces": "src/shared.py",
                },
            ])
            out = _lint_stdout(feat)
        self.assertNotIn("already delivered it", out)

    def test_no_warn_when_declared_produces_incremental(self):
        """#1041: a WU that declares the overlapping path under
        produces_incremental: is making a real, observable claim that this is
        an in-place edit to an existing file — the WARN is suppressed instead
        of sending the author toward an unobservable body-prose fix."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [
                {
                    "id": "FEAT-2026-0099/T01", "file": "WU-01.md",
                    "type": "implementation", "status": "done",
                    "produces": "src/shared.py",
                },
                {
                    "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                    "type": "implementation", "status": "pending",
                    "produces": "src/shared.py",
                    "produces_incremental": "src/shared.py",
                },
            ])
            out = _lint_stdout(feat)
        self.assertNotIn("already delivered it", out)

    def test_no_warn_for_events_jsonl(self):
        """events.jsonl is a common append-only surface many WUs legitimately
        declare; never treated as a clash."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [
                {
                    "id": "FEAT-2026-0099/T01", "file": "WU-01.md",
                    "type": "implementation", "status": "done",
                    "produces": "events.jsonl",
                },
                {
                    "id": "FEAT-2026-0099/T02", "file": "WU-02.md",
                    "type": "implementation", "status": "pending",
                    "produces": "events.jsonl",
                },
            ])
            out = _lint_stdout(feat)
        self.assertNotIn("already delivered it", out)


if __name__ == "__main__":
    unittest.main()
