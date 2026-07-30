---
gate: 2
open_questions:
  - "Tag namespace and lifetime: is pre-arm/<feature-id>/gate-<N> the name you want, and do these tags stay local or get pushed with the branch? T05 AC#3 asserts the literal string, so changing it later is a code change."
  - "LEARNINGS-pending.md location: feature-local (drafted) or a single .specfuse/LEARNINGS-pending.md across features? Feature-local keeps it in the PR diff; repo-level is one file to promote from."
  - "Scope of the blocking flip: T07 makes the whole lint_plan_next_draft warn set blocking under auto, not only the open_questions check. Narrower (open_questions only) is defensible if you want the first live ride to fail closed on fewer axes."
  - "Post-arm control flow: the driver runs one gate per invocation, so an auto-armed gate executes on the next invocation, not in the same process. Confirm that is what auto should mean for now, or say run-to-drain (FEAT-2026-0049) is the missing half."
  - "cost_budget_usd 31.50 on GATE-02.md: sum of drafted units plus one re-attempt of the largest, per planning-discipline section 5. Gate 1 came in 36% under estimate on substantive work, so this may be generous."
---

# Gate 2 review — live arming behind the dial

Written by `FEAT-2026-0053/G1-PLAN` at the gate-1 → gate-2 boundary. This file
supports the human read that arms gate 2. Gate 2 is the gate that makes arming
live, so the read is worth doing attentively — after it, this repo's driver can
flip a gate to `passed` without a human.

**Frontmatter note, and the feature's first dogfood of its own contract.** The
`open_questions:` list above is non-empty and deliberately so. Under
`autonomy_default: auto` a non-empty `open_questions` fires the
`open_questions_human_only` veto class and parks the feature — which is exactly
the intended behavior and exactly what should happen to a gate whose drafting
left five real decisions open. This feature runs `review`, so the list costs
nothing mechanically here; it is a live demonstration of the veto channel
working on its own author.

---

## Gate 1 summary

Gate 1 built the machinery `auto` needs and wired none of its behavior. Four
substantive units, all first-attempt passes except one correct block:

- **T01** `specfuse/loop/plan_baseline.py` — write-once `PLAN.baseline.json`
  snapshot of the as-activated plan graph.
- **T02** plan-next contract fields — `open_questions`, `human_only`,
  `provenance` documented in both `WU.template.md` copies, WARN-only checks in
  `lint_plan_next_draft`.
- **T03** `specfuse/loop/arm_eval.py` — `evaluate_arm_predicate`, pure and
  side-effect-free, seven stop classes, 19 focused test cases.
- **T04** shadow wiring — baseline write at first dispatch,
  `build_arm_predicate_event` at all three `awaiting_review` flip sites, zero
  behavior change.

35 tests across seven commands, zero failures. One non-passing attempt (T04
attempt 1, $1.22): a correct stop on an unowned event-schema registry, resolved
by narrowing AC#2 and tracking the gap as FEAT-2026-0060.

## What gate 2 does

Five substantive items from PLAN.md's sketch, drafted as five WUs plus the
closing pair. The shape follows gate 1's proven module-then-wiring split.

| WU | What | $ |
|---|---|---|
| T05 | `arm_txn.py` — the pure arm transaction: the whole write set, one path list, the tag name. No git in the module | 3.50 |
| T06 | The dial read and the arm branch at the one flip site that can arm; the revert tag; `docs/dev/auto-arm-recovery.md` | 3.50 |
| T07 | Contract-field lint warns → an eighth veto-only predicate class, blocking under `auto` only. **`human_only: true`** | 3.00 |
| T08 | `FEATURE-REVIEW.md` accumulation — every auto-armed gate's doubt reaches the PR read | 2.50 |
| T09 | LEARNINGS staging to `LEARNINGS-pending.md` under `auto`, with a post-pass invariant enforcing it | 2.50 |
| G2-CLOSE-INTERMEDIATE | retro, lessons, docs | 4.50 |
| G2-PLAN | draft gate 3 | 6.00 |

T05 → T06; T07, T08, T09 each hang off T06 and are independent of each other,
so any one of them can be rejected or deferred at arming without stranding the
others.

### The atomic arm transaction — why one commit is achievable without a refactor

`RETROSPECTIVE.md` does not report anything that invalidates the single-commit
design, and this unit checked the flip sites directly rather than taking that
silence as evidence. T04 wired three sites, and they are not equivalent:

| Flip site | Kind | Can arm? |
|---|---|---|
| Pre-flight baseline probe failure (`preexisting_gate_failure`) | escalation | never |
| Per-gate budget brake (`gate_budget_exceeded`) | escalation | never |
| Normal gate completion (all WUs `done`, `gate_reached`) | the arm site | yes |

