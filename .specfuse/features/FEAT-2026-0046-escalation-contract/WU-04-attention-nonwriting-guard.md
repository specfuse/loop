---
id: FEAT-2026-0046/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.00
produces:
  - tests/test_attention_nonwriting_guard.py
model: sonnet
effort: medium
gate_set: code
driver_version: 0.5.0
started_at: 2026-07-27T21:37:46.168581+00:00
duration_seconds: 211.475
cost_usd: 0.641066
input_tokens: 32
output_tokens: 8423
---

# Prove /attention cannot write state — grep guard plus a positive control

**Objective.** Ship the test that holds `/attention` to its read-only claim: a grep
over the skill text for write-verb instructions, expecting zero hits, plus a positive
control proving the pattern is capable of firing.

**Context.** Correlation ID `FEAT-2026-0046/T04`. Depends on `T03`, which authors the
skill this guard reads.

**Why a guard and not a sentence.**
`[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]` is the governing lesson: *"A skill may not own
a state transition the driver owns… the skill's non-writing is enforced by a
grep-shaped test over the skill text with a positive control."* It also names the
failure mode this WU must avoid — *"never as prose in the WU body, which verifies
nothing."* `/attention` presenting the queue is safe; `/attention` editing a WU status
or closing an issue is the divergence that cost issue #49, wearing a friendlier name.

**The positive control is the non-obvious half, and the reason this is its own work
unit.** The same lesson: *"also assert the forbidden pattern fires on a purpose-built
violating instruction, or the guard passes because its regex matches nothing rather
than because the skill is clean."* A guard that returns zero because it can never
match anything is indistinguishable, from the outside, from a guard protecting a clean
skill. The control removes that ambiguity — it is what makes criterion 2's zero mean
something.

Construct the violating instruction as a string literal inside the test. Do not write
a violating skill file to disk: a second `SKILL.md` under `plugins/` or `.specfuse/`
would be picked up by skill discovery and by the vendoring guard.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_attention_nonwriting_guard.py::TestAttentionNonWritingGuard::test_violating_instruction_is_detected`
   exists and **fails on HEAD before this WU runs** (the test file does not yet exist,
   which counts as red).
2. A test asserts the real `plugins/specfuse/skills/attention/SKILL.md` produces zero
   matches for the write-verb pattern.
3. A test asserts the same pattern produces at least one match against a purpose-built
   violating instruction defined as a string literal in the test module — the positive
   control.
4. The violating instruction used by the positive control is **not** written to any
   file on disk; it exists only as an in-memory string.
5. The write-verb pattern covers, at minimum, instructions to edit a work unit's
   `status`, to flip a gate's status, and to close a GitHub issue.
6. A test asserts the vendored copy at `.specfuse/skills/attention/SKILL.md` produces
   zero matches for the same pattern — the guard covers both copies, so vendoring
   cannot smuggle a violation past it.
7. `python3 -m pytest tests/test_attention_nonwriting_guard.py -q` exits zero after
   this WU's edits (the same file named in criterion 1).

**Do not touch.** Either copy of `attention/SKILL.md` — this WU asserts against T03's
output and must not edit the thing it is judging. If the guard fails because the skill
genuinely contains a write instruction, emit `status: blocked` and say so rather than
editing the skill to make your own test pass. Files owned by T01, T02, or T03.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus the scoped red/green run in criteria 1 and 7.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
real skill text produces a match, meaning T03 shipped a write instruction — report it,
do not edit the skill; or a pattern broad enough to satisfy criterion 5 cannot avoid
matching the skill's own legitimate prose about what it does *not* do, in which case
the pattern needs an exclusion the WU author must approve. If
`tests/test_attention_nonwriting_guard.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
