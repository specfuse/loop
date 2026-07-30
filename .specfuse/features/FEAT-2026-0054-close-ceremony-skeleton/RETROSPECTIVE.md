<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0054, Close-ceremony skeleton + in-session closing lint

**Verdict: `met_locally`.** Every gate-1 acceptance criterion that can be settled
inside an agent session was verified fresh in this session and passed, including the
load-bearing one — *lint-approves ⇒ guards-pass* — which was observed on a real
fixture dispatch, not argued from reading the source. Two criteria cannot be settled
here: the human acknowledgment that close-discipline §3 requires for the
contract-change list (an agent cannot supply the signature it is collecting), and the
portfolio success measure, which only a future feature's closing spend can show. Both
are recorded with exact re-run conditions under
[Hedged-verdict follow-up record](#hedged-verdict-follow-up-record).

One defect was found during verification, in a surface this WU is forbidden to patch:
`close-discipline.md` §4 describes the dispatch skeleton as creating more than it
actually creates. It is a prose-vs-mechanism gap, not a guard failure — the machinery
is correct and self-consistent. It is written up in full under
[The skeleton described and the skeleton shipped](#the-skeleton-described-and-the-skeleton-shipped)
and carried as follow-up **D3**.

## What shipped

| Unit | Deliverable |
|---|---|
| T01 | `specfuse/loop/closing_requirements.py` — 14 `Requirement` records across `close` (8), `close-intermediate` (4), `plan-next` (2), plus every shared literal (heading text, filename template, verdict set) the guards used to spell inline. The post-squash guards in `loop.py` now import from it. |
| T02 | `specfuse/loop/lint_closing.py` — `specfuse-lint --closing <feature-dir>`. Evaluates the in-progress closing WU against the registry over the **working tree**, pre-squash. Every finding is formatted `<req-id>: <reason> — would fail <guard> after squash`. Post-pass requirements are emitted as advisory `NOTE:` lines that never affect the exit code. |
| T03 | `precreate_dispatch_skeleton()` in `loop.py`, called from the attempt path before the agent session starts. Writes the `GATE-{N+1}-REVIEW.md` stub on `plan-next` dispatch, and retrospective section stubs on `close` / `close-intermediate`. Never writes a `verdict:` placeholder. Idempotent by per-section on-disk absence checks. |
| T04 | `close-discipline.md` §4 rewritten to point at the registry and the lint instead of restating guard strings; guard-defensive boilerplate deleted from `WU.template.md`; migration posture recorded (old guard-restating prose is inert, not wrong). |

## Oracles re-run fresh

close-discipline §1. Every command below was executed in this close session, exit code
read directly. No T01–T04 self-report is load-bearing anywhere in this document.

| Gate | Command | Exit | Result |
|---|---|---|---|
| tests | `python3 -m unittest discover -s tests -v` | 0 | `Ran 1875 tests in 62.592s` — `OK (skipped=3)` |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | 0 | `All checks passed!` |
| security | `bandit -r specfuse .specfuse/scripts -ll` | 0 | 0 medium, 0 high (89 low, all below the `-ll` threshold) |
| coverage | `coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90` | 0 | `TOTAL 5469 365 93%` |
| plan-lint | `python3 .specfuse/scripts/lint_plan.py <feature-dir>` | 0 | `OK — … is structurally valid.` |
| closing-lint | `specfuse-lint --closing <feature-dir>` | 0 | `CLOSING-READY` (after this document and the LEARNINGS entries landed; see below) |

Coverage of the surfaces this feature added or changed: `closing_requirements.py`
100%, `lint_closing.py` 83%, `loop.py` 92%, `lint_plan.py` 93%.

### The first full-suite run was red, and it was the environment

The first `unittest` run reported `FAILED (errors=11, skipped=3)`: 8 in
`test_lint_closing` (T02's own tests) and 3 in `test_autosync_no_cwd_leak`. Every one
died the same way — `git commit` returning 128 inside a throwaway repo, with
`error: Couldn't get agent socket?`. Cause: this machine sets `commit.gpgsign true`
with `gpg.format ssh` globally, and the sandbox this session runs under cannot reach
the ssh-agent socket, so every test that builds a scratch git repo fails to commit.
Re-running with signing disabled for the test process only —
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`, sandbox
still on — produced the green run recorded above.

This is worth naming rather than quietly working around, because it is the exact shape
of evidence a close is supposed to distrust: the tests that went red were the tests
belonging to the WU whose behaviour this close is checking, and the convenient reading
("T02 shipped something broken") was wrong. The cheap discriminator was that the
failures were in `_init_repo`, before any assertion ran.

Second-order note on my own process: an intermediate run reported 4 different errors in
`test_monitor_cli`, all `FileNotFoundError` on relative paths. That was my shell's
working directory having drifted into a scratch repo from an earlier command, not a
test-isolation defect. The clean run above was taken with the working directory pinned
to the repo root.

## End-to-end proof: lint-approves ⇒ guards-pass

This is the property the whole feature exists for, and the WU forbids closing `met` on
a source-reading argument for it. It was verified by executing both enforcement moments
against the same fixture trees in a throwaway git repo:
`/tmp/claude/e2e_closing_chain.py`, **51 checks, 0 failures, exit 0**.

The harness matters as much as the result, because the first two versions of it
reported divergences that were not real. The two enforcement moments read *different
git states by design*: `lint_closing` inspects the **working tree**
(`git status --porcelain`, `git diff HEAD`), while the post-squash guards inspect a
**commit range** (`git diff <head_before> HEAD`). Comparing them is only meaningful in
the order a real dispatch produces:

```
1. mutate the working tree          (what the agent session does)
2. lint the DIRTY tree              (pre-squash, in-session)
3. commit that exact tree           (the driver's squash)
4. run the guards over head_before..HEAD
```

Linting after step 3 makes the lint see a clean tree and report `close-b` / `close-c`
unmet while the guards pass — a false divergence produced entirely by the harness. Once
the harness reproduced the real ordering, **nine scenarios ran and the two moments
agreed in every one**, in both directions:

| Scenario | lint | guards | agree |
|---|---|---|---|
| A3 `plan-next`, skeleton untouched | 0 | pass | ✔ |
| A4 `plan-next`, `GATE-02-REVIEW.md` deleted | 1 | fail | ✔ |
| A5 `plan-next`, review restored | 0 | pass | ✔ |
| B4 `close`, skeleton only (agent wrote nothing) | 1 | fail | ✔ |
| B8 `close`, skeleton filled in — **the load-bearing case** | 0 | pass | ✔ |
| B10 `close`, `## Cost analysis` removed while `verdict: met` | 1 | fail | ✔ |
| B11 `close`, `### Failure-class breakdown` removed | 1 | fail | ✔ |
| B12 `close`, `verdict: mostly_met` (not in the allowed set) | 1 | fail | ✔ |
| B13 `close`, full re-attempt after a refusal | 0 | pass | ✔ |

Supporting observations from the same run:

- **The skeleton disarms the costliest guard.** `GATE-02-REVIEW.md` did not exist
  before dispatch; `precreate_dispatch_skeleton` created it; `assert_gate_review_exists`
  — $53.11 across 15 refusals per issue #261 — then passed with the agent having done
  nothing. Re-running pre-creation produced a byte-identical file.
- **Every finding names its later enforcer.** All findings across all scenarios matched
  `… — would fail assert_* after squash`. This is the FEAT-2026-0070 rule ("the earlier
  enforcer must name the later one") holding mechanically, not by convention.
- **The verdict window is respected.** With no `verdict:` written, the lint reported
  `close-b` and `close-d` and did *not* demand `close-e` (`## Cost analysis`); once
  `verdict: met` was written, `close-e` became live in the same session. No placeholder
  `verdict:` value was ever written into the WU file by the skeleton.
- **The guard bundle really ran.** `CLOSING_ASSERTIONS_BY_TYPE["close"]` holds all six
  pre-squash assertions and all six were executed on the lint-approved tree in B8.

## Idempotency, re-verified

Exercised fresh in this session (harness phase C), not inherited from T03's tests. A
feature directory was seeded with a hand-written `RETROSPECTIVE.md` already containing
`## Gate 1` prose, a `### Failure-class breakdown` table, and a
`## What the loop did NOT verify` section, then `precreate_dispatch_skeleton` was run
**three times** for a `close` WU and once more for a `close-intermediate` WU:

- C1 — prior content preserved byte-for-byte.
- C2 — no heading duplicated: `## Gate 1`, `### Failure-class breakdown`, and
  `## What the loop did NOT verify` each appear exactly once.
- C3 — the file was byte-identical afterwards; pre-creation was a pure no-op, appending
  nothing.
- C4 — the `close-intermediate` path did not re-add the `## Gate 1` section it would
  have created on an empty file.

## Historical-close regression

`specfuse-lint --closing .specfuse/features/FEAT-2026-0072-structural-invariant-guards`
exits **0**, as the criterion requires.

Stated precisely, because the exit code alone overstates it: 0072's close WU is
`status: done`, so the lint takes its no-closing-WU-in-progress path and prints
`CLOSING-READY — … (no closing WU currently in progress)`. What this regression proves
is that the lint does not crash, mis-parse, or invent findings on a real historical
feature folder authored long before the registry existed. It does not exercise the
requirement checks against that feature's artifacts, because a completed close has no
in-progress WU to evaluate. The requirement checks are exercised instead by the nine
fixture scenarios above.

## The skeleton described and the skeleton shipped

Verification found one real gap, and this feature's own close dispatch is the
demonstration.

`close-discipline.md` §4 — rewritten by T04, and shipped to every scaffold consumer —
tells the reader:

> Every `close` / `close-intermediate` / `plan-next` WU starts its session with the
> guard-required files and headings already scaffolded in place (`RETROSPECTIVE.md`,
> the `## Gate <N>` / `## Cost analysis` / `### Failure-class breakdown` sections, the
> `GATE-{N+1}-REVIEW.md` filename) […] You fill the skeleton in; you do not need to
> remember its shape from scratch.

What actually happened when this WU dispatched: **nothing was pre-created.** No
`RETROSPECTIVE.md`, no sections. Confirmed twice — by the feature directory listing at
session start, and by re-invoking `precreate_dispatch_skeleton` directly on this WU,
which returned having created the empty set. The first thing
`specfuse-lint --closing` said about this very feature was
`close-a: RETROSPECTIVE.md absent or empty in feature dir`.

That is not a bug in T03. It is what T03 was specified to do, and its behaviour is
internally consistent — every stub it writes is conditional:

| §4 promises | Mechanism actually writes it when |
|---|---|
| `GATE-{N+1}-REVIEW.md` | WU type is `plan-next` **and** a next gate exists. Never on a `close`. |
| `## Gate <N>` | WU type is `close-intermediate`. Never on a terminal `close`. |
| `### Failure-class breakdown` | Non-passing attempts exist **whose correlation ID parses to this gate** (see the filter caveat below). |
| `## Cost analysis` | **Never.** Deliberately excluded — it is verdict-conditional, and T03's docstring says so explicitly: pre-creation "never touches verdict-conditional headings such as `## Cost analysis`". |
| `RETROSPECTIVE.md` itself | Only as a side effect of one of the section stubs firing. A terminal `close` on a clean gate creates no file at all. |

So for the single most common closing shape — a terminal `close`, one gate, no
in-gate failures — §4 promises five things and the mechanism delivers zero. The prose
describes the union of every branch as though it were the guaranteed floor.

The irony is the point: this feature deleted a table of literal guard strings from this
rule *because a second copy of the requirements drifts*, and then reintroduced drift one
layer up — in the sentence describing the replacement. The lint is not affected; it
reads the registry and was correct about this feature throughout. Only the human-facing
sentence is wrong, and it is wrong in the expensive direction, telling a close agent it
can rely on a floor that is not there.

**Not patched here, deliberately.** The canonical file is
`specfuse/loop/data/rules/close-discipline.md`, inside this WU's do-not-touch boundary
(`specfuse/loop/**`), mirrored to `.specfuse/rules/close-discipline.md`; T04 owns both.
The WU's instruction for this case is explicit: *"if verification finds a defect,
escalate rather than patching here."* Carried as **D3**.

## Consumer-visible contract changes

close-discipline §3. This feature is scaffold infrastructure, so every item below
reaches every Specfuse-integrated project on its next `specfuse upgrade`. This section
is emphatically **not** `n/a`.

**1. `close-discipline.md` §4 was rewritten (behaviour-neutral, guidance-changing).**
The section that previously enumerated literal guard strings now points at
`closing_requirements.py` as the registry of record and at `specfuse-lint --closing` as
the mandatory pre-report check. No guard changed, was added, or was removed — the
enforcement surface is byte-for-byte the same set of assertions. What changed is what a
close agent is told to do before reporting. Consumers who wrote local process docs
quoting the old guard-string table will find those quotes now unreferenced by the rule.
*Caveat:* this rewritten section currently overstates the skeleton's coverage — see D3.

**2. `WU.template.md` lost its close-obligations boilerplate.** The guard-defensive
comment block that every newly drafted closing WU inherited is deleted. New WUs drafted
from the template will not carry it. Already-drafted WUs are unaffected and their stale
boilerplate is inert — the driver never read that prose, only the artifacts. Consumers
with a forked or vendored `WU.template.md` will see this as a conflict on upgrade.

**3. New CLI surface: `specfuse-lint --closing <feature-dir>`.** A new flag on an
existing entry point (no new binary). Exit 0 = every pre-squash-checkable closing
requirement met; exit 1 = at least one unmet, each printed as
`<req-id>: <reason> — would fail <guard> after squash`. Advisory `NOTE:` lines describe
post-pass requirements and never affect the exit code. This is additive; no existing
`specfuse-lint` invocation changes behaviour. Consumers wiring it into CI should note
that it is a *working-tree* check and is meaningful pre-squash, not after commit.

**4. New dispatch side effect: closing WUs may now start with files already on disk.**
This is the change most likely to surprise. Before this feature, a `close` /
`close-intermediate` / `plan-next` session began with whatever the agent inherited;
now the driver may have written `GATE-{N+1}-REVIEW.md` or appended stub sections to
`RETROSPECTIVE.md` *before the session starts*. Those files land in that WU's squash
commit and its diff. Anything downstream that asserts on closing-WU diff contents —
a review bot, a diff-size check, a `produces:`-shaped expectation — will see files the
agent did not author, each marked with an
`<!-- specfuse:skeleton-stub agent-completable -->` comment. Pre-creation is idempotent
and never clobbers existing content (verified above), but it is not a no-op on the diff.

**Human acknowledgment: not given.** close-discipline §3 requires this list to be
acknowledged by a human, and that unmet requirement is the primary reason the verdict is
hedged rather than `met`. Per `operator-escalation.md`, the acknowledgment must be the
operator's own words; an agent that drafts it has destroyed the signature it was
collecting. Tracked as **D1**.

## Cost analysis

Planned figures agree across both surfaces: `PLAN.md` frontmatter declares
`planned_cost_usd: 28.00`, and the five per-WU frontmatter values sum to exactly $28.00.
Gate 1's `cost_budget_usd` is $36.00.

| Unit | Planned | Actual | Delta |
|---|---|---|---|
| T01 — closing-requirement registry | $6.00 | $3.39 | −$2.61 (−44%) |
| T02 — `--closing` lint mode | $6.00 | $2.14 | −$3.86 (−64%) |
| T03 — dispatch skeleton pre-creation | $8.00 | $2.25 | −$5.75 (−72%) |
| T04 — contract surfacing (2 attempts) | $3.00 | $2.53 | −$0.47 (−16%) |
| **Subtotal, T01–T04** | **$23.00** | **$10.30** | **−$12.70 (−55%)** |
| G1-CLOSE — this session | $5.00 | not yet billed | — |
| **Feature total** | **$28.00** | **$10.30 + close** | — |

T04's $2.53 is two attempts: $1.21 for the attempt that blocked and $1.31 for the
re-armed attempt that passed. Even carrying a full escalation-and-re-arm cycle it came
in under its estimate.

**The delta named:** the four implementation units finished at **45% of plan**, and the
gate consumed **29% of its $36.00 budget** before the terminal close dispatched. Every
unit under-ran, which points at the estimator rather than at any one unit — this is a
refactor-shaped feature (the planning search found that every mechanism already had a
home, so three of four units were extension or reuse, not new construction), and it was
priced as though it were new construction. Compare FEAT-2026-0040, whose recorded lesson
was the opposite failure: a single unit at +295% consuming 97% of the gate budget before
its close. Sizing error in the cheap direction still costs something — it inflates the
padding that a genuinely expensive gate elsewhere in the portfolio could have used.

### Failure-class breakdown

One non-passing attempt in gate 1, out of six attempts total across five units.

| failure_class | non-passed attempts | dominant signature |
|---|---|---|
| `null` (agent-reported `blocked`, no gate ever ran) | 1 | T04 attempt 1 — WU do-not-touch clause contradicted repo ground truth |
| **total** | **1** | — |

T04's first attempt blocked without spinning: its WU body asserted that
`specfuse/loop/data/` is canonical for rules and templates and forbade editing
`.specfuse/rules/*` directly, while `scripts/sync-scaffold.sh` sets `SRC=.specfuse`
(canonical) and `DEST=specfuse/loop/data` (mirror). Satisfying the acceptance criteria
as written required either violating the do-not-touch clause or having the sync script
silently revert the work. The agent named the contradiction, cited the script lines and
the sync test's own header, and blocked in 202 seconds for $1.21 rather than guessing.
An operator re-armed it and the second attempt passed. This is the discipline working:
a plan-level contradiction reported as `blocked`, not written into a gate document and
closed `complete`.

**Filter caveat, and why this section exists at all.** The post-squash guard did *not*
require this section. `assert_failure_class_breakdown_when_failures_present` restricts
attempts to the current gate via `_gate_number_from_wu_id`, which only matches closing
IDs of the form `G<n>-…`; an implementation-WU ID like `FEAT-2026-0054/T04` parses to
`None` and is filtered out. Verified directly this session: the gate-filtered summary
for gate 1 reports no failures, while the unfiltered summary reports the one blocked
attempt. So a gate whose only non-passing attempts belong to implementation WUs — the
common case — can never trip this guard. That is pre-existing driver behaviour untouched
by this feature, so it is not this gate's defect to fix, but it is this close's business
to say out loud: the section is here because it is true, not because anything demanded
it. Carried as **D4**.

## What the loop did NOT verify

Two entries. The gate's criteria list has ten items, so this is 20% deferred — under the
30% threshold, and at (not above) the 2-entry threshold that would flag single-gate
sizing. Sizing is discussed under *What I'd change* on its own merits, not because this
list forced it.

1. **The portfolio success measure — closing-format refusal classes at zero
   occurrences.** `PLAN.md` records this explicitly as verified on the next generator
   feature, not in this repo, and the WU anticipates it as the expected entry. Nothing in
   this repository can produce the evidence: the measure is a *rate* over future closing
   attempts across the portfolio, and this feature's own close is a single data point
   that would be measuring the mechanism with itself. **Re-run condition:** after the
   next generator-class feature completes a multi-gate close on a driver carrying this
   feature, read its `events.jsonl` for `attempt_outcome` events with
   `failure_class: closing_deliverable_missing` on format-only assertions, or naming
   `assert_gate_review_exists`. Zero occurrences across that feature's closing WUs
   upgrades this to met.

2. **Human acknowledgment of the consumer-visible contract-change list.** close-discipline
   §3 requires the enumeration to be acknowledged by a human, and `operator-escalation.md`
   forbids an agent from drafting the acknowledgment it is collecting. **Re-run
   condition:** an operator reads the four numbered entries under
   [Consumer-visible contract changes](#consumer-visible-contract-changes) and
   acknowledges them in their own words — entry 4 in particular, since it changes what
   lands in every future closing-WU squash — via `/accept-hedged-close`, which records
   the reason and re-checks the verdict through the driver's `--recheck-verdict`
   primitive.

Note that D3 (the §4 overclaim) is deliberately *not* in this list: it was verified, and
it failed. It is a finding, not a deferral, and it lives in the follow-up record below.

## What worked

- **Extracting the registry first paid immediately.** T01 shipped nothing user-visible,
  and both T02 and T03 became small because of it — the lint's checkers and the skeleton
  writers read the same constants the guards read, so "do the lint and the guards agree?"
  reduces to "do they read the same registry?", which is a much cheaper question to keep
  true. The nine-scenario agreement result is downstream of that decision.
- **Making every finding name its post-squash guard.** `close-e: … — would fail
  assert_cost_analysis_section_when_met after squash` is directly actionable in a way
  that a bare "missing section" is not, and it means a close agent never has to hold the
  guard inventory in its head. It also makes divergence testable: I could assert on the
  *shape* of every finding, not just the count.
- **The planning-discipline existing-mechanism search.** PLAN.md's three-row search table
  found that the guards, the stub writers, and the CLI entry point all already existed,
  which is why three of four units were refactors. It also explains the cost under-run.
- **Blocking on a contradiction instead of guessing.** T04 attempt 1 cost $1.21 and
  produced an operator-actionable finding with citations. Three attempts of guessing at
  the canonical direction would have cost more and taught less.

## What I'd change

- **State a mechanism's trigger conditions, not its best case.** The D3 defect is a
  one-sentence overclaim, and it happened in the same edit that removed a duplicated
  guard table to prevent drift. Replacing duplicated machine detail with a pointer is
  right; the pointer then has to describe *when* the mechanism fires, or say nothing
  about coverage and let the lint be the answer. §4 should have read "pre-creation fills
  in whatever the registry can derive at dispatch time — run `specfuse-lint --closing` to
  see what is still missing" and stopped there.
- **Price refactor-shaped features as refactors.** A −55% gate-level under-run is a
  sizing miss even though it is the comfortable direction. When the existing-mechanism
  search concludes "every mechanism this feature needs has an existing home", that
  conclusion should feed the estimate, not just the design.
- **On single-gate sizing: one gate was right here.** Four substantive WUs with a clean
  dependency chain, one operator escalation, and a terminal close that had budget left to
  do real end-to-end work. The deferred list is two entries and both are structurally
  undeferrable-in-repo, not symptoms of an overstuffed gate. I would not split this.
- **The dogfood almost did not happen.** PLAN.md hoped this feature's own close would
  exercise T03's skeleton, and it technically did — by creating nothing, which is how the
  D3 gap surfaced. A fixture harness was needed anyway. Worth planning the fixture up
  front rather than treating the self-dogfood as the primary evidence, because the
  self-dogfood only covers whichever single branch the feature happens to land in.

## Issues resolved

- **#265** — closing-format guard requirements had no single machine-readable home and
  were duplicated into `close-discipline.md` prose. Resolved: `closing_requirements.py`
  is the registry both the guards and the lint read.
- **#261** — `assert_gate_review_exists`, "the costliest guard in the system" at $53.11
  across 15 refusals. Resolved: the correctly-named `GATE-{N+1}-REVIEW.md` stub is
  pre-created at `plan-next` dispatch; verified on fixture scenario A3, where the guard
  passed with the agent having done nothing.

## Lessons

Promoted to `.specfuse/LEARNINGS.md` — three entries: the state-model corollary for
two-moment enforcement, the pointer-prose drift rule, and the gate-filter blind spot in
the failure-class guard.

## Hedged-verdict follow-up record

close-discipline §2. One entry per criterion that is unmet or unverifiable here, with the
exact condition that upgrades it.

### D1 — Human acknowledgment of the contract-change list — OPEN

*Criterion, verbatim:* "**Consumer-visible contract changes enumerated and blocked on
operator acknowledgment (§3):** `close-discipline.md` §4 rewrite, `WU.template.md`
close-obligations change, the new `specfuse-lint --closing` surface, and the new dispatch
side-effect (skeleton files appearing in closing-WU squashes) — every scaffold consumer
sees these on next upgrade. Not `n/a`."

*Status:* the enumeration half is complete — all four items are written up above with
their upgrade impact. The acknowledgment half cannot be supplied by this session.

*Why unverifiable here:* an agent cannot give the human acknowledgment it was dispatched
to collect. `operator-escalation.md` names this explicitly as one of the three failures
the rule exists to prevent.

*Upgrade-to-met condition:* an operator reads
[Consumer-visible contract changes](#consumer-visible-contract-changes) and acknowledges
the four entries in their own words via `/accept-hedged-close`, which records the reason
and re-checks the verdict through the driver's `--recheck-verdict` primitive.

### D2 — Portfolio success measure: zero closing-format refusals — OPEN

*Criterion, verbatim (PLAN.md):* "closing-format refusal classes
(`closing_deliverable_missing` on format-only assertions, `assert_gate_review_exists`) at
zero occurrences."

*Why unverifiable here:* it is a rate over future closing attempts in other repositories.
This repo can produce at most one closing attempt, which is this one.

*Upgrade-to-met condition:* after the next generator-class feature closes on a driver
carrying this feature, scan its `events.jsonl` for `attempt_outcome` events with
`failure_class: closing_deliverable_missing` on format-only assertions or naming
`assert_gate_review_exists`; zero occurrences across that feature's closing WUs upgrades
this to met.

### D3 — `close-discipline.md` §4 overstates the skeleton's coverage — OPEN

*What is wrong:* §4 states that every closing WU starts with `RETROSPECTIVE.md`, the
`## Gate <N>` / `## Cost analysis` / `### Failure-class breakdown` sections, and the
`GATE-{N+1}-REVIEW.md` filename already in place. Each stub is in fact conditional, and
`## Cost analysis` is never pre-created by design. A terminal `close` on a gate with no
parseable in-gate failures — the most common shape, and the shape this very WU had —
receives nothing at all. Full analysis and the per-item table are under
[The skeleton described and the skeleton shipped](#the-skeleton-described-and-the-skeleton-shipped).

*Impact:* documentation only. No guard, no lint result, and no artifact is affected; the
lint reads the registry and was correct about this feature throughout. The risk is that a
close agent trusts a floor that is not there and skips a check the lint would have caught
in-session — which is the cost this feature was built to eliminate.

*Why not fixed here:* the canonical file is
`specfuse/loop/data/rules/close-discipline.md`, inside this WU's declared do-not-touch
boundary (`specfuse/loop/**`), mirrored to `.specfuse/rules/close-discipline.md`; T04
owns both, and the WU's instruction for a verification-found defect in that zone is to
escalate rather than patch.

*Upgrade-to-met condition:* §4's skeleton bullet is rewritten to describe the mechanism's
trigger conditions rather than the union of its branches (or to make no coverage claim
and defer to the lint), the change is applied to the canonical
`specfuse/loop/data/rules/close-discipline.md` and mirrored via
`scripts/sync-scaffold.sh` so `tests/test_scaffold_data_in_sync.py` stays green, and the
full suite is re-run.

### D4 — Failure-class guard cannot fire on implementation-WU failures — OPEN

*What is wrong:* `assert_failure_class_breakdown_when_failures_present` and the skeleton
writer both scope non-passing attempts to the current gate via `_gate_number_from_wu_id`,
which matches only `G<n>-…` closing IDs. An implementation-WU correlation ID such as
`FEAT-2026-0054/T04` parses to `None` and is filtered out, so a gate whose only
non-passing attempts are implementation WUs never triggers the requirement. Verified this
session by calling the summariser both ways on this feature's own `events.jsonl`.

*Impact:* the guard under-fires, and the skeleton correspondingly pre-creates nothing —
the two stay consistent with each other, so this is not a lint-vs-guard divergence, and
the property this feature ships is unaffected. The cost is that the retrospective section
whose entire purpose is accounting for failed attempts is not required in precisely the
case where attempts most commonly fail.

*Why not fixed here:* pre-existing driver behaviour in `specfuse/loop/loop.py`, untouched
by this feature and inside the do-not-touch boundary. Widening the filter would make an
existing guard fire on features it does not fire on today, which is a behaviour change
this feature's scope explicitly excludes ("any **new** guard … it adds none").

*Upgrade-to-met condition:* a follow-up feature decides whether gate attribution for
implementation WUs should come from the PLAN.md gate graph rather than from ID parsing;
if so, `_gate_number_from_wu_id`'s callers are changed to resolve a WU's gate through the
graph, with a test asserting that a `TNN` blocked attempt makes
`assert_failure_class_breakdown_when_failures_present` fire for its gate.
