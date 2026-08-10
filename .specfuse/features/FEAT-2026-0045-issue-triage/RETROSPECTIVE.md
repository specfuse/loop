<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0045: mechanism in a module, judgment in a skill

Terminal close for the feature's single gate. Correlation ID
`FEAT-2026-0045/G1-CLOSE`.

**Verdict: `met_locally`.** This is the verdict `PLAN.md` predicted at draft time, not
one discovered here. Every gate is green, and green means *the mechanism works over
fixture issue JSON with an injected runner* — a strictly smaller claim than "triage
works". The two surfaces that would make it the larger claim are unreachable from inside
a dispatched session and are recorded below with their `kind:` and re-run conditions.

## Gate 1

### What was built

Three substantive work units, one terminal close, one gate.

- **`T01` — `specfuse/loop/triage.py`, the deterministic half.** The closed category
  vocabulary `CATEGORIES = ("bug", "feature", "duplicate", "question", "wontfix")` and
  `CONFIDENCES = ("high", "low")`; the total category→route map behind `route_for`
  (`bug`→`fix-bug`, `feature`→`roadmap-add`, `duplicate`→`link-and-close`,
  `question`→`needs-human`, `wontfix`→`close`); the category→label projection behind
  `label_for`; the marker pair `render_marker` / `parse_marker` over
  `<!-- specfuse:triage category={category} confidence={confidence} -->`; and
  `list_untriaged`, which lists open issues over an injected runner and filters
  client-side on the marker's absence. Plus four `LabelSpec` entries in
  `specfuse/loop/labels.py` importing their names from `triage.py` rather than retyping
  them, and one new public predicate `has_finding_marker` in
  `specfuse/monitor/issues.py` so `triage.py` never re-types the finding-marker literal.
- **`T02` — `apply_triage(runner, repo, decisions, *, auto=False)`, the write path.**
  Marker first, label projection best-effort, idempotent on a body that already carries
  a marker, and a failed label write recorded in the returned report rather than raised.
  The `auto` dial downgrades a non-`high` confidence to the `question` category routed
  to `needs-human` — still marked, which is the point.
- **`T03` — `/triage-issues`, the judgment half.** Canonical at
  `plugins/specfuse/skills/triage-issues/SKILL.md`, vendored byte-identically into
  `.specfuse/skills/`, forward-symlinked from `.claude/skills/`. Its oracle is a drift
  test binding the documented vocabulary and routes to the module's constants.

The seam held. `triage.py` decides what counts as untriaged, what is already structured,
where a category routes, and how a decision is recorded. It never classifies free text —
no unit test in this feature claims otherwise, and the skill's own Version section says
so in its own words.

### Oracles re-run fresh (`close-discipline.md` §1)

Every oracle the feature's acceptance criteria name was re-run **in this session**, exit
codes read directly. No producing WU's self-report was inherited.

| Oracle | Command | Exit | Result |
|---|---|---|---|
| T01 AC2 — module symbol existence | `python3 -c "from specfuse.loop.triage import CATEGORIES, CONFIDENCES, route_for, render_marker, parse_marker, list_untriaged"` | **0** | all six names importable |
| T01 AC3 — monitor symbol existence | `python3 -c "from specfuse.monitor.issues import has_finding_marker"` | **0** | new public predicate importable |
| T02 AC2 — write-path symbol existence | `python3 -c "from specfuse.loop.triage import apply_triage"` | **0** | importable |
| T01/T02/T03 unit oracles | `python3 -m unittest tests.test_triage tests.test_triage_apply tests.test_triage_skill_contract tests.test_label_registry` | **0** | 26 tests, `OK` — including `test_untriaged_excludes_marked_issue`, `test_auto_dial_skips_low_confidence`, `test_marker_precedes_label_for_same_issue`, `test_label_failure_recorded_not_raised`, `test_second_call_over_marked_issue_performs_no_write`, `test_skill_vocabulary_matches_module` |
| T03 AC4 — **`tests.test_skills_vendored_in_sync`** | `python3 -m unittest tests.test_skills_vendored_in_sync` | **0** | 4 tests, `OK` — plugin and vendored copies byte-identical, no symlinks in either tree |
| T03 AC4 — direct tree comparison | `diff -r plugins/specfuse/skills/triage-issues .specfuse/skills/triage-issues` | **0** | no output |
| T03 AC5 — discovery symlink | `readlink .claude/skills/triage-issues` → `../../.specfuse/skills/triage-issues`; target `SKILL.md` exists | **0** | resolves, target present |
| T03 forward-completeness | `python3 -m unittest tests.test_skill_discovery_links` | **0** | `OK` |
| T03 AC6 — drift test is not proof | `grep -n "proof that an agent following" plugins/specfuse/skills/triage-issues/SKILL.md` | **0** | SKILL.md:155 |
| T03 AC7 — `duplicate` has no detection | `grep -n "no detection mechanism" …/SKILL.md` | **0** | SKILL.md:37, restated at :120 |
| T03 AC8 — "does NOT do" names route-acting | `grep -n "What this skill does NOT do" …/SKILL.md` | **0** | SKILL.md:116, first bullet is "Does not act on a route" |
| **The full `code` gate set** | `bash scripts/smoke-test.sh` | **0** | `smoke test: OK` — every gate in `.specfuse/verification.yml` |
| `plannext` gate | `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0045-issue-triage` | **0** | structurally valid |

