#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`specfuse lint` must reject what `load_wu` refuses (#3331).

`specfuse lint <feature-dir>` is documented as the gate that must exit 0 before
arming or dispatching. A folder it passes must dispatch — a lint that exits 0
on an undispatchable unit is a false green on the one check meant to prevent
exactly that.

The report named one invariant: `unsandboxed: true` with no
`unsandboxed_rationale`, which `load_wu` raises on and lint did not check. It
also guessed the miss was a class rather than a single case. Sweeping
`load_wu`'s eight `ValueError` invariants against a folder that lints clean
found **five** with no lint counterpart:

    unsandboxed without rationale   iterate_on_failure non-bool
    extra_gates non-list            prep non-list
    oracles non-list

The other three (`effort`, `produces`, `produces_driver_helper`) already exit
non-zero, but only incidentally — the scalar fails YAML parsing before
`load_wu`'s own check is reached.

These tests assert the pairing directly: for each invariant, a WU that
`load_wu` refuses must make `lint_plan` report an error.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop import lint_plan
from specfuse.loop import loop as L


WU = """\
---
id: FEAT-2026-9902/T01
type: implementation
status: pending
attempts: 0
{extra}---

# T

**Objective.** x

**Acceptance criteria.**

- x

**Do not touch.** x

**Verification.** x

**Escalation triggers.** x
"""

CASES = {
    "unsandboxed_without_rationale": "unsandboxed: true\n",
    "iterate_on_failure_non_bool": "iterate_on_failure: yes-please\n",
    "extra_gates_non_list": "extra_gates: 9\n",
    "prep_non_list": "prep: 4\n",
    "oracles_non_list": "oracles: 5\n",
}


class LintRejectsWhatTheDriverRefuses(unittest.TestCase):

    def _wu_path(self, tmp: Path, extra: str) -> Path:
        path = tmp / "WU-01-t.md"
        path.write_text(WU.format(extra=extra), encoding="utf-8")
        return path

    def test_load_wu_still_refuses_each_case(self):
        # Pins the premise: if a future change makes load_wu accept one of
        # these, the matching lint check below is dead weight and should go
        # with it rather than linger as an unexplained rule.
        for name, extra in CASES.items():
            with self.subTest(name), TemporaryDirectory() as t:
                tmp = Path(t)
                self._wu_path(tmp, extra)
                with self.assertRaises(ValueError):
                    L.load_wu(tmp, {"id": "FEAT-2026-9902/T01",
                                    "file": "WU-01-t.md", "depends_on": []})

    def test_lint_reports_an_error_for_each_case(self):
        for name, extra in CASES.items():
            with self.subTest(name), TemporaryDirectory() as t:
                tmp = Path(t)
                path = self._wu_path(tmp, extra)
                fm, _ = lint_plan.read_frontmatter(path)
                errs = lint_plan.wu_frontmatter_errors(fm, path.name)
                self.assertTrue(
                    errs, f"{name}: lint reported nothing for a unit load_wu refuses")

    def test_a_valid_unit_reports_nothing(self):
        # The control: the checks must not fire on the frontmatter every
        # existing feature already carries.
        with TemporaryDirectory() as t:
            tmp = Path(t)
            path = self._wu_path(
                tmp,
                "unsandboxed: true\nunsandboxed_rationale: dispatches nested sessions\n"
                "iterate_on_failure: true\nextra_gates: [live-verify]\n"
                "prep: [setup.sh]\noracles: [smoke]\n")
            fm, _ = lint_plan.read_frontmatter(path)
            self.assertEqual([], lint_plan.wu_frontmatter_errors(fm, path.name))

    def test_absent_optional_keys_report_nothing(self):
        with TemporaryDirectory() as t:
            tmp = Path(t)
            path = self._wu_path(tmp, "")
            fm, _ = lint_plan.read_frontmatter(path)
            self.assertEqual([], lint_plan.wu_frontmatter_errors(fm, path.name))


if __name__ == "__main__":
    unittest.main()
