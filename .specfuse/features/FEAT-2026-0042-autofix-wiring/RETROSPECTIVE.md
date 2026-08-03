# Retrospective — FEAT-2026-0042, Autofix wiring

## Gate 1

Gate 1 shipped the decision layer for autofix: a predicate that decides, durable
state that remembers, a registered failure label, and a headless mode for `fix-bug`.
Three implementation work units (T01, T02, T03), each `passed` on its first attempt.

**The dial is still inert, and that is the gate's success condition, not a shortfall.**
Setting `autofix: "on"` on a component today changes nothing observable. There is no
production caller: `grep -rn "monitor.autofix" specfuse/ | grep "\.py:"` returns two
hits, both docstring/registry references (`autofix_state.py:25`, `labels.py:93`), and
no import of `specfuse.monitor.autofix` outside `tests/`. `grep -rn "fix-bug\|fix_bug"
specfuse/` finds no invocation — only `autofix.py`'s docstring saying it does not
invoke one, and an unrelated string in `loop.py:2957`. The predicate decides, the
state records, the headless mode is documented, and nothing fires. A reader who
concludes from this gate that autofix is live has misread it; a reader who concludes
the gate is incomplete has misread it the other way.

### What was built

| WU | Deliverable | Shape |
| --- | --- | --- |
| T01 | `specfuse/monitor/autofix.py` | Pure `decide(...)` returning `AutofixDecision(decision, reason)` over a closed 3-value decision set (`FIRE` / `ROUTE_TO_HUMAN` / `DECLINE`) and 7 named reasons. Reads no file, touches no network. `CONFIDENCE_THRESHOLD = 0.8` is a module constant. Fails closed: any unevaluable input returns `DECLINE`. |
| T02 | `specfuse/monitor/autofix_state.py`, `specfuse/loop/labels.py` | Attempt state as an HTML-comment marker on the GitHub finding issue, following `issues.py`'s existing marker convention rather than a second one. `DAILY_CAP = 5` over a rolling 24h UTC window (not a calendar day). Fails closed on any unreadable read. `AUTOFIX_FAILED_LABEL` registered in `LABEL_REGISTRY` ahead of its consumer. |
| T03 | `plugins/specfuse/skills/fix-bug/SKILL.md` + vendored copy | An **invocation mode**, not a workflow change. Every interactive halt maps to one of exactly three outcomes (`refused` / `could_not_proceed` / `completed`) via an enumerated table. No refusal path weakened. |

### Three decisions worth carrying into gate 2

**The threshold and the cap are hardcoded on purpose.** `CONFIDENCE_THRESHOLD` and
`DAILY_CAP` are module constants, following FEAT-2026-0053's precedent for arm-predicate
stop classes: a safety threshold that lives in a config file can be tuned into
uselessness by the person it is meant to stop. `autofix: on|off` is per-component and
config; *how confident is confident enough* is not. Gate 2 must not relocate either
into `monitoring.yml`.

**Both layers fail closed, and they must keep doing so.** T01 returns `DECLINE` on an
unparseable diagnosis, an absent component, a malformed dial, or a state reader that
raises. T02 returns the conservative answer (an attempt exists; the cap is reached) on
any read it cannot complete. The asymmetry is deliberate: a guardrail that resolves
"unknown" to "probably fine" reads as present and is not.

**T03's refusal paths are a second guardrail, not an obstacle.** T01 decides the
finding *looks* small from the diagnosis. `fix-bug`, having read the actual code,
decides whether it *is* — and `refused` is a first-class outcome, not a failure. Gate 2
must treat a `refused` return as a normal, expected result of a fired run.

### The safety floor, restated for gate 2's reader

