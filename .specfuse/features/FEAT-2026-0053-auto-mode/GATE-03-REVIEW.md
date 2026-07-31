---
gate: 3
open_questions:
  - "T13 is the one scope decision on this gate: it widens PLAN.md's gate-3 boundary from documentation-only to give FEATURE-REVIEW.md a reader in /wrap-feature. Accept, reject, or defer with a named home. It strands nothing — T10, T11 and T12 do not depend on it — but a silent rejection ships the feature with its headline claim undelivered."
  - "judge_editing fires on this gate's own drafted WUs because three of them produce a mirrored scaffold copy under specfuse/loop/data/docs/, which the v1 JUDGE_PATHS prefix specfuse/loop/ cannot distinguish from driver source. Accept as a known v1 approximation, or narrow the prefix set so a documentation WU can arm under auto? Either way it needs a home; it is not fixable inside gate 3."
  - "docs/methodology.md §9 carries two claims with no implementation: the per-gate tightening-only autonomy override (nothing reads a per-gate autonomy field) and supervised as a level distinct from review (every consumer branches on == auto). T10 is instructed to record both as unbuilt. Confirm that is the call rather than building either."
  - "Gate 2's Findings §1 — budget_projection and gate_spent_usd under-read this feature's lifetime spend by $6.23 and $5.01 because neither reads cumulative_cost_usd or re_arm_history[].prior_cost_usd — still has no home. G3-CLOSE is instructed to re-measure and name one, not to fix it. Where does the fix go: an issue against arm_eval, or a roadmap feature?"
  - "cost_budget_usd 22.00 on GATE-03.md is the §5 shape (sum plus one re-attempt of the largest). Gate 2 has already consumed 93.4% of its own $31.50 brake with its plan-next still running, so the shape is not protecting closing-WU over-runs. Accept 22.00, or raise it knowing §5 says a closing-WU retry is a defect to diagnose rather than a cost to budget for?"
---

# Gate 3 review — docs, methodology, and the honest close

## Arming decisions (2026-07-31, at the gate-2 → gate-3 checkpoint)

Answers to the five `open_questions`, recorded here because `G3-CLOSE` reads
this file and several of them change what it must report.

1. **T13 — accepted, scoped in.** Gate 3 is terminal, so there is no later gate
   in this feature to hold it, and the alternative is shipping a feature whose
   own retrospective records its headline claim as undelivered. An accumulation
   file nothing reads is the checkpoint value silently not delivered, not a
   cosmetic gap. `PLAN.md`'s "docs and methodology rewrite" boundary is
   knowingly widened by this one WU; `G3-CLOSE` should enumerate that widening
   in its contract-change list rather than let it pass as documentation.

2. **`judge_editing` on documentation — accepted as a known v1 approximation.**
   Not fixed here; the fix is not gate 3's to make. Per this file's own
   recommendation, the decision is written into T11's scope as **AC#5a**: the
   stop-class page must name the case, state that no `auto` gate shipping
   documentation can arm, and give the human arm as its clearing action. The
   underlying narrowing of `JUDGE_PATHS` needs a home outside this feature.

3. **The two unbuilt §9 claims stay unbuilt, recorded as unbuilt.** Confirmed.
   The per-gate tightening-only override and `supervised`-as-a-distinct-level
   are design decisions worth preserving in prose; building either is a
   different feature, and deleting them silently loses the decision. T10's
   instruction stands.

4. **The `budget_projection` / `gate_spent_usd` under-read needs a roadmap
   feature, not an issue.** Neither reads `cumulative_cost_usd` nor
   `re_arm_history[].prior_cost_usd`, so both under-report any WU that was ever
   re-armed — $6.23 and $5.01 on this feature alone. That is a correctness
   defect in a stop class that gates autonomy, and it interacts with the
   `arm_eval` constants graduating to `agent-policy.yml`, which is feature-sized
   work. `G3-CLOSE` re-measures and names the number, as instructed, and does
   not fix it.

