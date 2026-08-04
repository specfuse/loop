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

---

## Gate 2

Gate 2 built the firing path and fired it once, for real. Three implementation work
units (T04, T05, T06), each recorded `passed` on its first attempt.

**The headline, stated before the detail, because the gate being green does not say
it.** The mechanism runs: on a real diagnosed finding, the predicate decided `FIRE`,
the attempt was durably recorded on the issue, a real headless `fix-bug` session was
launched, its result came back through T04's closed three-outcome set, and the failure
label was applied. **No pull request was produced.** The one live fire returned
`could_not_proceed`, so the end of the chain — *a fix run yields a reviewable pull
request* — is the one link this feature never observed. T06's own session reported
that honestly and ended `status: blocked`; the driver recorded it `passed` anyway, for
a reason that is itself the most generalizable finding in this gate (below). Gate 2 is
green. The end-to-end claim is not verified. Both are true, and the second is the one
that matters.

### What was built

| WU | Deliverable | Shape |
| --- | --- | --- |
| T04 | `specfuse/monitor/autofix_invoke.py` | Builds and classifies; runs nothing. `build_invocation()` returns a `(argv, prompt)` tuple following the driver's own `claude -p --model … --effort …` dispatch shape; `classify_outcome()` maps the session's result text onto `OUTCOMES = ("refused", "could_not_proceed", "completed")`, read from T03's `SKILL.md` contract rather than restated. Fails closed to `could_not_proceed`. The safety-floor prohibition is literal text in `_SAFETY_FLOOR`, embedded in the prompt the headless session reads. |
| T05 | `specfuse/monitor/autofix_run.py` | The wiring, and the dial's first consumer. Reads the finding issue and its latest diagnosis comment through `issues.py`'s existing markers, calls T01's `decide`, **records the attempt before invoking**, fires through T04, and applies `AUTOFIX_FAILED_LABEL` on a failing outcome. `__all__ = ("AutofixRunResult", "Invoker", "run_autofix", "main")`. Its own entry point — `python3 -m specfuse.monitor.autofix_run` — deliberately not a `specfuse-monitor` subcommand. Carries the §3 flag-scope table. |
| T06 | `tests/test_autofix_live.py` + the one-time live fire | A skip-guarded live harness (it decides `decline` on a dial-off component, so the repeatable suite reaches GitHub without firing) plus the single manual fire whose raw output is quoted below. The only `unsandboxed: true` work unit in the feature. |

### Decisions worth carrying past this feature

**Record the attempt before invoking.** `G1-PLAN` argued this at arming time and the
live run vindicated it in the sharpest possible way: the first fired attempt crashed
*after* the session ran, while applying the failure label. Because the marker was
already on the issue, the crash left a truthful record of a spent run rather than an
invisible one. Invoke-then-record loses the marker on exactly the kills this feature
has already suffered three of. T05's criterion 3 asserts the *order*, not just that
both happened, and that assertion is now the load-bearing one.

**The firing path has no scheduled caller, and that was a decision.** Row two of T05's
flag-scope table — `specfuse-monitor run` is "not gated, because it is deliberately not
wired" — is the reason "the dial goes live" does not mean "fixes now happen on their
own." Verified fresh here: `grep -n "autofix" specfuse/monitor/cli.py` returns nothing,
and no `[project.scripts]` console script reaches the module. A later feature that
wires the harvest cycle to this entry point is making a real autonomy decision and
should be made to say so.

**`refused` / `could_not_proceed` are outcomes, not errors — but they are also not
evidence.** Gate 1 was right that a non-`completed` return is a working second
guardrail. Gate 2 shows the other half: a mechanism whose only live exercise ends in
its refusal branch has demonstrated the refusal branch and nothing past it. Both
readings have to be held at once, and a close that keeps only the flattering one is
the failure mode `close-discipline.md` exists to prevent.

**A registry entry is not a provisioned label.** T02 registered
`auto-fix-attempted-failed` in `LABEL_REGISTRY` *specifically* to avoid issue #300's
failure — and the first fired run still crashed on `gh issue edit --add-label`, because
the label had never been created on the real repository. Registration is the
prerequisite; provisioning is a separate, runtime step that nothing in this feature
forces. See the lesson promoted to `LEARNINGS.md`.

### The live end-to-end run — raw evidence

