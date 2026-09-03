#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for the bold-preamble Do-not-touch extraction fix (FEAT-2026-0055/T05).

`check_produces_boundary` (FEAT-2026-0055/T02) was blind to the canonical
`**Do not touch.**` bold-preamble body shape — the shape 327/327 real WU
bodies in this repo use — because `slice_wu_section` discarded the label
line's own content. This file exercises the fixed extractor against the
retrospective's real fixture set: the canonical deadlock (must ERROR), and
the four false-positive shapes the satisfiability sweep found (must not
ERROR). See `RETROSPECTIVE.md` §2a and §3 in this feature's folder.
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
    """Canonical bold-preamble body — every section label on the same line
    as its content, the shape the shipped template prescribes."""
    return f"""
**Context.** Test context.

**Acceptance criteria.** Something happens.

**Do not touch.** {do_not_touch}

**Verification.** Run tests.

**Escalation triggers.** If stuck.
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


class TestBoldPreamble(unittest.TestCase):
    """RETROSPECTIVE.md §2a — the fx-deadlock fixture, canonical bold form."""

    def test_canonical_bold_form_deadlock_errors(self):
        """The FEAT-2026-0066/T04 shape, written in the template's canonical
        bold-preamble form: produces path falls inside the WU's own
        Do-not-touch pattern, all on the label line. Must ERROR — this is
        the exact case the feature was chartered to catch, and on HEAD (the
        `slice_wu_section` bug) it lints clean instead."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T04", "file": "WU-04-deadlock.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "`src/main/**` (T03 owns it); other features' folders; "
                    "`.git/`."
                ),
                "produces": "src/main/java/Reconciler.java",
            }])
            _, errs = _lint_stdout(feat)
        joined = "\n".join(errs)
        self.assertIn("ERROR", joined)
        self.assertIn("FEAT-2026-0099/T04", joined)
        self.assertIn("src/main/java/Reconciler.java", joined)
        self.assertIn("src/main/**", joined)
        self.assertIn("assert_produces_in_diff", joined)


class TestProhibitionScoping(unittest.TestCase):
    """RETROSPECTIVE.md §3 — the four false-positive shapes, reproduced as
    fixtures (copied section text, not the live feature paths)."""

    def test_allow_enumeration_these_files_change_does_not_fire(self):
        """FEAT-2026-0023/T01 shape: an enumeration of the WU's own
        deliverables, introduced by 'These files change:', followed by a
        real prohibition sentence. The enumerated paths must not be read as
        forbidding themselves."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T01", "file": "WU-01.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "These files change: `.specfuse/scripts/loop.py`, "
                    "`.specfuse/skills/draft-feature/SKILL.md`, "
                    "`.specfuse/skills/authoring-work-units/SKILL.md`, and "
                    "one new test file `tests/test_terminal_flip_ownership.py`. "
                    "Do NOT modify `auto_archive_feature`, "
                    "`assert_terminal_flips_fired`, `ensure_feature_branch` "
                    "(T03 owns it), or `.specfuse/verification.yml`. Do NOT "
                    "edit existing WU files, secrets, `.git/`."
                ),
                "produces": [
                    ".specfuse/scripts/loop.py",
                    "tests/test_terminal_flip_ownership.py",
                ],
            }])
            _, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])

    def test_allow_enumeration_new_does_not_fire(self):
        """A clause naming a 'new' deliverable is an allow-signal, not a
        prohibition — the deliverable it names must not fire the boundary
        check on itself."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T02", "file": "WU-02.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "This WU adds a new file `specfuse/loop/_helper.py`; "
                    "other features' folders; `.git/`."
                ),
                "produces": "specfuse/loop/_helper.py",
            }])
            _, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])

    def test_existing_qualifier_downgrades_to_warn_not_error(self):
        """FEAT-2026-0070/T08 shape: 'every existing `check_*` function' —
        the rule cannot tell whether a produces path matching `check_*` is
        the pre-existing surface the boundary protects or a new function
        this very WU adds. Must WARN, never ERROR."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T08", "file": "WU-08.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "`REQUIRED_SECTIONS`, `VALID_FEATURE_STATUS`, and every "
                    "existing `check_*` function in `lint_plan.py` — this WU "
                    "adds one function and one call, and changes no existing "
                    "finding."
                ),
                "produces": "check_new_prediction",
            }])
            out, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])
        self.assertIn("WARN", out)
        self.assertIn("check_new_prediction", out)

    def test_existing_qualifier_second_shape_does_not_error(self):
        """A second 'existing' shape drawn from the same retrospective
        pattern class — confirms the qualifier, not one lucky token match,
        drives the downgrade."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = _build_feature(Path(tmp), [{
                "id": "FEAT-2026-0099/T09", "file": "WU-09.md",
                "type": "implementation", "status": "pending",
                "do_not_touch": (
                    "Every existing `handler_*` route in `routes.py` — this "
                    "WU adds one new route and touches nothing else."
                ),
                "produces": "handler_reconcile",
            }])
            _, errs = _lint_stdout(feat)
        self.assertEqual([], [e for e in errs if "produces path" in e])


if __name__ == "__main__":
    unittest.main()
