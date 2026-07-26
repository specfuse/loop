<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: planning discipline

Encodes hard-won discipline from feature retrospectives — the checks that, applied
at design and arming time, would have prevented the most expensive re-plans. Each
check below is cheap (a grep, a sentence, a table, one local run) and guards a
failure mode that cost multiple gates when skipped. Provenance is named per check so
the reasoning survives the rule (the FEAT-2026-0049 / F1–F4 references resolve in the
retrospective of the specfuse-generator dogfood feature that motivated these checks).

These are **binding at draft, plan-next, and arm time**. A gate armed in violation
of any check is not ready, regardless of what a WU's frontmatter says.

## 1. Existing-mechanism search — before designing any enforcement or measurement

Before an ADR designs a validation rule, a severity level, an enforcement gate, or a
measurement, it must first establish that the mechanism does not already exist. The
ADR is **incomplete** without this section.

- **Grep the inventory.** Search the directory that holds the mechanism's
  siblings — for a validation rule, the project's rules directory (e.g.
  `grep -rl <concept> <path/to/validation/rules/>`); for an artifact, the
  tool's own inventory command (e.g. `<tool> templates`); for any other
  check, the directory that holds its siblings.
- **Record the grep command and its verdict** in the ADR — the exact command, and
  either "no existing mechanism, building new" or "found `<X>`, reusing / extending
  it". A verdict of "reusing" that then builds new anyway must say why.
- **Read the javadoc/description of anything the grep surfaces.** A rule that already
  covers the property may say so in its own words.

> **Provenance (FEAT-2026-0049 / F3).** The feature spent three gates building a
> `WARNING→ERROR` ladder on a new rule while the enforcement it needed already existed
> in `RelationshipSymmetryValidationRule` — whose javadoc (F-029, 2026-05-29) literally
> said the debt "surfaces as a Saturday-night surprise when the inference rule changes."
> A one-line grep of the rules directory at ADR time would have found it. Cost: two
> gates and a full pivot.

## 2. Escalation-predicate satisfiability — for any severity flip

Any plan that raises a check to `ERROR`, flips a `WARNING` to blocking, or asserts a
"zero issues" close predicate must answer, in writing, one question:

> **What does this rule report on a spec/input already in its intended final state?**

If the answer is anything other than **zero**, the predicate is **unsatisfiable** —
the rule fires on correct inputs, so "zero issues" can never be reached and the
severity flip forces wrong changes. **Stop and redesign** before arming: fix the rule
so a correct input reports zero, or route enforcement to a different mechanism (see §1).