5. **`cost_budget_usd: 22.00` accepted unchanged.** §5 is right that a
   closing-WU retry is a defect to diagnose rather than a cost to budget for,
   and raising the number to cover a predicted breach would convert a signal
   into noise. If gate 3 breaches it, that is the datum, and `G3-CLOSE` reports
   it alongside gate 2's true final number.

**§4 runtime probe — confirmed not required.** Checked against the four WU
bodies rather than taken from this file's claim, because gate 2's arming turned
on exactly this precondition. T10–T12 produce documentation and its mirrored
scaffold copies. T13 edits `wrap-feature`'s skill prose; its behavior keys on
the presence of a file, not on a default value. `G3-CLOSE` is the close. Nothing
on this gate flips a default or a severity, so §4 does not bind.

**Merge stays human.** Confirmed once more at the terminal gate, as this file
asks. Nothing in gate 3 touches it and T13 explicitly forbids softening it.

Written by `FEAT-2026-0053/G2-PLAN` at the gate-2 → gate-3 boundary. This file
supports the human read that arms gate 3, the terminal gate. After gate 3 there
is no further plan-next: this is the last checkpoint at which the shape of the
remaining work can change.

**Frontmatter note, and the feature's second dogfood of its own contract.** The
`open_questions:` list above is non-empty and deliberately so. Under
`autonomy_default: auto` a non-empty list fires the `open_questions_human_only`
veto and parks the feature — correct behavior for a gate whose drafting left
five real decisions open, one of which changes the gate's declared scope. This
feature runs `review`, so the list costs nothing mechanically; it is the veto
channel demonstrated on its own author, exactly as `GATE-02-REVIEW.md` did.

---

## Gate 2 summary

Gate 2 made `auto` real. Five substantive units, repeating gate 1's
module-then-wiring split:

- **T05** `specfuse/loop/arm_txn.py` — the pure arm transaction: the whole write
  set as one `paths` tuple plus the revert tag *name*. No git in the module,
  which is what makes the one-commit guarantee testable.
- **T06** the dial goes live — `autonomy_default` read at the single flip site
  that can arm; tag, apply, and carry every write into the one existing
  bookkeeping commit. The two escalation flip sites `return` before that line,
  so escalation overrides autonomy by control flow.
- **T07** the severity flip — `plan_next_lint` as the eighth predicate class and
  the third veto class. Three attempts spun on a sibling WU's test fixture
  before the operator root-caused it; $9.29 against a $3.00 estimate.
- **T08** `FEATURE-REVIEW.md` accumulation — verbatim `open_questions`, verbatim
  `## Doubt`, per-class verdict line, inside the same single arm commit.
- **T09** LEARNINGS staging — under `auto`, a closing WU touching
  `.specfuse/LEARNINGS.md` fails `assert_learnings_staged_under_auto`.

58 tests across nine commands, zero failures. Six non-passing attempts,
$9.010432 — 38.0% of substantive gate spend. Gate entry was not clean: a
pre-flight baseline probe escalated `preexisting_gate_failure` before any WU was
dispatched, which is why gate 2's first recorded event is an escalation.

## What gate 3 does

Four substantive WUs plus the terminal close. Three subjects the dispatch brief
named as minimum scope, plus one deliberate scope-boundary revision.

| WU | What | $ |
|---|---|---|
| T10 | `docs/methodology.md` §9 rewritten to the shipped dial; the two unbuilt claims recorded as unbuilt; the auto-arm concept folded in with the recovery procedure left in its own home | 3.00 |
| T11 | `docs/concepts/autonomy-stop-classes.md` — eight classes, three statuses, v1 constants, a clearing action per class, and how to read an `arm_predicate_evaluated` event | 3.00 |
| T12 | `docs/concepts/adopting-auto-mode.md` — artifact inventory, the three breakage items gate 2 flagged, the mid-life baseline hazard, the executable opt-in procedure. **`depends_on` T11** | 3.00 |
| T13 | `FEATURE-REVIEW.md` and `LEARNINGS-pending.md` reach the PR body via `/wrap-feature`. **`human_only: true`** | 3.00 |
| G3-CLOSE | terminal close: oracles fresh, contract changes across all three gates, what the loop did not verify, feature-arc verdict | 5.00 |

