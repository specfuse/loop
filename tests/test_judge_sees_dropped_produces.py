#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""A dropped `produces:` path reaches the judge (FEAT-2026-0114/T03).

`build_judge_bundle` now includes every gate unit's `produces_dropped:`
frontmatter as a bundle section, so a judge can grade a criterion against the
drop and its reason rather than against a silent edit.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specfuse.loop.judge import (
    DROPPED_PRODUCES_SECTION,
    build_judge_bundle,
    collect_produces_dropped,
    render_judge_prompt,
)

PLAN_MD = """\
---
id: FEAT-2026-9999
status: active
---

# A fixture feature

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9999/T01
        file: WU-01-fixture.md
      - id: FEAT-2026-9999/T02
        file: WU-02-fixture.md
```
"""

GATE_MD = """\
---
gate: 1
status: open
---

# Gate 1 — a fixture gate

## Definition of done

- A fixture criterion.
"""

WU_WITH_DROP = """\
---
id: FEAT-2026-9999/T01
type: implementation
produces:
  - src/kept.py
produces_dropped:
  - path: src/unneeded.py
    reason: "verified attempt did not need this path"
---

# A fixture unit
"""

WU_WITHOUT_DROP = """\
---
id: FEAT-2026-9999/T02
type: implementation
produces:
  - src/other.py
---

# Another fixture unit
"""


def _feature_dir(tmp: str, *, with_drop: bool) -> Path:
    d = Path(tmp)
    (d / "PLAN.md").write_text(PLAN_MD)
    (d / "GATE-01.md").write_text(GATE_MD)
    (d / "WU-01-fixture.md").write_text(WU_WITH_DROP if with_drop else WU_WITHOUT_DROP)
    (d / "WU-02-fixture.md").write_text(WU_WITHOUT_DROP)
    return d


class TestCollectProducesDropped(unittest.TestCase):

    def test_collects_unit_id_path_and_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp, with_drop=True)
            dropped = collect_produces_dropped(d, 1)
        self.assertEqual(
            dropped,
            [("FEAT-2026-9999/T01", "src/unneeded.py",
              "verified attempt did not need this path")],
        )

    def test_no_drops_yields_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp, with_drop=False)
            dropped = collect_produces_dropped(d, 1)
        self.assertEqual(dropped, [])

    def test_missing_plan_yields_empty_list_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            dropped = collect_produces_dropped(Path(tmp), 1)
        self.assertEqual(dropped, [])


class TestBundleAndPromptCarryDroppedSection(unittest.TestCase):

    def test_bundle_and_prompt_show_unit_path_and_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp, with_drop=True)
            bundle = build_judge_bundle(d, 1, diff_text="", measurements="")
            prompt = render_judge_prompt(bundle)

        self.assertIn(f"## {DROPPED_PRODUCES_SECTION}", prompt)
        self.assertIn("FEAT-2026-9999/T01", bundle.produces_dropped)
        self.assertIn("FEAT-2026-9999/T01", prompt)
        self.assertIn("src/unneeded.py", prompt)
        self.assertIn("verified attempt did not need this path", prompt)

    def test_no_drops_renders_the_literal_none_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _feature_dir(tmp, with_drop=False)
            bundle = build_judge_bundle(d, 1, diff_text="", measurements="")
            prompt = render_judge_prompt(bundle)

        self.assertIn(f"## {DROPPED_PRODUCES_SECTION}", prompt)
        heading_index = prompt.index(f"## {DROPPED_PRODUCES_SECTION}")
        following = prompt[heading_index:heading_index + 200]
        self.assertIn("(none)", following)
        self.assertNotIn("src/unneeded.py", prompt)


if __name__ == "__main__":
    unittest.main()
