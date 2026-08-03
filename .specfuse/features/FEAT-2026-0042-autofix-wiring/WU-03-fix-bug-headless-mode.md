---
id: FEAT-2026-0042/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - plugins/specfuse/skills/fix-bug/SKILL.md
  - .specfuse/skills/fix-bug/SKILL.md
  - tests/test_fix_bug_headless.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T23:04:51.558842+00:00
duration_seconds: 580.502
cost_usd: 1.647922
input_tokens: 72
output_tokens: 17708
---

# A headless mode for `fix-bug`: every halt becomes a recorded outcome

**Objective.** Give the existing `fix-bug` skill a headless mode in which every point
that currently halts for a human resolves to an explicit, recorded outcome instead —
so an automated caller gets a verdict rather than a hang.

**Context.** Correlation ID `FEAT-2026-0042/T03`. Read `PLAN.md` first. The roadmap
row for this feature assumed headless invocation already existed; it does not. The
skill is titled "Fix a reported bug (interactive)", carries the
`operator-escalation.md` framing that halts for a human decision, and has refusal
paths that propose `/draft-feature`.

**What this WU changes, and what it must not.** It adds a **mode**. It does not alter
the bug-fix workflow, the refusal criteria, the test-first discipline, or the
`1 bug = 1 branch = 1 PR` hard contract. Interactive behaviour must be byte-for-byte
unchanged — a human running `/fix-bug NN` sees exactly what they see today.

**The refusal paths are a feature, not an obstacle.** `fix-bug` already refuses work
that is large, complex, or risky and proposes promoting it to a feature. Under
headless invocation that refusal becomes a **second guardrail** behind T01's
predicate: T01 decides the finding *looks* small; `fix-bug` decides, having read the
actual code, whether it *is*. Preserve every refusal — do not weaken one to make a
headless run more likely to produce a PR.

**The trap, stated so it is not rediscovered.** A skill has **three surfaces**:

```
plugins/specfuse/skills/fix-bug/SKILL.md   canonical source
.specfuse/skills/fix-bug/SKILL.md          synced copy
.claude/skills/fix-bug                      discovery symlink (already exists)
```

Editing only the canonical copy leaves the two out of sync and fails the scaffold
sync guard. FEAT-2026-0072 fixed this class after four skills sat undiscoverable for
seven weeks. The symlink already exists for `fix-bug`; the two file copies must match.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `operator-escalation.md`.

## The contract

In headless mode every halt maps to a named terminal outcome, and the set of outcomes
is closed and stated in the skill. At minimum it must distinguish:

- **refused** — the skill's existing criteria say this is not a bug-sized fix, with
  the reason;
- **could not proceed** — a precondition was missing (issue unreadable, no reproducing
  test possible, working tree unclean);
- **completed** — the fix ran and produced a branch and a pull request.

A headless run **never** asks a question, never waits, and never silently proceeds
past a decision an interactive run would have escalated. Where the interactive path
would present options to an operator, the headless path records the option it would
have presented and exits with the corresponding outcome.

**This WU does not invoke the mode.** It defines it. Gate 2 wires the caller and runs
it live; gate 1 fires nothing.

**Acceptance criteria.**

1. `tests/test_fix_bug_headless.py::TestFixBugHeadless::test_headless_outcomes_are_closed_and_named`
   exists and **fails on HEAD before this WU runs** (no headless mode is documented,
   which counts as red).
2. That test asserts the SKILL.md documents a closed set of headless outcomes, each
   named, and that the set includes refused, could-not-proceed, and completed. It
   passes after this WU's edits.
3. A test asserts the skill states that a headless run **never prompts, never waits,
   and never proceeds past a decision** — as an explicit rule, not implied by the
   method.
4. A test asserts every existing refusal path is reachable in headless mode and maps
   to the refused outcome — the refusal criteria are unchanged and none is weakened.
   Enumerate them from the current skill body rather than assuming a count.
5. A test asserts the interactive path is **unchanged**: diff the interactive
   sections against HEAD and assert the only additions are headless-mode content.
   Quote the diff summary.
6. `plugins/specfuse/skills/fix-bug/SKILL.md` and `.specfuse/skills/fix-bug/SKILL.md`
   are byte-identical. Assert with `diff` and quote the (empty) output.
7. `tests/test_skill_discovery_links.py` and the scaffold sync tests pass. Run them
   by name and quote the results.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/autofix.py` and `specfuse/monitor/autofix_state.py`
— T01 and T02 own them. The bug-fix workflow itself: the test-first discipline, the
`1 bug = 1 branch = 1 PR` contract, and every refusal criterion stay exactly as they
are. Any other skill under `plugins/specfuse/skills/`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criteria 5 and 6 are
load-bearing: an unintended change to the interactive path would reach every human
running `/fix-bug`, and a mirror drift fails the sync guard with an error that reads
as an unrelated scaffold problem.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: a
halt in the interactive flow has no sensible headless mapping without changing what
the skill decides (say which halt — that is a real design gap, not a wording
problem); the closed outcome set cannot cover a refusal path without weakening it; or
adding the mode would require editing the bug-fix workflow this WU may not touch. Do
**not** invoke the headless mode against a real issue, create a branch, or open a
pull request from this work unit — gate 1 fires nothing, and the live run is gate 2's.
