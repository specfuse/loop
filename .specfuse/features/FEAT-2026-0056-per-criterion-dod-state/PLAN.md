---
feature_id: FEAT-2026-0056
title: Per-criterion DoD state + incremental re-close
slug: per-criterion-dod-state
branch: feat/FEAT-2026-0056-per-criterion-dod-state
roadmap_goal: Each close attempt records per-criterion pass/fail state, and a re-dispatched close re-verifies only failed and newly-added criteria plus the oracles whose scope cannot be bounded.
autonomy_default: review
status: done
planned_cost_usd: 41.00   # re-derived by G1-PLAN once gate 2 had work units; see GATE-02-REVIEW.md
---

# Plan: Per-criterion DoD state + incremental re-close

A close returning `not_met` today throws away everything the previous close attempt
proved. The fix WUs land, the close is re-dispatched, and it re-verifies the entire
definition of done from scratch — the full test suite, the full regeneration, the
whole scenario matrix — including criteria that were green on the prior attempt and
whose inputs never changed. FEAT-2026-0066 ran G2-CLOSE three times and G3-CLOSE
across five attempts for $48.50 of close spend. Close attempts are the costliest
attempt type portfolio-wide ($4.2 average against $3.5 for implementation), and four
of the ten most expensive work units in the corpus are closes.

This feature gives a close a memory. Each close attempt writes a per-gate artifact
recording, per acceptance criterion, which oracle proved it, that oracle's exit code,
and the tree state it ran against. A re-dispatched close reads that artifact and
re-verifies only what it must.

**What "only what it must" means here is deliberately conservative, and the headline
number in the roadmap row was wrong.** See § *Scope decision: what invalidates a
cached green* below. Gate 1's T04 corrects the roadmap's benefit paragraph rather
than leaving a claim the design cannot reach.

This file owns the **shape** of the feature: the gate order, which work units belong
to each gate, and the dependency edges between them. It does **not** own status —
each WU file owns its own status, and each GATE file owns its gate's status. Detail
only as far as the next gate; plan-next drafts the gate after that from the
retrospective and lessons.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**

  ```
  grep -rniE 'criteri' specfuse --include='*.py'
  grep -rn 'verdict' specfuse/loop/closing_requirements.py specfuse/loop/gate_eval.py
  grep -rn 're_arm|rearm' specfuse/loop/loop.py
  ```

- **Verdict:** `found three adjacent mechanisms, extending them — no persisted
  per-criterion state exists.`

- **What the greps surfaced, and why each does not suffice on its own:**

  - `loop.py:3920 build_autoclose_debt_enumeration` already extracts per-criterion
    acceptance bullets from every substantive WU in a gate, via
    `_wu_sections.slice_acceptance_criteria` and `_DEBT_AC_ITEM_RE`. Its own
    docstring says it "only reads files the driver has already located" — it
    enumerates for a one-shot debt worklist and persists nothing. **T02 hoists this
    extraction so the new artifact and the debt enumeration share one parser rather
    than growing a second.**
  - `close-discipline.md` §2's hedged-verdict follow-up record, with
    `closing_requirements.FOLLOW_UP_KIND_MEANINGS`, `KIND_FIELD_RE`, and
    `verdict_ceiling_for_kinds`, is a per-entry classified record living inside a
    markdown artifact, regex-parsed and lint-enforced. That is structurally the
    same shape this feature needs. **It classifies why a criterion is unmet at
    terminal-verdict time; it carries no per-attempt pass state and no oracle
    identity.** T01 follows its shape rather than inventing a new one.
  - `re_arm_count` / `re_arm_history` / `folded_through_re_arm` and
    `rearm_reproduction_gate` (`loop.py:1752-1891`) are the existing re-dispatch
    state surface a close carries across attempts. **They account for cost,
    duration, and tokens across re-arms — nothing about verification outcomes.**
    T02 depends on this machinery's fold semantics, and specifically on the
    artifact surviving it.

  No mechanism anywhere persists pass/fail *per criterion* across close attempts,
  and nothing bounds an oracle's scope. That is what this feature builds.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

T03 introduces a new blocking `specfuse-lint --closing` finding, which is a severity
flip in §2's sense: a tree that lints clean today can lint dirty after it.

- **What does the rule report on an input already in its intended final state?**
  **Zero.** The requirement's `applies_when` is the existence of the gate's
  `GATE-NN-CRITERIA.md` artifact. A close in its intended final state has every
  entry carrying a recognized `kind:` and `state:`, and every `broad` entry proved
  by the current attempt — so the finding list is empty.

- **What does it report on the existing corpus?** **Zero, by construction.** No
  feature in `.specfuse/features/` has a criteria artifact, so the requirement does
  not fire on any of them. This is a claim, not yet a fact — and
  `[FEAT-2026-0055/G1-CLOSE]` is the lesson that says exactly this shape of claim
  reported `passed` on its first attempt and was wrong by 15 findings. So the sweep
  is an **arming precondition**, not something T03's session self-reports: `GATE-01.md`
  § *Arming discipline* requires the §4 runtime probe be run and its output pasted
  into the gate file before T03 is armed. A non-zero probe means T03 is mis-scoped
  and is re-drafted rather than absorbing the difference silently.

