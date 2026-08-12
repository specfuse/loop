#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Regression test for issue #795 — gate_eval.py backtest can't target an
external repo because it resolves repo_root from its own __file__ path
instead of accepting an explicit --repo argument.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_scripts = str(REPO_ROOT / ".specfuse/scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

import gate_eval  # noqa: E402

PLAN_MD = """---
feature_id: FEAT-2026-9999
status: active
---

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units: []
```
"""


class TestBacktestRepoFlag(unittest.TestCase):
    def test_backtest_targets_external_repo_via_repo_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            target_repo = Path(tmp)
            feature_dir = target_repo / ".specfuse" / "features" / "FEAT-2026-9999-widget"
            feature_dir.mkdir(parents=True)
            (feature_dir / "PLAN.md").write_text(PLAN_MD)

            argv = ["gate_eval.py", "backtest", "FEAT-2026-9999", "--repo", str(target_repo)]
            old_argv = sys.argv
            sys.argv = argv
            out = io.StringIO()
            try:
                with redirect_stdout(out):
                    gate_eval.main()
            finally:
                sys.argv = old_argv

            self.assertIn("FEAT-2026-9999", out.getvalue())
            self.assertNotIn("no feature matches", out.getvalue())


if __name__ == "__main__":
    unittest.main()