**Auto-merge belongs to [FEAT-2026-0048](../../roadmap.md#feat-2026-0048), which is
`blocked`. It is impossible in this feature.** No work unit in either gate may merge a
pull request, enable auto-merge, or push to a protected branch, and no gate-2 draft may
widen this. The worst outcome this feature can produce is **an unwanted pull request on
a branch** — cheap to close, nothing on a protected branch, nothing in production.

That is a constraint inherited from the roadmap, not a decision gate 2 gets to revisit.
A gate-2 draft that believes it needs to merge anything has crossed into 0048's
territory and is an escalation to the operator, not a design choice. `G1-PLAN` must
carry this paragraph into gate 2's drafts.

**The gate-1 safety property held.** No gate-1 work unit invoked `fix-bug`, created a
branch, opened a pull request, or made a writing `gh` call at runtime. Verified by the
greps quoted above plus `tests/test_autofix_state.py`, which stubs the injected runner
and additionally greps its own subject for `subprocess\.|requests\.|urllib|os\.system`
so a raw call that escaped the stub would fail the suite. `record_attempt()` does shell
a `gh issue edit`, but it takes an injected runner, has no production caller, and is
never invoked against a real repository in this gate.

### The one thing gate 1 got wrong: a test that can only pass once

`tests/test_fix_bug_headless.py::test_interactive_sections_unchanged_only_additions`
compares the working-tree `SKILL.md` against `git show HEAD:<path>` and asserts the
diff is non-empty and purely additive. During T03's session HEAD was the pre-WU commit,
the diff was real, and the test passed. The driver then committed T03 — and that commit
made HEAD identical to the working tree, so the diff is now empty and the assertion
fails permanently:

```
FAIL: test_interactive_sections_unchanged_only_additions
AssertionError: 0 not greater than 0 : expected additive headless-mode content
but diff summary is 0 line(s) removed, 0 line(s) added

Ran 2106 tests in 71.158s
FAILED (failures=1, skipped=3)
```

The test was green when the driver verified T03 and red the moment the driver committed
it. It is red on the branch now, and it is red in CI, which runs the same
`python3 -m unittest discover -s tests`. This close found it only because
`close-discipline.md` §1 requires re-running the oracles fresh rather than inheriting
T03's `done`; the `plannext` gate set this close is verified against (`lint_plan.py`
alone) would never have surfaced it.

