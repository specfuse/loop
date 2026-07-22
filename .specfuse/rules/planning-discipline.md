<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: planning discipline

Encodes hard-won discipline from feature retrospectives — the checks that, applied
at design and arming time, would have prevented the most expensive re-plans. Each
check below is cheap (a grep, a sentence, a table, one local run) and guards a
failure mode that cost multiple gates when skipped. Provenance is named per check so
the reasoning survives the rule.

These are **binding at draft, plan-next, and arm time**. A gate armed in violation
of any check is not ready, regardless of what a WU's frontmatter says.

## 1. Existing-mechanism search — before designing any enforcement or measurement

Before an ADR designs a validation rule, a severity level, an enforcement gate, or a
measurement, it must first establish that the mechanism does not already exist. The
ADR is **incomplete** without this section.

- **Grep the inventory.** For a validation rule:
  `grep -rl <concept> src/main/java/.../validation/rules/`. For an artifact:
  `java -jar specfuse-generator.jar templates`. For any check: the directory that
  holds its siblings.
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

`plan-next` and `close` / `close-intermediate` WUs are systematically under-estimated.
When drafting their `planned_cost_usd`, use a **floor of $5.00** — never the $2–3 that
"it's just bookkeeping" suggests. A gate `cost_budget_usd` set to the sum of $2–3
planning estimates is a brake that fires by construction on the first real close.

> **Provenance (FEAT-2026-0049 + LEARNINGS [FEAT-2026-0044]).** Planning/close WUs ran
> 2.8–5.2× their $2–3 estimates: `plan-next` at $5.90 and $15.65, `close-intermediate`
> at $5.67, against $2–3 drafts. LEARNINGS `[FEAT-2026-0044]` had already predicted this
> systematic under-estimation; the floor makes the prediction binding.

## Why these live together

Each is a one-time check that trades a minute at design/arm time against a gate (or
three) of rework. They share a root: **automation and authors both trust a claim
without the cheap check that would test it** — a grep not run (§1), a contradiction not
read (§2), a scope not tabled (§3), a suite not run (§4), an estimate not calibrated
(§5). State the check, run it, record the verdict. Every plan, every arm.
