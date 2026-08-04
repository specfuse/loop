<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0059: a hedged close answers "why not `met`" before it is asked

Single terminal gate, three implementation work units, one close. Every WU passed on
its first attempt with no escalations, and the whole gate's substantive spend came in
at **$6.12 against $9.50**.

The feature's real test is not in the suite. This close hedges — `met_locally` — so
**its own follow-up record is the first one ever written under the contract T01
shipped**, and the section [Was classifying easier than prose?](#was-classifying-easier-than-prose)
reports what that was actually like. No test can produce that evidence.

## Gate 1 — the classification, the headline, and the queue

### What was built

**T01 — the `kind:` contract and the lint that means it (`done`, 1 attempt, $2.774868
against $3.50).** `close-discipline.md` §2 gains a fourth required field per follow-up
entry: a `kind:` from a closed set of four. `specfuse/loop/closing_requirements.py`
holds the set (`FOLLOW_UP_KIND_MEANINGS` / `FOLLOW_UP_KINDS`), the entry-matching
regex (`KIND_FIELD_RE`), the hedged-verdict set (`HEDGED_VERDICT_VALUES`), and the one
function that turns a set of kinds into a verdict ceiling
(`verdict_ceiling_for_kinds`, returning `REWORK_EXISTS` or `NO_IN_REPO_REWORK`).
Requirement `close-j` (`applies_when: verdict_hedged`, phase `pre-squash`) is enforced
by `_check_hedged_followup_kinds_classified` in `lint_closing.py`. Oracle:
`tests/test_hedged_kind_contract.py`, red on HEAD before the WU ran because no such
check existed at all.

**T02 — lead with the ceiling, not the quotes (`done`, 1 attempt, $2.023180 against
$3.50).** `/accept-hedged-close`'s step 2 was rewritten to read every entry's `kind:`
**before printing anything**, compute the ceiling through T01's helper, and print the
headline first — `"no in-repo rework can raise this verdict"` or `"rework exists:
<the named re-run condition>"` — with entry detail after it rather than before. Step
3's reason prompt is scaffolded from that ceiling: it names *what is being accepted*
and supplies no reason text. Oracle: `tests/test_accept_hedged_close_headline.py`.

**T03 — a routed finding gets a queue, not a paragraph (`done`, 1 attempt, $1.318926
against $2.50).** Each `routed-finding` entry now prompts for its tracking surface —
an existing issue or roadmap reference, `create` to run `/roadmap-add` or `gh issue
create`, or `"nowhere, deliberately"` — and the answer is written into the acceptance
record **next to the entry it belongs to**, not as a loose appendix. The prompt is
explicitly non-blocking: any answer is accepted, because a mandatory sub-decision
would turn a single-confirm skill into the multi-step interrogation this feature
exists to remove. The other three kinds never trigger it, with the reason stated in
the skill. Oracle: `tests/test_routed_finding_tracking.py`.

### Oracles re-run fresh (close-discipline §1)

Re-run in this session, exit codes read directly — not inherited from any WU's
self-report. The full `code` gate set from `.specfuse/verification.yml`, plus the
three feature oracles by name.

```
$ .venv/bin/python -m pytest tests/test_hedged_kind_contract.py \
      tests/test_accept_hedged_close_headline.py \
      tests/test_routed_finding_tracking.py \
      tests/test_accept_hedged_close_skill.py \
      tests/test_skill_discovery_links.py tests/test_scaffold_data_in_sync.py
64 passed in 2.69s
EXIT=0

$ .venv/bin/python -m unittest discover -s tests
Ran 2206 tests in 91.870s
OK (skipped=3)
TESTS_EXIT=0

$ .venv/bin/ruff check specfuse .specfuse/scripts tests scripts
All checks passed!
LINT_EXIT=0

$ .venv/bin/bandit -r specfuse .specfuse/scripts -ll
SEC_EXIT=0

$ .venv/bin/coverage run --source=specfuse -m unittest discover -s tests \
      && .venv/bin/coverage report --fail-under=90
TOTAL   6950   457   93%
COV_EXIT=0

$ python3 .specfuse/scripts/leak_scan.py --all
leak-scan: gitleaks 8.30.1
leak-scan: clean
LEAK_EXIT=0

$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 49 events.jsonl file(s), 1150 event(s) checked
EVENT_GATE_EXIT=0

$ python3 .specfuse/scripts/roadmap_link_gate.py
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 8 warning(s)
ROADMAP_GATE_EXIT=0

$ python3 .specfuse/scripts/arm_sweep_gate.py
evaluable=10 evaluated=10 could_not_evaluate=0 excluded_no_baseline=42
ok: 10 evaluable feature(s) swept clean, no not_evaluable verdicts
ARM_SWEEP_EXIT=0
```

**Both mirror pairs are byte-identical**, asserted rather than claimed:

```
$ diff specfuse/loop/data/rules/close-discipline.md .specfuse/rules/close-discipline.md
RULES_IN_SYNC exit=0

$ diff plugins/specfuse/skills/accept-hedged-close/SKILL.md \
       .specfuse/skills/accept-hedged-close/SKILL.md
SKILL_IN_SYNC exit=0
```

**A sandbox artefact, recorded so the next close does not misread it.** The first
targeted run of `tests/test_hedged_kind_contract.py` inside the command sandbox
produced **5 false failures**, all with the same cause: every test that builds a
scratch repository hits `git commit`, and commit signing needs an SSH agent socket the
sandbox denies —

```
error: Couldn't get agent socket?
fatal: failed to write commit object
returned non-zero exit status 128
```

Re-run unsandboxed, the same five pass. This is the same class of trap
FEAT-2026-0042's close hit from the other direction (a live test that fires when the
suite runs unsandboxed) and is promoted to `LEARNINGS.md` below.