The `code` set was run through `scripts/smoke-test.sh` rather than a hand-picked subset,
because that script derives its gate list from `.specfuse/verification.yml` and therefore
cannot drift from CI. Inside it: **2533 tests `OK` (3 skipped)**, `ruff` clean, `bandit`
clean at medium+, **coverage 93% overall** against the 90% floor with
`specfuse/loop/triage.py` itself at **93%**, leak-scan clean, event-type gate, roadmap-link
gate, arm-sweep gate, monitoring-example lint, and all six `bats` suites green.

Nothing in this feature calls live GitHub, in the tests or in the gates. That was a design
requirement, not a shortcut — see the constraint section in `PLAN.md`.

### The one thing that went wrong

`T03` attempt 1 failed `files_changed_mismatch` on `.claude/skills/triage-issues
(symlink)`: the attempt declared the discovery symlink as a changed path without having
run `scripts/sync-scaffold.sh`, which is what creates it. Attempt 2 ran the script and
passed. Cost: **$1.327890**, 22.9% of the feature's implementation spend, on a guard
doing exactly its job — the alternative was a WU reporting `done` on a deliverable that
did not exist.

The lesson generalizes and is promoted below: a path produced by a helper script is only
declarable once the script has actually been run in that attempt.

## Consumer-visible contract changes

Per `close-discipline.md` §3. **Not `n/a`.** Five items, each with its consumer impact.
Every one of them is **additive** — nothing was removed, renamed, or made stricter, and
no previously-passing consumer breaks. The enumeration found nothing that was not
planned; all five trace to a decision recorded in `PLAN.md` before dispatch.

1. **`specfuse/loop/triage.py` is a new importable module in the wheel.** Public surface:
   `CATEGORIES`, `CONFIDENCES`, `BUG_LABEL`, `FEATURE_LABEL`, `DUPLICATE_LABEL`,
   `WONTFIX_LABEL`, `CATEGORY_LABEL_MAP`, `route_for`, `label_for`, `render_marker`,
   `parse_marker`, `list_untriaged`, `apply_triage`. Nothing previously occupied that
   import path. `CATEGORIES` and `CONFIDENCES` are **closed tuples by contract** — a
   sixth category or a third confidence is a scope change, not a code change, and both
   `route_for` and `label_for` raise on a non-member rather than returning a default.
2. **`specfuse.monitor.issues.has_finding_marker` is a new public symbol** in the monitor
   package. `T01` added it so `triage.py` need not re-type the finding-marker literal
   that `issues.py` already owns. Purely additive: no existing public behaviour in that
   module changed, and the predicate is a one-liner over the private `_MARKER_PREFIX`
   convention already there. A consumer that had been recognising harvester issues by
   re-typing the literal should switch to this predicate.
