---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_gate_timings -v -b"
cost_budget_usd: 22.00
baseline:
  sha: 21191ae86fa93b0ae51ef939b522bd15b130ba6c
  probed_at: 2026-11-25T15:20:21.670930+00:00
  tree: 07bbf72d1e7af3c1a03af605f40e5563dc3a18db:0ec7c6da6e74f0b56753f09657b654a6d289b91b:12064a6191eeb830a9826d911a8543fbaba3da75:1fb7d45b824d49ab8dee91cfcfb29ac17ff37a8f:27968248a450a842ccd187b7dce0fb0ded934866:287efde8f90320baffac08f5f3287b9456a65cb9:2e29b2f7e073a0cbe290f01d3b397e1cdd10c81c:302816f6805b548990c2e47c2264d6c68679b21d:42796ea0e0a6c03811b0e4bc9dbd3b5ee62dd2e4:4acc6dfc5e8cece358c167d876515eba4a39a500:7d6f6c977308ee2b7fe76ffe4f86fda3c776ef38:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:91b2fa050120acfd6e3c5950af079ababcddb2a5:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d74b7d113b844e84f0009098f576fd28477f072d:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366
  entry_sha: 21191ae86fa93b0ae51ef939b522bd15b130ba6c
  source: attributed:FEAT-LOOP-2026-0250/T01
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "(failures=2,"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
    - gate: roadmap-link-gate
      failure_class: other
      failure_signature: "ERROR: roadmap.md:131: ref '#feat-loop-2026-0250' in roadmap…und in roadmap.md or roadmap-archive.md"
broad_run:
  tree: 07bbf72d1e7af3c1a03af605f40e5563dc3a18db:0ec7c6da6e74f0b56753f09657b654a6d289b91b:12064a6191eeb830a9826d911a8543fbaba3da75:27968248a450a842ccd187b7dce0fb0ded934866:287efde8f90320baffac08f5f3287b9456a65cb9:2e29b2f7e073a0cbe290f01d3b397e1cdd10c81c:302816f6805b548990c2e47c2264d6c68679b21d:38e1639a0c46c0cd3e0a1bcee16359e18cf4c70f:42796ea0e0a6c03811b0e4bc9dbd3b5ee62dd2e4:4acc6dfc5e8cece358c167d876515eba4a39a500:83478ee1d28da445abebbea95e402a2501fa1343:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:ae39d552df928f10c8c11cb2a541575d68665933:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d74b7d113b844e84f0009098f576fd28477f072d:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-11-25T15:49:51.825704+00:00
  ok: true
  failing: []
---

# Gate 1 — per-gate timings are recorded, and `specfuse stats` reads them

## Definition of done

**Stated as an outcome.** In temporary feature folders, with real gate subprocesses (commands
that sleep a known time and exit 0 or 1) and a stubbed agent session:

1. **Attempt phase.** Each attempt emits one `gate_result` event per gate in its set, the
   `feature_oracle` included, carrying `attempt`, `gate`, `ok`, `duration_seconds` and
   `phase: attempt`. A gate's `duration_seconds` is at least its command's sleep. A gate skipped
   because a dependency failed records `ok: false`, `skipped: true`, `duration_seconds: 0`.
2. **Split.** `attempt_outcome` carries `agent_seconds` and `verify_seconds`, and
   `agent_seconds + verify_seconds <= duration_seconds`. An attempt that stopped before
   verification (the agent reported blocked) records `verify_seconds: 0`.
3. **Baseline and broad phases.** The baseline probe and the broad run each emit one
   `gate_result` per gate with `phase: baseline` or `phase: broad`. A broad run skipped because
   the tree is unchanged emits none.
4. **Stats.** `specfuse stats` (text and `--json`) reports the agent/verify split per feature and
   the slowest gates (runs, total, median, max seconds). On a corpus with no `gate_result` events
   and no split fields it says "not recorded", never zeros.
5. **Nothing existing changes.** `duration_seconds` keeps its meaning; every existing test that
   stubs `verify_fn` passes unchanged; `gate_result` is in `driver-event.schema.json` and every
   emitted event type validates against it.

The `feature_oracle` proves 1–5. It is red on the current tree; `FEAT-LOOP-2026-0250/T01` is the
walking skeleton that creates `tests/test_gate_timings.py` and turns clause 1 and clause 5's
schema half green, with every other class `unittest.skip` naming its owner (T02–T04). A skip
surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **One runner.** Timing lives in `_run_gate_set()`; the three phases differ only in the `phase`
  tag and correlation ID they emit with.
- **Positive controls.** Clause 1 pairs a passing gate with a failing one and a skipped
  dependent; clause 3 pairs a fresh broad run with a tree-unchanged skip; clause 4 pairs a new
  corpus with an old one.
- **Real subprocesses, stubbed agent.** Gate durations come from real `sleep` commands, so a
  duration recorded as a constant fails the lower-bound check.
- **Expected self-halt.** `loop.py` and the event schema are judge surfaces; acknowledge the
  stop with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
