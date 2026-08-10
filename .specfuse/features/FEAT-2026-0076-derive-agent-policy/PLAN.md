---
feature_id: FEAT-2026-0076
title: Policy-interview skill — derive-agent-policy
slug: derive-agent-policy
branch: feat/FEAT-2026-0076-derive-agent-policy
roadmap_goal: Make agent-policy.yml's premise true — the agent stops guessing the operator's intent because a skill actually asks, proposing from repo evidence what the repo can answer and asking only what it cannot.
autonomy_default: review
status: active
planned_cost_usd: 38.50
---

# Plan: Policy-interview skill — derive-agent-policy

`.specfuse/agent-policy.yml` shipped as the file the agent reads *instead of
guessing intent*. Every value in it is currently a default an agent chose. This
feature asks.

Drafted through a real `/draft-feature` interview (2026-08-10), unlike
FEAT-2026-0044/0047/0048 which were drafted solo the night before. The four
decisions below are the operator's, recorded with their reasoning — there is no
*Assumed decisions* section here, and that difference is the point of the
feature.

## Operator decisions taken at drafting

1. **Both halves, staged across two gates.** Gate 1 bootstraps a policy file
   from nothing; gate 2 reviews and corrects one that already exists. Bootstrap
   alone would not solve the problem that motivated the feature — this
   repository's file already exists and is full of agent-chosen values — but
   review-first would design the provenance mechanism before the interview's
   shape is settled. Gate 1 proves the questions are right on a greenfield repo;
   gate 2 adds review knowing what the questions actually are.
2. **Disjoint key ownership, not a single writer.** `/groom-backlog` already
   writes this file, so this skill is a second writer of it. The invariant
   becomes **one writer per key block**: `derive-agent-policy` owns `rules`,
   `budgets`, `escalation`; `/groom-backlog` owns `queue:`; neither writes the
   other's keys. Folding grooming in would restore a cleaner invariant but make
   a ten-minute periodic ritual carry the weight of a full policy interview.
   The boundary is written into **both** skills (T03) rather than remembered.
3. **A reference implementation plus a named deferral.** The feature ships
   `propose_policy_defaults` so "propose from evidence" is falsifiable, *and*
   the close explicitly defers "an agent following the prose reproduces this on
   an unseen tree" as one named post-merge operator run. See § *The oracle
   problem* — this is the failure that created FEAT-2026-0069.
4. **`autonomy_default: review`.** Decision 1's whole rationale is that gate 1's
   retrospective should inform gate 2. `auto` would draft and arm gate 2 without
   that read, skipping the checkpoint the staging exists to create. One human
   touch mid-feature, deliberately.

## Scope boundary

**IN.** The `propose_policy_defaults` reference implementation; the
`derive-agent-policy` skill (`SKILL.md` + `PROMPT.md`, canonical in `plugins/`);
the disjoint-key boundary in both skills; and, in gate 2, review of an existing
file.

**OUT — `queue:`.** `/groom-backlog` owns it (decision 2). This skill must not
write that key, and T03 makes the boundary testable.

**OUT — the schema and its validation.** `agent_policy.py` owns
`validate_agent_policy` and the `DEFAULT_*` constants. This feature *consumes*
them to propose values; it does not extend the schema. A new dial is the
feature that introduces it, not this one.

**OUT — the scoring formula.** FEAT-2026-0011 owns ranking and is `blocked` on
ADR-0002.

**OUT — the agent runner.** FEAT-2026-0049 consumes this file. Nothing here
schedules or executes anything.

**OUT — writing this repository's own policy values.** The named operator run
in § *The oracle problem* is a *review* against this repo's file; changing those
values is the operator's call afterwards, not a work unit's.

## The oracle problem

`[FEAT-2026-0069/G2-CLOSE]` is the binding precedent, and it is about this exact
shape of feature:

> FEAT-2026-0039's gates were green and its skill still emitted 30 components on
> its first real repo, because a passing fixture and an agent-executed skill are
> different oracles.

A skill is prose. Prose passes code gates trivially. So this plan writes gate 1's
definition of done **as what the gate can decide** — the algorithm proposes X
from fixture evidence, and the prose describes that algorithm — and schedules the
genuine gap as one named post-merge run rather than letting a green gate read as
"the skill is proven".

