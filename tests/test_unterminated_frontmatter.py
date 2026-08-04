#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""#306 — a malformed WU must be a finding, not a traceback.

Reported as "crashes on an HTML comment in WU frontmatter". The comment is a
red herring: it sits in the *body*. The real defect is an **unterminated**
frontmatter block — an opening `---` with no closing one — so the reader scans
past the end of the block and parses the whole document as frontmatter,
crashing on the first line that is not `key: value`.

Two real files in FEAT-2026-0020 carry exactly one `---`. Until this is fixed
that folder is unevaluable by *every* check, because the crash happens before
any of them run.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tests._loop_loader import load_lint

lint_plan = load_lint()

_UNTERMINATED = """\
---
id: FEAT-2026-0099/T01
type: implementation
status: done

<!--
Copyright 2026 Specfuse Contributors
-->

# A work unit whose frontmatter was never closed
"""

_PLAN = """\
---
feature_id: FEAT-2026-0099
title: Probe
branch: feat/probe
roadmap_goal: probe
status: active
---

```yaml
gates:
  - gate: 1
    work_units:
      - id: FEAT-2026-0099/T01
        file: WU-01.md
        depends_on: []
```
"""


class TestUnterminatedFrontmatter(unittest.TestCase):
    def _feature(self, tmp: str, wu_text: str) -> Path:
        feat = Path(tmp) / "feat"
        feat.mkdir()
        (feat / "PLAN.md").write_text(_PLAN)
        (feat / "WU-01.md").write_text(wu_text)
        return feat

    def test_read_frontmatter_does_not_swallow_the_body(self):
        """The precise bug: the scan runs off the end and eats the document."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "WU-01.md"
            p.write_text(_UNTERMINATED)
            with self.assertRaises(lint_plan._miniyaml.MiniYAMLError) as ctx:
                lint_plan.read_frontmatter(p)
            msg = str(ctx.exception)
            self.assertIn("---", msg)
            self.assertNotIn("not a `key: value` line", msg,
                             "message blames the body instead of the missing "
                             "delimiter, which is what sent #306 chasing an "
                             "HTML comment")

    def test_lint_reports_a_finding_instead_of_raising(self):
        """A parser that cannot evaluate a folder must say so, not crash."""
        with tempfile.TemporaryDirectory() as tmp:
            feat = self._feature(tmp, _UNTERMINATED)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                errs = lint_plan.lint(feat)   # must not raise
            blob = " ".join(str(e) for e in errs) + buf.getvalue()
            self.assertIn("WU-01.md", blob)
            self.assertTrue(
                any("---" in str(e) for e in errs),
                f"no finding named the unterminated block: {errs}",
            )

    def test_a_well_formed_wu_is_unaffected(self):
        good = _UNTERMINATED.replace("status: done\n", "status: done\n---\n")
        with tempfile.TemporaryDirectory() as tmp:
            feat = self._feature(tmp, good)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                errs = lint_plan.lint(feat)
            self.assertEqual(
                [e for e in errs if "---" in str(e)], [],
                "a closed frontmatter block was reported as unterminated",
            )

    def test_html_comment_in_the_body_is_fine(self):
        """The thing #306 blamed must keep working."""
        good = _UNTERMINATED.replace("status: done\n", "status: done\n---\n")
        self.assertIn("<!--", good)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "WU-01.md"
            p.write_text(good)
            fm, body = lint_plan.read_frontmatter(p)
            self.assertEqual(fm.get("id"), "FEAT-2026-0099/T01")
            self.assertIn("<!--", body)


class TestRealFolderIsEvaluable(unittest.TestCase):
    """The folder from the report must lint without crashing."""

    def test_feat_0020_lints(self):
        feat = (
            Path(__file__).resolve().parents[1]
            / ".specfuse" / "features" / "FEAT-2026-0020-public-readiness-prep"
        )
        if not feat.is_dir():
            self.skipTest("feature folder not present")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            lint_plan.lint(feat)   # must not raise


if __name__ == "__main__":
    unittest.main()
