# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead: in
this feature directory, not in the repo-wide file that every future feature's
planning step loads. A closing WU's own post-pass check refuses to pass if
its diff touches `.specfuse/LEARNINGS.md` while this feature is in `auto`
mode — this file is where those lessons go instead.

**How a human promotes an entry from here.** At PR review for this feature:

1. Read each entry below. Judge it the way you would judge any
   `LEARNINGS.md` candidate — does it generalize into a rule that should
   change how a FUTURE work unit, in any feature, is written or executed?
2. For each entry you accept, copy it into `.specfuse/LEARNINGS.md` (below
   the `<!-- lessons work units append below this line -->` marker, in that
   file's existing entry format) in the same commit or a follow-up commit to
   the PR branch.
3. For each entry you reject or narrow, leave it here — do not delete it
   silently; a short note on why it didn't generalize helps the next person
   who drafts a similar feature.
4. This file is not read by planning. Nothing here shapes another feature
   until a human has done step 2.

## Format

```
- [FEAT-YYYY-NNNN/G1] Implementation WUs must name the module a new route/handler
  lives in; "add it to the router" cost a blocked attempt when no router existed yet.
```

## Entries

<!-- closing work units append below this line -->

- [FEAT-2026-0050/G2] **When a feature's goal is an end-to-end outcome, some
  gate's Definition of Done must assert the end-to-end outcome — otherwise
  "every acceptance criterion is green" is structurally incapable of meaning
  "the feature works", and no amount of verification discipline can close the
  gap.** This feature shipped seven implementation work units, thirty-nine
  acceptance criteria, nine dispatched sessions, and zero failures — and did
  not remove the bottleneck it was filed for, because two seams between the
  units were never assigned to anyone. Gate 1's DoD stopped at "an operator
  reply is parsed back to per-question answers"; gate 2's stopped at
  "`FeatureProvider` dispatches that path on `needs_drafting`". Both are true.
  Neither implies a question issue was ever posted or that a real run ever
  takes the new branch. Every unit-local criterion was individually correct and
  collectively insufficient, which is the property that makes this failure
  invisible at arming: there is nothing wrong to point at in any single work
  unit. Planning rule: read the roadmap row's own benefit sentence, and check
  that at least one gate's DoD contains a claim that would be *false* if the
  benefit were not delivered. If every DoD line would still be true with the
  pieces disconnected, the plan has no end-to-end gate and one must be added
  before arming.

- [FEAT-2026-0050/G2] **An injectable seam with a safe default ships dead
  unless a work unit explicitly owns the injection site.** T07 added
  `FeatureProvider(answer_gate=...)`, defaulting to a fallback-only reader —
  correct, documented in the constructor's own comment, and the mechanical form
  of "worst case is status quo". But `default_providers` in
  `specfuse/agent/run.py` constructs the provider without that argument, so the
  new branch is unreachable in every real run, and T07's tests pass because they
  inject the gate themselves. A test that supplies the dependency proves the
  branch works; it says nothing about whether production ever supplies it.
  Authoring rule: a work unit that introduces a constructor parameter, a hook,
  or a strategy object must either wire the production call site in the same
  unit or name, in its own body, the successor unit that will — and the
  successor must exist in the plan graph, not in prose. The same rule covers
  its mirror image: a unit whose criteria assert the *absence* of an effect for
  testability ("renders a body and issues no `gh` command") needs a named unit
  that supplies the effect, or the capability is permanently one call short.

- [FEAT-2026-0050/G2] **Auto-close is a deferral with interest, not a saving —
  budget it as debt.** Gate 1 auto-closed at `evaluate_auto_close`, so
  `G1-CLOSE-INTERMEDIATE`'s $6.00 was never spent and the gate landed at 40% of
  budget. What it actually did was defer the per-criterion enumeration for
  T01–T03 to the terminal close, which then spent a real session re-verifying
  all 19 against fresh oracles. The `specfuse:autoclose-debt` marker made that
  debt visible and reconcilable, which is the mechanism working — but the money
  moved, it did not vanish. Estimating rule: when a gate is expected to
  auto-close, do not read its underspend as headroom for a later gate, and do
  size the terminal close for the predecessor debt it will inherit. A terminal
  close reconciling three work units' worth of deferred criteria is doing a
  close-intermediate's work on top of its own.

- [FEAT-2026-0050/G2] **Price an implementation work unit whose oracles are
  scoped unit tests over a new, self-contained module near the observed median,
  not at a padded floor.** Seven implementation units here were estimated at
  $25.00 total and spent $8.12 — a per-unit ratio of 0.29–0.40 with almost no
  variance, which is systematic bias rather than noise. The one estimate that
  was nearly right was `plan-next` ($9.00 planned, $6.37 actual), argued up from
  the floor on distributional evidence. The asymmetry is the lesson:
  `planning-discipline.md` §5's floors are calibrated for *closing* units, whose
  cost is dominated by guard-contract round-trips; an implementation unit that
  creates one new module plus its test file, with no cross-cutting edits and no
  external oracle, is a different distribution and does not inherit that
  padding. Uniform padding also hides its own cost: $30 of unspent budget here
  bought a feature whose headline benefit is unmeasured, and no line item ever
  overran to signal it.
