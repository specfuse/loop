# Retrospective — FEAT-2026-0058, feature decision registry + override lint

## Gate 1

**Verdict: `partially_met`.** Every work unit is `done`, every named oracle
re-ran green in this session, and the lint ships at ERROR severity as `PLAN.md`
D2 required. What is not met is the gate's own headline claim about the
load-bearing half of the guard: measured against this feature's own artifacts,
the non-restatement check is inert on the one file that actually restates. The
per-entry follow-up record is below.

### What shipped

- `specfuse/loop/decisions_format.py` — the `DECISIONS.md` parser: entry ID,
  statement, owner, a bounded `status`, provenance, and the three override
  provenance fields. A malformed entry lands in `ParseResult.errors` rather
  than being dropped.
- `.specfuse/templates/DECISIONS.template.md` and its packaged copy under
  `specfuse/loop/data/templates/`, byte-identical (`cmp` exit 0), registered in
  all nine of this repository's hard-coded seeded-template registries.
- `check_decision_citations` and `check_decision_override_signoff` in
  `specfuse/loop/lint_plan.py`, both ERROR.
- This feature's own `DECISIONS.md`, carrying D1–D4 — the format's first real
  consumer.

### Oracles re-run fresh in this session (close-discipline.md §1)

Nothing below is inherited from a producing WU's self-report.

| Oracle | Exit |
| --- | --- |
| `./scripts/smoke-test.sh` (unsandboxed — 17 gates, 3493 tests) | `0` — `smoke test: OK` |
| `python3 -m unittest tests.test_decisions_format tests.test_decision_citation_lint tests.test_decision_override_lint` | `0` — 24 tests OK |
| each of the 20 acceptance-criterion test nodeids, run individually | `0` each |
| `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry` | `0` |
| `cmp .specfuse/templates/DECISIONS.template.md specfuse/loop/data/templates/DECISIONS.template.md` | `0` |

Per-criterion state, oracle, and scope classification are recorded in
`GATE-01-CRITERIA.md`.

### What the guard covers, and what it does not

`[FEAT-2026-0071/G1-CLOSE]`: *a partial structural guard described as a total
one is how the unguarded fields stop being reviewed.* So, plainly:

**Covered — citation integrity.** An artifact citing a decision ID absent from
the feature's `DECISIONS.md` is an ERROR. Observed firing: appending
`Per D9, the sign-off is optional.` to a copy of `WU-03-override-signoff-lint.md`
produced exit 1 and
`ERROR: WU-03-override-signoff-lint.md: cites decision 'D9', which is not in DECISIONS.md`.

**Covered — non-restatement.** An artifact reproducing a decision's statement
text instead of citing its ID is an ERROR, fuzzily matched so the
FEAT-2026-0066 dropped-clause shape is caught. Observed firing: D3's statement
with one clause dropped, appended to a copy of `WU-02-citation-lint.md`
(a file that does not cite `D3`), produced exit 1 and
`ERROR: ... reproduces decision D3's statement text instead of citing 'D3'`.

**Covered — unsigned overrides.** A decision at `overridden-pending-signoff`
missing any provenance field, a decision reaching `ratified` carrying
`overridden_from` without `signed_off_by`/`signed_off_at`, and a
`signed_off_by` holding a placeholder rather than a name are each an ERROR.
All three observed firing on purpose-built bad copies of this feature's own
`DECISIONS.md`.

**NOT covered — semantic agreement between a cited decision and the work done
under it.** This is `PLAN.md` D1's deliberate scope boundary, and it is
unguarded *by construction*: no test detects it, and none could without the
contradiction detection D1 rejected. Observed not firing: appending
`Per D1, the lint performs full contradiction detection between artifact prose
and the registry; reference integrity is out of scope.` — a citation of D1
asserting the exact opposite of D1 — to a copy of
`WU-03-override-signoff-lint.md` produced **exit 0, no findings**. A correctly
formed citation attached to prose that contradicts the decision it cites is
invisible to this feature, permanently.

**NOT covered — restatement inside any file that cites the decision's ID
anywhere.** The non-restatement exemption for legitimate quotation
(`WU-02` criterion 3) is scoped **per whole artifact file**, not per region. A
single `D3` token anywhere in a document exempts that entire document from
restatement checking for D3. This is not a documented scope boundary; it is an
implementation consequence, and it is load-bearing:

- Measured over this feature's own six graph artifacts × four decisions, the
  non-restatement check is live on **3 of 24 (artifact, decision) pairs —
  12.5%**. PLAN.md, GATE-01.md, WU-01 and WU-90 each cite all four IDs and are
  therefore fully exempt.
- Running `lint_plan._restates` directly over the real artifacts:
  **`PLAN.md` restates D1's and D3's registry statements today** and the lint
  reports zero errors, because `PLAN.md` also cites `D1` and `D3`.
- Confirmed by injection: the same one-clause-dropped restatement that errors
  in `WU-02` produces **exit 0** when appended to `PLAN.md`, and **exit 0**
  when the file also contains the string `See D3.`

**NOT covered — any artifact outside the PLAN/gate/WU graph.**
`check_decision_citations` walks `PLAN.md`, the gate files, and the WU files
named in the graph. `RETROSPECTIVE.md`, `GATE-NN-REVIEW.md`,
`GATE-NN-CRITERIA.md`, `LEARNINGS-pending.md`, `DECISIONS.md` itself and
anything under `work/` are never scanned. Observed not firing: the same
restatement written into `RETROSPECTIVE.md` produced **exit 0**.

**NOT covered — sealed history.** `done` and `abandoned` features are exempt,
matching `check_closing_guard_literals`. Observed: the same unsigned override
that errors on this `active` feature produces no decision finding once
`PLAN.md` reads `status: done`.

**Observed defect, not a scope boundary — one unsigned override reports as
seven errors, six of them misdirecting.** When an override's provenance is
incomplete the parser refuses the entry, so its ID drops out of `valid_ids`
and every artifact legitimately citing that ID is then reported as a dangling
citation. Setting D4 to `overridden-pending-signoff` with no provenance fields
produced 7 ERRORs: the correct one naming `D4 is override provenance
incomplete, missing: overridden_from, signed_off_by, signed_off_at`, plus six
of the form `cites decision 'D4', which is not in DECISIONS.md. Add the
decision to the registry` — advice that is wrong, because the decision *is* in
the registry. `WU-03` criterion 5 exists so an operator does not have to
re-derive which field is absent; the cascade puts that back.

### The red-before tests are fixtures, and the sequencing condition never held

`[FEAT-2026-0034/G1-CLOSE/hand-check-the-invariants-before-automating-them]`.
Every red-before test in this feature — all 24 across the three modules —
constructs a synthetic feature folder in a `tempfile.TemporaryDirectory()`.
Not one of them exercises real producer output. **A green suite here does not
prove the checker fires on anything a real drafting session wrote**, and a
reader must not conclude the lint found nothing because there was nothing to
find.

The corollary is worse than `WU-90` anticipated. `WU-90` assumes the tree was
repaired ahead of the feature. **It was not.** `PLAN.md` D2 and `GATE-01.md`'s
precondition both require FEAT-2026-0050's D1–D3 prose to be converted to a
`DECISIONS.md` in its own PR, merged before this gate runs.
`.specfuse/features/FEAT-2026-0050-async-drafting-interview/` has **no
`DECISIONS.md`**, and FEAT-2026-0050 is now `status: done` — sealed history,
and therefore permanently exempt from both checks. The gate was dispatched
anyway.

`GATE-01.md` named this exact outcome in advance: *"If this gate is dispatched
with that repair unmerged, T02 will find the tree already clean for the wrong
reason — no feature cites anything yet — and its ERROR-on-a-populated-tree
claim becomes unfalsifiable."* That is what happened. Measured on this tree:
67 feature folders, exactly **two** not `done`/`abandoned` (this one, `active`;
FEAT-2026-0011, `blocked`), and exactly **one** carrying a `DECISIONS.md` —
this feature's own. `test_check_runs_clean_over_this_repository` passes over a
live in-scope corpus of **one folder, the one the feature wrote itself**. The
ERROR-severity satisfiability argument of D2 is therefore true but vacuous, and
the two prior in-tree runtime probes `GATE-01.md`'s arming discipline asked for
were never recorded.

### Did the format hold? (D4's deferred close-ceremony consumer)

