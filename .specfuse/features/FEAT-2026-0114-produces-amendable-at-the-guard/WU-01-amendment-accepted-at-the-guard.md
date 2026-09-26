---
id: FEAT-2026-0114/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 6.00
produces_driver_helper:
  - produces_amendments
  - apply_produces_amendment
  - resolve_produces_amendable
produces:
  - specfuse/loop/loop.py
  - tests/test_produces_amendment_e2e.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T15:00:01.649146+00:00
duration_seconds: 199.736
cost_usd: 1.078728
input_tokens: 60
output_tokens: 16507
---

# A verified attempt drops a `produces:` path it did not need

**Objective.** Let a RESULT block drop a declared `produces:` path with a reason,
so an attempt that passed verification but solved the unit elsewhere passes
instead of refusing with `produces_not_in_diff`.

**Context.** FEAT-2026-0114/T01, this gate's **walking skeleton**: wire the thinnest
end-to-end path and turn `GATE-01.md`'s `feature_oracle` green; T02–T04 refine it.
The guard site is the `produces_not_in_diff` branch in `run()`'s attempt loop
(`specfuse/loop/loop.py`, the block that calls `resolve_produces_refusal(wu,
touched, wu.result_block)`). Add `produces_amendments(result_block)`, the sibling
of `produces_justifications`: it reads `result_block["produces_amended"]`, a list
of `{path, reason}` dicts, drops malformed entries silently and normalises paths
the same way. Extend `resolve_produces_refusal` (or wrap it) so an unmatched entry
that appears in the amendments with a non-blank reason is moved from `remaining`
to a third return value `dropped`. When `remaining` is empty and `dropped` is
not, call `apply_produces_amendment(wu, dropped)`: rewrite the unit's `produces:`
through `write_frontmatter_block` without the dropped paths, write a
`produces_dropped:` block listing each `path` and `reason`, sync `wu.produces`
in memory, print one line per drop, and let the pass proceed. Refuse with
today's summary when the amended list would be empty for an `implementation`
unit, or when `resolve_produces_amendable(cfg)` (reads `verification.yml`
`defaults.produces_amendable`, default `True`, the `defaults` block
`resolve_max_attempts` reads) is false. The passed `attempt_outcome` carries
`extras={"produces_amended": [...]}` beside the existing `produces_justified`.
Red test first: `tests/test_produces_amendment_e2e.py` is the gate's oracle,
shaped like `tests/test_produces_justification.py`'s
`TestProducesJustificationIntegration` harness (`integration_workspace`, stubbed
`dispatch` and `verify`).

**Acceptance criteria.**

1. `tests/test_produces_amendment_e2e.py` fails on HEAD before this unit's edits
   (the module is absent); after, `python3 -m unittest tests.test_produces_amendment_e2e -v -b`
   exits 0.
2. That module asserts, end to end through `loop.run()`: a unit declaring
   `produces: [src/a.py, src/b.py]` whose attempt 1 writes only `src/a.py` and
   returns a RESULT dropping `src/b.py` under `produces_amended:` with a reason
   ends `done` on attempt 1; `produces:` on disk is `[src/a.py]`;
   `produces_dropped:` on disk names `src/b.py` with that reason; the passed
   `attempt_outcome` payload has `produces_amended` naming `src/b.py`.
3. Two more cases in the same module: an amendment that would drop every
   declared path of an implementation unit is refused with the existing
   `produces_not_in_diff` outcome; with `defaults: produces_amendable: false`
   in the fixture's `verification.yml` the same RESULT as case 2 is refused.
4. `python3 -m unittest tests.test_produces_justification tests.test_guard_repair_e2e tests.test_deliverable_presence_gate tests.test_attempt_outcome_contract -v -b`
   exits 0 with no edit to those modules; `produces_amended` is an `extras`
   field, not a new outcome string.

**Do not touch.** `produces_justifications` and the meaning of
`produces_unchanged:`; the four other guard sites and `refusal_history` (T02);
`judge.py` (T03); `.specfuse/rules/` and `docs/` (T04); `.specfuse/verification.yml`;
plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`, then the
gate's `feature_oracle`. The broad tier is the driver's, once per gate — never
run in-session.

**Escalation triggers.** Stop with `status: blocked` if `write_frontmatter_block`
cannot rewrite a list-valued `produces:` without disturbing neighbouring keys
(name the key it disturbed); or if criterion 4 names a test that asserts an
unjustified unmatched path *must* refuse in a way the amendment path would
violate (that is an arming finding, not a test to rewrite).
