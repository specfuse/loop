#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""ATX-heading section detection in lint_plan.py.

Orchestrator-dispatched WU bodies use ATX headings (## Context, ## Acceptance
criteria, …) rather than the bold-preamble form (**Context.**) the loop's own
WUs use.  Broadening the section regex to admit #+\s* in addition to \** must:
  - pass ATX-headed bodies
  - still pass bold-headed bodies (regression guard)
  - still reject bodies that genuinely omit a required section
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FEATURE = REPO_ROOT / ".specfuse/features/FEAT-2026-0001-health-endpoint"

_ATX_BODY = """\
## Context

Part of feature FEAT-2026-0001. Operators verify health without logs.

## Acceptance criteria

`GET /health` responds 200 with JSON body containing `status: "ok"` and a version string.

## Do not touch

Generated directories, other routes, secrets, `.git/`.

## Verification

The `code` gates in `.specfuse/verification.yml`.

## Escalation triggers

If no router module exists yet, emit `status: blocked` — separate unit of work.
"""


def copy_example_to(tmp: Path) -> Path:
    dest = tmp / "feature"
    shutil.copytree(EXAMPLE_FEATURE, dest)
    return dest


def _replace_wu_body(wu_path: Path, new_body: str) -> None:
    """Swap the body of a WU file, preserving its frontmatter block intact."""
    text = wu_path.read_text()
    lines = text.splitlines()
    j = 1
    while j < len(lines) and lines[j] != "---":
        j += 1
    fm_part = "\n".join(lines[: j + 1]) + "\n"
    wu_path.write_text(fm_part + "\n" + new_body)


class TestSectionHeadingForms(unittest.TestCase):
    """lint_plan.lint() section detector accepts ATX and bold; rejects missing."""

    def test_atx_headed_sections_pass(self):
        """## Heading form must satisfy the mandatory-section check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            _replace_wu_body(feature / "WU-01-health-endpoint.md", _ATX_BODY)
            errs = lint_plan.lint(feature)
            section_errs = [e for e in errs if "missing section" in e]
            self.assertEqual(
                section_errs,
                [],
                f"ATX-headed WU must pass section check; section_errs={section_errs}",
            )

    def test_bold_headed_sections_pass(self):
        """**Bold.** form must still pass — regression guard for loop's own WUs."""
        errs = lint_plan.lint(EXAMPLE_FEATURE)
        section_errs = [e for e in errs if "missing section" in e]
        self.assertEqual(
            section_errs,
            [],
            f"bold-form WU must pass section check; section_errs={section_errs}",
        )

    def test_missing_section_fails(self):
        """A WU genuinely missing a required section must still be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            feature = copy_example_to(Path(tmpdir))
            wu = feature / "WU-01-health-endpoint.md"
            text = wu.read_text()
            assert "**Escalation triggers.**" in text, "sentinel not found"
            wu.write_text(text.replace("**Escalation triggers.**", "**Hints.**", 1))
            errs = lint_plan.lint(feature)
            section_errs = [e for e in errs if "missing section" in e]
            self.assertTrue(
                section_errs,
                "WU with missing section must produce section errors",
            )
            self.assertTrue(
                any("Escalation triggers" in e for e in section_errs),
                f"error must name the missing section; section_errs={section_errs}",
            )