T10, T11 and T13 are independent. T12 `depends_on` T11 — **declared, not
discovered**. Both add a page under `docs/concepts/` and therefore both edit
`docs/README.md`'s concepts index and `DOCS_TRACKED` in
`tests/test_scaffold_data_in_sync.py`. Gate 2's Findings §3 cost $5.01 and three
sessions because two WUs shared a fixture nobody had crossed against the plan's
independence claim; this gate crosses the shared surfaces at drafting and orders
the two WUs so the edits are sequential.

### The scope-boundary revision — T13, and why it is not deferred

`PLAN.md`'s scope boundary named gate 3 as *"docs and methodology rewrite"*.
T13 is not documentation. Gate 2's retrospective (Findings §5, and *What the
loop did NOT verify* item 4) records that `FEATURE-REVIEW.md` is written and
never read: `grep -rn "FEATURE-REVIEW" .specfuse/skills specfuse/loop/data`
returns zero matches, nothing surfaces it into a PR body, and `/wrap-feature`
does not know it exists. That retrospective asks `G2-PLAN` to either scope the
last hop into gate 3 or record a deliberate deferral with a home.

**Scoped in, for one reason: gate 3 is terminal.** There is no later gate in
this feature to hold it. Under `auto` the accumulation is the mechanism that
trades four human gate reads for one PR read — an unread accumulation file is
not a cosmetic gap, it is the checkpoint value silently not being delivered. The
alternative is shipping a feature whose headline claim is undelivered and whose
retrospective says so.

**It is `human_only: true` because that judgment is the human's, not the
planner's.** Rejecting T13 at this checkpoint is legitimate and strands nothing.
A rejection should name a home for the gap — FEAT-2026-0047 (outbound
notifications) is the nearest existing surface, but the fit is approximate and
naming it here is a suggestion, not a decision.

## Planning-discipline applicability (§§2–4)

Stated positively rather than by omission, because gate 2's arming turned on a
§4 precondition and a reader arriving from that gate will look for the same
thing here.

- **§4 runtime probe — not required.** §4 binds a gate whose WUs flip a
  **default value** or a **severity**. T10–T12 are documentation; T13 edits a
  skill's prose and changes behavior on the presence of a file, not on a
  default. Nothing in gate 3 flips either. **Check this reading against the four
  WU bodies before accepting it** — if any of them turns out to change a default
  or a severity, the probe becomes mandatory and `GATE-03.md`'s arming
  discipline is wrong.
- **§2 satisfiability — nothing to answer.** No severity flip, no "zero issues"
  close predicate. Gate 1's PLAN.md required gate 2 to answer §2 again because
  gate 2 carried T07; gate 3 carries no equivalent. That is a different
  statement from silence, which is why it is written down.
- **§3 flag-scope table — not applicable.** No gate-3 WU introduces, gates on,
  or flips a behavior flag.

## The arm predicate, run live against this drafted gate

Run in this session after the drafts were written —
`evaluate_arm_predicate(<this feature>, 2)`:

```
would_arm: False
  budget_projection            clean   projected spend $64.56 within 2.0x baseline planned total $54.00 (cap $108.00)
  judge_editing                fired   T10 produces specfuse/loop/data/docs/methodology.md;
                                       T11 produces specfuse/loop/data/docs/concepts/autonomy-stop-classes.md;
                                       T12 produces specfuse/loop/data/docs/concepts/adopting-auto-mode.md
  decision_class_paths         clean   no drafted WU touches dependency manifests
  retroactive_edits            clean   no passed-gate baseline WU altered or removed
  drift_caps                   clean   added WUs and gates within drift caps
  missing_provenance           clean   every added WU carries a provenance field
  open_questions_human_only    fired   GATE-03-REVIEW.md missing open_questions field; human_only flagged: T13
  plan_next_lint               fired   GATE-03-REVIEW.md: missing open_questions frontmatter field
```

