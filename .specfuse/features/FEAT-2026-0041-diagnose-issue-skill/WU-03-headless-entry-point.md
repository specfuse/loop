---
id: FEAT-2026-0041/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/monitor/diagnose_cli.py
  - tests/test_diagnose_headless.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T20:38:54.003375+00:00
duration_seconds: 645.125
cost_usd: 1.236018
input_tokens: 70
output_tokens: 12163
---

# The headless entry point — identical output, second path

**Objective.** Ship the headless diagnosis path so a finding can be diagnosed without
an interactive session, producing a comment body **byte-identical** to the one the
interactive skill produces for the same input.

**Context.** Correlation ID `FEAT-2026-0041/T03`. Read `PLAN.md` first. The roadmap
row's phrase is "identical comment format from both entry points" — the identity is the
deliverable here, not the invocation. T01 owns the format; this WU makes a second
caller of it and proves the two agree.

**Why identity is the whole point.** Two entry points that drift produce two comment
dialects, and FEAT-2026-0042 then parses whichever it happens to meet. Because T01
owns rendering, identity is achievable by construction — both paths call one renderer.
The test exists to hold that property as the module grows, not to discover it now.

**Scope, narrowly.** This ships the headless *invocation* — the entry point that takes
a finding and emits a diagnosis comment body. It does **not** ship the auto-trigger,
the `diagnose: auto` dial, harvester wiring, or per-fingerprint dedupe; those are out
of this feature by the operator decision recorded in `PLAN.md`, and a follow-on roadmap
row is filed at close. An entry point that can be *called* headlessly is what unblocks
that future row; calling it on a schedule is that row's job.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

**Acceptance criteria.**

1. `tests/test_diagnose_headless.py::TestDiagnoseHeadless::test_both_entry_points_render_identical_body`
   exists and **fails on HEAD before this WU runs** (no headless entry point exists,
   which counts as red).
2. That test constructs one `Diagnosis` and asserts the body the headless path emits is
   **byte-identical** to the body the interactive path emits — not "equivalent", not
   "both parse to the same fields". Compare the strings. It passes after this WU's edits.
3. A test asserts the headless path renders through `diagnosis.py` rather than
   assembling a body itself: grep the module for any literal marker or heading template
   and assert there is none.
4. A test asserts the headless path fails loudly on a finding it cannot parse — a named
   error, non-zero exit — rather than emitting a diagnosis with empty fields. A
   confidently-formatted empty diagnosis is worse than a refusal.
5. A test asserts an unparseable or missing `fix_scope` from the analysis step is
   rejected before render, not defaulted. Defaulting a field FEAT-2026-0042 gates on
   would silently route real work.
6. The entry point makes no `gh` call and no network call of its own — it produces a
   body; posting is the caller's job. Assert with
   `grep -n "subprocess\|gh \|requests\|urllib" specfuse/monitor/diagnose_cli.py` and
   quote the output.
7. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/diagnosis.py` — T01 owns the contract.
`plugins/specfuse/skills/` and `.specfuse/skills/` — T02 owns the skill; if the two
paths cannot be made to agree without editing the skill, that is an escalation.
Harvester scheduling surfaces (`schedule.py`, `cli.py` run paths) — out of scope.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Criterion 2 is the load-bearing one and
must be a literal string comparison — a test that asserts "both parse to equal fields"
would pass while the rendered bodies differ in whitespace or ordering, which is exactly
the drift this WU exists to prevent.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the two
entry points cannot produce byte-identical bodies without changing T01's renderer
(which this WU may not touch); the headless path needs a `Diagnosis` field T01 does not
expose; or making the paths agree would require the skill to stop rendering through the
module. Do **not** invoke `gh` from this work unit — sandboxed, and its failure is a
sandbox artifact rather than a defect. T04 is the unit that proves the `gh` round-trip.