D4 defers wiring `closing_requirements.py` to this format until the format has
survived a feature. This close is the first evidence, and the answer the
deferred roadmap row should be planned against is **partly, with one named
gap**:

- **This feature's D1–D4 fit the schema mechanically.** All four parse clean
  (`parse_decisions` → 4 entries, 0 errors), each carries an owner and a
  `PLAN.md D<n>` provenance link, and the closed `status` set held every value
  needed.
- **But D1–D4 were copied, not moved.** `PLAN.md` still carries the full
  decision prose, and `_restates` confirms D1 and D3 are near-verbatim
  duplicates of their registry statements. The registry is currently a *second
  copy*, which is the drift shape this feature exists to remove — reproduced in
  its own dogfood, and invisible to its own lint for the file-scoped-exemption
  reason above. "The format held" and "the artifacts stopped restating" are
  different claims, and only the first is true.
- **FEAT-2026-0050's D1–D3 were never migrated, so half of this criterion's
  evidence does not exist.** Assessing them against the schema by hand: D3 (one
  sentence) fits cleanly. D1 and D2 do not fit without loss — each is a decision
  *plus* an enumerated `Rejected:` block with the reasoning for each rejected
  alternative, plus a consequence paragraph. The schema has `statement`,
  `owner`, `status`, `provenance` and the override fields, and **no field for
  rejected alternatives or their rationale**. Compressing D1 to a `statement`
  discards the two rejected designs and why — which is most of what a later
  reader wants from a decision record, and exactly the material a close
  ceremony's contract-change consumer would want to cite.

**Recommendation for the deferred roadmap row:** it should not be planned as
"wire `closing_requirements.py` to the existing format". It needs, first, a
`rejected_alternatives` field (or an explicit ratified decision that rejected
alternatives stay in PLAN prose), and second, the exemption fix below —
otherwise the consumer will be reading a registry that the lint permits to
diverge from the PLAN it was extracted from.

### Consumer-visible surface added by this feature

`close-discipline.md` §3 requires this enumeration **and** a matching
`CHANGELOG.md` `Unreleased` append. **The enumeration is here; the CHANGELOG
append was not made, and this section is deliberately not titled with §3's
guard heading.** `WU-90`'s *Do not touch* rule confines this close to the
feature folder, and `CHANGELOG.md` is outside it; writing §3's heading without
the append would fail `close-k` and block the close, so the material is
recorded here under a heading that does not claim the append happened. This is
stated rather than left silent, because a §3 section that a guard passes by
heading-absence is the same failure mode this feature's own criterion 2 is
about. **The append is a required follow-up — see the record below.**

- `added` — `.specfuse/templates/DECISIONS.template.md`: a new seeded scaffold
  template shipped by `init.sh` and `specfuse upgrade` into every target
  project. (FEAT-2026-0058)
- `added` — `specfuse/loop/decisions_format.py`: `parse_decisions`,
  `ParseResult`, `STATUS_VALUES`, and the entry dataclass, importable from the
  loop package. (FEAT-2026-0058)
- `changed` — `specfuse lint` / `python3 -m specfuse.loop.lint_plan` gains two
  **ERROR**-severity checks, `check_decision_citations` and
  `check_decision_override_signoff`. A feature folder that carries a
  `DECISIONS.md` can now fail lint, and therefore fail arming, for a dangling
  citation, a restatement, or an unsigned override. Opt-in per feature — a
  folder with no `DECISIONS.md` is unaffected — and `done`/`abandoned` features
  are exempt, so no existing tree turns red. (FEAT-2026-0058)

No removals and no renames. No existing flag, function signature, or file
format changed.

## Cost analysis

Gate budget `$20.00`. Reconciled from
`.specfuse/features/FEAT-2026-0058-decision-registry/events.jsonl`.

| WU | planned | actual, every attempt | as the gate ledger reports it | attempts |
| --- | --- | --- | --- | --- |
| T01 decisions format | `$6.00` | **`$6.8199`** | `$1.8657` | 4 (3 failed, escalated, re-armed, 1 passed) |
| T02 citation lint | `$5.00` | `$2.5379` | `$2.5379` | 1 |
| T03 override lint | `$4.00` | `$1.2524` | `$1.2524` | 1 |
| G1-CLOSE | `$5.00` | **not recorded** | not recorded | ≥2 (frontmatter `attempts: 2`) |
| **total** | `$20.00` | **`$10.6102` + close** | `$5.6560` + close | |

