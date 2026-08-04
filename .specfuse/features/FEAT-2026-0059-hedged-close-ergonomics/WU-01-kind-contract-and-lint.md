---
id: FEAT-2026-0059/T01
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - .specfuse/rules/close-discipline.md
  - specfuse/loop/closing_requirements.py
  - specfuse/loop/lint_closing.py
  - tests/test_hedged_kind_contract.py
produces_driver_helper:
  - FOLLOW_UP_KINDS
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-04T12:18:07.407747+00:00
duration_seconds: 1155.843
cost_usd: 2.774868
input_tokens: 104
output_tokens: 28315
---

# `kind:` on every hedged follow-up, and a lint that means it

**Objective.** Add a required `kind:` to `close-discipline.md` §2's hedged-verdict
follow-up record, with four values, and a `closing_requirements` check that refuses a
hedged close whose record lacks it.

**Context.** Correlation ID `FEAT-2026-0059/T01`. Read `PLAN.md` first — it records
why there are four kinds rather than the roadmap row's three, and why the lint is
scoped to the close being linted rather than sweeping the corpus. Do not reopen
either decision.

**The four kinds, and why the fourth exists.**

```
acceptance-discharged        needs a human signature; accepting IS the discharge
externally-verifiable-later  needs a real run or environment; upgradeable at a named condition
routed-finding               now owned elsewhere; tracked on another surface
inherent                     not assertable, ever
```

`inherent` is not in the roadmap row. FEAT-2026-0042's close invented the category in
prose because the contract had no slot — *"Fix correctness — **Inherent.** Not
deferred, not scheduled, not a gap. **Never.**"* Shipping three values forces the next
close to invent it again in different words, and leaves a reader with no mechanical
way to tell "nobody has done this yet" from "this can never be done".

**The verdict ceiling follows mechanically from the set**, which is the property T02
consumes: if **any** entry is `externally-verifiable-later`, rework exists. If none
is, `met` is unreachable by any in-repo work. Expose that as a function here so T02
reads a computed answer rather than re-deriving the rule.

**The trap, stated so it is not rediscovered.** Two hedged records already exist —
FEAT-2026-0041's and FEAT-2026-0042's retrospectives — and **neither carries
`kind:`**. A lint that sweeps `.specfuse/features/*/RETROSPECTIVE.md` would be red on
arrival and unfixable without rewriting closed features. Scope the check to the close
work unit currently being linted: it fires when *this* close writes a hedged verdict,
which is the moment the contract applies. Do not read historical records.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`,
`close-discipline.md`.

**Acceptance criteria.**

1. `tests/test_hedged_kind_contract.py::TestHedgedKindContract::test_hedged_close_without_kind_fails_lint`
   exists and **fails on HEAD before this WU runs** (no such check exists, so a
   hedged close with an unclassified record lints clean today — that counts as red).
2. That test builds a close WU with `verdict: met_locally` and a §2 record whose
   entries carry no `kind:`, and asserts `specfuse-lint --closing` reports a failure
   naming the missing field. It passes after this WU's edits.
3. A test asserts a hedged close whose every entry carries a **valid** `kind:` lints
   clean.
4. A test asserts an **unrecognised** `kind:` value fails, naming the four legal
   values in the message — a typo must not silently pass as classified.
5. A test asserts a close with `verdict: met` is unaffected: no §2 record is required
   and the new check does not fire. The check applies to hedged verdicts only.
6. **Historical records are not read.** A test asserts the check inspects only the
   close WU under lint — plant a malformed §2 record in a *different* feature's
   retrospective and assert it produces no finding. This is the satisfiability
   guarantee from `PLAN.md`, held as a test rather than a claim.
7. A helper exposes the verdict ceiling from a set of kinds — returning "rework
   exists" when any entry is `externally-verifiable-later` and "no in-repo rework can
   raise this" otherwise — with one test per branch, including the empty-record edge.
8. `close-discipline.md` §2 documents all four kinds, what each means for the
   verdict ceiling, and that `kind` is written by the close WU (which has the
   context) and never inferred by a reader.
9. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `verdict_permits_terminal_flips` and anything deciding *when* a
verdict hedges — out of scope per `PLAN.md`; this WU changes how a hedge is
explained. `plugins/specfuse/skills/accept-hedged-close/` — T02 owns the skill.
FEAT-2026-0041's and FEAT-2026-0042's retrospectives: they are closed records, not
migration targets.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Criterion 6 is the load-bearing
one — a check that sweeps retrospectives passes every other criterion here and is red
on this tree the moment it ships.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
four kinds cannot classify an entry shape that `close-discipline.md` §2 already
requires (say which — that is a real contract gap, not a naming problem); the lint
cannot be scoped to the close under lint without reading other features' files; or
adding a required field to §2 would make an existing *unhedged* close fail, which
would mean the check is firing outside its intended scope.
