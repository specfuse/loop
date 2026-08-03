---
id: FEAT-2026-0041/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - plugins/specfuse/skills/diagnose-issue/SKILL.md
  - .specfuse/skills/diagnose-issue/SKILL.md
  - tests/test_diagnose_issue_skill.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T20:12:23.114993+00:00
duration_seconds: 862.191
cost_usd: 2.293991
input_tokens: 114
output_tokens: 17265
---

# `/diagnose-issue NN` — the interactive entry point

**Objective.** Ship the `/diagnose-issue NN` skill: read a harvester finding issue,
read the component source it implicates, produce the analysis, render it through T01's
contract, and post it as a comment.

**Context.** Correlation ID `FEAT-2026-0041/T02`. Read `PLAN.md` first — it records
the scope boundary (no auto-trigger, no dial) and the three-surface skill obligation
below. T01's module owns the comment format; this skill produces the *analysis* and
calls the module to format it. Do not re-specify the format in prose.

**The trap, stated so it is not rediscovered.** A skill has **three surfaces**:

```
plugins/specfuse/skills/diagnose-issue/SKILL.md   canonical source
.specfuse/skills/diagnose-issue/SKILL.md          synced copy
.claude/skills/diagnose-issue                     discovery symlink -> ../../.specfuse/skills/diagnose-issue
```

Writing only the canonical copy leaves the skill invisible to Claude Code. This is the
exact failure FEAT-2026-0072 fixed after four skills sat undiscoverable for **seven
weeks**, including one shipped the same day it went missing. `scripts/sync-scaffold.sh`
creates the symlink; whether you run it or write the surfaces directly is your call,
but all three must exist and `tests/test_skill_discovery_links.py` must pass.

**What the skill does and does not decide.** It produces root cause, evidence trail,
candidate fix, `confidence`, and `fix_scope`. It does **not** decide whether to fix
anything — FEAT-2026-0042 owns that, gating on the fields this skill emits.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `operator-escalation.md`.

## The skill's shape

Follow the existing skills' structure (`attention`, `fix-bug` are the closest
analogues): a `## Hard rules` section, a `## When to invoke` section, a `## Method`
with numbered steps, and the binding **escalation framing** section every skill in this
repo carries.

Hard rules the skill must state for itself, at minimum: it posts exactly **one**
diagnosis comment per invocation; it never closes or edits the finding issue; it never
invents a root cause when the evidence does not support one — an honest
`confidence: low` with the evidence gap named beats a confident guess; and it renders
through `diagnosis.py` rather than hand-writing the comment body.

**Acceptance criteria.**

1. `tests/test_diagnose_issue_skill.py::TestDiagnoseIssueSkill::test_skill_present_on_all_three_surfaces`
   exists and **fails on HEAD before this WU runs** (no skill directory exists, which
   counts as red).
2. That test asserts the canonical file exists, the synced copy exists, the
   `.claude/skills/` entry exists and resolves inside `.specfuse/skills/`, and the
   canonical and synced copies are byte-identical. It passes after this WU's edits.
3. `tests/test_skill_discovery_links.py` passes — the existing guard from
   FEAT-2026-0072, which is the one this WU is most likely to trip. Run it by name and
   quote the result.
4. A test asserts the SKILL.md body instructs rendering through `diagnosis.py` and does
   **not** restate the comment format — grep the body for the module name, and assert
   it carries no literal marker template of its own. One contract, one home.
5. A test asserts the SKILL.md carries the escalation-framing section every skill in
   this repo binds to (`operator-escalation.md`), matching the shape used by the
   existing skills.
6. The skill's own hard rules include the one-comment-per-invocation rule, the
   never-close-the-issue rule, and the honest-low-confidence rule, each as a stated
   rule rather than implied by the method.
7. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/diagnosis.py` — T01 owns the contract; if the skill
needs a field the model does not expose, that is an escalation, not a quiet edit to
T01's module. `specfuse/monitor/issues.py`. The headless entry point — T03 owns it.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Criterion 3 is load-bearing: the
skill-discovery guard fails in a way that reads as an unrelated symlink problem rather
than "you wrote one surface of three," so run it by name and quote it.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
three skill surfaces cannot be made consistent without editing `sync-scaffold.sh`
itself (that is a different feature's territory); T01's `Diagnosis` model lacks a field
the skill genuinely needs to express a diagnosis; or the skill cannot state its method
without specifying the comment format, which would mean the T01 boundary is drawn
wrong. Do **not** invoke `gh` from this work unit — it is sandboxed and `gh` will fail
with an invalid-token or TLS error that is a sandbox artifact, not a defect. The skill
*describes* posting via `gh`; T04 is the unit that *proves* it works.
