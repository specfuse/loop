---
gate: 2
open_questions:
  - "T06 picks one of the three remedies gate 1's retrospective named for finding 2, and the retrospective explicitly said the choice was not that session's to make. The draft picks the pristine-entry skip: an entry with `state: unverified`, no `kind:`, and no `oracle:` is not a finding; anything a close has touched still is. The two rejected shapes and why are in WU-06's Context. Accept, or name the other remedy — this is the only design choice in the gate that a later WU cannot walk back."
  - "The driver must be stopped after T08 reports `done` and restarted before G2-CLOSE dispatches. This is an operator action mid-gate, not a WU, and gate 2 is terminal so there is no gate boundary to hide it behind. G2-CLOSE blocks if it did not happen. Confirm you will do it, or say G2-CLOSE should fall back to a labelled fresh-interpreter composite and accept a weaker feature-level answer."
  - "Gate 1's `close-discipline.md` §3 contract-change list is still awaiting human acknowledgment (RETROSPECTIVE.md, last line of that section). Item 1 — the new blocking `close-l` / `close-intermediate-f` finding — is the item that needed a real decision, and T06 changes its behaviour. Acknowledge gate 1's list as it stands, or defer acknowledgment to G2-CLOSE's combined enumeration and say so, so G2-CLOSE knows which it is answering."
  - "T05's carve-out preserves any untracked file whose basename matches `GATE-NN-CRITERIA.md` through a failed attempt's cleanup. That is a permanent, driver-wide exception in the same class as the `events.jsonl` one, and it applies to every feature in every downstream project after upgrade — not only to features using this artifact. Accept the blast radius, or require the narrower parameter-threading shape and accept the ~15 call-site edits WU-05's escalation trigger currently refuses."
---

# Gate 2 review — the incremental re-close policy

Drafted by `FEAT-2026-0056/G1-PLAN` from gate 1's `RETROSPECTIVE.md` and
`.specfuse/LEARNINGS.md`. Gate 2's shape, the disposition of the draft-time proposal,
and everything this session changed in a not-yet-reached part of the plan.

## Does gate 1's record still support gate 2's premise?

**Yes, conditionally, and the condition is now gate 2's first work unit.**

`WU-91`'s escalation trigger says to block if gate 1's retrospective shows the
recorded per-criterion state is not trustworthy enough to build a skip policy on.
It shows something narrower and fixable. Three findings, each read against that
question:

- **Finding 3 (the artifact does not survive a failed attempt)** is the one that
  could have invalidated the premise. Gate 1's close executed
  `_clean_attempt_untracked`'s real decision rule and recorded
  `criteria artifact still present after attempt reset: False`. On HEAD, a
  multi-attempt close — the exact scenario this feature exists to serve — reads a
  blank artifact every time. That is not "the state is untrustworthy in principle";
  it is a named defect on a named line with a named precedent (`events.jsonl`'s
  carve-out, two lines away). `T05` fixes it and is ordered first, with no
  dependencies, so if it blocks, the gate stops before spending on the consumer.

- **Finding 2 (a fresh artifact is born 41 findings deep)** does not touch
  trustworthiness at all — the recorded content is fine; the *lint's* initial-state
  predicate is wrong. `T06`.

