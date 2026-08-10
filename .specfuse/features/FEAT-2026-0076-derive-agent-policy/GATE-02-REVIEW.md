---
gate: 2
open_questions:
  - "Accept the shipped-baseline comparison as gate 2's provenance mechanism? T04/T05/T06 are drafted on it; choosing the provenance-recording shape instead means redrafting all three and widening PLAN.md's scope boundary."
  - "File the provenance-recording shape as a successor feature (a roadmap row), or drop it? The recommendation below declines it for this feature but does not decide its future."
human_only: true
---

# Gate 2 review — the arming decision

Drafted by `FEAT-2026-0076/G1-PLAN` on 2026-08-10, against what gate 1 actually
learned. Nothing here is armed: every gate-2 work unit ships `status: draft` and
`GATE-02.md` still reads `status: open`. This feature runs
`autonomy_default: review` **specifically** so you read this before arming
(`PLAN.md` decision 4) — that checkpoint is the reason the gates were staged at
all.

---

## The provenance question

`PLAN.md` left one question deliberately undecided, and gate 1's close was told
to produce the input for it:

> **How does review tell an agent-chosen default from a deliberate operator
> choice?**

### What gate 1 reported — the count that decides it

**3 of 4 values derivable on a realistic repository unaided; 4 of 4 with the
`gh` runner the skill's prose tells the operator to inject.** Measured against
this repository's own root, 284 completed work units of real history:

| value | derived? | proposed | live value | evidence class |
|---|---|---|---|---|
| `budgets.max_tokens_per_run` | yes | 873,000 | 2,000,000 | p90 cost over 214 passing attempts, **converted** at 200,000 tokens/$ with 1.5x headroom |
| `budgets.max_items_per_day` | yes | 28 | 10 | 284 completed WUs, **converted** through a 10%-of-volume heuristic |
| `rules.bugs.test_paths` | yes | `['tests/']` | *absent* | directly read: tree and `verification.yml` gate commands agree |
| `budgets.max_open_prs` | only with a runner | 3 unaided / count+2 with one | 3 | live `gh pr list`; withheld entirely with no runner |

### The recommendation

**Take the comparison shape — but widened to the *shipped baseline*, not the
`DEFAULT_*` constants alone. No schema change.**

This is the first of `PLAN.md`'s two shapes, corrected by something gate 1
surfaced that was not visible at drafting. It is a third shape only in the sense
that the original phrasing of shape 1 does not work as written.

**The reason, stated as the count.** 3 of 4 derivable means the *proposal* — not
the provenance classification — carries most of review's signal. Review's job is
to put the current value next to what the evidence now suggests and let the
operator judge; provenance is the secondary hint that tells them whether anyone
ever looked. With three of four values carrying live evidence, and the fourth
recoverable by injecting a runner, the cheap comparison covers the surface that
matters. The expensive, accurate mechanism would buy precision on the hint while
the primary signal was already available for free.

Two further findings from gate 1 push the same way:

1. **The proposals disagree with the live values by enough that the distinction
   is secondary.** 873,000 vs 2,000,000 (2.3x) and 28 vs 10 (2.8x). Review will
   surface both whichever mechanism is chosen. The mechanism only decides
   whether it can also say *why* the current value is what it is.
2. **Where the comparison is lossy, it is lossy in the harmless direction.**
   This repository's three budget values are byte-identical to
   `.specfuse/agent-policy.yml.example` — every one of them is the example's
   value, unedited. The lossy case is an operator who *deliberately* chose a
   value equal to the shipped one; in exactly that case the review shows the
   same delta, the operator says "yes, I chose that", and nothing is lost but a
   sentence.

### Why "shipped baseline" and not "`DEFAULT_*` constants"

Gate 1's retrospective is blunt about it, and this is the correction that makes
shape 1 viable at all:

> **The "compare against the shipped `DEFAULT_*` constants" option is not
> implementable for three of the four keys.** `agent_policy.py` defines exactly
> three constants — `DEFAULT_MAX_DIFF_LINES`, `DEFAULT_MAX_MERGES_PER_DAY`,
> `DEFAULT_TEST_PATHS`. The three `budgets` keys are *required* fields with no
> constant at all.

