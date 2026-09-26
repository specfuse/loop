---
id: FEAT-2026-0114/T02H
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - specfuse/loop/loop.py
  - tests/test_produces_repair_note.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.25.0
started_at: 2026-09-26T15:30:01.364172+00:00
duration_seconds: 78.991
cost_usd: 0.296324
input_tokens: 30
output_tokens: 3850
---

# The refusal excerpt names both escape hatches

**Objective.** Put the two RESULT keys, `produces_unchanged:` and
`produces_amended:`, in the first sentence of the `produces_not_in_diff` note,
so the 500-character `failure_excerpt` (head plus tail) still names them after
the verbatim YAML example T02 appended.

**Context.** FEAT-2026-0114/T02H, hygiene for T02 (gate 1 broad run,
2026-09-26): `tests/test_produces_justification.py::test_justifying_the_wrong_path_or_nothing_useful_is_still_refused`
asserts the refusal's `failure_excerpt` plus `summary` contains
`produces_unchanged`. After T02 the note reads summary, then a long sentence
that mentions the key only around its 300th character, then the example;
`extract_failure_excerpt` keeps the first ~250 and last ~250 characters, so the
key fell in the elided middle. The fix is in the `_prod_note` assembly at the
`produces_not_in_diff` site in `specfuse/loop/loop.py`: right after
`prod_summary`, add one short line naming both keys and what each is for
(`produces_unchanged:` — the deliverable already holds at HEAD;
`produces_amended:` — the plan named a path this solution did not need), then
the existing sentence, then `PRODUCES_REPAIR_EXAMPLE`. Do not change
`extract_failure_excerpt` or its cap. Red test first: extend
`tests/test_produces_repair_note.py` with one assertion that
`extract_failure_excerpt(note)` for a real refusal contains both key names.

**Acceptance criteria.**

1. `python3 -m unittest tests.test_produces_justification -v -b` exits 0 with
   no edit to that module (it fails on HEAD before this unit's edit).
2. `tests/test_produces_repair_note.py` gains one test asserting that the
   `failure_excerpt` recorded on a `produces_not_in_diff` attempt contains
   both `produces_unchanged:` and `produces_amended:`; it fails on HEAD and
   passes after.
3. `python3 -m unittest tests.test_produces_amendment_e2e tests.test_guard_repair_e2e tests.test_produces_repair_note -v -b`
   exits 0.

**Do not touch.** `extract_failure_excerpt` and its cap; `PRODUCES_REPAIR_EXAMPLE`'s
content; `produces_amendments` / `apply_produces_amendment` (T01);
`judge.py` (T03); `.specfuse/rules/` and `docs/` (T04); plus
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gates in `.specfuse/verification.yml`. The broad
tier is the driver's, once per gate — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if a first line naming
both keys still does not reach the excerpt head (say the head length you
measured); or if criterion 1 needs any edit to `tests/test_produces_justification.py`.