**T01 overran, and the ledger hides it.** Its four attempts split across two
arming cycles. The 2026-08-20 cycle spent `$1.2075` + `$1.5576` + `$2.1891` =
`$4.9542` across three failed attempts and escalated `spinning_detected`; the
2026-08-21 re-arm passed first try at `$1.8657`. `task_completed` records
`cost_usd: 1.865657` and `cumulative_cost_usd: 1.865657` — the counter reset at
re-arm, so the gate ledger under-reports T01 by `$4.95` and reads 31% of plan
for a unit that actually spent 114% of it. `planned_cost_usd` had already been
raised `$4.00` → `$6.00` after that escalation (PLAN.md); against the original
`$4.00` the lifetime figure is 170%.

**Almost all of that `$4.95` was a driver reporting bug, not the work.** The
three failed attempts each rediscovered one more of the nine hard-coded
seeded-template registries, because the attempt note showed `PASS` headers with
the real fault (`### sync-scaffold-symlinks-bats: FAIL`) buried thousands of
lines below — the hyphenated-gate-name parser defect, since fixed as #2557.
Attempt 3's recorded `failure_class: other / no_gate_marker` is that bug's
signature. The re-armed attempt, dispatched after the fix with the registry list
written into `WU-01`'s body, passed in one.

**T02 and T03 came in at 51% and 31% of plan**, one attempt each, no failures —
the same systematic over-estimate FEAT-2026-0050's close recorded for
implementation units whose oracles are scoped unit tests over a new module.

**The close's own spend is unreconcilable.** `WU-90` frontmatter reads
`attempts: 2`, so at least one prior close attempt ran, but `events.jsonl`
contains **no `attempt_outcome` or `task_completed` event for
`FEAT-2026-0058/G1-CLOSE`**, and none of the four `work/driver-*.log` files
covers a close dispatch. Its cost is not recoverable from any artifact in this
feature folder. The producing WUs' data — what the reconciliation actually
needs — is complete, so this is reported rather than escalated, but the gate's
true total against `$20.00` cannot be stated: it is `$10.6102` plus an unknown.

### Failure-class breakdown

Three non-passing attempts in gate 1, all FEAT-2026-0058/T01, all in the
discarded 2026-08-20 arming cycle. (`summarize_attempt_failure_classes` reports
`(no non-passing attempts in scope)` for the current cycle; these are recorded
from `events.jsonl` because they are real spend against the gate budget.)

| attempt | `failure_class` | `failure_signature` | cost |
| --- | --- | --- | --- |
| 1 | `tests` | `test_specfuse_tree_complete` | `$1.2075` |
| 2 | `tests` | `test_no_orphan_files_in_package_data` | `$1.5576` |
| 3 | `other` | `no_gate_marker` | `$2.1891` |

One root cause across all three: a new seeded scaffold template must be
registered in nine hard-coded registries, and the failure surfaced one registry
at a time because the gate-marker parser could not name the failing gate.

## What the loop did NOT verify (gate 1)

Every one of the 19 recorded acceptance criteria was verified in-loop this
attempt against a fresh oracle — see `GATE-01-CRITERIA.md`. Nothing on the
per-criterion list is deferred.

Deferred beyond the per-criterion list:

- **`close-discipline.md` §3's `CHANGELOG.md` `Unreleased` append.** Deferred
  because `WU-90`'s *Do not touch* confines this close to the feature folder.
  Where it actually gets checked: nowhere automatically — `close-k` passes by
  heading-absence, which is precisely why it is written down here. It must be
  done by the operator at PR review for this feature, or by whoever accepts the
  hedged verdict; the four classified entries are ready to copy from
  *§ Consumer-visible surface added by this feature*.
- **`GATE-01.md`'s two arming-discipline probes.** The runtime probe of the
  non-restatement matcher over the six decisions-prose PLAN files, and the
  `driver_edit.is_driver_module_path` predicate check, were to be run and
  recorded in the gate review before arming. No gate review exists and neither
  result was recorded. This close ran the matcher over this feature's own
  artifacts after the fact (§ *What the guard covers*), which is what surfaced
  the PLAN.md restatement; it did not run it over the other six. Where it gets
  checked: the re-run condition on entry 1 below.