Two of the three fired classes were expected and resolve as this file lands:
`open_questions_human_only` and `plan_next_lint` both fired on the review file's
absence at the moment of the run, and the former will keep firing on the
non-empty `open_questions` list and on T13's `human_only` flag — which is the
veto channel working as designed.

**`judge_editing` is the one worth reading carefully, and it is new
information.** It fires because T10, T11 and T12 each declare a mirrored
scaffold copy under `specfuse/loop/data/docs/` in `produces:`, and
`_matches_judge_path` is a prefix test against `JUDGE_PATHS`, which contains
`specfuse/loop/`. The predicate cannot tell a documentation file shipped as
package data from driver source. This is the same class of v1 approximation the
module already documents for `pyproject.toml` (matched whole-file, so it
double-fires on `judge_editing` and `decision_class_paths`) — but the
consequence is sharper than the `pyproject.toml` case: **every documentation
work unit in this repo mirrors into `specfuse/loop/data/docs/`, so under `auto`
no gate that ships documentation can ever arm.** It costs nothing on this
feature, which runs `review`. It is open question 2, and the fix is not gate 3's
to make.

## Cost

### Gate 2's closing pair, and gate 1's, against the $10.50 floor

`RETROSPECTIVE.md` asked this unit to state `G1-PLAN`'s actual against $6.00 —
`G2-CLOSE-INTERMEDIATE` was the first surface that could see it, and it did not.
Stated here from `events.jsonl`, along with the half of gate 2's pair that is
readable. This unit cannot read its own cost.

| Unit | Planned | Actual | Delta |
|---|---|---|---|
| G1-CLOSE-INTERMEDIATE | $4.50 | $3.345159 | −$1.15 (−25.7%) |
| G1-PLAN | $6.00 | $6.684054 | +$0.68 (+11.4%) |
| **Gate 1 pair** | **$10.50** | **$10.029213** | **−$0.47 (−4.5%)** |
| G2-CLOSE-INTERMEDIATE | $4.50 | $5.671201 | +$1.17 (+26.0%) |
| G2-PLAN (this unit) | $6.00 | not readable from inside | — |
| **Gate 2 pair** | **$10.50** | **≥ $5.67** | — |

Gate 1's closing pair landed within 5% of its §5 floor — the floor is calibrated
about right for a clean gate. Gate 2's `close-intermediate` ran 26% over, on a
gate with six non-passing attempts and an escalation to write up. That is
consistent with the floor being a function of what the gate did rather than of
the WU type, which §5 does not currently model.

**The brake will be breached on gate 2 and will not fire.** Gate-2 spend to date
is **$29.411246 against `cost_budget_usd: 31.50` — 93.4% consumed with this unit
still running.** `_should_halt_for_budget` is evaluated *before* each dispatch,
so an overrun inside the last WU is structurally invisible to it; gate 2's
retrospective predicted a ~$2.3 overrun assuming the pair repeated gate 1's
actuals, and the `close-intermediate` alone already came in $2.33 above that
assumption. `G3-CLOSE` should state gate 2's true final number.

### Re-baseline and delta against $54.00

`PLAN.md`'s `planned_cost_usd` was **$54.00** when this unit found it — gate 1's
six units ($23.50), gate 2's seven ($25.50), and gate 3's close placeholder
($5.00). Gate 3's four substantive units add **$12.00**.

**New `planned_cost_usd`: $66.00. Delta: +$12.00 (+22.2%).**

This is the last re-baseline the feature gets: every gate is now drafted, so
$66.00 is a complete figure rather than the partial one every prior value was.
Feature spend to date, from `events.jsonl` across all attempts, is
**$47.791070** — 72.4% of the new plan with gate 3 entirely unrun.

`GATE-03.md` carries `cost_budget_usd: 22.00` — the $17.00 sum plus one
re-attempt of the largest unit ($5.00, `G3-CLOSE`), the defensive-padding shape
§5 recommends.

## Doubt

Five things this draft is least sure about, in the order they would hurt.

