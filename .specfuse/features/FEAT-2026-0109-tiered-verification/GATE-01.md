---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_lazy_baseline_e2e -q"
baseline:
  sha: cc8b2613561af3cda5297d5088b33ea3158ccedc
  probed_at: 2026-09-08T11:26:09.498081+00:00
  entry_sha: cc8b2613561af3cda5297d5088b33ea3158ccedc
  failing: []
---

# Gate 1 — the probe stops running when nothing is wrong, and still attributes when something is

## Definition of done

- **The gate-entry probe does not run on the green path.** Entering a gate
  dispatches its first unit without executing the `code` set.
- **A unit's first verification failure triggers attribution**: the driver runs
  `probe_baseline` against the post-reset tree and decides whether the failure
  pre-existed. A pre-existing failure escalates `preexisting_gate_failure` as
  it does today and **is not counted against the unit's attempts**; a genuine
  failure counts normally and the unit retries.
- **Attribution runs at most once per gate.** A second failing unit does not
  re-probe if the gate already has a fresh attribution record for this tree.
- **The probe that does still run is keyed on the tree hash**, not the HEAD
  sha, so a bookkeeping commit that leaves the code tree identical does not
  invalidate the record — the case that made every restart re-probe.
- **The baseline record says how it was determined.** Its block carries
  provenance distinguishing "probed at gate entry", "attributed after
  `<wu_id>` failed", and "skipped". An escalation is readable without
  guessing which path produced it.
- Absent-key and flag behaviour is preserved: `--no-baseline-probe` and the
  `baseline_probe` key still mean what they mean today.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## This gate's oracle

```
python3 -m unittest tests.test_lazy_baseline_e2e -q
```

Red on HEAD by construction. T01 is the tracer bullet that makes it green, and
the only unit permitted to leave stubs behind it. The test must drive the real
dispatch path — a green gate entry that never executes the `code` set, then a
failing unit that triggers attribution — and assert on **observable effects**
(the gate set did not run; the baseline record exists afterwards and names the
unit that triggered it), not on a helper returning the right value in
isolation. A feature about not running verification, whose oracle only checked
a helper, would be its own hollow pass.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Gate 2 is armed from here, and `plan-next` must draft **gate 2's own
`feature_oracle`** along with its units (#3262 — a gate with no substantive
units carries no oracle requirement, so the obligation lands exactly when
`plan-next` gives gate 2 real work).

- **Runtime probe for a default flip (§4).** T01 changes a default the driver
  applies on every gate entry. It may not be armed on "mechanical, nothing
  design-open" — run the exact command T01's tests gate will run and paste the
  result into `GATE-01-REVIEW.md`.
- **Review-summary obligation.** State how gate 2's oracle advances this
  gate's, per the `plan-next` contract FEAT-2026-0101/T04 added.

## Reflection notes

<Written by the human at review time. Whether the lazy probe ever mis-attributed
a failure, how often attribution actually fired, and whether the one-wasted-
dispatch cost showed up in practice.>
</content>