**This close did not repair it** — WU-90's *Do not touch* assigns T01–T03's source to
those work units. The fix belongs in a T03 re-arm: pin the comparison to the recorded
pre-WU baseline SHA (`GATE-01.md`'s `baseline.sha`) rather than the moving `HEAD`, or
assert the additive property against the section structure rather than a diff. Gate 2
must not be armed on a red suite.

## Cost analysis

**Planned.** Gate-1 work-unit estimates sum to **$22.00** — $4.00 (T01) + $4.00 (T02) +
$3.50 (T03) + $4.50 (G1-CLOSE-INTERMEDIATE) + $6.00 (G1-PLAN). `GATE-01.md` carries a
**$28.00** budget: the $22.00 sum plus one re-attempt of the largest WU ($6.00,
`G1-PLAN`), the defensive padding the GATE template prescribes while the closing-WU
retry defect (#260) is open.

**Actual, from `events.jsonl` `attempt_outcome` payloads (the authoritative source).**

| WU | Planned | `attempt_outcome` `cost_usd` | Attempts | Outcome |
| --- | ---: | ---: | ---: | --- |
| T01 | $4.00 | $1.1631516 | 1 | passed |
| T02 | $4.00 | $2.7355710 | 1 | passed |
| T03 | $3.50 | $1.6479222 | 1 | passed |
| **Recorded total** | **$11.50** | **$5.5466448** | 3 | — |
| G1-CLOSE-INTERMEDIATE | $4.50 | (this WU, in flight) | — | — |
| G1-PLAN | $6.00 | (not yet dispatched) | — | — |

**Reconciliation against frontmatter.** Each WU's `cost_usd` frontmatter field equals
its `attempt_outcome` payload to six decimal places (1.163152 / 2.735571 / 1.647922).
The two surfaces agree exactly; there is no frontmatter-vs-events discrepancy.

**The recorded total is a lower bound, and here is the gap.** The branch history carries
`f9d47a2 chore(loop): recover FEAT-2026-0042/T03 from an infra kill`, and `GATE-01.md`'s
baseline was re-probed at that SHA at `2026-08-03T23:02:08Z` — between T02's completion
(`22:58:26Z`) and T03's recorded `task_started` (`23:04:51Z`). That killed T03 attempt
emitted no `attempt_outcome` event, so its spend appears in neither `events.jsonl` nor
any WU's frontmatter. Its magnitude is **unrecorded, not estimated**: true gate-1
implementation spend is `$5.55 + <unrecorded infra-kill attempt>`. No number is invented
here.

**Reading.** Implementation work landed at $5.55 against $11.50 planned — 48% of
estimate, all three WUs first-attempt passes on sonnet/medium. The $28.00 gate budget is
not at risk: even with both closing WUs at their full $10.50 planned, the gate lands
near $16.05, well inside budget. The consistent overestimate of sonnet/medium
implementation WUs on this repo is a planning-calibration observation, not a defect —
the padding exists for the re-attempt case, which did not occur here.

### Failure-class breakdown

(no non-passing attempts in scope)

Every `attempt_outcome` in `events.jsonl` carries `outcome: passed` with
`failure_class: null` and `failure_signature: null`. The infra-killed T03 attempt noted
above emitted no `attempt_outcome` event at all, so it is absent from this breakdown by
construction rather than classified as passing — an infra kill is not a failure class
the driver records.

## What the loop did NOT verify

**Fix correctness — inherent, not a gap for gate 2 to close.** Nothing in this feature
asserts that an automated fix produces a *correct* patch, and nothing in gate 2 will
either. Every criterion in gate 1 asserts the **decision** is right (fires only when it
should) or the **mechanism** is sound (state persists, halts map to outcomes). This is
the same inherent limit FEAT-2026-0041 recorded for diagnosis quality: patch quality is
a judgement about generated code, not a property a test can hold. A criterion of the
form "the autofix produces a correct patch" would be unsatisfiable and must not be
written into gate 2. The mitigations are structural, not verificational — the confidence
threshold, the `fix_scope` route-out, `fix-bug`'s own refusal paths, one run per
fingerprint, the daily cap, and above all the human merge floor.

**Nothing fires yet, by design.** No end-to-end behaviour was exercised because there is
no caller. The predicate has never been handed a real diagnosis, `record_attempt` has
never written to a real issue, `daily_cap_reached` has never counted real markers, and
`fix-bug` has never run headless. Gate 2 owns the firing wiring and its live run. Until
then, every guarantee in gate 1 is a unit-test guarantee about a component in isolation.

**The `AUTOFIX_FAILED_LABEL` has never been applied.** It is registered in
`LABEL_REGISTRY` and created by the label-sync path, but no code path applies it — gate 1
has no fired attempt with an outcome to label. Registering ahead of the consumer is
deliberate (issue #300: code that queries an unregistered label gets every `gh issue
create --add-label` rejected until a human creates it by hand), but it means the label's
end-to-end path is unexercised.

**The rolling-window boundary is verified only against injected clocks.**
`test_autofix_state.py` holds the 24h boundary at both edges with a fixed `now`, which
is the right oracle for the arithmetic. It does not verify behaviour against real
GitHub timestamps or clock skew between an Actions runner and an AKS CronJob
(FEAT-2026-0043) writing markers into the same issue body.

### Deferred verification

| Criterion | Why not verified in-loop | Where it actually gets checked |
| --- | --- | --- |
| `tests/test_fix_bug_headless.py` passes as a standing oracle (T03) | It passed at T03's verification and was broken by the commit that followed it — it compares against a moving `HEAD`. Repairing it is T03's source, which this close is forbidden to touch. | A T03 re-arm, before gate 2 is armed. Confirmed red here by a fresh full-suite run; also red in CI. |
| `decide()` returns `FIRE` on a real diagnosed finding (T01) | No production caller exists in gate 1; the gate's safety property is that none may. | Gate 2's live end-to-end run, drafted by `G1-PLAN`. |
| `record_attempt()` / `daily_cap_reached()` against real GitHub state (T02) | Verified against an injected runner stub only — a real `gh` write in gate 1 would violate the gate's no-writes boundary. | Gate 2's live end-to-end run. |
| `AUTOFIX_FAILED_LABEL` is applied to a finding issue (T02) | No fired attempt exists to have an outcome worth labelling. | Gate 2, once a fired run's result is known. |
| `fix-bug` headless mode produces one of its three outcomes on a real issue (T03) | T03 ships a documented mode; invoking it is firing, which gate 1 forbids. | Gate 2's live end-to-end run. |
| Fix correctness | **Inherent** — see above. Not deferred to gate 2 or anywhere else. | Nowhere. Mitigated structurally, never asserted. |

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3, across all of gate 1's producing WUs. **Blast
radius measured, not assumed** (per `[FEAT-2026-0059/G1-CLOSE]`): every entry below was
checked for whether it appears in a shipped scaffold surface.

1. **`fix-bug` gains a documented headless mode.** `plugins/specfuse/skills/fix-bug/SKILL.md`
   and its `.specfuse/` vendored copy gain a `## Headless mode` section defining
   `mode: headless` and a closed three-outcome set (`refused`, `could_not_proceed`,
   `completed`) with an exhaustive halt→outcome mapping table. **This ships to
   downstream projects** — the skill is part of the scaffold, so any project on a newer
   scaffold sees the new section. **Purely additive and non-breaking**: interactive
   behaviour is byte-for-byte unchanged (that is what the now-broken additive test was
   asserting), no refusal criterion was weakened or removed, and a human typing
   `/fix-bug NN` sees exactly what they saw before. Callers that do not pass
   `mode: headless` are unaffected.

2. **New public module `specfuse.monitor.autofix`.** Additive: `decide()`,
   `AutofixDecision`, `RateLimitStateReader`, `FIRE` / `ROUTE_TO_HUMAN` / `DECLINE`,
   `DECISIONS`, the seven `REASON_*` constants, and `CONFIDENCE_THRESHOLD`. Nothing
   existed at this import path before; nothing imports it in production yet. No existing
   symbol changed. Non-breaking.

3. **New public module `specfuse.monitor.autofix_state`.** Additive:
   `has_prior_attempt()`, `record_attempt()`, `daily_cap_reached()`,
   `GitHubAutofixState`, `AUTOFIX_FAILED_LABEL`, `ROLLING_WINDOW_SECONDS`, `DAILY_CAP`.
   It *reads* `specfuse.monitor.issues` (`DEFAULT_LIST_LIMIT`, `FINDING_LABEL`,
   `find_finding_issue`) but changes nothing there. Non-breaking.

4. **New label in `LABEL_REGISTRY`: `auto-fix-attempted-failed`**, described
   "auto-fix attempted, failed", consumer `monitor/autofix_state.py`. This is the one
   entry with a **real downstream effect**: the label-sync path creates every
   `LABEL_REGISTRY` label the target repo is missing, so a repo running label sync after
   upgrading gains one new GitHub label it did not have. Additive — no label was renamed
   or removed, and nothing applies this one yet. Note the spelling: the roadmap row
   describes it in prose as "auto-fix attempted, failed"; the registered label *name* is
   the slug `auto-fix-attempted-failed` and the prose is its `description`. Any gate-2
   code must use the constant, never a hand-written literal (issue #300).

5. **No change to the `autofix` dial's schema or default.** `autofix: on|off` already
   existed in `monitoring.yml`'s schema and was already validated by
   `lint_monitoring.py`. `"off"` remains the shipped default for every component in
   `.specfuse/monitoring.yml.example`. This gate added the dial's *consumer*, not the
   dial. No existing config becomes invalid, and no existing config changes behaviour.

**Human acknowledgment required.** Per §3 this list blocks on the operator reading it.
Item 4 is the only one with a visible effect on a repo that upgrades without touching
any code; item 1 is the only one that changes a shipped document a human reads.

## Documentation reconciliation

The roadmap row for [FEAT-2026-0042](../../roadmap.md#feat-2026-0042) remains accurate
and stays `active`, which is correct for a non-terminal gate — the terminal flip belongs
to `G2-CLOSE`, and `PLAN.md`'s `status` is untouched by this close.

One correction the roadmap row deserves, recorded here rather than applied (the row
states the feature's *goal*, and rewriting a goal mid-feature would lose the record of
what was actually promised): the row's phrasing **"auto-fire headless `/fix-bug NN`"**
presupposes that headless invocation existed. It did not — see the lesson below.

### T03 widened scope, and the roadmap row is why

`PLAN.md`'s existing-mechanism search (`planning-discipline.md` §1) caught this at draft
time rather than mid-attempt: `.specfuse/skills/fix-bug/SKILL.md` was titled
"(interactive)", carried the `operator-escalation.md` framing that halts for a human,
and had refusal paths proposing `/draft-feature`. There was no headless mode to invoke.
The roadmap row had treated the invocation surface as a given and priced only the
*guarding* of it.

**What it cost.** Because the gap was found at draft time, not attempt time, the cost
was a planning cost, not a re-attempt: T03 was scoped as a real work unit ($3.50
planned, $1.65 actual) instead of appearing as unbudgeted mid-attempt scope creep in a
wiring WU. That is the cheap version of this failure. The expensive version — the one
the next feature reading a roadmap row should fear — is discovering it inside an
implementation attempt, where the choice is between a blocked WU and silently widening
scope.

**For the next reader of that row:** the headless mode now exists as of this gate, so
the row's premise is true going forward. It was not true when the row was written.

---

*Correlation ID: `FEAT-2026-0042/G1-CLOSE-INTERMEDIATE`. This is a non-terminal gate:
no terminal verdict is written here — `G2-CLOSE` owns it. Gate 2's drafts are `G1-PLAN`'s.*