3. **Four new labels in `LABEL_REGISTRY`: `triage:bug`, `triage:feature`,
   `triage:duplicate`, `triage:wontfix`.** The registry goes from nine entries to
   thirteen. Every consumer repository must run `provision_labels` to have them created
   on GitHub. **This is a cosmetic-degradation contract, not a hard requirement** — the
   distinction §3 asks for. Per `PLAN.md`'s "tolerate absence" decision, `apply_triage`
   records a failed label write in its returned report and never raises, so a repository
   that never provisions still gets *correct* triage: the marker lands, the category is
   authoritative, and only the colour swatch in the GitHub UI is missing. A repository
   that does provision gains four labels it did not have. `question` deliberately reuses
   the **existing** `triage-question` label rather than minting a fifth.
4. **The triage marker format is now a published contract:**
   `<!-- specfuse:triage category={category} confidence={confidence} -->`. FEAT-2026-0048
   will read it as its machine-readable intake. **Once an issue in any repository carries
   one, changing this format orphans that issue** — it would scan as untriaged forever and
   be re-triaged on every run. Treat the format as frozen; a future change needs a
   migration that reads both shapes, not an edit.
5. **`/triage-issues` is a new skill in the published plugin** at
   `plugins/specfuse/skills/triage-issues/SKILL.md`, vendored into `.specfuse/skills/` and
   discovery-symlinked from `.claude/skills/`. Any project upgrading its scaffold gains a
   new slash command. It writes nothing without a per-issue operator accept and never acts
   on a route.

Appended to `CHANGELOG.md`'s `Unreleased` section under `### Added`, five entries tracing
to `FEAT-2026-0045` — the same enumeration, put where a consumer reads it.

**Human acknowledgment is outstanding.** §3 requires a human to acknowledge this list, and
an agent cannot supply the acknowledgment it was dispatched to collect —
`operator-escalation.md`'s never-author rule forbids the substitute. That is entry **D3**
in the hedged record below.

## Cost analysis

`events.jsonl`'s `attempt_outcome` sum is authoritative. It reconciles **exactly** with
the independent `task_completed` sum ($5.800839 both ways) and with every work unit's
frontmatter `cost_usd` field. No gap, no lower bound needed.

| Work unit | Planned | Attempts | Actual | Variance |
|---|---|---|---|---|
| T01 — triage mechanism | $4.50 | 1 | **$2.412055** | −$2.09 (−46.4%) |
| T02 — write path + `auto` dial | $5.00 | 1 | **$1.002454** | −$4.00 (−79.9%) |
| T03 — `/triage-issues` skill | $3.50 | 2 | **$2.386330** | −$1.11 (−31.8%) |
| **Implementation subtotal** | **$13.00** | **4** | **$5.800839** | **−$7.20 (−55.4%)** |
| G1-CLOSE — this session | $5.00 | 1 (in flight) | not yet in `events.jsonl` | — |
| **WU sum incl. close** | **$18.00** | — | $5.800839 + this close | — |
| **Gate budget** | **$23.00** | — | headroom before close: **$17.199161** | — |

Per-attempt ledger, in emission order:

| # | WU | Attempt | Outcome | Cost | Duration |
|---|---|---|---|---|---|
| 1 | T01 | 1 | `passed` | $2.412055 | 1381.0s |
| 2 | T02 | 1 | `passed` | $1.002454 | 728.0s |
| 3 | T03 | 1 | `files_changed_mismatch` | $1.327890 | 756.5s |
| 4 | T03 | 2 | `passed` | $1.058440 | 751.4s |

Total wall-clock across the four implementation attempts: **3617.0s (60.3 min)**.

**Reading the variance honestly.** The $18.00 WU sum and $23.00 gate budget were both
overestimates by a wide margin, and the $5.00 padding `planning-discipline.md` §5 asks for
was never needed — the one re-attempt cost $1.33, and the implementation set still came in
at 45% of its estimate. That is not a planning success to celebrate: a plan that
over-reserves by 55% is as poorly calibrated as one that under-reserves, it just fails
safely. The likely cause is that all three units were narrow, fixture-tested, pure-Python
work against an existing convention rather than a new one — the cheapest shape this
repository builds — and the estimates were drawn from features that had to invent their
seam. Estimate this shape lower next time.

### Failure-class breakdown

Four `attempt_outcome` events across the gate's implementation units. One non-passing.

| Failure class | Count | Share of attempts | Cost | Where |
|---|---|---|---|---|
| `files_changed_mismatch` | 1 | 25% | $1.327890 | T03 attempt 1, signature `triage-issues (symlink)` |
| (passed) | 3 | 75% | $4.472949 | T01, T02, T03 attempt 2 |

