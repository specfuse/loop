---
gate: 1
status: open        # open | awaiting_review | passed
cost_budget_usd: 29.00
baseline:
  sha: fd59b7b2e9edaae139769a2d8b9325ea48d51204
  probed_at: 2026-08-05T23:40:22.255818+00:00
  failing: []
---

# Gate 1 — a close records per-criterion state that survives a re-arm

## Definition of done

- A parser/renderer module exists for the per-gate criteria-state artifact, with a
  stable criterion identity, an oracle-kind classification (`narrow` / `broad`), and
  a per-entry state that round-trips through parse and render.
- Every `close` and `close-intermediate` dispatch has `GATE-NN-CRITERIA.md`
  pre-created in its session, seeded from the gate's substantive WUs' acceptance
  criteria — through the same extraction `build_autoclose_debt_enumeration` uses,
  hoisted rather than duplicated.
- The artifact survives `fold_cumulative_on_rearm`, proven by a test that re-arms a
  close WU and asserts the artifact's entries are intact.
- `specfuse-lint --closing` refuses a close whose criteria artifact has an entry
  with a missing or unrecognized `kind:` or `state:`, or a `broad` entry reading
  `pass` without an `attempt:` matching the current one — with the requirement
  declared in `closing_requirements.py` so the driver and the lint read one registry.
- `close-discipline.md` gains the per-criterion state section; `GATE.template.md` and
  `WU.template.md` point at it; `.specfuse/roadmap.md`'s FEAT-2026-0056 benefit
  paragraph is re-baselined to what oracle-kind invalidation can actually deliver.
- `RETROSPECTIVE.md` exists; lessons are promoted to `.specfuse/LEARNINGS.md`; gate
  2's work units are drafted and `GATE-02-REVIEW.md` is written.

Gate 1 is non-terminal, so the closing sequence is `close-intermediate` followed by
`plan-next`. **Gate 1 makes no close cheaper** — nothing reads the recorded state to
skip work until gate 2. That is the intended shape, not an omission.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4). REQUIRED for T03.** T03
  introduces a new blocking `specfuse-lint --closing` finding — a tree that lints
  clean today can lint dirty after it. Before arming, apply T03's requirement
  locally and run the exact command its tests gate will run, plus a sweep of
  `specfuse-lint --closing` over every existing feature's closing WUs. Paste the
  resulting finding list into `GATE-02-REVIEW.md`'s predecessor section below.
  **Expected at draft time: zero findings** — the requirement's `applies_when` is
  the existence of `GATE-NN-CRITERIA.md`, and no feature in `.specfuse/features/`
  has one. If the probe returns a non-empty list, T03's scope is wrong and it must
  be re-drafted before dispatch rather than absorbing the difference.

  This probe is not optional bookkeeping. `[FEAT-2026-0055/G1-CLOSE]` is the same
  shape: a "reports zero findings across every existing feature folder" criterion
  reported `passed` on its producing unit's first attempt, and the close re-running
  the one-line sweep found 15 findings across 4 features.

- **Flag-scope table (§3).** Not applicable — no work unit in this gate introduces,
  gates on, or flips a behavior flag. The `narrow` / `broad` oracle kinds are data
  on a criterion entry, not a flag over code paths.

- **Escalation-predicate satisfiability (§2).** Answered in `PLAN.md`. The load-bearing
  half is that the requirement is gated on artifact existence, which is what makes
  zero reachable on the legacy corpus without any reconciliation work.

## Arming probe result (§4)

### Baseline, captured at draft time (before T03 exists)

The probe's question is "does T03 add findings", so the pre-change finding set has to
be on record or the post-change sweep has nothing to subtract. Command:

```
for d in .specfuse/features/*/; do
  out=$(.venv/bin/specfuse-lint "$d" --closing 2>&1); rc=$?
  if [ $rc -ne 0 ]; then echo "### $d (exit $rc)"; echo "$out" | head -4; fi
done
```

Three features report findings today; **none is attributable to this feature's work**,
since `close-l` and `close-intermediate-f` do not yet exist:

```
### .specfuse/features/FEAT-2026-0001-health-endpoint/ (exit 1)
  - plan-next-a: GATE-02-REVIEW.md absent or empty

### .specfuse/features/FEAT-2026-0036-adopt-ruff-016/ (exit 1)
  - close-a: RETROSPECTIVE.md absent or empty in feature dir
  - close-b: no LEARNINGS.md additions and no 'nothing generalizes' note
  - close-d: verdict frontmatter field is absent

### .specfuse/features/FEAT-2026-0056-per-criterion-dod-state/ (exit 1)
  - close-intermediate-a: RETROSPECTIVE.md absent in feature dir
  - close-intermediate-b: no LEARNINGS.md additions and no 'nothing generalizes' note
```

FEAT-2026-0001 is a bundled fixture and FEAT-2026-0036 never ran its close — both are
the same pre-existing exclusions FEAT-2026-0072's gate-1 probe enumerated. This
feature's own two are expected: its close has not run yet.

### Post-change probe (run before arming T03 — REQUIRED)

<Apply T03's requirement locally, re-run the sweep above, and paste the output here.
The arming condition is **the finding set is unchanged from the baseline** — not that
it is empty. Any new finding carrying `close-l` or `close-intermediate-f` means the
`applies_when` gating does not hold and T03 is mis-scoped: re-draft, do not arm.>

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
