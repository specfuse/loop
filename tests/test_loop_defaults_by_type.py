#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Defaults-by-WU-type policy — FEAT-2026-0007/T06.

Verifies that:
  (a) WU with no model and type: implementation loads with wu.model == 'sonnet'.
  (b) WU with no effort and type: plan-next loads with wu.effort == 'high'.
  (c) WU with model: opus and type: implementation loads with wu.model == 'opus'
      (explicit override wins).
  (d) lint_plan exits 0 on a WU that omits model entirely (model-optional
      regression — FEAT-2026-0005/G1-LESSONS fixture pattern).
  (e) lint_plan rejects a WU whose model key is present but has no value
      (escalation trigger: present-but-empty must not silently pass).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_loop, load_lint

loop = load_loop()
lint = load_lint()


def _write_wu(
    tmp: Path,
    *,
    wu_id: str = "FEAT-2026-9999/T06",
    wu_type: str = "implementation",
    model: str | None = None,
    effort: str | None = None,
    model_empty: bool = False,
) -> Path:
    """Write a minimal WU file to tmp.

    model_empty=True writes `model:` with no value (present-but-empty case).
    model=<str> writes `model: <str>`. Both absent by default.
    """
    fname = wu_id.split("/")[-1]
    if model_empty:
        model_line = "model:\n"
    elif model is not None:
        model_line = f"model: {model}\n"
    else:
        model_line = ""
    effort_line = f"effort: {effort}\n" if effort is not None else ""
    path = tmp / f"WU-{fname}.md"
    path.write_text(
        f"---\nid: {wu_id}\ntype: {wu_type}\n"
        f"{model_line}{effort_line}"
        f"status: pending\nattempts: 0\n---\n\n"
        f"# Test unit {fname}\n\n"
        "**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    return path


def _make_feature(tmp: Path, model: str | None = None,
                  model_empty: bool = False) -> Path:
    """Build a minimal single-gate feature dir for lint testing."""
    fdir = tmp / "FEAT-2026-9999-defaults"
    fdir.mkdir()
    _write_wu(fdir, wu_id="FEAT-2026-9999/T06", wu_type="implementation",
              model=model, model_empty=model_empty)
    plan = (
        "---\nfeature_id: FEAT-2026-9999\ntitle: defaults test\n"
        "branch: feat/defaults\nroadmap_goal: test\nstatus: active\n---\n\n"
        "```yaml\ngates:\n"
        "  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        "      - id: FEAT-2026-9999/T06\n        file: WU-T06.md\n"
        "        depends_on: []\n"
        "      - id: FEAT-2026-9999/G1-RETRO\n        file: WU-G1-RETRO.md\n"
        "        depends_on: [FEAT-2026-9999/T06]\n"
        "      - id: FEAT-2026-9999/G1-LESSONS\n        file: WU-G1-LESSONS.md\n"
        "        depends_on: [FEAT-2026-9999/G1-RETRO]\n"
        "      - id: FEAT-2026-9999/G1-DOCS\n        file: WU-G1-DOCS.md\n"
        "        depends_on: [FEAT-2026-9999/G1-LESSONS]\n"
        "      - id: FEAT-2026-9999/G1-PLAN\n        file: WU-G1-PLAN.md\n"
        "        depends_on: [FEAT-2026-9999/G1-DOCS]\n"
        "```\n"
    )
    (fdir / "PLAN.md").write_text(plan)
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    body = (
        "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
        "**Do not touch.** test\n\n**Verification.** test\n\n"
        "**Escalation triggers.** test\n"
    )
    for wu_id, wtype in [
        ("FEAT-2026-9999/G1-RETRO", "retrospective"),
        ("FEAT-2026-9999/G1-LESSONS", "lessons"),
        ("FEAT-2026-9999/G1-DOCS", "docs"),
        ("FEAT-2026-9999/G1-PLAN", "plan-next"),
    ]:
        tnn = wu_id.split("/")[-1]
        (fdir / f"WU-{tnn}.md").write_text(
            f"---\nid: {wu_id}\ntype: {wtype}\nmodel: sonnet\n"
            f"status: pending\nattempts: 0\n---\n\n# {tnn}{body}"
        )
    return fdir


class TestModelDefaultByType(unittest.TestCase):

    def test_absent_model_implementation_defaults_to_sonnet(self):
        """(a) No model + type:implementation -> wu.model == 'sonnet'."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), wu_type="implementation")
            ref = {"id": "FEAT-2026-9999/T06", "file": "WU-T06.md", "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)
            self.assertEqual(wu.model, "sonnet")

    def test_absent_effort_plan_next_defaults_to_high(self):
        """(b) No effort + type:plan-next -> wu.effort == 'high'."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), wu_id="FEAT-2026-9999/T06", wu_type="plan-next")
            ref = {"id": "FEAT-2026-9999/T06", "file": "WU-T06.md", "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)
            self.assertEqual(wu.effort, "high")

    def test_explicit_model_overrides_type_default(self):
        """(c) model:opus on type:implementation -> wu.model == 'opus' (override wins)."""
        with tempfile.TemporaryDirectory() as tmp:
            _write_wu(Path(tmp), wu_type="implementation", model="opus")
            ref = {"id": "FEAT-2026-9999/T06", "file": "WU-T06.md", "depends_on": []}
            wu = loop.load_wu(Path(tmp), ref)
            self.assertEqual(wu.model, "opus")


class TestLintModelOptional(unittest.TestCase):

    def test_lint_exits_0_when_model_absent(self):
        """(d) lint exits 0 on a WU that omits model field entirely."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _make_feature(Path(tmp), model=None)
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "model" in e]
            self.assertEqual(model_errs, [],
                             f"unexpected model errors: {model_errs}")

    def test_lint_rejects_present_but_empty_model(self):
        """(e) model: with no value is rejected by lint."""
        with tempfile.TemporaryDirectory() as tmp:
            fdir = _make_feature(Path(tmp), model_empty=True)
            errs = lint.lint(fdir)
            model_errs = [e for e in errs if "model" in e]
            self.assertEqual(len(model_errs), 1,
                             f"expected 1 model error for empty model, got: {model_errs}")


if __name__ == "__main__":
    unittest.main()