Verified independently while drafting (`grep -n "^DEFAULT_"
specfuse/loop/agent_policy.py` returns exactly those three lines). Of the four
in-scope keys, the constants cover **one** — `rules.bugs.test_paths`, via
`DEFAULT_TEST_PATHS`. A mechanism built on them alone would silently say nothing
about the three budget keys, which are the keys with the interesting deltas.

So the baseline is the **union of two sources**, recorded per key so a reader
knows which one answered:

| in-scope key | baseline source |
|---|---|
| `rules.bugs.test_paths` | `agent_policy.DEFAULT_TEST_PATHS` |
| `budgets.max_tokens_per_run` | `.specfuse/agent-policy.yml.example` |
| `budgets.max_items_per_day` | `.specfuse/agent-policy.yml.example` |
| `budgets.max_open_prs` | `.specfuse/agent-policy.yml.example` |

### The honesty condition the recommendation depends on

The comparison is a **hint, and asymmetric**. The drafted work units carry this
as a hard requirement rather than a nicety, because a classification an operator
over-trusts is worse than none:

- *Differs from the shipped baseline* → someone chose it. **Reliable.**
- *Matches the shipped baseline* → probably nobody chose it. **Lossy**, and the
  caveat must ride along in the returned data (T04 criterion 5) and in the prose
  (T05 criterion 5). Review says "this matches the shipped default, so it may
  never have been decided" — never "this was never decided".

## Scope boundary — the shape not taken

The alternative, **recording provenance when a value is written**, is accurate
and is a **schema change**. `PLAN.md` § *Scope boundary* puts it out:

> **OUT — the schema and its validation.** `agent_policy.py` owns
> `validate_agent_policy` and the `DEFAULT_*` constants. This feature *consumes*
> them to propose values; it does not extend the schema. A new dial is the
> feature that introduces it, not this one.

**This recommendation does not cross that boundary, and gate 2 as drafted does
not need it crossed.** Stated plainly because criterion 3 of `G1-PLAN` exists to
prevent the opposite — a plan that quietly widens scope and lets the widening
surface as a defect two gates later.

If you prefer the provenance-recording shape, it needs **one of two things, and
neither is a work unit's to grant**: you widen `PLAN.md`'s scope boundary
explicitly, or it becomes its own feature. The recommendation here is the
second — file it as a successor roadmap row. It is a genuinely better mechanism
and gate 1's numbers do not justify paying for it inside this feature; that is a
different trade-off from "it is not worth doing." Open question 2 is that
decision, and it is yours.

**Choosing it instead means redrafting T04, T05, and T06.** They are written
against the comparison shape throughout — do not arm them and expect them to
absorb a schema change.

---

## What is drafted

Three substantive work units, inserted **above** the existing `G2-CLOSE`
placeholder, whose `depends_on` and acceptance criteria are now filled in. The
shape deliberately repeats gate 1's — code, then prose describing the code, then
a fence on the prose — because that decomposition produced four first-attempt
passes.

| WU | file | type | depends on | planned | what it does |
|---|---|---|---|---|---|
| `T04` | `WU-04-policy-review.md` | implementation | — | $3.50 | `review_agent_policy` in a new `specfuse/loop/policy_review.py`: reads an existing policy file, returns per-key current / proposed / baseline / classification |
| `T05` | `WU-05-review-mode-prose.md` | implementation | T04 | $3.50 | the review half of `SKILL.md` + `PROMPT.md`, with a structural test naming T04's API as exact literals |
| `T06` | `WU-06-non-clobber-invariant.md` | implementation | T05 | $2.50 | fences review mode against writing `queue`/`version`/`rules.triage` and against dropping keys the file carries |
| `G2-CLOSE` | `WU-90-gate-2-close.md` | close | T04, T05, T06 | $5.00 | terminal close (pre-existing placeholder, criteria now filled in) |