**The named deferral, fixed here so the close cannot soften it:** *an agent
following `derive-agent-policy`'s prose, run against a repository whose policy
file it has not seen, proposes the values `propose_policy_defaults` computes.*
The re-run condition is one operator invocation against **this repository's own
`.specfuse/agent-policy.yml`** — which is also the review the operator actually
wants, so the deferral and the first real use are one action.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  - `grep -n "^def " specfuse/loop/events_stats.py specfuse/loop/cost.py`
  - `grep -n "^def " specfuse/loop/gate_commands.py`
  - `grep -rln "def discover_components\|def suggest_checks" specfuse/`
  - `grep -n "^def \|^DEFAULT_" specfuse/loop/agent_policy.py`
- **Verdict:** `three mechanisms found and reused; the proposal layer itself does not exist and is built new.`

| Surface this feature needs | Existing mechanism | Verdict |
|---|---|---|
| Budget proposals from run history | `events_stats.collect(roots) -> dict` | **reuse** — T01 |
| `test_paths` evidence from gate commands | `gate_commands.iter_code_gates`, `code_gate_names` | **reuse** — T01 |
| Defaults and validation to propose against | `agent_policy.DEFAULT_*`, `validate_agent_policy` | **consume, do not extend** — T01/T02 |
| Interview skill structure and posture | `derive-verification`, `derive-monitoring` (`SKILL.md` + `PROMPT.md`) | **copy the shape** — T02 |
| Anything that derives or proposes config values | none | **building new** — T01 |

**Roadmap-row verb check** (`[FEAT-2026-0045/G1-CLOSE/verb-check-table-earns-its-cost]`):

| Verb from the row | Mechanism it assumes | Backed? |
|---|---|---|
| "proposing from repo evidence" | something that reads history/tree | **yes** — `events_stats`, `gate_commands` |
| "draft and never auto-write" | the derive-* posture | **yes** — both siblings implement it |
| "staged per-block accepts" | prose contract only | **prose** — T02's structural test is the only enforcement possible |
| "one interview per config surface, each with a single writer" | the one-writer invariant | **no, and it is why decision 2 exists** — this feature makes it one writer per *block*, not per file |

The fourth verb was wrong as written. Recorded here rather than quietly satisfied.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

This feature raises no check to `ERROR` and flips no severity. It adds no
validation: `validate_agent_policy` already rejects a malformed value for every
key this skill proposes, and T01 must produce values that pass it.

- **What does the rule report on an input already in its intended final state?**
  Not applicable — no new rule. The relevant property is the inverse and is
  T01's: **every proposal it emits must validate clean.** A proposer that emits
  a value its own validator rejects would be the feature failing at its purpose,
  and T01 asserts against it directly.

## Task graph

```yaml
# Two gates (operator decision 1). Gate 1 is non-terminal: close-intermediate
# then plan-next. Gate 2 carries a lone terminal close placeholder so the linter
# reads gate 1 as non-terminal; plan-next inserts its substantive WUs before it.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0076/T01
        file: WU-01-policy-proposals.md
        depends_on: []
      # Hygiene WU inserted at operator review between T01 and T02: T01 silently
      # withheld both budget proposals for any relative `repo_root`, because the
      # scratch symlink scoping `events_stats.collect` to this repo alone was
      # built from an unresolved path. A withheld proposal is supposed to mean
      # "no evidence exists"; it meant "the code could not see the evidence",
      # which is the outcome this feature exists to prevent. Every T01 fixture
      # used an absolute tempdir, so all twelve criteria passed. Inserted before
      # T02 so the skill's prose does not describe an under-proposing algorithm.
      - id: FEAT-2026-0076/T01H
        file: WU-01H-relative-repo-root.md
        depends_on: [FEAT-2026-0076/T01]
      - id: FEAT-2026-0076/T02
        file: WU-02-derive-agent-policy-skill.md
        depends_on: [FEAT-2026-0076/T01H]
      - id: FEAT-2026-0076/T03
        file: WU-03-disjoint-key-ownership.md
        depends_on: [FEAT-2026-0076/T02]
      - id: FEAT-2026-0076/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0076/T01
          - FEAT-2026-0076/T01H
          - FEAT-2026-0076/T02
          - FEAT-2026-0076/T03
      - id: FEAT-2026-0076/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0076/G1-CLOSE-INTERMEDIATE]

  - gate: 2
    file: GATE-02.md
    work_units:
      # Drafted by G1-PLAN against what gate 1 actually learned. All four ship
      # `status: draft` (unarmed); the operator arms them at the gate-1 review
      # after reading GATE-02-REVIEW.md. The provenance mechanism these units
      # assume — comparison against the shipped baseline, no schema change — is
      # decided in that artifact, reasoned from gate 1's derivability count.
      - id: FEAT-2026-0076/T04
        file: WU-04-policy-review.md
        depends_on: []
      - id: FEAT-2026-0076/T05
        file: WU-05-review-mode-prose.md
        depends_on: [FEAT-2026-0076/T04]
      - id: FEAT-2026-0076/T06
        file: WU-06-non-clobber-invariant.md
        depends_on: [FEAT-2026-0076/T05]
      - id: FEAT-2026-0076/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on:
          - FEAT-2026-0076/T04
          - FEAT-2026-0076/T05
          - FEAT-2026-0076/T06
```