Only one site can arm, and each of the three already performs **exactly one**
bookkeeping commit covering its gate-file write and its events append. The arm
therefore extends an existing single commit's path list rather than introducing
a second commit or restructuring the close path. **The G1-PLAN escalation
trigger for this — "the flip sites make a single atomic arm impossible without a
close-path refactor" — does not fire.**

The recovery rule keyed on that commit: because the arm is one commit, a crash
leaves either an uncommitted working tree (the driver's existing
refuse-on-dirty / reset path discards it — nothing to do) or a complete arm
(reset to `pre-arm/<feature-id>/gate-<N>`). There is no third state. T06 ships
that as `docs/dev/auto-arm-recovery.md`; gate 3 folds it into the methodology.

## Escalation-predicate satisfiability (planning-discipline §2)

> **What does the flipped rule report on an input already in its intended final
> state?** **Zero.**

The full answer lives in `WU-07`'s body, where the WU that performs the flip has
to carry it. The short form: the check set is `GATE-{N+1}-REVIEW.md` frontmatter
carrying an explicit `open_questions:` list (`[]` satisfies it — the contract
requires the field, not a non-empty value), plus per-draft-WU checks for a
well-formed ID, positive `planned_cost_usd`, valid `type`, five non-empty
mandatory sections, and `produces_driver_helper` when the body names driver
wiring. Each is satisfiable by an author who knows the contract, and all are
satisfiable simultaneously — no two trade against each other, which is the
contradiction §2 exists to catch.

**Read this answer against the check set before accepting it.** §2's provenance
is a case where the contradiction was answerable by reading a document against
itself and nobody did.

## §4 runtime probe — MANDATORY BEFORE ARMING, AND NOT YET RUN

`planning-discipline.md` §4 is explicit that a gate whose WUs flip a severity
may **not** be armed on "mechanical, nothing design-open." T07 is a severity
flip. Before flipping gate 2's WUs to `pending`:

1. Apply T07's change locally.
2. Run the **exact** lint command T07's tests gate will run, over **every**
   feature folder in this repo — the full oracle, not a subset.
3. **Paste the resulting finding list into this section**, below the census.
   That list becomes T07's enumerated migration surface, so the WU does not
   discover its own breakage attempt by attempt.

### Pre-flip census — drafting evidence, NOT the probe

This unit ran the *existing* warn-only `lint_plan_next_draft` over all 43
feature folders in `.specfuse/features/`, gates 0–5. It is recorded here because
it materially informs the satisfiability answer, and it is labeled loudly
because **it is not the §4 probe**: it was taken before the change existed,
which is precisely the condition §4 refuses to accept as arming evidence.

**26 findings, of two kinds:**

- **25 × `GATE-NN-REVIEW.md: missing 'open_questions:' frontmatter field`**, one
  per pre-T02 review file, spread across 17 features (FEAT-2026-0003, -0007,
  -0010, -0015, -0016, -0018, -0024, -0025, -0026, -0027, -0028, -0032, -0039,
  -0040, -0053, -0069, -0070). Every one of them is a feature drafted before T02
  existed, and every one runs `autonomy_default: review`. None is an input in
  its intended final state under the new contract, and none is ever evaluated by
  the flipped class, which only runs on the feature being armed. **These are
  evidence, not a migration backlog** — T07's Do-not-touch says so explicitly.
- **1 × a raised `MiniYAMLError`**, not a finding at all:
  `FEAT-2026-0020-public-readiness-prep/GATE-02-REVIEW.md` line 14 is not a
  `key: value` line, so the frontmatter reader raised straight out of the lint.
  A raise is not a verdict. Under a blocking flip an unhandled raise would take
  down the close path, so **T07 AC#5 requires a malformed review file to produce
  a fired class naming the parse failure**, following T04's `evaluation_error`
  degradation precedent. This is the census earning its cost.

The 26th finding is also a live reminder for anyone authoring frontmatter in
this repo: the loop's parser is a strict subset. Block scalars (`>`, `|`),
single quotes, flow mappings and multi-line values all raise rather than parse.
This unit hit that itself while drafting and rewrote five `provenance:` fields
to single-line double-quoted strings.

### Probe finding list

> **Paste here before arming. Do not arm this gate on an empty section.**

## Cost

### Gate 1 closing pair, against the $10.50 floor

`RETROSPECTIVE.md` asked this unit to state the closing-pair actual, since
`G1-CLOSE-INTERMEDIATE` could not read its own final cost and this is the first
surface that can see both. Half of it is knowable here; the other half is this
unit, which cannot read its own cost either.

| Unit | Planned | Actual | Delta |
|---|---|---|---|
| G1-CLOSE-INTERMEDIATE | $4.50 | $3.345159 (1 attempt, passed) | −$1.15 (−25.7%) |
| G1-PLAN (this unit) | $6.00 | not readable from inside | — |
| **Pair** | **$10.50** | **≥ $3.35** | — |