### The four kinds versus the roadmap row's three

The roadmap row proposed three — `acceptance-discharged`, `externally-verifiable-later`,
`routed-finding`. **This feature shipped four**, adding `inherent`. That was a
decision, not an oversight, and the evidence is a record that already exists in this
repository.

FEAT-2026-0042's close had to invent the category in prose, because the contract had
no slot for it. Its third follow-up entry reads:

> *"Fix correctness — **Inherent.** Not deferred, not scheduled, not a gap.
> **Never.** Mitigated structurally; asserted nowhere. This row exists so no future
> reader mistakes it for outstanding work."*

Shipping three values would have forced the next close to invent it a second time, in
different words, and left a reader with no mechanical way to distinguish *"nobody has
done this yet"* from *"this can never be done"* — which is exactly the distinction the
operator needs to decide whether to accept or wait.

The addition costs the ceiling rule nothing. Only `externally-verifiable-later` implies
rework exists; `inherent` collapses to `NO_IN_REPO_REWORK` alongside
`acceptance-discharged` and `routed-finding`, for a different reason each time. Four
kinds, two ceilings, one function.

`PLAN.md`'s scope boundary holds the line on a fifth: four cover every entry across
the three hedged closes observed, and a new one gets added when a real close needs it,
not speculatively.

### The lint's scope is the satisfiability guarantee, held as a test

Two hedged records already exist — FEAT-2026-0041's and FEAT-2026-0042's
retrospectives — and neither carries `kind:`, because both predate it. A check that
swept `.specfuse/features/*/RETROSPECTIVE.md` would have satisfied every other
criterion in T01 and been **red on arrival**, unfixable without rewriting closed
features' history.

`close-j` reads only `ctx.feature_dir`'s own `RETROSPECTIVE.md`. T01's criterion 6
holds that as a test rather than a claim: it plants a malformed record in a *different*
feature's retrospective and asserts no finding is produced. This is the shape
FEAT-2026-0060 paid two blocked attempts and $4.48 to learn, and it did not repeat.

### Consumer-visible contract changes

