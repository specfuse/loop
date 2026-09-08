---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_feature_oracle_e2e -q"
baseline:
  sha: c87253320408b600d52dbb5c99e239d24f01f365
  probed_at: 2026-09-08T00:36:26.522214+00:00
  entry_sha: df61e150605ea1949fb065a01d44cbd8ca7713e4
  failing: []
---

# Gate 1 — a gate's definition of done is an executable oracle the driver runs

## Definition of done

- A gate declares `feature_oracle` in its `GATE-NN.md` frontmatter. The driver
  reads it, synthesizes a one-element gate list, and runs it through the
  existing `_run_gate_set` — inheriting that runner's timeout, process-group
  kill, Windows bash routing, degraded-oracle detection and report format. No
  second execution path exists.
- The oracle runs as part of **every unit's verification** in that gate, so a
  unit that breaks the gate's end-to-end behaviour fails on the attempt that
  broke it rather than at close.
- The **close re-runs it** and records the verdict in `## Measurements`, and
  `specfuse lint --closing` fails a close that omits it. This is what makes the
  judge's binary signal real: the judge already reads measurements.
- A declared oracle that is **empty or whitespace-only** is a CONFIGURATION
  ERROR before any unit dispatches — never a silent skip and never a silent
  pass.
- A declared oracle whose **command the shell cannot run at all** (exit status
  127) is detected when it runs and reported as a configuration problem naming
  the gate file, not as an ordinary gate failure attributable to the unit under
  test. Nothing passes silently either way; the requirement is correct
  *attribution*, because an ordinary `FAIL` tells the next agent its code is
  broken when the real defect is the declaration.
  **Narrowed after this gate's first close (issue #3260).** The original wording
  demanded a configuration error "before any unit dispatches" for any command
  that "cannot be resolved". Pre-flight resolution of an arbitrary shell string
  — pipes, `&&`, environment-dependent lookup — is not reliably decidable, and
  the judge correctly refused a `met` against the wording as written. Pre-flight
  resolution is explicitly **out of scope**; run-time attribution is what T05
  delivers.
- A gate declaring no `feature_oracle` is ERROR when its feature is `active`,
  WARN when `planned` / `blocked` / `deferred`, skipped when the gate is
  `passed` or the feature is `done` / `abandoned`. The corpus sweep reports
  **zero ERRORs and exactly four WARNs** (FEAT-2026-0052/GATE-01,
  FEAT-2026-0081/GATE-01, FEAT-2026-0081/GATE-02, FEAT-2026-0082/GATE-01), plus
  FEAT-2026-0011 which has no gate files.
- `GATE.template.md` carries the key, `/draft-feature` refuses to draft a gate
  without one, `plan-next` drafts the next gate's oracle and states in its
  review summary how it advances the prior gate's, and `methodology.md`
  documents the key in its one home.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is a single-gate feature with a terminal `close` (`docs/methodology.md` §6,
ceremony proportionality). There is no `plan-next` and no next gate to arm.

## This gate's oracle

```
python3 -m unittest tests.test_feature_oracle_e2e -q
```

Red on HEAD by construction — the mechanism does not exist yet. T01 is the
tracer bullet that makes it green, and it is the only unit permitted to leave
stubs behind it. The test must build a temp feature folder whose `GATE-01.md`
declares an oracle, drive a unit through `verify()`, and assert both that the
oracle command actually executed and that its verdict reached the close's
recorded measurements — not that a helper function returns the right value in
isolation. A feature about feature oracles that asserted only on helpers would
be the recursive hollow pass `[FEAT-2026-0008/G1-CLOSE]` names.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

No next gate is armed from here. Two items still bind on this gate's review:

- **Escalation-predicate satisfiability (§2).** T03 introduces an ERROR.
  `PLAN.md` answers what it reports on inputs already in their final state —
  zero, measured by sweep, with the graduated-by-feature-status scoping that
  makes it so. Re-run that sweep at close; a rule that fires on the four known
  WARN gates at ERROR level is unsatisfiable and must not ship.
- **Runtime probe for a severity flip (§4).** T03 flips a severity. It may not
  be accepted on "mechanical, nothing design-open" — run the exact command
  T03's tests gate will run and paste the finding list.

## Reflection notes

<Written by the human at review time. What surprised you, whether the oracle
caught anything the unit gates missed, and whether the tracer-bullet ordering
actually held.>
</content>