The single failure is described under "The one thing that went wrong" above. It was a
declaration error, not a defect in the deliverable, and the guard caught it pre-squash.

## What the loop did NOT verify

Four things. The first two are the deferred acceptance surfaces `PLAN.md` named at draft
time; the third is a deliberate scope decision; the fourth is a bookkeeping note.

1. **Triage against a live GitHub repository.** Nothing in this feature ever called `gh`.
   Every test injects a fake runner and asserts over fixture issue JSON. So the following
   are all unobserved: that `gh issue list --json number,title,body,labels` returns the
   shape `_list_open_issues` parses; that `gh issue edit --body` preserves a marker
   appended to a real body; that `gh issue edit --add-label` fails the way
   `apply_triage`'s tolerance path expects when a label is unprovisioned; and that the
   marker survives GitHub's own body rendering. Recorded as **D1** below.
2. **That an agent following `SKILL.md`'s prose reproduces the module's routing on an
   unseen issue.** The drift test proves the documented vocabulary and routes match
   `triage.py`'s constants — that prose has not drifted from code. It proves nothing about
   classification quality. No test in this repository composes the skill with the module
   end-to-end. Recorded as **D2** below.
3. **`duplicate` shipped with no detection mechanism, by operator decision at draft time.**
   The module gives the category a marker, a route (`link-and-close`) and a label, and
   nothing else — no similarity search, no automatic linking, no candidate suggestion. The
   skill proposes it from reading and the operator confirms. This was a considered
   trade-off recorded in `PLAN.md`'s scope boundary: cutting the category entirely would
   have left the skill unable to express one of the most common triage outcomes, so it
   ships judgment-only rather than not at all. It is named here so no future reader infers
   from the green suite that detection exists. Related and equally undecided: whether a
   *stale* triage should ever be revisited. v1 is "marked means done".
4. **No predecessor auto-close debt markers exist to reconcile.**
   `grep -rn "specfuse:autoclose-debt" .specfuse/features/FEAT-2026-0045-issue-triage/`
   returns nothing (exit 1). This feature has one gate, dispatched with
   `auto_close_disabled: true`, so no gate in it auto-closed and there is no debt for the
   terminal close to inherit. `close-g` is a post-pass check and is not verifiable in this
   session; this is the observation it would be checking against.

## Hedged-verdict follow-up record

`close-discipline.md` §2. Verdict: **`met_locally`**. One entry per unmet criterion — the
criterion, why it is unverifiable here, the exact re-run condition that upgrades it, and a
`kind:`.

**Computed ceiling: `rework exists`** — D1 is `externally-verifiable-later`, so
`verdict_ceiling_for_kinds({externally-verifiable-later, inherent, acceptance-discharged})`
returns `REWORK_EXISTS`. The operator has a real choice between accepting this hedge now
and waiting for D1's named condition. Note what that choice does *not* include: D2 is
`inherent` and will never be assertable by any in-repo work, so a `met` verdict on this
feature is unreachable through D2 no matter what is built. Accepting the hedge is the
expected outcome, not a fallback.

### D1 — Triage against a live GitHub repository — OPEN

- *Criterion, verbatim:* "A repository can scan its open issues, obtain a per-issue
  category and route, and have that decision recorded in an authoritative body marker
  projected to a human-visible label — interactively through `/triage-issues`, or
  headlessly behind an explicit `auto` argument that applies only high-confidence
  decisions." (`GATE-01.md`, Definition of done.)
- *Status:* proven over fixture issue JSON with an injected runner, at every branch —
  scan, marker round-trip, write order, idempotency, label-failure tolerance, and the
  `auto` downgrade. Unproven against a real GitHub repository.
- *Why unverifiable here:* `gh` does not work inside a dispatched `claude -p` session. The
  symptom is an invalid-token error from `gh auth status` and a TLS certificate failure
  from `gh issue view`, while the same token succeeds from the operator's own shell; the
  cause is the command sandbox, corrected in `[FEAT-2026-0014/T01/gh-claudeP-broken]` by
  FEAT-2026-0041 after the original mis-diagnosis blamed the `gh` binary. `PLAN.md` made
  "no work unit has live GitHub as its oracle" a design requirement for exactly this
  reason, so this gap is structural to the environment and not a hole in the test set.
