#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for check_produces_boundary (FEAT-2026-0055/T02).

ERROR when a WU's own `produces:` path (or `produces_driver_helper` surface)
falls inside its own Do-not-touch section's paths — a structural deadlock.
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


def _body_sections(do_not_touch: str) -> str:
    return f"""
## Context
Test context.

## Acceptance criteria
- something.

## Do not touch
{do_not_touch}

## Verification
- run tests.

## Escalation triggers
- if stuck.
"""


def _wu_text(
    wid: str,
    wu_type: str,
    status: str,
    do_not_touch: str,
    produces=None,
    produces_driver_helper: str | None = None,
) -> str:
    lines = ["---", f"id: {wid}", f"type: {wu_type}", f"status: {status}"]
    if produces is not None:
        if isinstance(produces, list):
            lines.append("produces:")
            for p in produces:
                lines.append(f"  - {p}")
        else:
            lines.append(f"produces: {produces}")
    if produces_driver_helper is not None:
        lines.append(f'produces_driver_helper: "{produces_driver_helper}"')
    lines.append("---")
    return "\n".join(lines) + "\n" + _body_sections(do_not_touch)


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
                w["id"], w["type"], w["status"], w["do_not_touch"],
                produces=w.get("produces"),
                produces_driver_helper=w.get("produces_driver_helper"),
            )
        )
    return feat


def _lint_stdout(feat: Path) -> tuple[str, list[str]]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        errs = lint_plan.lint(feat)
    return buf.getvalue(), errs


class TestProducesBoundary(unittest.TestCase):

    def test_errors_when_produces_inside_own_do_not_touch(self):
        """T04-shape: produces path falls inside the WU's own Do-not-touch
        pattern. ERROR names the WU, the offending path, the matched
        Do-not-touch pattern, and the post-attempt guard it preempts."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": "- `src/main/**` (owned by another WU).",
                "produces": "src/main/Foo.java",
            }])
            _, errs = _lint_stdout(feat)
        joined = "\n".join(errs)
        self.assertIn("ERROR", joined)
        self.assertIn("FEAT-2026-0099/T04", joined)
        self.assertIn("src/main/Foo.java", joined)
        self.assertIn("src/main/**", joined)
        self.assertIn("assert_produces_in_diff", joined)

    def test_carveout_except_suppresses_match(self):
        """0066/T04's re-armed body: an explicit 'except' carve-out on the
        same bullet suppresses the match — lints clean."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "- `src/main/**`, except `src/main/Foo.java` "
                    "(this WU's own deliverable)."
                ),
                "produces": "src/main/Foo.java",
            }])
            _, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])

    def test_plain_prose_mention_does_not_fire(self):
        """A Do-not-touch sentence mentioning a path in plain words (no
        backticks) never fires the rule — prose-safety."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "- Do not touch anything under src/main, it belongs to "
                    "another team."
                ),
                "produces": "src/main/Foo.java",
            }])
            _, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])

    def test_produces_driver_helper_naming_forbidden_surface_errors(self):
        """produces_driver_helper naming a surface inside the WU's own
        Do-not-touch pattern is the same deadlock shape — ERROR."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T04", "file": "WU-04.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": "- `src/main/**` (owned by another WU).",
                "produces_driver_helper": "src/main/Helper.java — new helper",
            }])
            _, errs = _lint_stdout(feat)
        joined = "\n".join(errs)
        self.assertIn("ERROR", joined)
        self.assertIn("produces_driver_helper", joined)
        self.assertIn("src/main/Helper.java", joined)
        self.assertIn("assert_produces_in_diff", joined)

    def test_clean_when_produces_outside_do_not_touch(self):
        """produces path outside the Do-not-touch pattern -> no ERROR (the
        ordinary case, e.g. this feature's own T01/T02 overlap)."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T02", "file": "WU-02.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": "- `specfuse/loop/loop.py` (T03's surface).",
                "produces": "specfuse/loop/lint_plan.py",
            }])
            _, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])


if __name__ == "__main__":
    unittest.main()