- **Whether the checks behave on a second real feature.** Not deferred by
  choice — see entry 2. No environment or credential is missing; the corpus is.

## Hedged-verdict follow-up record

### The non-restatement check is inert on any file that cites the decision ID anywhere

- **criterion (verbatim, `GATE-01.md` Definition of done):** "`specfuse lint`
  fails a feature whose artifact cites a decision ID absent from the registry,
  and fails one whose artifact reproduces a decision's statement instead of
  citing its ID. ERROR, not WARN — and the tree passes."
- **why it is unmet:** the second clause holds only for artifacts that do not
  cite the decision's ID. The legitimate-quotation exemption is scoped per whole
  file, so one `D3` token anywhere exempts the entire document. Measured on this
  feature's own artifacts the check is live on 3 of 24 (artifact, decision)
  pairs, and `PLAN.md` — which restates D1 and D3 today, confirmed by running
  `_restates` directly — is fully exempt. Non-restatement is `PLAN.md` D1's
  stated load-bearing half ("if artifacts may only cite, there is no second copy
  to drift"); at 12.5% coverage, with the drift present and unflagged in the
  dogfood itself, the claim is not met.
- **re-run condition that would upgrade this to `met`:** scope the exemption to
  the citing region rather than the whole file (or require the citation to be
  adjacent to the quotation), then (a) re-run
  `lint_plan._restates` over this feature's six graph artifacts and observe zero
  restatements after `PLAN.md`'s D1/D3 prose is replaced by citations, and (b)
  `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
  exits 0.
- **kind:** `externally-verifiable-later`

### The ERROR-on-a-populated-tree claim rests on a precondition that never held

- **criterion (verbatim, `WU-02` acceptance criterion 6):** "**The check runs
  clean over this repository's real tree**, with the FEAT-2026-0050 repair
  merged (see `GATE-01.md`'s precondition). Asserted by a test that runs it over
  `.specfuse/features/` and expects zero errors — the satisfiability claim made
  falsifiable rather than assumed."
- **why it is unmet:** the test passes, but the clause it is conditioned on is
  false. FEAT-2026-0050 has no `DECISIONS.md`; the repair never landed, and
  FEAT-2026-0050 is now `done` and permanently exempt. One folder in 67 is in
  scope — the one this feature wrote — so a green sweep is unfalsifiable exactly
  as `GATE-01.md` predicted. Every red-before test is a synthetic
  `TemporaryDirectory` fixture, so nothing in this feature has been observed
  firing on real producer output written by a session that was not this one.
- **re-run condition that would upgrade this to `met`:** a second live
  (non-`done`, non-`abandoned`) feature adopts a `DECISIONS.md` — FEAT-2026-0011
  or the next drafted feature — and
  `python3 -m unittest tests.test_decision_citation_lint.TestCitationIntegrity.test_check_runs_clean_over_this_repository`
  exits 0 with at least two folders in scope, with the in-scope count asserted
  rather than assumed.
- **kind:** `externally-verifiable-later`

### One unsigned override reports as seven errors, six naming the wrong repair

- **criterion (verbatim, `WU-03` acceptance criterion 5):** "The error message
  names the decision ID and the missing field, so an operator fixing it does not
  have to re-derive which of four fields is absent."
- **why it is unmet:** the override message itself is correct, but it does not
  arrive alone. An entry with incomplete override provenance is refused by the
  parser and drops out of `valid_ids`, so every artifact citing that ID is
  additionally reported as a dangling citation. Observed: 7 ERRORs for one
  fault, six of them advising "Add the decision to the registry" for a decision
  that is in the registry. An operator does have to re-derive which finding is
  real.
- **re-run condition that would upgrade this to `met`:** a refused entry's ID
  stays known to the citation check (or the citation check is skipped for IDs
  present-but-unparseable), and re-running the injection — this feature's `D4`
  set to `overridden-pending-signoff` with no provenance fields — yields exactly
  one ERROR, the override one.
- **kind:** `externally-verifiable-later`

**Verdict ceiling.** All three entries are `externally-verifiable-later`, so by
`closing_requirements.verdict_ceiling_for_kinds` rework exists: the operator has
a real choice between accepting the hedge now and doing the three named
re-runs. None of the three needs an environment, a credential, or a deployed
component — all are in-repo work.

### Discharge record — entries 1 and 3 (operator-directed, post-close)

Recorded 2026-08-21. The operator elected to do the rework rather than accept
the hedge. Entries 1 and 3 are **discharged against their own stated re-run
conditions**; entry 2 is **not**, and remains open.

**Entry 3 — discharged.** `valid_ids` now unions the parsed entries' IDs with
`parsed.errors`' IDs, so a present-but-unparseable decision stays known to the
citation check. `DecisionParseError` already carried `decision_id`; nothing in
the parser's shape had to change. Re-running the named injection — this
feature's `D4` set to `overridden-pending-signoff` with no provenance fields,
cited from `PLAN.md`, `GATE-01.md` and `WU-01.md` — now yields **exactly one
ERROR, the override one**, where it previously yielded four (one real, three
spurious dangling-citation findings; the record's "seven" counts the larger
artifact set of the original observation). Pinned by
`tests/test_decision_followups_discharged.py::TestOneUnsignedOverrideReportsOnce`.

**Entry 1 — discharged, in both halves.** The exemption is now scoped to the
quotation rather than the file: `_restates` returns the matching word span, and
`_cited_near` asks whether the decision's ID appears within
`_CITATION_PROXIMITY_WORDS` of it. The record understated the defect — the old
exemption did not require a citation at all, only that the bare token `D3`
occur somewhere in the document, since `_DECISION_CITATION_RE` is `\bD\d+\b`.

Both halves of the stated re-run condition were run:

- **(a)** `_restates` over this feature's graph artifacts reports **zero
  restatements**, after `PLAN.md`'s D1 and D3 prose was replaced by citations
  to `DECISIONS.md` (the rationale unique to `PLAN.md` was kept; only the
  duplicated statement text was removed).
- **(b)** `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0058-decision-registry`
  exits **0**.

Coverage over this feature's own artifacts, measured the same way the record
measured it: **4 of 36 (artifact, decision) pairs the check could fire on,
now 36 of 36.** The record's "3 of 24" reflects the artifact set at close
time; the ratio moved from 11% to 100% on the current set.

**A limit this discharge does not remove, recorded deliberately.** A *labelled*
second copy — `D1 — <statement text>` — remains exempt, because the ID sits
adjacent to the text and that is indistinguishable, mechanically, from the
legitimate quotation criterion 3 requires be allowed. The check now catches a
statement copied away from its ID; it does not catch one copied next to it.
`PLAN.md` was the instance that mattered and it now cites, but the guard rests
on artifacts choosing to cite rather than quote. This is D1's
"unguarded by construction" boundary moving, not disappearing.

**Entry 2 — NOT discharged.** Its re-run condition needs a second live
(non-`done`, non-`abandoned`) feature carrying a `DECISIONS.md`. Measured
2026-08-21, the live corpus is **exactly two folders**: FEAT-2026-0011
(`blocked`, no `DECISIONS.md`, PLAN-only, no gates or work units) and this
feature. The only way to reach two in-scope folders today would be to give
FEAT-2026-0011 a registry it has no decisions for — manufacturing corpus to
satisfy a test, which is the defect shape this feature exists to remove. Left
open to discharge honestly when the next feature is drafted (FEAT-2026-0052 and
FEAT-2026-0081 are queued and undrafted) or when ADR-0002 unblocks
FEAT-2026-0011 and it acquires real decisions.

The verdict therefore stays hedged, but for **one** reason instead of three.

## Generalizable lessons

Staged to `LEARNINGS-pending.md` in this feature directory
(`autonomy_default: auto`, so `close-i` forbids writing `.specfuse/LEARNINGS.md`
directly). Four entries:

1. An exemption scoped to the wrong unit silently inverts a guard's coverage —
   measure live coverage over the real corpus, not just the red-before fixture.
2. A sequencing precondition enforced only by prose gets skipped — assert the
   in-scope corpus size in the test, not just zero findings.
3. Cost counters reset on re-arm — reconcile by summing `attempt_outcome` rows,
   not from `cumulative_cost_usd`.
4. A close WU's *Do not touch* must permit the surfaces its own binding close
   obligations require, or the obligation is dropped by a guard that passes on
   absence.