## Scope decision: what invalidates a cached green

The state unit is the **WU acceptance criterion**, and each entry records the oracle
command and exit code that proved it. Identical oracle commands run once per close
attempt rather than once per criterion.

Invalidation is by **oracle kind**, not by diff intersection:

- A `narrow` oracle has a knowable scope — a scoped test nodeid, a symbol-existence
  import, a structural assert, a grep with a countable output. Its green survives a
  re-close.
- A `broad` oracle does not — the full test suite, a full regeneration, a scenario
  matrix. **It re-runs unconditionally on every close attempt.**

Two alternatives were considered and rejected. **Path-intersection invalidation**
(each criterion records the paths its oracle covers, taken from the producing WU's
`produces` / `files_changed`) asserts something false: a test's true dependency set
is not the paths its WU wrote, so a change in `loop.py` can break a test whose WU
never named it. Its failure mode is a silent green on a criterion that would now
fail. **Diff-derived test selection** (map changed source paths to test modules, run
that subset as the regression check) is the only option that reaches the roadmap's
headline number, and it builds a second, weaker definition of the tests gate
alongside `verification.yml` — whose own header names that drift as how "six gates
ended up declared and never run."

**The honest consequence.** This repository's `tests` gate is
`python3 -m unittest discover -s tests -v -b` — one command, 2200 tests, no diff
awareness. It is a `broad` oracle and it re-runs every attempt. So the saving this
feature delivers is the per-criterion agent reasoning, the regeneration, and the
scenario matrix — **not** the suite, and therefore not "roughly halves close cost."
T04 corrects the roadmap row's `**Benefits.**` paragraph to what the design can
actually reach.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0056/T01
        file: WU-01-criteria-state-schema.md
        depends_on: []
      - id: FEAT-2026-0056/T02
        file: WU-02-precreate-criteria-artifact.md
        depends_on: [FEAT-2026-0056/T01]
      - id: FEAT-2026-0056/T03
        file: WU-03-criteria-state-lint.md
        depends_on: [FEAT-2026-0056/T01]
      - id: FEAT-2026-0056/T04
        file: WU-04-rules-templates-rebaseline.md
        depends_on: [FEAT-2026-0056/T01, FEAT-2026-0056/T02, FEAT-2026-0056/T03]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0056/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on:
          - FEAT-2026-0056/T01
          - FEAT-2026-0056/T02
          - FEAT-2026-0056/T03
          - FEAT-2026-0056/T04
      - id: FEAT-2026-0056/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0056/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0056/T05
        file: WU-05-criteria-artifact-survives-attempt-reset.md
        depends_on: []
      - id: FEAT-2026-0056/T06
        file: WU-06-pristine-entries-are-not-findings.md
        depends_on: []
      - id: FEAT-2026-0056/T07
        file: WU-07-reverification-worklist.md
        depends_on: [FEAT-2026-0056/T05]
      - id: FEAT-2026-0056/T08
        file: WU-08-worklist-reaches-the-close-session.md
        depends_on: [FEAT-2026-0056/T06, FEAT-2026-0056/T07]
      # --- closing sequence: 1-WU close (terminal gate) ---
      # OPERATOR STEP between T08 and G2-CLOSE: restart the driver. T05 and T08
      # edit loop.py's reset and dispatch paths; a running driver caches
      # specfuse.loop.loop in sys.modules and cannot execute them. See
      # GATE-02.md § Arming discipline and
      # [FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart].
      - id: FEAT-2026-0056/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on:
          - FEAT-2026-0056/T05
          - FEAT-2026-0056/T06
          - FEAT-2026-0056/T07
          - FEAT-2026-0056/T08
```

## Notes

- **Gate 1 skips nothing.** It makes per-criterion state *recorded* and *linted*; no
  close gets cheaper until gate 2 consumes it. This split is deliberate — the risky
  half of the feature is the policy deciding what a close may skip, and it lands
  after the state surface is proven. Same schema-then-consumer cut FEAT-2026-0069
  used across its two gates.
- **The artifact must survive the re-arm fold.** `[FEAT-2026-0053/G2-CLOSE]` is the
  lesson: an aggregate reading a per-cycle field silently under-counts every
  re-armed unit, and the error concentrates in exactly the work the aggregate exists
  to catch. Per-criterion state whose whole purpose is to outlive a re-dispatch must
  not live in a field `fold_cumulative_on_rearm` zeroes. That is why it is a
  standalone per-gate artifact and not close-WU frontmatter, and why T02 carries an
  explicit test for it.
- **The feature-level question never caches.** `[FEAT-2026-0057/G1-CLOSE]` — "re-running
  every producing unit's own oracle is not the feature-level re-run
  `close-discipline.md` §1 asks for; a close must ask a question no unit's criteria
  asked." Caching is scoped to per-unit criterion re-verification. The close's own
  feature-level question is out of scope for the cache in both gates.
- Dependencies live here, not in WU frontmatter.
- WU file numbers track the correlation sub-ID; closing units use the reserved 90+
  range so they sort last.
