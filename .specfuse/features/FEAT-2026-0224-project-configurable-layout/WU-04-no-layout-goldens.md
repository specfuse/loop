---
id: FEAT-2026-0224/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - tests/test_layout_no_layout_goldens.py
  - tests/test_layout_end_to_end.py
model: sonnet
effort: medium
gate_set: code
re_arm_count: 1
re_arm_history:
  -
    timestamp: 2026-10-28T01:27:50+00:00
    prior_status: blocked_human
    prior_attempts: 2
    prior_cost_usd: 0.584336
    prior_duration_seconds: 117.939
    reason: "Operator chose option 3 (gate-status 2026-10-27): produces glob under tests/ became unittest module tests.fixtures.layout_goldens.**; WU rewritten .py-only, selector bug filed separately"
re_arm_override: true
escalation_reason: spinning_signature_repeat
escalation_failure_class: tests
escalation_failure_signature: (errors=1)
duration_seconds: 61.947
cost_usd: 0.295318
input_tokens: 24
output_tokens: 6497
cumulative_cost_usd: 0.584336
cumulative_duration_seconds: 117.939
cumulative_input_tokens: 40
cumulative_output_tokens: 11059
cumulative_attempts: 2
folded_through_re_arm: 1
driver_version: 0.29.1
started_at: 2026-10-28T01:28:24.586995+00:00
---

# T04 — no-layout goldens, recorded before any consumer changes

**Objective.** Oracle clause 1 (except the template, which T07 adds) is proven by
committed goldens on deterministic surfaces only, recorded against HEAD's
`lint_roadmap` before T05 edits it.

**Context.** Everything this unit produces is a `.py` file. (Re-armed after two
attempts failed on a drafting defect: a `tests/fixtures/layout_goldens/**` entry in
`produces:` was turned by the narrow tier into the unittest module name
`tests.fixtures.layout_goldens.**`. Do not add non-`.py` paths under `tests/` to
this unit.)

`tests/test_layout_no_layout_goldens.py` carries the fixtures **and** the goldens
as module-level constants:

- `FIXTURES`: a mapping of fixture name to `{repo-relative path: file text}` for
  three fixture repos, none with a `layout.yml`. `clean` has no blocked rows.
  `blocked_resolves` has a blocked row whose `docs/adr/…` link resolves.
  `blocked_dangling` has a blocked row whose link does not resolve, plus an orphan
  section, so both ERROR and WARN findings appear. A helper writes one fixture
  into a `tempfile.TemporaryDirectory()` per test. **No fixture link carries a
  `#fragment`** (PLAN decision 5).
- `GOLDEN_GET`, `GOLDEN_LINK` and `GOLDEN_LINT`: the expected outputs as string
  literals.

With no `layout.yml`, the test asserts:
- `python3 -m specfuse.loop.layout get <key>` stdout for every key equals
  `GOLDEN_GET`.
- `python3 -m specfuse.loop.layout link` for the `block-feature` example equals
  `GOLDEN_LINK`.
- `lint_roadmap(<fixture>)` findings, rendered one per line as
  `severity file:line message` with the file name only (never the temp dir path),
  equal `GOLDEN_LINT[<fixture>]`.

Goldens are generated once in this unit by running the code on HEAD and pasting the
output into the constants. The test never regenerates them: no `--update` flag, and
no code path writes the constants. Un-skip `NoLayoutGoldens` in the oracle module;
it runs the same assertions on `blocked_dangling` by importing `FIXTURES` and
`GOLDEN_LINT` from this module.

**Acceptance criteria.**

1. `tests/test_layout_no_layout_goldens.py` passes on this unit's tree, and
   `tests/test_layout_end_to_end.py::NoLayoutGoldens` passes. Its `lint_roadmap`
   goldens were generated before any edit to `lint_roadmap.py` in this feature:
   `git log --oneline -- specfuse/loop/lint_roadmap.py` shows no FEAT-2026-0224
   commit at this unit's HEAD.
2. Positive control: `GOLDEN_LINT["blocked_dangling"]` contains at least one ERROR
   line and one WARN line, because a golden of `[]` everywhere would prove nothing.
   A test asserts that no `FIXTURES` file text matches `\]\([^)]*\.md#`.

**Red-test exemption (§12).** Goldens pin HEAD's behaviour, so they pass on HEAD by
design; the red-then-green proof for this unit is T05's criterion 2 (goldens pass
unchanged after the consumer edit).

**Do not touch.** `specfuse/` (this unit adds tests only). No file outside the
`produces:` list, and no non-`.py` path under `tests/`.

**Verification.** The narrow tier for `implementation`.

**Escalation triggers.** If `lint_roadmap` output is non-deterministic across runs
(ordering, absolute paths in messages), stop: normalise in the test only by
escalating — the finding text is user-visible.
