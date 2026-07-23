---
feature_id: FEAT-YYYY-NNNN
title: <short feature title>
slug: <feature-slug>
branch: feat/FEAT-YYYY-NNNN-<feature-slug>
roadmap_goal: <one line copied from the roadmap — the north star this feature serves;
  plan-next anchors every drafted gate to this and flags if a retrospective implies
  it should change>
autonomy_default: review        # auto | review | supervised
status: active                  # active | deferred | done | abandoned
                                # deferred = parked pending an external decision/dependency; resumable, non-dispatchable
# planned_cost_usd: 0.00        # OPTIONAL — sum of WU planned costs; lint warns when missing or when delta from WU sum > 10%
---

# Plan: <short feature title>

<One or two paragraphs of human-facing intent. The work units carry the executable
detail; this is the why.>

This file owns the **shape** of the feature: the gate order, which work units belong
to each gate, and the dependency edges between them. It does **not** own status —
each WU file owns its own status, and each GATE file owns its gate's status. Detail
only as far as the next gate; plan-next drafts the gate after that from the
retrospective and lessons.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

Before any ADR or gate designs a validation rule, a severity level, an enforcement
gate, or a measurement, establish that it does not already exist. **An ADR without
this section is incomplete.** If this feature designs no such mechanism, write
exactly `n/a — no enforcement or measurement designed` and stop — do not fabricate
a grep to fill the section.

- **Grep command run:** `<the exact command — e.g. grep -rl <concept>
  src/main/java/.../validation/rules/>`
- **Verdict:** `<"no existing mechanism, building new" | "found <X>, reusing/extending">`
- **If reusing:** name `<X>` and quote the line of its javadoc/description that
  confirms it covers the property. If building new despite a hit, say why the hit does
  not suffice.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

If this feature raises a check to `ERROR`, flips a `WARNING` to blocking, or asserts a
"zero issues" close predicate, answer here:

- **What does the rule report on an input already in its intended final state?**
  `<answer>`
- If that answer is **not zero**, the predicate is unsatisfiable — the rule fires on
  correct inputs. **Redesign before drafting gates:** fix the rule so a correct input
  reports zero, or route enforcement to the mechanism found in the search above.

## Task graph

```yaml
# Closing shape (FEAT-2026-0015):
#   Non-terminal gate (gate 1): 2-WU → close-intermediate + plan-next.
#   Terminal gate (gate 2): 1-WU → close.
#   Gate 2's WUs are drafted by gate 1's plan-next; scaffold them here so
#   lint can identify gate 1 as non-terminal from the start.
#   Legacy 4-WU sequence (RETRO/LESSONS/DOCS/PLAN) is accepted by lint but emits WARN.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-YYYY-NNNN/T01
        file: WU-01-<slug>.md
        depends_on: []
      - id: FEAT-YYYY-NNNN/T02
        file: WU-02-<slug>.md
        depends_on: [FEAT-YYYY-NNNN/T01]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-YYYY-NNNN/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-YYYY-NNNN/T01, FEAT-YYYY-NNNN/T02]
      - id: FEAT-YYYY-NNNN/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-YYYY-NNNN/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # --- closing sequence: 1-WU close (terminal gate) ---
      # Scaffold this now so lint can identify gate 1 as non-terminal.
      # G1-PLAN fills in the substantive WUs above this entry when gate 1 completes.
      - id: FEAT-YYYY-NNNN/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on: []   # G1-PLAN will set real depends_on when it drafts gate 2
```

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never needs to
  know its own dependencies — they are satisfied by the time the driver hands it the
  file. Deps are scheduling metadata, and scheduling is the driver's job.
- WU file numbers track the correlation sub-ID where it exists (`WU-07` ↔ `/T07`).
  Closing units use a reserved high range (90+) so they sort last.