- **Finding 1 (the driver that dispatched gate 1's close predated T02)** is not a
  defect in the state either. It is a sequencing hazard, and it is the one the
  retrospective explicitly handed to this session: "That belongs in gate 2's plan as
  a step, not in `LEARNINGS.md` as a second copy of a rule that is already there."
  It is now an arming precondition in `GATE-02.md`, a comment in `PLAN.md`'s graph
  where the step falls, and `G2-CLOSE`'s criterion 2 with a `blocked` outcome
  attached.

What gate 1 proved positively is the load-bearing half: seeded through the real
entrypoint, the artifact carried 41 correctly-identified entries with stable IDs
(`T01#1` … `T04#10`), every one `state: unverified` with `kind` absent — exactly
T02's contract. The schema, the identity function, the parser, the seeding, and the
lint's *final*-state behaviour are all proven. Gate 2 is not building on sand; it is
building on a floor with two holes that gate 1's own close located precisely.

**Nothing here weakens "a `broad` oracle's green is never carried forward."** T07's
criterion 5 asserts it for `attempt == current` as well as for a stale attempt — a
`broad` entry is routed to re-verification unconditionally, without an attempt
comparison, which is strictly stronger than the lint T03 shipped. T08's criterion 6
asserts it again at the render layer. If either cannot hold, both WUs' escalation
triggers say `blocked`, not "reconcile".

## What this session changed in a not-yet-reached part of the plan

Surfaced here rather than applied silently, per `WU-91` criterion 8.

1. **`GATE-02.md`'s `## Definition of done` is rewritten, not edited.** Two bullets
   were added that the draft-time proposal could not have contained (T05's survival,
   T06's initial-state lint), one bullet was merged into another, and one was
   answered with "the mechanism already exists — build nothing." The bullet-by-bullet
   disposition table is in `GATE-02.md`. Only one bullet is inherited **unchanged**:
   the feature-level-question exclusion, marked deliberately accepted because nothing
   gate 1 observed argues against it and `PLAN.md` § *Notes* names it load-bearing.

2. **`WU-90-gate-2-close.md`'s body was a placeholder and is now written against
   gate 2's actual work.** Its scaffolded criteria said `G1-PLAN` would replace them.
   Twelve criteria now; the `close-discipline.md` obligations are unchanged in
   substance, and criteria 2, 3, 6, and 9 are new or materially rewritten.

3. **`GATE-02.md` gains `cost_budget_usd: 23.00`.** Sum of the gate's WU estimates
   ($3.00 + $3.00 + $3.00 + $4.00 + $5.00 = $18.00) plus one re-attempt of its
   largest ($5.00, `G2-CLOSE` at the `planning-discipline.md` §5 `close` floor). The
   §5 corollary's shape exactly.

4. **`PLAN.md`'s frontmatter `planned_cost_usd` was raised from $28.00 to $41.00.**
   The $28.00 figure predates gate 2 having any work units at all; the two gates' WU
   estimates now sum to $41.00 ($12.50 gate-1 producing + $10.50 gate-1 closing +
   $18.00 gate 2), and `lint_plan.py` flags a >10% divergence between the two. It is
   a re-derivation from the WU estimates, not a re-forecast: nothing about the work
   got more expensive, the plan simply now has the units it was always going to have.
   The number to judge the feature against is still the two gate `cost_budget_usd`
   values, and gate 1 actually spent $6.99 on its producing units — 44% under plan —
   so $41.00 is very likely high. `G2-CLOSE`'s criterion 5 reconciles against the
   gate budgets and names this change. **Reject it and revert to $28.00 if you
   consider a feature-level planned cost a fixed baseline that `plan-next` should not
   move**; the WARN it produces is warn-only.

5. **`PLAN.md`'s gate-2 graph carries a comment marking the driver restart between
   `T08` and `G2-CLOSE`.** A comment, because the restart is not a work unit and
   there is nothing in the graph schema that represents an operator action. It is
   enforced by `G2-CLOSE` criterion 2, not by the comment.

6. **Not fixed, not gate 2's, recorded so it does not evaporate:**
   `closing_requirements.consumer_visible_section_is_na` classifies a §3 section by
   substring, so a real enumeration that quotes the exemption line is read as exempt.
   Gate 1's close tripped it on its first draft and rewording flipped it back. It
   belongs to FEAT-2026-0064. `G2-CLOSE`'s criterion 9 warns its session about it
   rather than relying on the same luck.

## Predecessor gate's §4 probe

`GATE-01.md` § *Arming probe result (§4)* left its post-change section unfilled. Gate
1's close ran the sweep and found the arming baseline had been measured with the
installed `specfuse-lint` console script, which resolves `specfuse.loop` from
`site-packages` (0.7.1) — a build containing no `close-l`, no
`close-intermediate-f`, and no `criteria_state` module. The re-run from source
reached the same verdict (zero findings attributable to the two new requirements)
for a reason nobody had checked: no feature carries a criteria artifact, so
`applies_when` short-circuits before any differing code is reached. **The sweep would
have reported identically had T03 shipped nothing.**

That is why `GATE-02.md`'s §4 probe for `T06` is specified with four parts including
a positive control, and why every sweep criterion in gate 2 names the
`.specfuse/scripts/` shim explicitly. `GATE-01.md` itself is not edited — gate 1 is
closed and `plan-next` does not touch a passed gate.

## Cross-repo contracts

None. Every value gate 2's work units name — `ORACLE_KINDS`, `CRITERION_STATES`,
`criterion_id_for`'s `<sub_id>#<ordinal>` shape, `close-l` /
`close-intermediate-f`, `applies_when="criteria_artifact_present"`,
`_clean_attempt_untracked`, `reset_preserving_events`, `execute_unit_attempt`,
`format_oracle_capture` — was read from this repo's working tree while drafting, and
the line numbers cited in the WU bodies are from that read. No value is invented from
another system's vocabulary, so `/authoring-work-units` §8's table has no rows.

## Red-test coverage

`WU-91` criterion 4: every behaviour-introducing implementation WU names a scoped
test that fails on HEAD before it runs. All four do; none takes the
`Red-test exempt:` carve-out.

| WU | Red test (criterion 1 in each) | Green (last criterion) |
|---|---|---|
| `T05` | `tests/test_loop_criteria_survival.py::test_criteria_artifact_survives_attempt_reset` | ✓ |
| `T06` | `tests/test_lint_closing_criteria_pristine.py::test_pristine_seeded_entry_is_not_a_finding` | ✓ |
| `T07` | `tests/test_criteria_worklist.py::test_broad_pass_never_carries_forward` | ✓ |
| `T08` | `tests/test_loop_worklist_injection.py::test_close_dispatch_prompt_carries_worklist` | ✓ |

`T05`'s escalation triggers additionally treat a red test that *passes* on HEAD as a
block rather than a convenience — the tautology guard from
`[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/survival-needs-the-whole-path-set]` rule (b),
which is the rule gate 1's own survival test violated.

## Cost

| Work unit | planned | why |
|---|---|---|
| `T05` survival carve-out | $3.00 | Driver reset path, small change, careful negative-observation test. |
| `T06` pristine-entry skip | $3.00 | One predicate plus a four-part probe; gate 1's comparable lint unit (`T03`) cost $2.31. |
| `T07` worklist partition | $3.00 | Pure function, no wiring. Gate 1's comparable pure-data unit (`T01`) cost $0.60 against $3.00, so this is likely over-estimated in the same direction. |
| `T08` prompt injection | $4.00 | The only unit doing structural wiring across two modules and a seam test. Gate 1's structural units came closest to their estimates. |
| `G2-CLOSE` | $5.00 | `planning-discipline.md` §5 `close` floor, not raised to absorb a retry. |
| **sum** | **$18.00** | |
| **`cost_budget_usd`** | **$23.00** | sum + one re-attempt of the largest WU (§5 corollary). |

Gate 1's producing units came in 44% under plan and the two that did structural work
were closest to estimate — so `T08` is the estimate to trust and `T07` the one most
likely to overshoot downward. The budget is padding for a known-open defect
(first-attempt closing-WU success runs 51–74%), not a prediction that `G2-CLOSE`
retries.

## Reflection notes

<Written by the human at review time.>
