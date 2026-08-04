---
id: FEAT-2026-0059/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - plugins/specfuse/skills/accept-hedged-close/SKILL.md
  - .specfuse/skills/accept-hedged-close/SKILL.md
  - tests/test_accept_hedged_close_headline.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-04T12:37:23.333894+00:00
duration_seconds: 724.948
cost_usd: 2.02318
input_tokens: 88
output_tokens: 19912
---

# Lead with the ceiling, not the quotes

**Objective.** Rewrite `/accept-hedged-close`'s step 2 so it opens with the verdict
ceiling the classification implies, and scaffolds the reason prompt from that
classification — instead of quoting the raw record and demanding a one-line reason
after a wall of text.

**Context.** Correlation ID `FEAT-2026-0059/T02`. Read `PLAN.md` and T01's result
first. T01 owns the `kind:` contract and exposes the ceiling helper; this WU is a
consumer of both.

**The two questions the skill must answer before the operator asks them.**

Measured, not assumed. On FEAT-2026-0042 the operator asked verbatim *"why did it not
complete with met?"* after reading the existing output. On FEAT-2026-0041 the answer
— that accepting was the only available move — was derivable but buried in four
paragraphs.

1. **Why isn't this `met`?** → the ceiling headline, computed from T01's helper:
   - every entry `acceptance-discharged` / `routed-finding` / `inherent` →
     **"no in-repo rework can raise this verdict"**
   - any entry `externally-verifiable-later` → **"rework exists: `<the named
     condition>`"**, so the operator has a real choice between accepting now and
     staying hedged until that condition is met.
2. **What kind of reason is expected?** → a prompt scaffolded from the classification.

**The never-author rule is binding and is the hard edge here.**
`operator-escalation.md` forbids authoring the operator's justification. Scaffolding
means naming *what is being accepted* and leaving the words to the human — not
pre-filling a plausible sentence they can press enter on. A pre-filled reason is
worse than a blank line, because it invites accepting a sentence the operator never
thought. If the implementation finds itself producing a default reason string, that
is the rule being broken, not a convenience.

**Do not infer `kind` from prose.** T01's contract puts it in the record because the
close has the context. If an entry lacks `kind:` — a record written before T01
shipped — say so plainly and fall back to today's behaviour for that entry. Do not
pattern-match wording to guess.

**The trap, stated so it is not rediscovered.** A skill has **three surfaces**: the
canonical `plugins/specfuse/skills/…/SKILL.md`, the vendored `.specfuse/skills/…`
copy, and the `.claude/skills/` discovery symlink (already present for this skill).
The two file copies must be byte-identical or the scaffold sync guard fails with an
error that reads like an unrelated problem.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `operator-escalation.md`.

**Acceptance criteria.**

1. `tests/test_accept_hedged_close_headline.py::TestAcceptHedgedCloseHeadline::test_skill_leads_with_the_verdict_ceiling`
   exists and **fails on HEAD before this WU runs** (the skill has no ceiling
   headline, which counts as red).
2. That test asserts the SKILL.md's step 2 instructs the ceiling headline to be
   printed **before** the entry detail, and names both branches. It passes after this
   WU's edits.
3. A test asserts the skill documents the mapping from each of T01's four kinds to
   its ceiling contribution, and that only `externally-verifiable-later` implies
   rework exists.
4. A test asserts the skill still **requires the operator's own words** and states
   the never-author rule explicitly — and that it contains no pre-filled reason
   string an operator could accept unread.
5. A test asserts the skill states what to do with an entry carrying **no** `kind:`
   (records written before T01): report it as unclassified and fall back, never
   guess from wording.
6. Both SKILL.md copies are byte-identical. Assert with `diff` and quote the (empty)
   output. `tests/test_skill_discovery_links.py` and the scaffold sync tests pass —
   run them by name and quote the results.
7. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `close-discipline.md` and `closing_requirements.py` — T01 owns the
contract; if the skill needs a kind the contract does not define, that is an
escalation. The routed-finding tracking prompt — T03 owns it. Anything deciding when
a verdict hedges.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criteria 4 and 6 are
load-bearing: a scaffold that shades into authoring breaks a binding rule and would
survive every other test here, and a mirror drift fails the sync guard with an error
that reads as unrelated scaffold breakage.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
ceiling cannot be stated without re-deriving T01's rule in the skill (one home for
the rule — if the helper does not expose what is needed, that is an escalation);
scaffolding the prompt cannot be done without pre-filling text, which the never-author
rule forbids; or the skill's existing single-confirm posture cannot accommodate the
headline without becoming a multi-prompt flow, which would trade one friction for
another.
