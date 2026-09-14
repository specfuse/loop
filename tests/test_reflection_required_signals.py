#
# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`reflection_required` must see a gate's own eventful history (#3318).

FEAT-2026-0111's gate 1 had a feature-level halt at gate entry, an
operator-inserted hygiene unit, a discarded attempt cycle, a `not_met` close
and a re-scoped definition of done — and `reflection_required` returned False
with `reasons=[]`, because the shared auto-close predicate reads only per-WU
blocked/replan events and per-WU cost overruns.

Two facts sit in that feature's own `events.jsonl` and were never consulted:

* a `human_escalation` whose `correlation_id` is the FEATURE, not a work unit
  (`reason: preexisting_gate_failure`, `payload.gate: 1`), and
* a `judged` event for this gate recording `judge_verdict: not_met`.

Either one means the gate did not go as planned. Neither changes
`evaluate_off_plan_signal`, which `evaluate_auto_close` also uses — auto-close
eligibility is a different question and is deliberately untouched.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from specfuse.loop import loop


PLAN = """\
---
feature_id: FEAT-2026-9501
title: probe
slug: probe
status: active
---

# Plan

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-9501/T01
        file: WU-01-a.md
        depends_on: []
```
"""

WU = """\
---
id: FEAT-2026-9501/T01
type: implementation
status: done
attempts: 1
cost_usd: 1.00
planned_cost_usd: 1.00
---

# A

**Objective.** x

**Acceptance criteria.**

- x

**Do not touch.** x

**Verification.** x

**Escalation triggers.** x
"""

GATE = "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n\n## Definition of done\n\nx\n"


class ReflectionSeesTheGatesOwnHistory(unittest.TestCase):

    def _feature(self, tmp: str, events: list[dict]) -> Path:
        d = Path(tmp)
        (d / "PLAN.md").write_text(PLAN, encoding="utf-8")
        (d / "GATE-01.md").write_text(GATE, encoding="utf-8")
        (d / "WU-01-a.md").write_text(WU, encoding="utf-8")
        (d / "events.jsonl").write_text(
            "".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
        return d

    def test_an_on_plan_gate_with_no_history_still_skips_reflection(self):
        # The control. Without this, "always return True" would pass the rest.
        with TemporaryDirectory() as tmp:
            d = self._feature(tmp, [
                {"event_type": "attempt_outcome",
                 "correlation_id": "FEAT-2026-9501/T01",
                 "payload": {"outcome": "passed", "cost_usd": 1.00}},
            ])
            self.assertFalse(loop.reflection_required(d, 1))

    def test_a_feature_level_escalation_on_this_gate_requires_reflection(self):
        # FEAT-2026-0111's actual halt: correlation_id is the feature, not a WU,
        # so the per-WU blocked_human_events metric never saw it.
        with TemporaryDirectory() as tmp:
            d = self._feature(tmp, [
                {"event_type": "attempt_outcome",
                 "correlation_id": "FEAT-2026-9501/T01",
                 "payload": {"outcome": "passed", "cost_usd": 1.00}},
                {"event_type": "human_escalation",
                 "correlation_id": "FEAT-2026-9501",
                 "payload": {"reason": "preexisting_gate_failure", "gate": 1}},
            ])
            self.assertTrue(loop.reflection_required(d, 1))

    def test_a_prior_not_met_close_on_this_gate_requires_reflection(self):
        with TemporaryDirectory() as tmp:
            d = self._feature(tmp, [
                {"event_type": "attempt_outcome",
                 "correlation_id": "FEAT-2026-9501/T01",
                 "payload": {"outcome": "passed", "cost_usd": 1.00}},
                {"event_type": "judged",
                 "correlation_id": "FEAT-2026-9501/G1-CLOSE",
                 "payload": {"gate": 1, "judge_verdict": "not_met"}},
                {"event_type": "judged",
                 "correlation_id": "FEAT-2026-9501/G1-CLOSE",
                 "payload": {"gate": 1, "judge_verdict": "met"}},
            ])
            # A later `met` does not erase the earlier `not_met`: the gate still
            # went round twice, which is the thing worth reflecting on.
            self.assertTrue(loop.reflection_required(d, 1))

    def test_history_on_a_different_gate_is_not_this_gates_business(self):
        with TemporaryDirectory() as tmp:
            d = self._feature(tmp, [
                {"event_type": "attempt_outcome",
                 "correlation_id": "FEAT-2026-9501/T01",
                 "payload": {"outcome": "passed", "cost_usd": 1.00}},
                {"event_type": "human_escalation",
                 "correlation_id": "FEAT-2026-9501",
                 "payload": {"reason": "preexisting_gate_failure", "gate": 2}},
                {"event_type": "judged",
                 "correlation_id": "FEAT-2026-9501/G2-CLOSE",
                 "payload": {"gate": 2, "judge_verdict": "not_met"}},
            ])
            self.assertFalse(loop.reflection_required(d, 1))


if __name__ == "__main__":
    unittest.main()