- *Exact re-run condition that upgrades to `met`:* post-merge, the operator runs
  `/triage-issues` from their own shell against this repository's own open issues,
  accepts at least one decision in each of two categories, and confirms by inspection
  that (a) the accepted issues' bodies carry
  `<!-- specfuse:triage category=… confidence=… -->`, (b) the projected `triage:*` label
  appears on each — or, if `provision_labels` has not been run, that the report records
  the label write as failed and the run did not raise, and (c) a second `/triage-issues`
  run does not re-propose those issues. A plainly-reported failure at any of the three is
  a better result than the fixtures can supply and downgrades nothing already asserted.
- **kind:** `externally-verifiable-later`
- *Ceiling contribution:* **this is the entry that makes the ceiling `rework exists`.* The
  re-run condition is real, named, and cheap — one operator session, no code.

### D2 — An agent following the skill's prose reproduces the module's routing — OPEN

- *Criterion, verbatim:* "An agent following T03's prose reproduces the module's routing
  on an unseen issue." (`WU-90-gate-1-close.md`; the underlying claim behind `GATE-01.md`'s
  "`/triage-issues` exists at the canonical plugin path and is vendored in sync".)
- *Status:* the drift test `test_skill_vocabulary_matches_module` passes — every member of
  `CATEGORIES` appears in `SKILL.md`, every route string appears, and `SKILL.md` names no
  category outside `CATEGORIES`, with the constants imported rather than hardcoded. That
  is prose-code agreement, which is worth having and is all it is.
- *Why unverifiable here:* no test in this repository composes the skill with the module.
  Doing so would require executing an agent against unseen issue text and scoring its
  classification — skill-composition testing, which does not exist in this repository and
  is a feature in its own right, not a fix for this one. This is precisely the gap
  `[FEAT-2026-0069/G2-CLOSE]` records, applied at authoring time rather than discovered at
  close, and the skill's own Version section states the limitation so the passing test is
  never read as "the skill is proven".
- *Exact re-run condition that upgrades to `met`:* **none exists.** No re-run of any
  current or plausible in-repo oracle upgrades this. It would take building
  skill-composition testing — a harness that drives an agent over a labelled corpus of
  issue text and scores routing against `route_for` — and that is a different feature with
  its own scope, budget, and acceptance criteria. Until such a harness exists, the honest
  statement is the one in `SKILL.md`.
- **kind:** `inherent`
- *Ceiling contribution:* none, and it caps the feature: this entry can never be
  discharged by in-repo rework, so `met` is unreachable through it.

### D3 — Human acknowledgment of the consumer-visible contract-change list — OPEN

- *Criterion, verbatim:* "Consumer-visible contract changes are enumerated per the section
  above, with human acknowledgment — or the explicit `n/a` line if the enumeration
  genuinely comes up empty, which it should not."
- *Status:* the enumeration half is **complete** — five items above, each with its consumer
  impact, and all five appended to `CHANGELOG.md`'s `Unreleased`. Not `n/a`. The
  acknowledgment half is outstanding.
- *Why unverifiable here:* an agent cannot give itself the human acknowledgment §3
  requires. `operator-escalation.md`'s never-author rule forbids the substitute.