**Red-test-first (`/authoring-work-units` §12).** All three implementation WUs
introduce behaviour and each names a scoped test that fails on HEAD; none takes
the exemption. T04 → `tests/test_policy_review.py::TestReviewAgentPolicy::test_baseline_match_is_classified_and_caveated`
(module and test file both absent). T05 →
`tests/test_derive_agent_policy_review_mode.py::TestReviewMode::test_prose_names_review_api_literals`
(test file absent). T06 →
`tests/test_agent_policy_key_ownership.py::TestReviewModePreservation::test_review_mode_states_non_clobbering`
(statement absent from the prose).

**Cost.** $14.50 drafted + $5.00 (one re-attempt of the largest, the close) =
`GATE-02.md` `cost_budget_usd: 19.50`, per `planning-discipline.md` §5's
corollary. `PLAN.md`'s `planned_cost_usd` moves $29.00 → **$38.50**, and its
§ *Notes* now records both moves rather than carrying the stale $27.00 gate 1's
close flagged.

The estimates are deliberately below gate 1's equivalents (T01 $4.50 → T04
$3.50; T02 $5.00 → T05 $3.50). Gate 1's implementation WUs came in at ~40% of
estimate — "the estimate priced the novelty of the goal; the spend reflected the
maturity of the parts" — and gate 2's parts are more mature still: `T04`
composes a `propose_policy_defaults` that now exists, and `T05` extends a
`SKILL.md` rather than creating one. T06 is held at $2.50 against T03's $2.00
because T03 is the one gate-1 unit that went **over** (+27.2%), and it is the
same kind of work.

## Planning-discipline checks (`.specfuse/rules/planning-discipline.md`)

**§1 Existing-mechanism search.** Commands run while drafting:

- `grep -rn "review_agent_policy\|policy_review" specfuse tests plugins .specfuse` → no hits
- `grep -rn "agent-policy.yml.example" specfuse/ .specfuse/scripts/` → no hits
- `grep -n "^DEFAULT_" specfuse/loop/agent_policy.py` → exactly three constants

**Verdict:** *two mechanisms consumed, the baseline-comparison layer built new.*

| Surface gate 2 needs | Existing mechanism | Verdict |
|---|---|---|
| Evidence-backed proposals to compare against | `policy_proposals.propose_policy_defaults` | **reuse** — T04 |
| A baseline for `test_paths` | `agent_policy.DEFAULT_TEST_PATHS` | **consume, do not extend** — T04 |
| A baseline for the three `budgets` keys | none — nothing in `specfuse/` reads `.specfuse/agent-policy.yml.example` programmatically | **building new** — T04 |
| Disjoint-key boundary + its test | `tests/test_agent_policy_key_ownership.py` (T03) | **extend** — T06 |
| Skill structure and drafting posture | `derive-agent-policy` `SKILL.md`/`PROMPT.md` (T02) | **extend** — T05 |

**§2 Escalation-predicate satisfiability.** Gate 2 raises no check to `ERROR`
and flips no severity. It adds no validation rule; `validate_agent_policy` is
consumed unchanged. Not applicable.

**§3 Flag-scope table.** No behaviour flag is introduced, gated on, or flipped.
Omitted per the rule.

**§4 Runtime probe before arming a default/severity flip.** No gate-2 work unit
flips a default value or a severity. T04 adds a module, T05 and T06 add prose
and tests; nothing changes an existing threshold. No probe is owed. **Note the
easy misreading:** T04 *reads* `DEFAULT_*` and the example file's values — it
changes neither, and this repository's own `.specfuse/agent-policy.yml` is on
every drafted WU's do-not-touch list.

## Cross-repo contracts (`/authoring-work-units` §8)

The rule's warning is that a `plan-next` draft confidently invents plausible
cross-surface values it cannot see. Every value gate 2's drafts name is
in-repository and was checked against its source while drafting:

