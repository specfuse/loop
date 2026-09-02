#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`WU.template.md` must lint clean once rendered into a real feature folder.

The template is the file every WU is copied from, but nothing ever fed it to
`lint_plan` — the linter only ever sees the *result* of an author editing it.
So a template could ship (and did ship, at 199 lines) prescribing a shape the
linter's own required-section check would reject, and the failure would surface
at a newcomer's first `specfuse lint`, not here.

This module renders the template into a temporary feature folder with a minimal
PLAN.md and runs `lint_plan.lint` over it, per LEARNINGS `[FEAT-2026-0015/G1]`
(the shipped artifact is checked by the checker that will judge it, not by a
hand-written restatement of what the checker wants).

It also pins the two properties FEAT-2026-0084/T02 set the template to: a
70-line ceiling, and exactly the five mandatory `**Section.**` preambles the
linter requires.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

REPO_ROOT = Path(__file__).resolve().parent.parent
WU_TEMPLATE = REPO_ROOT / ".specfuse" / "templates" / "WU.template.md"

TEMPLATE_LINE_CEILING = 70

# The five sections `lint_plan.REQUIRED_SECTIONS` enforces on a dispatchable WU,
# in the `**Section.**` preamble form 327 existing bodies use.
MANDATORY_SECTIONS = (
    "Context",
    "Acceptance criteria",
    "Do not touch",
    "Verification",
    "Escalation triggers",
)
_SECTION_PREAMBLE_RE = re.compile(
    r"^\*\*(?:" + "|".join(MANDATORY_SECTIONS) + r")\.\*\*", re.MULTILINE
)

_FEATURE_ID = "FEAT-2026-0099"
_IMPL_ID = f"{_FEATURE_ID}/T01"
_CLOSE_ID = f"{_FEATURE_ID}/G1-CLOSE"
_IMPL_FILE = "WU-01-impl.md"
_CLOSE_FILE = "WU-90-gate-1-close.md"

_PLAN = f"""\
---
feature_id: {_FEATURE_ID}
title: Template render check
branch: feat/template-render-check
roadmap_goal: The shipped WU template lints clean when rendered.
status: active
---

# Plan: template render check

```yaml
gates:
  - gate: 1
    work_units:
      - id: {_IMPL_ID}
        file: {_IMPL_FILE}
        depends_on: []
      - id: {_CLOSE_ID}
        file: {_CLOSE_FILE}
        depends_on: [{_IMPL_ID}]
```
"""

_CLOSE_WU = f"""\
---
id: {_CLOSE_ID}
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
---

# Close gate 1

**Context.** Terminal close for {_FEATURE_ID}.

**Acceptance criteria.** The feature's oracles re-run fresh and pass.

**Do not touch.** Anything outside this feature folder.

**Verification.** `specfuse lint --closing` exits 0.

**Escalation triggers.** A criterion that cannot be verified here.
"""


def render_template(wu_id: str = _IMPL_ID) -> str:
    """Return the shipped template with its placeholder ID bound to `wu_id`.

    This is the whole rendering an author does by hand: swap the placeholder
    correlation ID for a real one. Everything else in the template — including
    the angle-bracket title placeholder — is left exactly as shipped, because
    that is the state the linter has to accept for the template to be usable.
    """
    return WU_TEMPLATE.read_text(encoding="utf-8").replace("FEAT-YYYY-NNNN/T01", wu_id)


def _build_feature(root: Path) -> Path:
    feat = root / f"{_FEATURE_ID}-template-render-check"
    feat.mkdir()
    (feat / "PLAN.md").write_text(_PLAN, encoding="utf-8")
    (feat / _IMPL_FILE).write_text(render_template(), encoding="utf-8")
    (feat / _CLOSE_FILE).write_text(_CLOSE_WU, encoding="utf-8")
    return feat


def test_rendered_template_passes_lint():
    """The shipped template, rendered into a feature folder, lints with no errors."""
    with tempfile.TemporaryDirectory() as tmp:
        feat = _build_feature(Path(tmp))
        errs = lint_plan.lint(feat)
    assert errs == [], (
        "WU.template.md does not lint clean when rendered into a feature folder.\n"
        "The template is what every WU is copied from; a template the linter "
        "rejects makes every fresh WU start red.\n\nErrors:\n"
        + "\n".join(f"  {e}" for e in errs)
    )


class TestWUTemplateRendersLintable(unittest.TestCase):
    """Unittest surface for the same checks (`unittest discover` is the gate)."""

    def test_rendered_template_passes_lint(self):
        test_rendered_template_passes_lint()

    def test_template_stays_under_the_line_ceiling(self):
        lines = WU_TEMPLATE.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(
            len(lines), TEMPLATE_LINE_CEILING,
            f"WU.template.md is {len(lines)} lines, over the "
            f"{TEMPLATE_LINE_CEILING}-line ceiling (FEAT-2026-0084/T02). Field "
            f"semantics belong in docs/methodology.md §2, one line per field.",
        )

    def test_template_carries_exactly_the_five_mandatory_sections(self):
        text = WU_TEMPLATE.read_text(encoding="utf-8")
        found = _SECTION_PREAMBLE_RE.findall(text)
        self.assertEqual(
            len(found), len(MANDATORY_SECTIONS),
            f"expected exactly {len(MANDATORY_SECTIONS)} `**Section.**` "
            f"preambles in WU.template.md, found {len(found)}",
        )
        for section in MANDATORY_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(f"**{section}.**", text)


if __name__ == "__main__":
    unittest.main()