> **Provenance (FEAT-2026-0049 / F3).** ADR D3 ("omission = intent — a non-owning
> reference is declared by omission") and D6 ("`ERROR` when the rule reports zero
> issues") contradicted each other inside the same document: post-flip, every correct
> omission still tripped the rule, so "zero" was unreachable. The contradiction was
> answerable by reading the ADR against itself. Separately, the *shipped* rule
> false-positived ~35 of 49 on real specs (#821) — a severity flip forcing wrong
> changes, exactly what this check prevents.

## 3. Flag-scope table — for any WU introducing or flipping a behavior flag

A WU that introduces, gates on, or flips a behavior flag must contain a **flag-scope
table**: every code path the flag is claimed to affect, marked *gated* / *not gated*,
with a one-line *why* per row. The arming review checks the feature's headline claim
("the flip retires inference", "the flag makes X strict") against the table — a claim
the table does not support is a scope mismatch, and scope mismatches surface gates
later as defects, not at arming.

| Code path | Gated by flag? | Why |
|---|---|---|
| `<path/method>` | yes / no | <one line> |

> **Provenance (FEAT-2026-0049 / F1).** The plan enumerated both inference paths
> (bare-FK and `$ref`) on day one, but no document ever crossed "which paths does the
> `explicitRelationshipsOnly` flag gate" against "the flip retires inference." The flag
> was built FK-path-only, deliberately and correctly — but the mismatch with the
> headline claim surfaced two gates later (F1), and again as a runtime defect (F4).

## 4. Runtime probe before arming a default/severity flip

A gate whose WUs flip a **default value** or a **severity** may **not** be armed on
"mechanical, nothing design-open." Before arming, apply the change locally and run the
**exact command the WU's tests gate will run** (the full oracle, not a subset), and
paste the resulting failure list into the gate review. The probe is the arming
evidence; "nothing design-open" without it is a claim, not a fact.

- Run the *full* oracle. A subset hides failures in the paths the change touches that
  the subset does not exercise.
- The probe's failure list becomes the WU's enumerated test surface — the WU no longer
  discovers its own breakage attempt by attempt.

> **Provenance (FEAT-2026-0049 / F4).** Gate 4 was armed on "nothing is design-open"
> without ever applying the default flip and running the full suite once. The WU then
> spun three times (~$14) on a real defect that one local run exposed in seconds — and
> the first two diagnoses were made against a *subset*, missing failures the full suite
> showed. Contrast: an earlier gate's "measure before drafting" probe (a `WARNING` run
> over the real specs) worked and correctly shrank the next WU's scope.

## 5. Planning-WU cost floor

`plan-next` and `close` / `close-intermediate` WUs are under-estimated by the $2–3 that
"it's just bookkeeping" suggests, and they do not all cost the same. When drafting their
`planned_cost_usd`, use these floors:

| WU type | floor | observed median | observed p90 |
|---|---|---|---|
| `plan-next` | **$6.00** | $3.57 | $6.10 |
| `close` | **$5.00** | $2.73 | $5.42 |
| `close-intermediate` | **$4.50** | $2.01 | $4.34 |

Each floor sits at roughly the **p90 of attempts that passed** — generous enough that a
normal draft is not immediately over, tight enough that a gate budget summed from them is
not fiction.

**A closing-WU retry is a defect to diagnose, not a cost to budget for.** The temptation is
to raise these floors until they absorb a second attempt. Do not: **28% of all closing-WU
spend is currently burned on attempts the driver refused**, and a floor sized to swallow
that makes the refusals invisible and permanent. If a closing WU retries, read the failure
class and fix the cause — most of them are guard-contract mismatches, not hard work.

**Corollary for `cost_budget_usd`.** Set a gate's budget to the **sum of its WU estimates
plus one re-attempt of its largest WU**. This is deliberately *defensive rather than
correct*: first-attempt success on closing WUs runs 51–74%, so a budget with no headroom
halts gates routinely. It is padding for a known-open defect, not a statement that retries
are normal — revisit it when the guard-contract gap closes.

> **Provenance — 158 closing WUs across 9 repositories**, deduplicated on
> `(correlation_id, timestamp)` from every `.specfuse/features/*/events.jsonl`. Costs are
> for attempts that **passed**; failed attempts are counted as waste, not as cost.
>
> | WU type | WUs | first-try | median | p90 | max |
> |---|---|---|---|---|---|
> | `plan-next` | 62 | 74% | $3.57 | $6.10 | $7.83 |
> | `close` | 61 | 69% | $2.73 | $5.42 | $11.44 |
> | `close-intermediate` | 35 | 51% | $2.01 | $4.34 | $6.85 |
>
> **This table replaces two earlier revisions of §5 that were each derived from a single
> feature.** The first set a flat $5.00 floor from FEAT-2026-0049; the second raised it to
> $12.00/$8.00 from FEAT-2026-0069, whose `plan-next` cost $16.44 — **4.6× the median of
> 62 observations.** Both generalised a rule from an outlier, which is the failure
> `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` names for plans and which applies at least as
> strongly to rules. A floor is a distribution question; answer it with a distribution.
>
> **Where the money actually goes.** Of $794.18 total closing-WU spend, **$221.72 (28%)
> was spent on refused attempts.** Three driver guards whose exact format requirements
> appear in **no authoring surface** account for $99.30 of that — 45% of all waste:
> `assert_gate_review_exists` ($53.11), `assert_failure_class_breakdown_when_failures_present`
> ($23.70), `assert_retrospective_gate_section` ($22.49). By contrast
> `assert_verdict_well_formed` fired 10 times for **$0.00**, because it is checked before
> the agent spends anything. The improvement lever is the guard contracts and when they are
> checked — not the floor.

## Why these live together

Each is a one-time check that trades a minute at design/arm time against a gate (or
three) of rework. They share a root: **automation and authors both trust a claim
without the cheap check that would test it** — a grep not run (§1), a contradiction not
read (§2), a scope not tabled (§3), a suite not run (§4), an estimate not calibrated
(§5). State the check, run it, record the verdict. Every plan, every arm.