- *Exact re-run condition that upgrades to `met`:* an operator reads
  [Consumer-visible contract changes](#consumer-visible-contract-changes) — paying
  particular attention to item 4, the marker format, which FEAT-2026-0048 will depend on
  and which cannot be changed once issues carry it — and acknowledges the list in their
  own words via `/accept-hedged-close`, which records the reason and re-checks the verdict
  through the driver's `--recheck-verdict` primitive.
- **kind:** `acceptance-discharged`
- *Ceiling contribution:* none — no in-repo rework can discharge this; accepting **is** the
  discharge.

## Handoff to FEAT-2026-0044 — the `auto` dial has no permanent home yet

**This is an unfinished handoff, not a shipped feature.** Reported here explicitly so
FEAT-2026-0044's drafting session finds the decision rather than re-deciding it. The same
paragraph is recorded in that feature's roadmap detail section, which is where drafting
actually reads.

The `auto` dial exists today as an explicit keyword argument —
`apply_triage(runner, repo, decisions, *, auto=False)` — and reads no configuration file
of any kind. That was a deliberate choice, not an oversight: `.specfuse/agent-policy.yml`
is FEAT-2026-0044's core deliverable and does not exist. Building a minimal reader here
would have taken 0044's scope, left it shipping against a partial schema someone else
authored, and declared a config surface nothing consumes — the drift shape FEAT-2026-0058
exists to prevent. The `autofix` dial was checked as a precedent and rejected: it is
per-*component* in `monitoring.yml`, and inbound issues are not components, so no existing
file had a legitimate claim on this dial.

**What FEAT-2026-0044 must do:** wire its policy file to this parameter. The parameter
already exists, is already tested at both settings (`test_auto_dial_skips_low_confidence`
and `test_auto_false_applies_decision_as_given`), and its exact behaviour is fixed — under
`auto=True` a decision whose confidence is not `high` is recorded as the `question`
category and routed to `needs-human`, **still marked**, never skipped. 0044 supplies the
value; it does not need to redesign the semantics, and it should not re-litigate where the
dial lives.

## FEAT-2026-0048's blocker set, as measured

Measured, not assumed. `.specfuse/roadmap.md:854` reads:

> **Blocked by.** [FEAT-2026-0045](#feat-2026-0045) — needs machine-readable triage
> intake; [FEAT-2026-0046](roadmap-archive.md#feat-2026-0046) — refusals and guardrail
> failures escalate through the contract

Two blockers. FEAT-2026-0046 is **`done`** (`.specfuse/roadmap.md:64`, archived detail
section reads `**Status: done.**`). FEAT-2026-0045 — this feature — is **not yet `done`**.

**The set is therefore not empty, and no roadmap edit is due yet.** On a hedged verdict the
driver deliberately withholds the terminal flips: the gate stays `awaiting_review`,
`PLAN.md` stays `active`, and this feature's roadmap row stays `active`. So at the moment
this close finishes, 0048 still has one live blocker — this one.

**What makes the set empty, and the edit that follows.** The operator accepts this hedge
via `/accept-hedged-close`, which re-checks the verdict through the driver's
`--recheck-verdict` primitive and fires the terminal flips, at which point FEAT-2026-0045
reads `done`. *Then*, and only then, both of 0048's blockers are `done` and the edit is:
change the status column of the `| FEAT-2026-0048 | … |` row (`.specfuse/roadmap.md:66`)
from `blocked` to `planned`, change `**Status: blocked.**` to `**Status: planned.**` in its
detail section (`.specfuse/roadmap.md:856`), and remove or annotate the `**Blocked by.**`
line at `.specfuse/roadmap.md:854` — `roadmap_link_gate.py` emits a WARN (non-failing) for
a Blocked-by block on a non-blocked row, so leaving it there is untidy rather than broken.

**This close does not perform that flip.** It is the operator's, per this WU's do-not-touch
list, and it is not due until the acceptance above has happened.

Note for whoever makes it: 0048 also consumes the marker format (contract item 4). It
should read this retrospective's contract-change section before it starts, not after.

## Lessons promoted

Three entries appended to `.specfuse/LEARNINGS.md`, each tagged `[FEAT-2026-0045/G1-CLOSE]`.
Both candidates the WU named were assessed; both were promoted, with the second reframed.

1. **Declare precedence between two redundant records** — promoted, and it generalizes well
   past marker-vs-label. The usual response to "two records of one fact will drift" is to
   cut one; the cheaper move is often to declare which one wins, make the other a
   projection, and order the writes so the authoritative one lands first. Stated generally
   because the shape recurs anywhere a machine-readable fact needs a human-visible echo.
2. **The verb-check table** — promoted as a **recommendation to standardize**, not as a
   restatement of the practice. Assessed rather than assumed: it earned its keep here,
   finding one of four roadmap-row verbs ("behind an `auto` dial") backed by nothing that
   exists, which is what produced the dial decision above instead of a mid-gate block. One
   in four is a high enough hit rate to justify the table's cost. But making it a *standard
   section* is an edit to `planning-discipline.md`, which is a rule change and not this
   WU's to make — so the LEARNINGS entry records the evidence and names the recommendation
   for whoever next touches that rule.
3. **A script-produced path is not declarable until the script has run** — from this gate's
   one real failure, generalized past `sync-scaffold.sh` to any deliverable a helper
   generates.

## Closing state

- Gate 1: all three implementation units `done`; this close is the fourth and last unit.
- Verdict: **`met_locally`**, as `PLAN.md` predicted. Ceiling: `rework exists` (D1).
- The driver owns every terminal flip. On a hedged verdict it withholds them by design, so
  the gate stays `awaiting_review`, `PLAN.md` stays `active`, and the roadmap row stays
  `active` until an operator accepts through `/accept-hedged-close`. Nothing here was
  hand-flipped.
- Next: `/accept-hedged-close FEAT-2026-0045` (acknowledging the contract list discharges
  D3 at the same time), then `/wrap-feature`, then D1's live-repository run — and only
  after that, the FEAT-2026-0048 roadmap edit named above.

## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Recorded:** 2026-08-10T00:31:13Z

**Operator's reason, verbatim:** "accepting since D2 can never close"

**Operator's acknowledgment of the consumer-visible contract-change list, verbatim:**
"marker format is fine"

The operator confirmed they read all three follow-up entries as quoted before accepting.

**Computed ceiling at acceptance:** `rework exists`, from
`verdict_ceiling_for_kinds({externally-verifiable-later, inherent, acceptance-discharged})`
— named by D1.

### Standing follow-ups, carried forward

Accepting this hedge ships the feature with these open. It does not discharge them. They
are reproduced exactly as the hedged-verdict follow-up record above states them; no entry
is dropped, paraphrased, or marked done.

**D1 — Triage against a live GitHub repository — OPEN.** `kind: externally-verifiable-later`.
Carried forward as written.

> **Evidence note, recorded alongside D1 rather than inside it.** D1's named re-run
> condition was executed in the operator's own shell on 2026-08-10, before this
> acceptance and ahead of the sequence the closing state above anticipated. What ran:
> `list_untriaged` against this repository returned 25 untriaged rows; three were accepted
> across three categories (#796 `bug`, #298 `feature`, #248 `question`); all three bodies
> carried a parseable marker afterwards (`('bug','high')`, `('feature','high')`,
> `('question','high')`); a second scan returned 22 and re-proposed none of them; and
> re-applying the same decisions returned `skipped=True` with no second write. The label
> half split usefully: `triage-question` was already provisioned so #248's label wrote,
> while `triage:bug` and `triage:feature` were registered but not yet created, so those
> two writes failed, were recorded in the report, and did **not** raise — the live
> confirmation of this feature's "registered is not provisioned" decision, which no
> fixture could have produced. `provision_labels` was then run (created all four
> `triage:*` labels, zero failures).
>
> **This note does not close D1.** The entry stays OPEN because this skill does not
> discharge follow-ups, and because the run surfaced a defect that qualifies the result
> (below). Whoever revisits D1 should read this note and the defect together.

**D2 — An agent following the skill's prose reproduces the module's routing — OPEN.**
`kind: inherent`. Carried forward as written. No re-run condition exists; `met` is
unreachable through this entry by any in-repo work. This is the entry the operator's
acceptance reason names.

**D3 — Human acknowledgment of the consumer-visible contract-change list — OPEN.**
`kind: acceptance-discharged`. Carried forward as written. The operator's acknowledgment
recorded above is this entry's discharge condition; it is left OPEN in this record because
this skill does not mark entries discharged.

### Defect found by D1's run, filed rather than folded in

`apply_triage`'s idempotency check keys on the **marker alone**, so an issue whose marker
wrote but whose label write failed is skipped on every later run and can never have its
label projected — even after the label is created. Confirmed live: after `provision_labels`
created `triage:bug` and `triage:feature`, re-applying #796 and #298 returned
`skipped=True, label_written=False` and both issues remained unlabelled.

`PLAN.md` justified the marker-first order by calling a missing label "cosmetic and
**repairable**", and `WU-02` restated it as "merely lacks a swatch". The ordering decision
is still correct; the word "repairable" was unearned, because no code path repairs it.

Filed as **https://github.com/specfuse/loop/issues/1163** with the full evidence trail and
two candidate fix shapes. The two affected issues were hand-repaired
(`gh issue edit --add-label`) so the repository ends in the intended state; that repair is
outside `apply_triage` and is not a fix.