Gate 2 repeats gate 1's dependency shape for the same reasons. T05 depends on
T04 because the skill's prose must describe an algorithm that exists — the
constraint `[FEAT-2026-0069/G2-CLOSE]` records and gate 1 honoured between T01
and T02. T06 depends on T05 because it fences the prose T05 writes.

T02 depends on T01 because the skill's prose must describe an algorithm that
exists. T03 depends on T02 because it edits the file T02 creates.

## Open question for gate 2 — deliberately not decided now

**How does review tell an agent-chosen default from a deliberate operator
choice?** Two shapes: compare against the shipped `DEFAULT_*` constants (cheap,
and lossy when an operator deliberately chooses a value equal to the default), or
record provenance when written (accurate, and a schema change this feature's
scope boundary puts out).

Left to `G1-PLAN` on operator decision. Gate 1 will report how many values are
even derivable, which is the input that should decide it — deciding now would be
guessing ahead of the evidence.

**Answered by `G1-PLAN`, 2026-08-10 — see `GATE-02-REVIEW.md` § *The provenance
question*.** Gate 1 reported **3 of 4 derivable unaided, 4 of 4 with a `gh`
runner**, and the recommendation follows that count: **comparison, widened to the
shipped baseline** — `agent_policy.DEFAULT_*` where a constant exists,
`.specfuse/agent-policy.yml.example` where one does not, because gate 1 also
found that none of the three `budgets` keys has a `DEFAULT_*` constant at all.
**No schema change is taken, so the scope boundary above stands unwidened**; the
provenance-recording shape is recommended as a successor feature, not folded in.
The recommendation is the operator's to accept at the arming review.

## Notes

- **`planned_cost_usd` is $38.50, the sum of the work units that actually
  exist.** The figure has moved twice, and both moves are recorded rather than
  overwritten. At drafting it was $27.00 — gate 1's five units plus gate 2's
  close placeholder. T01H was inserted mid-gate at operator review and added
  $2.00, taking it to **$29.00**; gate 1's close caught that this prose still
  said $27.00 and reported the staleness rather than editing it, since `PLAN.md`
  prose was not that close's to rewrite. `G1-PLAN` then drafted gate 2's three
  substantive units (T04 $3.50, T05 $3.50, T06 $2.50 — **$9.50**), taking the
  feature to **$38.50** and setting `GATE-02.md`'s `cost_budget_usd` to $19.50
  at the same time (gate 2's four units, $14.50, plus one re-attempt of its
  largest, $5.00 — `planning-discipline.md` §5 corollary).

  The drafting forecast for the whole feature was ~$37; that number was a
  forecast, not a plan, and was deliberately not recorded in frontmatter where
  lint would compare it against undrafted work. It is now superseded by the
  drafted sum above and is close to it — which is worth one line in gate 2's
  cost analysis, given gate 1's implementation spend came in at ~40% of
  estimate.

- **Skills are canonical in `plugins/specfuse/skills/`** and vendored into
  `.specfuse/skills/` by `scripts/sync-scaffold.sh`, which also creates the
  `.claude/skills/` discovery link. `tests/test_skills_vendored_in_sync.py` and
  `tests/test_skill_discovery_links.py` both fail if a skill exists in only one
  place — run the script rather than hand-creating links.
- Both siblings ship `SKILL.md` **and** `PROMPT.md`; this skill matches.
- No work unit here emits a committed executable, so
  `/authoring-work-units` §11 (shellcheck / bats) does not apply.