Reproduced from `FEAT-2026-0042/T06`'s recorded RESULT block, not summarised. Two
redactions are marked inline and are the only edits: the GitHub account name, and the
absolute temporary clone path (`never-touch.md` §2 / `security-boundaries.md` posture
on values that identify an operator's machine). No probe output is otherwise altered.

```
PROBE_BEGIN gh-auth-status (sandboxed, first try — the known artifact)
github.com
  X Failed to log in to github.com using token (GH_TOKEN)
  - The token in GH_TOKEN is invalid.
exit=1
PROBE_END gh-auth-status

PROBE_BEGIN gh-auth-status (unsandboxed retry)
github.com
  ✓ Logged in to github.com account <redacted> (GH_TOKEN)
  - Active account: true
  - Git operations protocol: ssh
  - Token scopes: 'admin:org', 'admin:repo_hook', 'repo', 'workflow', 'write:packages'
exit=0
PROBE_END gh-auth-status
```

```
PROBE_BEGIN clone-status-planted-bug
?? specfuse/monitor/_t06_scratch_bug.py
PROBE_END clone-status-planted-bug
```

The clone lived at `<redacted-tmp>/feat-2026-0042-t06-clone-71323`; the planted defect
was `add_positive(a, b)` returning `a - b`. It never entered this repository's working
tree.

```
PROBE_BEGIN gh-issue-create
https://github.com/specfuse/loop/issues/373
exit=0
PROBE_END gh-issue-create

PROBE_BEGIN gh-issue-comment-diagnosis
https://github.com/specfuse/loop/issues/373#issuecomment-5173947856
exit=0
PROBE_END gh-issue-comment-diagnosis
```

The diagnosis was rendered through `specfuse.monitor.diagnosis.render(Diagnosis(…,
confidence=0.95, fix_scope="small"))` — above T01's `CONFIDENCE_THRESHOLD = 0.8`, and
`small`, so the predicate had a genuine `FIRE` input rather than a hand-written one.

**The first fired attempt crashed after the session ran:**

```
PROBE_BEGIN fired-run-first-attempt-stderr
subprocess.CalledProcessError: Command '['gh', 'issue', 'edit', '373', '--repo',
'specfuse/loop', '--add-label', 'auto-fix-attempted-failed']' returned non-zero
exit status 1.
PROBE_END fired-run-first-attempt-stderr
```

**The second, clean attempt completed:**

```
PROBE_BEGIN fired-run-stdout
{"decision": "fire", "reason": "eligible", "outcome": "could_not_proceed"}
PROBE_END fired-run-stdout
```

```
PROBE_BEGIN gh-issue-view-json-body
"<!-- specfuse:finding fingerprint=feat-2026-0042-t06-1785810844-71323 -->\n\n...
\n\n<!-- specfuse:autofix-attempt fingerprint=feat-2026-0042-t06-1785810844-71323 at=1785811116.3010828 -->\n"
labels: monitoring-finding, auto-fix-attempted-failed
PROBE_END gh-issue-view-json-body
```

**Reading it, plainly.** `decision: fire` and the attempt marker prove the decision
layer and the durable state work against a real issue. `outcome: could_not_proceed`
proves the invoker launched a session and classified what came back. It does **not**
prove a fix run produces a pull request, because none was produced — `gh pr list --repo
specfuse/loop --search "FEAT-2026-0042/T06" --state all` returned `[]` and the clone's
branch list was unchanged. T06's criterion 7 ("on `completed`: a real pull request
exists") is **unmet**, and T06 said so: it ended `status: blocked` with
`blocked_reason` naming exactly that.

**Two caveats on this evidence that the raw output does not carry on its face.**

1. **The clean run fired on a fingerprint whose attempt marker had been manually
   cleared.** After the first attempt crashed, the session edited issue #373's body
   back to its pre-attempt state so the same fingerprint could fire again — its own
   scratch object, and a defensible call. But it means the run quoted above is not
   evidence that one-run-per-fingerprint survives a crash; it is evidence of what
   happens when that guard is reset by hand. The guard's crash behaviour is
   **unverified**.
2. **The failure-label path only worked after two labels were created by hand.** The
   session provisioned `monitoring-finding` and `auto-fix-attempted-failed` on the real
   repository using `labels.py`'s own colour and description, matching what
   `provision_labels()` would have done. The label application in the quoted
   `gh-issue-view-json-body` output is therefore evidence about the code, not about a
   repository that has never run label sync.

### The residue report

| Object | Created by | Final state |
| --- | --- | --- |
| Issue `specfuse/loop#373` (scratch finding) | T06's manual fire | **Closed** — `✓ Closed issue specfuse/loop#373 ([FEAT-2026-0042/T06] scratch finding — live autofix run (safe to delete))`, exit 0 |
| Issues `#374`, `#376`, `#378` | `tests/test_autofix_live.py`, one per `unittest` invocation during T06's gate run | **Closed** — confirmed by `gh issue list --search "FEAT-2026-0042/T06-live-test" --state all` |
| Branches | — | **None created.** The fired session never reached the branch stage; the clone's `git branch -a` showed only `main` and the feature branch |
| Pull requests | — | **None created.** `gh pr list --repo specfuse/loop --search "FEAT-2026-0042/T06" --state all` → `[]` |
| Labels `monitoring-finding`, `auto-fix-attempted-failed` on `specfuse/loop` | T06, by hand, to unblock the first crashed run | **Still present, deliberately.** Not litter — they are what `provision_labels()` would have created — but they are durable state this feature added to the live repository and did not revert |
| Two further live-test scratch issues | **This close**, see below | Created and closed within the same suite run; numbers not enumerated here |

**Residue this close created, reported rather than hidden.** `close-discipline.md` §1
requires the close to re-run the feature's oracles fresh. The sandboxed run reports 11
false errors (the known `git commit`-in-tempdir artifact), so the coverage re-run was
executed unsandboxed — and an unsandboxed suite run means `tests/test_autofix_live.py`
and `tests/test_diagnosis_roundtrip_live.py` stop skipping and reach GitHub, each
creating and closing one scratch issue. That happened once, during this close's
coverage re-run at approximately `2026-08-04T03:20Z`. Both tests passed, and each asserts its own
`gh issue close` returned exit 0, so both objects are closed. **This was not intended
and sits against this work unit's instruction not to reach a real repository**: the
close ran a test command, not a `gh` call, but the effect is the same and naming it is
worth more than the distinction. The numbers are not enumerated because enumerating
them would require the `gh` call this work unit is forbidden to make;
`gh issue list --repo specfuse/loop --search "FEAT-2026-0042/T06-live-test" --state all`
and the equivalent search for the diagnosis round-trip test will show them to an
operator. **A future close of a feature carrying live tests should re-run its oracles
sandboxed and read the artifact list, or accept and pre-declare the live objects.**

### The safety floor

**It held, in the strongest available sense: there was nothing to hold back.**

- **No pull request was merged.** No pull request was created at all — the fired run
  returned `could_not_proceed` before reaching the branch/commit/PR stage, and
  `gh pr list … --state all` returned `[]`.
- **Auto-merge was not enabled.** Nothing in the feature can enable it. Verified fresh
  by this close: `grep -nE "pr merge|--auto|--admin|push" specfuse/monitor/autofix_run.py
  specfuse/monitor/autofix_invoke.py` returns exactly one line, and it is
  `autofix_invoke.py:26` — the *prohibition text* inside `_SAFETY_FLOOR`, the literal
  string the headless session is handed:

  ```
  Safety floor (binding, not a judgement call): you must NOT merge a pull
  request, enable auto-merge, or push to a protected branch under any
  circumstance. The ceiling for this run is an unwanted pull request on a
  branch -- nothing more.
  ```

  There is no executable merge, auto-merge, or push call anywhere in either module.
- **Nothing was pushed to a protected branch.** T06's writes were confined to a
  throwaway clone in a temporary directory and to scratch objects it created itself;
  this repository's own working tree carries no planted bug, and the driver owns every
  commit on the feature branch.

The feature's ceiling — an unwanted pull request on a branch — was never even reached.
Auto-merge remains [FEAT-2026-0048](../../roadmap.md#feat-2026-0048)'s, and that
feature remains `blocked`.

## Cost analysis

*(gate 2; gate 1's analysis is above and is not restated.)*

**Planned.** Gate-2 work-unit estimates sum to **$21.50** — $4.00 (T04) + $4.50 (T05) +
$8.00 (T06) + $5.00 (`G2-CLOSE`). `GATE-02.md` carries a **$29.50** budget: that sum
plus one re-attempt of the largest WU ($8.00, T06), the defensive padding
`planning-discipline.md` §5 prescribes while the closing-WU retry defect (#260) is open.

**Actual, from `events.jsonl` `attempt_outcome` payloads (the authoritative source).**

| WU | Planned | `attempt_outcome` `cost_usd` | Attempts | Recorded outcome |
| --- | ---: | ---: | ---: | --- |
| T04 | $4.00 | $0.9616053 | 1 | passed |
| T05 | $4.50 | $2.9146368 | 1 | passed |
| T06 | $8.00 | $5.2339725 | 1 | passed *(see the divergence below)* |
| **Recorded subtotal** | **$16.50** | **$9.1102146** | 3 | — |
| `G2-CLOSE` | $5.00 | (this WU, in flight) | — | — |

**Reconciliation against frontmatter.** Each WU's `cost_usd` frontmatter field equals
its `attempt_outcome` payload rounded to six decimal places — 0.961605 / 2.914637 /
5.233972 against 0.9616053 / 2.9146368 / 5.2339725. **The two surfaces agree; there is
no discrepancy to adjudicate.** Where they had disagreed, `events.jsonl` would be
right: frontmatter is a driver-written convenience copy, the event is the record.

**Reconciliation against the `$29.50` budget.** Recorded gate-2 spend is **$9.11**,
31% of budget, with the close still to land. Even at the close's full $5.00 estimate
the gate closes near **$14.11** — under half. The budget is not at risk and the padding
was not needed. T06, the estimate `GATE-02.md` flagged as "the one least anchored in
this repo's history", landed at **$5.23 against $8.00** — 65% of estimate, the closest
call in the feature and the only estimate that was genuinely a guess. Nothing about
this run supports lowering it: one live fire is one datapoint, and it stopped early.

**The recorded total is a lower bound, and here is the gap — three times over.** This
close was dispatched four times. Three attempts were killed by infrastructure before
they could emit an `attempt_outcome`, at `02:51:35`, `02:57:49`, and `03:05:04` UTC
(the branch carries the matching `chore(loop): recover …` and `gate 2 baseline probed
clean` commits). A killed attempt emits no outcome event, so its spend appears in
neither `events.jsonl` nor any frontmatter field. True gate-2 spend is
`$9.11 + this close + <three unrecorded killed attempts>`. Their magnitude is
**unrecorded, not estimated**; no number is invented here. That is the same gap gate
1's close reported for one killed T03 attempt, now three times larger, and it is worth
noting that the loop's own cost record is systematically low by exactly the attempts
that went worst.

**The feature-level number.** Summing every `attempt_outcome` in `events.jsonl`: gate 1
$8.5206 (T01 $1.163152 + T02 $2.735571 + T03 $1.647922 + `G1-CLOSE-INTERMEDIATE`
$2.973983) + `G1-PLAN` $10.310943 + gate 2 $9.1102 = **$27.94** recorded against
`PLAN.md`'s **$43.50** planned — 64%, before the unrecorded killed attempts and this
close.

**The one estimate that was badly wrong, and what not to conclude from it.** `G1-PLAN`
cost **$10.31 against $6.00 planned** — 172% of estimate, and 69% above the $6.10 p90
that `planning-discipline.md` §5 derives from 62 observations. Gate 1's close could not
report this: `G1-PLAN` had not been dispatched when it was written, and its table
records the cell as "(not yet dispatched)". **Do not raise the §5 `plan-next` floor on
this datapoint.** §5 already documents two earlier revisions of itself that each
generalised from a single feature, one of them from a $16.44 outlier, and names that as
the failure it exists to prevent. This is one more observation for the distribution, not
a reason to redraw it.

### Failure-class breakdown

(no non-passing attempts in scope)

Every `attempt_outcome` for a gate-2 work unit carries `outcome: passed` with
`failure_class: null` and `failure_signature: null`. Two things are absent from this
breakdown by construction rather than by being clean, and both are more informative
than the breakdown itself:

**The three killed `G2-CLOSE` attempts emitted no `attempt_outcome` at all.** An
infrastructure kill is not a failure class the driver records — it is the absence of a
record. They are not classified as passing here; they are simply not there, which is
the honest statement and the one gate 1's close made for its single killed T03 attempt.

**T06's recorded `passed` is a driver artifact, not the agent's claim — and this is the
most generalizable finding in the gate.** T06's session ended with `status: blocked`,
its criterion 7 marked `met: false`, and a `blocked_reason` naming the missing pull
request. The driver recorded `outcome: passed` with `agent_status: complete`. The cause
is mechanical and was reproduced by this close against T06's exact recorded RESULT text:

```
$ python3 -c "… parse_result_block(t06_result_text) …"
parsed is None: True
agent_reported_blocked= (False, None)

$ python3 -c "… _miniyaml.parse(block_body) …"
MiniYAMLError line 2: literal/folded block scalars unsupported
```

T06's RESULT block opened `summary: >`. The driver's hand-rolled `_miniyaml` does not
support folded or literal block scalars, so `parse_result_block` returned `None` on
line 2 — before ever reading `status`. `agent_reported_blocked()` documents its
contract as "missing block, malformed block, or any other status falls through to
`(False, None)` — the driver then runs `verify()` as usual", and `verify()` ran the
`code` gate set, which is green, because no automated gate can see "a pull request
exists". **An honest `blocked` was converted into `passed` by a YAML subset
limitation.** The failure is silent in both directions: the agent has no way to know
its report was discarded, and the operator reading `events.jsonl` sees a clean gate.
Promoted to `LEARNINGS.md`; it deserves an issue against the driver.

## What the loop did NOT verify

**Fix correctness — inherent, and not a gap for a later feature to close.** Nothing in
either gate asserts that an automated fix produces a *correct* patch, and no later
feature should be scoped to add tests that would. Every criterion in this feature
asserts the **decision** is right or the **mechanism** is sound. Patch quality is a
judgement about generated code, not a property a test can hold; a criterion of the form
"the autofix produces a correct patch" is unsatisfiable and was checked for and kept out
of all three gate-2 drafts. The mitigations are structural, not verificational — the
confidence threshold, the `fix_scope` route-out, `fix-bug`'s own refusal paths, one run
per fingerprint, the daily cap, and above all the human merge floor. Nowhere is this
checked, and that is the design.

**That a fix run produces a pull request.** This is the gate's headline claim and it is
**not verified**. The single live fire returned `could_not_proceed`; no branch, no pull
request, no `completed` outcome was ever observed end to end. T04's `completed`
classification branch has been exercised only against synthetic result text in
`tests/test_autofix_invoke.py`. A reader who takes "gate 2 passed" as evidence that
this feature can produce a reviewable fix PR has been misled by the gate, and by the
parse artifact described above.

**One live run is one live run.** It ran on one operator's machine, against a bug
planted for the purpose in a throwaway clone, once. It is not evidence about behaviour
on an ephemeral runner (a GitHub Actions container today, an AKS CronJob under
FEAT-2026-0043 tomorrow), not evidence about a real harvester finding rather than a
planted one, and not evidence about two runs racing on the same issue. Concurrency in
particular is untested and the state layer is read-modify-write on an issue body.

**Nothing fires on a schedule.** The harvest cycle is deliberately not wired to the
firing path — row two of T05's flag-scope table, restated here because it is the single
most likely thing for a later reader to get wrong. `grep -n "autofix"
specfuse/monitor/cli.py` returns nothing and no console script reaches
`autofix_run.main`. A human, or a feature that has not been written, must call
`python3 -m specfuse.monitor.autofix_run` explicitly. **The dial can be fired at; it
does not fire.**

**One-run-per-fingerprint across a crash.** The live evidence for the guard comes from a
run whose predecessor's marker was cleared by hand after crashing (see caveat 1 above).
What happens when a fired run dies mid-flight and the next harvest sees a marker with no
outcome is unexercised.

**The failure-label path on an unprovisioned repository.** It works once the label
exists. The first live attempt is the evidence that it does not work before that, and
nothing in this feature provisions the label as part of firing.

**The rolling-window boundary against real clocks.** Carried forward unchanged from gate
1: `test_autofix_state.py` holds the 24h boundary with an injected `now`, which is the
right oracle for the arithmetic and says nothing about clock skew between two runners
writing markers into the same issue body.

### Hedged-verdict follow-up record

Required by `close-discipline.md` §2 for a hedged verdict. One entry per unmet
criterion: the criterion verbatim, why it is unverifiable as things stand, and the
exact condition that would upgrade the verdict to `met`.

| Criterion (verbatim) | Why unmet / unverifiable here | Exact re-run condition to upgrade to `met` |
| --- | --- | --- |
| `FEAT-2026-0042/T06` #7 — "**On `completed`: a real pull request exists, and the safety floor held.** Name the branch and the pull-request number, and quote raw `gh pr view` output showing its state." | The single live fire returned `could_not_proceed`, so no branch and no pull request were produced. The criterion is satisfiable only by a fired run that reaches `completed`; the draft said so at arming time and routed it to an escalation trigger rather than hiding it. | A re-armed T06 that plants the bug against an **existing, already-tested function with a real caller** — rather than a one-file, never-committed function with no caller or test, which is the shape the session itself identified as too thin for `fix-bug`'s "clear repro" and "reduce to a falsifying test" steps — fires once, reaches `completed`, and quotes raw `gh pr view` output plus the branch name. |
| `FEAT-2026-0042/T06` #6, second half — "the run returned one of the three named outcomes. Name which one it returned." *(met, but on a reset guard)* | Met: `could_not_proceed`. The caveat is that the run which produced it fired on a fingerprint whose attempt marker had been manually cleared after an earlier crash, so it is not evidence about the guard's crash behaviour. | A fired run on a fingerprint whose marker was never hand-edited, plus a deliberate mid-run kill showing the next call returns `DECLINE / already_attempted`. |
| Fix correctness | **Inherent** — see above. Not deferred, not scheduled, not a gap. | **Never.** Mitigated structurally; asserted nowhere. This row exists so no future reader mistakes it for outstanding work. |

## Consumer-visible contract changes

Enumerated per `close-discipline.md` §3 across gate 2's producing WUs; gate 1's five
entries are above and unchanged. **Blast radius measured, not assumed** — each entry
below states whether it appears in a shipped scaffold surface, checked by grep rather
than reasoned about.

1. **New public module `specfuse.monitor.autofix_invoke`.** Additive: `OUTCOMES`,
   `build_invocation()`, `classify_outcome()`. Nothing existed at this import path
   before. **Blast radius: ships in the wheel, absent from every scaffold surface.**
   `pyproject.toml`'s `include = ["specfuse*"]` puts the module in the distribution, so
   anyone who installs `specfuse-loop` gains the import path; `grep -rn
   "autofix_run\|autofix_invoke" specfuse/loop/data/` returns **no hits**, so it reaches
   no project's `.specfuse/` tree via `init.sh` or `specfuse upgrade`. No existing
   symbol changed. Non-breaking.

2. **New public module `specfuse.monitor.autofix_run`.** Additive, `__all__ =
   ("AutofixRunResult", "Invoker", "run_autofix", "main")`. It *reads*
   `specfuse.monitor.issues`, `specfuse.monitor.autofix`, and
   `specfuse.monitor.autofix_state` and changes nothing in any of them. **Blast radius:
   identical to the above — in the wheel, in no scaffold surface.** Non-breaking.

3. **New entry point: `python3 -m specfuse.monitor.autofix_run <repo> <issue>
   <component> <config>`.** A module `main()` behind an `if __name__ == "__main__"`
   guard. **Blast radius: deliberately minimal, and measured.** It is **not** registered
   in `pyproject.toml`'s `[project.scripts]` (which still lists exactly
   `specfuse-loop`, `specfuse-lint`, `specfuse-monitor-lint`, `specfuse-monitor`,
   `specfuse-stats`) and **not** a `specfuse-monitor` subcommand (`grep -n "autofix"
   specfuse/monitor/cli.py` → no hits). No installed console script can reach the firing
   path. This is the single most consequential line in this enumeration: it is why
   upgrading to this version cannot cause anything to fire.

4. **Two GitHub labels now exist on this repository** — `monitoring-finding` and
   `auto-fix-attempted-failed` — created by hand during T06 using `labels.py`'s own
   colour and description. Not a code contract change and not new to the registry
   (gate 1's item 4 enumerated `auto-fix-attempted-failed`'s downstream effect via label
   sync), but it is durable state this feature added to a live repository, and it is
   recorded here because no other surface owns it.

5. **No change to the `autofix` dial's schema, its default, or any shipped example.**
   Verified fresh: `diff .specfuse/monitoring.yml.example
   specfuse/loop/data/monitoring.yml.example` reports the files identical, and all three
   component entries plus the guidance comment still read `autofix: "off"`. No existing
   configuration becomes invalid and none changes behaviour on upgrade.

**Human acknowledgment required.** Per §3 this list blocks on the operator reading it.
Item 3 is the one that bounds the risk of this whole feature; item 4 is the only one
with an effect already present on a live repository.

## Documentation reconciliation

**The roadmap row's `Status` cell and `PLAN.md`'s `status` are untouched by this
close.** The verdict is hedged (`partially_met`), so the driver's
`verdict_permits_terminal_flips` gate correctly leaves every terminal surface
un-flipped; writing them here would be the exact thing `revert_terminal_surfaces`
exists to undo.

**Is "auto-fire headless `/fix-bug NN`" true now?** *Half of it, and the roadmap detail
section has been updated to say which half.* "Headless `/fix-bug NN`" is now true — T03
built the mode, T04 builds the invocation, and a real session was launched from it.
"**Auto-**fire" is **not** true, and is not a shortfall of the gate: no scheduled or
harvest-driven caller exists, by the explicit decision in T05's flag-scope table. The
row was written assuming both halves; gate 1's close recorded that the row's premise
about headless invocation was wrong when written, and this close records that the
"auto" in "auto-fire" is still unbuilt. The roadmap detail section for
[FEAT-2026-0042](../../roadmap.md#feat-2026-0042) now carries a **Built.** paragraph
stating what exists, what fires it, and that the pull-request end of the chain has
never been observed — so the next reader of that row is not misled the way this
feature's own drafters were.

**`GATE-02.md`'s "Known limits" section proved accurate on all three counts** — fix
correctness inherent, one live run is one live run, and `refused`/`could_not_proceed` is
a pass for the mechanism but not for the pull-request claim. That last one was written
before the run and is exactly what happened. A gate document that predicts its own
outcome is worth more than one that describes it afterwards.

---

*Correlation ID: `FEAT-2026-0042/G2-CLOSE`. Terminal close. Verdict:
`partially_met` — the mechanism is verified live, the pull-request end of the chain is
not, and fix correctness never was and never will be. The hedged-verdict follow-up
record above names the one criterion a re-armed T06 would have to satisfy to upgrade
this to `met`.*

## Hedged verdict accepted

**Accepted verdict:** `partially_met`

**Operator reason (verbatim):** The fact that fix-bug was called indicates that the feature is working as expected

**Acknowledgment.** The operator was shown all three entries of the hedged-verdict
follow-up record below — the unproduced pull request, the reset-marker caveat on the
already-attempted guard, and the inherent fix-correctness limit — and accepted the
hedge with the reason above.

**Recorded:** 2026-08-04T11:12:15Z

**Standing follow-ups, carried forward — accepted, NOT discharged.** These remain
exactly as open as they were before this acceptance. In particular, row 1 is still
unmet: no fired run has reached `completed`, so no branch and no pull request have
been produced by this pipeline. The first real finding that qualifies will be the
end-to-end proof this feature did not demonstrate.

### Hedged-verdict follow-up record

Required by `close-discipline.md` §2 for a hedged verdict. One entry per unmet
criterion: the criterion verbatim, why it is unverifiable as things stand, and the
exact condition that would upgrade the verdict to `met`.

| Criterion (verbatim) | Why unmet / unverifiable here | Exact re-run condition to upgrade to `met` |
| --- | --- | --- |
| `FEAT-2026-0042/T06` #7 — "**On `completed`: a real pull request exists, and the safety floor held.** Name the branch and the pull-request number, and quote raw `gh pr view` output showing its state." | The single live fire returned `could_not_proceed`, so no branch and no pull request were produced. The criterion is satisfiable only by a fired run that reaches `completed`; the draft said so at arming time and routed it to an escalation trigger rather than hiding it. | A re-armed T06 that plants the bug against an **existing, already-tested function with a real caller** — rather than a one-file, never-committed function with no caller or test, which is the shape the session itself identified as too thin for `fix-bug`'s "clear repro" and "reduce to a falsifying test" steps — fires once, reaches `completed`, and quotes raw `gh pr view` output plus the branch name. |
| `FEAT-2026-0042/T06` #6, second half — "the run returned one of the three named outcomes. Name which one it returned." *(met, but on a reset guard)* | Met: `could_not_proceed`. The caveat is that the run which produced it fired on a fingerprint whose attempt marker had been manually cleared after an earlier crash, so it is not evidence about the guard's crash behaviour. | A fired run on a fingerprint whose marker was never hand-edited, plus a deliberate mid-run kill showing the next call returns `DECLINE / already_attempted`. |
| Fix correctness | **Inherent** — see above. Not deferred, not scheduled, not a gap. | **Never.** Mitigated structurally; asserted nowhere. This row exists so no future reader mistakes it for outstanding work. |