Per `close-discipline.md` §3. **Not `n/a`** — this feature changes a rule contract that
ships in the scaffold, so every downstream project inherits these on its next upgrade.
This list is the raw material [FEAT-2026-0064](../../roadmap.md#feat-2026-0064)'s
CHANGELOG will consume, so it is enumerated per surface rather than summarised as
"the rules changed".

1. **`close-discipline.md` §2 gains a required per-entry field.** Every hedged close in
   every downstream project must now write `kind:` on each follow-up entry, from a
   closed set of four. This is an **addition to a required contract**: a hedged close
   that would have passed before now fails the lint. Unhedged closes (`verdict: met`)
   are unaffected — `close-j` is `applies_when: verdict_hedged`.
2. **`specfuse-lint --closing` gains requirement `close-j`.** New failure line:
   `close-j: ... has no **kind:** field` / `... has kind '<x>', not one of [...]`. A
   project that greps the lint's output will see an ID it has not seen before.
3. **The record's entry format is now machine-read.** `KIND_FIELD_RE` matches
   `**kind:** \`<value>\`` and entries are split on `^### `. A record written in a
   different shape (a YAML block, a table row, `kind:` unbackticked) lints as
   *missing*, not as *differently formatted*. This is the one item most likely to
   surprise a project that already writes §2 records by hand.
4. **`closing_requirements.py` gains public names.** `FOLLOW_UP_KIND_MEANINGS`,
   `FOLLOW_UP_KINDS`, `HEDGED_VERDICT_VALUES`, `HEDGED_RECORD_HEADING`,
   `HEDGED_RECORD_HEADING_RE`, `KIND_FIELD_RE`, `REWORK_EXISTS`, `NO_IN_REPO_REWORK`,
   and `verdict_ceiling_for_kinds()`. Additive; nothing was removed or renamed.
5. **`/accept-hedged-close` changes its output shape.** Step 2 now prints a ceiling
   headline **before** any entry detail, where it previously opened with the quoted
   record. An operator or script that expected the record first sees a different first
   line. Additive in content, reordered in presentation.
6. **`/accept-hedged-close` gains a per-entry prompt on `routed-finding`.** One
   additional question per routed entry, non-blocking, any answer accepted. It does not
   change the skill's single-confirm posture and never fires for the other three kinds.
7. **The acceptance record gains per-entry tracking answers.** Written next to the
   entry, not appended — a consumer parsing `## Hedged verdict accepted` sees
   interleaved content it did not see before.
8. **`docs/methodology.md` and `WU.template.md` restate the four-field record.** Both
   previously described §2 as three fields. A close WU drafted from the template now
   gets the `kind:` obligation and its literal format in the template text.

**Acknowledgment is outstanding.** §3 requires the human to acknowledge this list, and
an agent cannot supply the acknowledgment it was dispatched to collect. That is entry
**D1** below and is the reason this close is `met_locally` rather than `met`.

## Cost analysis

`events.jsonl`'s `attempt_outcome` sum is authoritative. Reconciled against every WU
frontmatter figure exactly — **no gap, no lower bound needed on the implementation
side**.

| Work unit | Planned | Attempts | Actual | Variance |
|---|---|---|---|---|
| T01 — `kind:` contract + lint | $3.50 | 1 | **$2.774868** | −$0.73 (−20.7%) |
| T02 — verdict-ceiling headline | $3.50 | 1 | **$2.023180** | −$1.48 (−42.2%) |
| T03 — routed-finding tracking | $2.50 | 1 | **$1.318926** | −$1.18 (−47.2%) |
| **Implementation subtotal** | **$9.50** | **3** | **$6.116974** | **−$3.38 (−35.6%)** |
| G1-CLOSE — this session | $5.00 | 1 (in flight) | not yet in `events.jsonl` | — |
| WU sum incl. close | $14.50 | — | $6.12 + close | — |
| Gate budget | $19.50 | — | headroom before close: **$13.38** | — |

Per-attempt ledger, in emission order:

```
T01 attempt 1  passed   $2.7748677   -> task_completed cost_usd 2.774868
T02 attempt 1  passed   $2.0231799   -> task_completed cost_usd 2.023180
T03 attempt 1  passed   $1.3189263   -> task_completed cost_usd 1.318926
                        -----------
attempt_outcome sum      $6.1169739
```

Frontmatter reconciliation, each line checked independently:

- T01 `cost_usd: 2.774868` = its single `attempt_outcome` ✔
- T02 `cost_usd: 2.02318` = its single `attempt_outcome` ✔
- T03 `cost_usd: 1.318926` = its single `attempt_outcome` ✔
- Sum of all three = $6.116974 = the `attempt_outcome` total ✔
- Every `task_completed` `cumulative_cost_usd` equals its `cost_usd` (no re-arms) ✔

**The close WU's own spend is not in this total.** `G1-CLOSE` is in flight as this file
is written; the driver appends its `attempt_outcome` after the session. $6.12 is
therefore complete for implementation and a **lower bound for the gate**. At $13.38 of
headroom against a $5.00 close estimate, the gate lands inside $19.50 unless the close
overruns by 168%.

**GATE-01.md's estimating note was right, and for the reason it gave.** It set
implementation estimates below this repo's drafting habit deliberately, citing
FEAT-2026-0034 landing $2.21 and $1.17 against $4.00 and $3.50, and still came in 36%
under. The pattern now has enough repetitions to be a habit rather than a run of luck:
implementation WUs in this repository are consistently over-estimated, closing WUs
consistently under-estimated, and issue #260 tracks the `planning-discipline.md` §5
floor that produces the second half of that split. This gate is one more data point for
#260 and the first in a while where the padding was never needed — no re-attempt, no
escalation, nothing to absorb.

### Failure-class breakdown

**No non-passing attempts.** Three implementation WUs, three attempts, three passes,
zero escalations, zero re-arms, $0.00 of spend on failure. There is no breakdown to
give.

That is worth one sentence of analysis rather than none: all three WUs were authored
with a named red-on-HEAD oracle and a `produces:` list that matched what the work
actually touched, which are the two conditions FEAT-2026-0073's close identified as the
root of its own four wasted attempts (`produces_not_in_diff`, `deliverable_missing`,
`files_changed_mismatch` — all one root cause, a declared path with no honest diff).
T02 and T03 deliberately **share** two `produces` paths, and `WU-03` says so in prose
with the ordering constraint spelled out; that is the shape that usually produces a
mismatch, and naming it in the body appears to have been sufficient.

## What the loop did NOT verify

Per `close-discipline.md` §2 and the deferred-verification obligation. Three entries.
No predecessor auto-close debt markers exist in this feature (single gate, no
auto-close), so `close-g` has nothing to reconcile.

**1. Whether the ceiling headline actually helps a human decide faster.**

- *Criterion:* the feature's whole reason for existing — that an operator reading
  `/accept-hedged-close`'s output learns *why this isn't `met`* without having to ask.
  `PLAN.md` grounds it in a measured question: on FEAT-2026-0042 the operator asked,
  verbatim, *"why did it not complete with met?"*
- *Why it was not verified in-loop:* **no test can measure it.** The suite asserts the
  headline is printed, that it is printed *before* the entry detail, that both branches
  are named, and that the kind→ceiling mapping is documented. Every one of those is a
  fact about the file's text. Whether a human reading that text decides faster is an
  observation about a person, and the tests are silent on it. This close does not claim
  otherwise, and a reader should not read seven green oracles as evidence for it.
- *Where it actually gets checked:* an operator running `/accept-hedged-close` on the
  next real hedge — which is **this feature's own hedge**. Carried as follow-up **D2**
  below with its exact re-run condition.

**2. Human acknowledgment of the consumer-visible contract-change list.**

- *Criterion:* `close-discipline.md` §3 — enumerate every consumer-visible change and
  **block on explicit human acknowledgment**.
- *Why it was not verified in-loop:* the enumeration half is complete (eight items
  above). The acknowledgment half cannot be supplied by the session that was dispatched
  to collect it; `operator-escalation.md` names authoring the human's side as one of the
  failures the rule exists to prevent.
- *Where it actually gets checked:* the operator reads
  [Consumer-visible contract changes](#consumer-visible-contract-changes) and
  acknowledges it in their own words via `/accept-hedged-close`. Carried as **D1**.

**3. That `routed-finding` and `inherent` behave correctly on a real record.**

- *Criterion:* T03's prompt, and the ceiling contribution of `inherent`, on an entry a
  close actually wrote rather than a fixture.
- *Why it was not verified in-loop:* this close's own record legitimately contains
  neither kind (see D1 and D2 — one `acceptance-discharged`, one
  `externally-verifiable-later`). Both are covered by unit tests against constructed
  records, and `verdict_ceiling_for_kinds` is tested per branch including the empty set.
  What is missing is an end-to-end run over a real record containing them.
- *Where it actually gets checked:* the first hedged close whose record carries a
  `routed-finding` or `inherent` entry. Not carried as a follow-up of this feature —
  fabricating an entry of each kind to exercise the code would have made the record
  dishonest, which is a worse outcome than an untested path. Recorded here so the gap
  is named rather than silent.

**Not a gap, recorded to prevent a misreading:** FEAT-2026-0041's and
FEAT-2026-0042's unclassified records are **deliberately not migrated**, per
`PLAN.md`'s scope boundary and `GATE-01.md`'s known-limits section. They are records of
what those closes knew at the time. A future reader finding them without `kind:` has
not found outstanding migration work.

**One pre-existing finding reproduced, owned elsewhere.** `close-discipline.md` §4
states that every closing WU starts its session with the guard-required files and
headings already scaffolded in place, `RETROSPECTIVE.md` among them. This session
started with **no `RETROSPECTIVE.md` at all** — `specfuse-lint --closing` opened with
`close-a: RETROSPECTIVE.md absent or empty in feature dir`. That is exactly
FEAT-2026-0054's follow-up **D3** (*"§4 overstates the skeleton's coverage"*),
reproduced verbatim on a terminal close with no in-gate failures — the shape D3 named
as receiving nothing. It is documentation-only, affects no guard or artifact, is owned
by that feature's follow-up list, and is **not** re-raised here as a follow-up of this
feature. It is noted because a second sighting is evidence the first was not a one-off.

## Hedged-verdict follow-up record

`close-discipline.md` §2. Verdict: **`met_locally`**. One entry per unmet criterion —
the criterion verbatim, why it is unverifiable here, the exact re-run condition that
upgrades it, and a `kind:`.

**Computed ceiling: `rework exists`** — D2 is `externally-verifiable-later`, so
`verdict_ceiling_for_kinds({acceptance-discharged, externally-verifiable-later})`
returns `REWORK_EXISTS` and the operator has a real choice between accepting now and
waiting for D2's named condition. See the note under
[Was classifying easier than prose?](#was-classifying-easier-than-prose) — the word
"rework" reads oddly for this particular pair, and that is a finding, not a defect.

### D1 — Human acknowledgment of the consumer-visible contract-change list — OPEN

- *Criterion, verbatim:* "Consumer-visible contract changes are enumerated per
  `close-discipline.md` §3, or the explicit `n/a` line is written. At least two are
  known: `close-discipline.md` §2 gains a required field (every downstream project's
  next hedged close must supply it), and `/accept-hedged-close` changes its output
  shape."
- *Status:* the enumeration half is **complete** — eight items, above, each with its
  consumer impact. Not `n/a`. The acknowledgment half is outstanding.
- *Why unverifiable here:* an agent cannot give itself the human acknowledgment §3
  requires. `operator-escalation.md`'s never-author rule forbids the substitute.
- *Exact re-run condition that upgrades to `met`:* an operator reads
  [Consumer-visible contract changes](#consumer-visible-contract-changes) and
  acknowledges the eight items in their own words via `/accept-hedged-close`, which
  records the reason and re-checks the verdict through the driver's
  `--recheck-verdict` primitive.
- **kind:** `acceptance-discharged`
- *Ceiling contribution:* none — no in-repo rework can discharge this; accepting **is**
  the discharge.

### D2 — Whether the ceiling headline helps a human decide faster — OPEN

- *Criterion, verbatim:* "`## What the loop did NOT verify` names the one thing tests
  cannot reach: whether the ceiling headline actually helps a human decide faster. No
  test can measure that; it is verified only by an operator running
  `/accept-hedged-close` on the next real hedge, and the close should say so rather
  than imply the tests covered it."
- *Status:* the section is written and says exactly that. The underlying claim — that
  the ergonomics improved — is unverified.
- *Why unverifiable here:* it is an observation about a human's reading experience. The
  suite can assert the headline exists, precedes the detail, names both branches, and
  maps all four kinds; it cannot assert that any of that changed a decision. `PLAN.md`
  measured the *problem* (the operator's verbatim question on FEAT-2026-0042); only a
  real run can measure the *fix*.
- *Exact re-run condition that upgrades to `met`:* an operator runs
  `/accept-hedged-close --feature FEAT-2026-0059` against this very record and reports
  whether the printed ceiling headline (`rework exists: <D2's condition>`) answered
  *"why isn't this `met`?"* before they had to ask — and whether the scaffolded reason
  prompt named what was being accepted clearly enough to write a reason against. A
  plainly-stated "no, it did not help" is a valid result and would be better evidence
  than the tests currently supply; it downgrades nothing already asserted.
- **kind:** `externally-verifiable-later`
- *Ceiling contribution:* **this is the entry that makes the ceiling
  `rework exists`.* The re-run condition is real and named, so the operator's choice
  between accepting now and waiting is a genuine one — with the loop this feature ties:
  the run that would discharge D2 is the same run that discharges D1.

## Was classifying easier than prose?

Acceptance criterion 3 asks this close to report plainly whether classifying its own
gaps was easier or harder than writing the old free-prose record. This is the only
evidence the feature works that no test could have produced, so it gets a straight
answer rather than a favourable one.

**Easier, and the saving was specific rather than general.** Two things changed
concretely against the shape of FEAT-2026-0054's and FEAT-2026-0042's records:

1. **The "is this a gap or is this the ceiling?" paragraph disappeared.** Both prior
   records spend real prose distinguishing "nobody has done this yet" from "this can
   never be done" — FEAT-2026-0042 needed three sentences and a bolded **Never.** to
   say `inherent`. Here the distinction is one token per entry, and the prose is free
   to describe the criterion instead of defending its own category.
2. **The ceiling was computed, not argued.** Under the old contract this close would
   have had to reason, in prose, about whether an operator had a real alternative to
   accepting. With two `kind:` values written, that answer is a function call, and the
   record states it rather than making a case for it.

**Harder in one specific way, and it is worth recording.** Deciding D2's kind took real
thought. "An operator observes whether the headline helped" is upgradeable at a named
condition, so `externally-verifiable-later` is correct — but the first instinct was
`inherent`, because *"no test can measure this"* pattern-matches to "not assertable,
ever". The distinction that resolved it: `inherent` means **nobody** can ever assert
it; `externally-verifiable-later` means **no test in this environment** can, but a
named party at a named moment can. A close that reaches for `inherent` whenever the
suite is silent will over-use it, and the four-kind table's one-line definitions do not
draw that line as sharply as this paragraph does. That is promoted to `LEARNINGS.md`.

**One honest wrinkle in the output.** The computed ceiling for this record is
`rework exists`, because D2 is `externally-verifiable-later`. The string is accurate
under the rule's definition and the mechanical derivation is right — but for this pair
of entries there is no *rework* in the ordinary sense; both entries are discharged by
the same single operator run, and neither asks for code. An operator reading
`"rework exists: an operator runs /accept-hedged-close..."` may briefly expect there is
something to build. The rule is correct; the word is doing double duty for "a re-run
condition exists". Not raised as a follow-up — it is a wording observation on a
one-instance sample, and `PLAN.md`'s posture on speculative additions applies to
speculative rewordings too. If a second close reports the same friction,
`NO_IN_REPO_REWORK`/`REWORK_EXISTS` are two string constants in one module and the fix
is cheap.

**The contract was exercised by its own feature.** That was the interesting outcome
available here, and it landed: this record is the first one written under it, the lint
that refuses an unclassified record was run against it (below), and it passed.

## Lessons promoted

Three entries appended to `.specfuse/LEARNINGS.md`, tagged `FEAT-2026-0059/G1-CLOSE`:

1. **A contract that makes a close classify its own gaps beats one that asks for
   prose** — the generalizable form of this feature, assessed as criterion 6 asked. It
   does generalize beyond hedged verdicts: the property is that the party with the
   context supplies one bounded token, and every downstream reader gets a mechanical
   answer instead of a reading of prose.
2. **A "no test can assert this" category needs the *who* and *when*, not just the
   *whether*** — the D2-vs-`inherent` distinction above, which cost this close real
   deliberation on a four-value set.
3. **A sandbox that denies the commit-signing agent turns every scratch-repo test
   red** — the `Couldn't get agent socket?` trap, and its inverse sibling from
   FEAT-2026-0042.

## Closing state

- Verdict: **`met_locally`** (`WU-90-gate-1-close.md` frontmatter).
- Terminal surfaces stay un-flipped by design — gate `awaiting_review`, roadmap row
  `active`, `PLAN.md` `active`. This close does not write any of them;
  `fire_terminal_flips` is their one owner, gated on `verdict_permits_terminal_flips`.
- `specfuse-lint --closing` exits 0 against this record — including `close-j`, the
  check this feature shipped, run against the first record ever written under it.
- The path out is `/accept-hedged-close`, which discharges D1 and D2 in the same run.