The half that is readable came in **under** its `planning-discipline` §5 floor,
on a first-attempt pass. Combined with gate 1's substantive units running 35.8%
under estimate, gate 1 so far has spent **$11.70 against a $28.00 gate budget**.
The pattern is the one issue #260 already tracks across three features; this
review adds an observation, not an argument. **`G2-CLOSE-INTERMEDIATE` should
state this unit's actual against $6.00** — it is the first surface that can.

### Re-baseline and delta against $28.50

`PLAN.md`'s `planned_cost_usd` was **$28.50** (gate 1's six units at $23.50 plus
gate 3's close placeholder at $5.00). Gate 2's seven drafted units add **$25.50**.

**New `planned_cost_usd`: $54.00. Delta: +$25.50 (+89.5%).**

That near-doubling is not scope growth — $28.50 was always a partial figure
covering only the drafted work, exactly as PLAN.md's own note said. It will move
again when `G2-PLAN` drafts gate 3's substantive units, which are currently
represented by a $5.00 close placeholder alone.

`GATE-02.md` carries `cost_budget_usd: 31.50` — the $25.50 sum plus one
re-attempt of the largest unit ($6.00, `G2-PLAN`), the defensive-padding shape
§5 recommends.

## Doubt

Five things this draft is least sure about, in the order they would hurt.

1. **The first live arm is not on this feature, so gate 2 ships tested but
   unridden.** `[FEAT-2026-0007/G2-LESSONS]` is the reason and it is a good one,
   but the consequence stands: every auto-arm path in gate 2 is verified by
   tests and by no production ride. `RETROSPECTIVE.md` Findings §3 sharpens
   this — the predicate's *approval* path has never executed against a real
   feature directory, only fixtures, on any of 43 real folders. T06 AC#6
   requires at least one real-feature-directory exercise for that reason, but a
   copied folder in a test is still not a driver run.
2. **This feature's own baseline is post-drift and proves nothing.** Findings §2:
   `PLAN.baseline.json` for FEAT-2026-0053 will be captured on the next driver
   invocation, from a PLAN.md that already contains gate 2 — because this very
   unit just put it there. `drift_caps` and `retroactive_edits` will report clean
   and mean nothing on this feature. Neither `GATE-02.md`'s definition of done
   nor `G2-CLOSE-INTERMEDIATE` may cite them as evidence, and both now say so.
3. **T06 is the biggest single-WU risk in the feature.** It touches the close
   path, adds a git tag, changes what a gate status means under one dial value,
   and has to keep two escalation sites provably inert. Its flag-scope table has
   eight rows for a reason. If any WU in gate 2 spins, the prior is on this one.
4. **`gate_auto_armed` is a second unregistered event type.** T04 established the
   precedent deliberately and the operator confirmed it, so this is not a
   re-litigation — but FEAT-2026-0060 now has three driver-local types outside
   both the envelope enum and the per-type registry rather than two, and gate 2
   is where an *arming* decision starts living on that unvalidated stream.
5. **Five items were sized as five WUs, and T08/T09 are small.** They were kept
   separate because they touch different surfaces with different failure modes
   (an append inside the arm commit vs. a post-pass invariant plus templates),
   and because separate units can be rejected independently at this checkpoint.
   Merging them is a defensible call for the human to make; the sizing is honest
   either way, not padded.

## What to check at this checkpoint

- **Run the §4 probe and paste its output above.** This is the one blocking
  precondition. Everything else on this list is judgment.
- **Answer the five `open_questions`.** Under `auto` they would have parked the
  feature; under `review` they are yours to settle.
- **Read T07's satisfiability answer against `lint_plan_next_draft`'s actual
  check set**, not against this summary of it.
- **Check T06's flag-scope table against the headline claim** — *"an `auto`
  feature arms its next gate without a human"*, not *"runs unattended to
  completion"*. A path the table does not cover is a scope mismatch, and §3's
  provenance is a feature where exactly that surfaced two gates later as a
  defect.
- **First-firing check for gate 1**, carried forward from `GATE-01.md`:
  confirm `events.jsonl` carries an `arm_predicate_evaluated` event for gate 1.
  **`GATE-01.md` says an absent event means escalate; `RETROSPECTIVE.md`
  Findings §1 shows that inference does not hold on this gate** — the driver
  process that closed gate 1 predates T04's commit and cannot emit the event
  regardless of T04's correctness. If the closing process predates the commit,
  re-run the driver rather than escalating.
- **Decide whether merge stays human.** It does, by PLAN.md's scope boundary,
  without exception. Gate 2 changes nothing about it. Worth confirming out loud
  once, here, at the gate that makes arming automatic.