| Value named in a draft | Authoritative source | Checked |
|---|---|---|
| `propose_policy_defaults(repo_root=None, *, runner=None)` | `specfuse/loop/policy_proposals.py:58` | ✅ signature read |
| `DEFAULT_TEST_PATHS`, `DEFAULT_MAX_DIFF_LINES`, `DEFAULT_MAX_MERGES_PER_DAY` | `specfuse/loop/agent_policy.py:77-83` | ✅ exactly these three |
| `validate_agent_policy` | `specfuse/loop/agent_policy.py:186` | ✅ |
| Top-level keys `version`, `queue`, `rules`, `budgets`, `escalation` | `agent_policy.REQUIRED_TOP_LEVEL_FIELDS` | ✅ |
| `.specfuse/agent-policy.yml.example` carries the three `budgets` keys | the file itself | ✅ read; live file byte-identical on all three |
| `specfuse/loop/policy_review.py`, `review_agent_policy` | **minted here** — grep confirms both names are unused | ✅ free |
| `tests/test_policy_review.py`, `tests/test_derive_agent_policy_review_mode.py` | **minted here** — neither exists | ✅ free |
| `scripts/sync-scaffold.sh` is the vendoring path | `PLAN.md` § *Notes*; `tests/test_skills_vendored_in_sync.py` | ✅ |

Nothing in gate 2 crosses a repository boundary, so there is no value here that
could only be verified in another repo.

## Before you arm — a checklist

1. **Answer open question 1.** Accept the shipped-baseline comparison, or send
   T04–T06 back for a redraft against the provenance-recording shape (and widen
   `PLAN.md`'s scope boundary if you do).
2. **Answer open question 2.** File the provenance-recording shape as a
   successor roadmap row, or decide it is not wanted.
3. **Read T04's criteria 5–7.** They are the honesty conditions the whole
   recommendation rests on. If you would rather review just print the numbers
   without a classification at all, say so now — it makes T04 smaller, not
   larger.
4. Flip `T04`, `T05`, `T06` and `G2-CLOSE` from `draft` to `pending`, flip
   `GATE-01.md` to `passed`, and use `/arm-gate` rather than editing by hand.
5. Write your reflection into `GATE-01.md` § *Reflection notes* — it is
   currently the template placeholder.

## Doubt

Three things I am not confident about, recorded rather than smoothed over.

**The strongest argument against my own recommendation.** The count says "most
values are derivable", and I read that as "comparison suffices." The opposite
reading is available and is not silly: what gate 1 actually found is that *every
budget value in the file that motivated this feature is the shipped example's
value, unedited, and `test_paths` is absent entirely*. On that reading the file
has no operator intent in it to protect, the provenance mechanism has nothing to
distinguish yet, and the comparison shape is being chosen because the hard case
does not exist in the sample rather than because it handles it. The failure mode
lands later, on a repository where someone *has* tuned their budgets — and there
the lossy direction stops being harmless. I still recommend comparison, because
a cheap mechanism shipped now can be replaced by the accurate one when a
tuned-file case actually appears, and the reverse ordering costs a schema
migration. But the count is weaker evidence than its precision suggests: it is
one repository's history, and it is this repository's.

**Two of the three derived values are conversions, not measurements.**
`max_tokens_per_run` converts cost at an assumed 200,000 tokens/$; 
`max_items_per_day` applies a 10%-of-volume heuristic to a total with no per-day
breakdown behind it. Gate 1 disclosed both in the evidence strings, correctly.
But review mode puts a converted number next to the operator's real one and
invites a correction — and "3 of 4 derivable" quietly counts two conversions as
derivations. If you think a converted proposal should be presented differently
from a measured one (`test_paths` is the only directly-read value of the four),
that is a change to T05's readout and it is cheaper to ask for now than after
T04 lands.

**A lint WARN you will see and should not be alarmed by.** T06 declares
`produces: tests/test_agent_policy_key_ownership.py`, which T03 already
delivered as a `done` WU, so `check_produces_satisfiability` will emit a WARN.
It is informational, `lint_plan.py` still exits 0, and the alternative —
splitting the review-mode ownership assertions into a separate suite from the
ownership suite they belong to — would be worse structure bought for a quieter
lint. Flagged so it does not read as an oversight at arming time.

## Not blocking, but worth your attention

Gate 1 measured this repository's own policy file against the proposals and
found `max_tokens_per_run` 2.3x and `max_items_per_day` 2.8x above what the
evidence suggests, with `rules.bugs.test_paths` absent. `PLAN.md` § *Scope
boundary* puts changing those values **out** of this feature — it is your call,
made after the named operator run, not a work unit's. Recorded here only so the
numbers are in front of you at the same time as the mechanism that produced
them.