1. **Three of four substantive WUs deliver prose, and prose has no oracle.** The
   tests T10–T12 name prove the mirrored copies byte-match and that nothing
   regressed. They prove nothing about whether §9 is now *true*, whether a
   stop-class entry's clearing action actually clears anything, or whether an
   operator could follow the opt-in procedure. The acceptance criteria are
   written as literal greps and structural checks precisely because that is the
   most a machine can hold here — **the human reading this gate, and later the
   PR, is the real oracle, and this gate is more dependent on that than either
   of its predecessors.**
2. **T13 might be the wrong call.** It is the only WU on this gate that changes
   behavior, on a gate PLAN.md declared documentation-only, drafted by a planner
   that cannot weigh "ship the last hop" against "keep the terminal gate clean"
   the way its author can. The argument for scoping it in is real and stated
   above; so is the argument that a terminal gate is the worst place to add
   behavior. `human_only: true` exists so this does not get decided by default.
3. **`judge_editing` firing on documentation is a finding this gate surfaces and
   cannot fix.** Under `auto`, no gate that ships a documentation file can arm,
   because every documentation file in this repo has a mirrored copy under
   `specfuse/loop/data/`. That is a bigger statement than it looks: it means the
   *first* `auto` feature to write docs parks, and its operator will be reading
   `arm_eval.py` to find out why unless T11's page lands with this case named.
   T11's brief does not currently name it; if the human accepts open question 2
   as a v1 approximation, that decision should be written into T11's scope at
   arming.
4. **Gate 2 is going to close over its brake and gate 3's brake is built the
   same way.** $22.00 by §5's shape, on a gate whose largest unit is the close
   and whose closing pairs have run −4.5% and +26.0% on the two prior gates. §5
   is explicit that a closing-WU retry is a defect to diagnose rather than a
   cost to budget for, so raising the number is the wrong instinct — but stating
   that and then setting a number that will probably be breached is not
   comfortable, and it is open question 5 rather than a settled thing.
5. **Four WUs sized identically at $3.00 is a smooth-looking estimate, and
   gate 2 just proved smooth estimates wrong.** Gate 2's five units were priced
   $2.50–$3.50 and came in 58.3% over in aggregate, with two *first-attempt
   passes* landing 44% and 72% over. The distinguishing property gate 2 named
   was that its units wired behavior into each other; gate 3's do not, which is
   the argument for the flat number. It is an argument, not evidence, and issue
   #260 now has five data points pointing in two directions.

## What to check at this checkpoint

- **Decide T13.** Accept, reject, or defer with a home. This is the one decision
  that changes what the gate is. Everything else on this list is a read.
- **Answer the five `open_questions`.** Under `auto` they would have parked the
  feature; under `review` they are yours to settle.
- **Check the §4 reading.** `GATE-03.md` claims no runtime probe is required
  because nothing on this gate flips a default or a severity. Read the four WU
  bodies against that claim rather than taking it from this file — gate 2's
  arming turned on exactly this precondition.
- **Read T11's acceptance criteria against the clearing-action requirement.** A
  stop-class reference that describes eight classes without saying what an
  operator does about each is the failure this gate exists to prevent, and AC#2
  is the only thing standing between the page and that outcome.
- **Confirm the two unbuilt §9 claims should stay unbuilt.** The per-gate
  tightening-only override and `supervised`-as-a-level are documented today and
  implemented nowhere. T10 is told to record them as unbuilt. Building either is
  a different feature; deleting them silently loses a design decision.
- **Do not cite this feature's own baseline as evidence, still.** Carried
  forward from gate 2 unchanged: `PLAN.baseline.json` was captured after this
  feature's own gate-2 drafting, so a clean `drift_caps` verdict measures
  nothing. The honest first test of drift detection is a feature whose first
  dispatch happens after this branch merges.
- **Confirm merge stays human.** It does, by PLAN.md's scope boundary, without
  exception, and nothing in gate 3 touches it — T13 explicitly forbids softening
  it. Worth confirming out loud once more at the terminal gate.
