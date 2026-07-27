# GATE-02-REVIEW — FEAT-2026-0070, gate 2 arming record

Written by `FEAT-2026-0070/G1-PLAN` at gate-1 close. This is the artifact the human reads
to **review and arm** gate 2 — the four drafted WUs sit at `status: draft` until someone
walks this document and flips them.

Gate 2's job, from `GATE-02.md`: *an auto-closed gate's skipped ceremony is a visible debt,
not a silent saving* (#241).

**The headline finding is in § *Satisfiability*.** The obvious form of gate 2's post-pass
invariant was applied locally and run against every feature in this repo. It **fires on 6
of the 11 features that have auto-closed a gate**, every one of them `status: done` and
correctly closed. That form is unsatisfiable and is not what got drafted. The drafted form
is marker-gated and reports zero on all 11. If you read one section, read that one.

---

## 1. What gate 1 actually shipped

Four WUs, all passing on their first recorded attempt, against three issues.

| WU | shipped | where |
|---|---|---|
| T01 | `fire_terminal_flips` flips the roadmap row from **any** non-`done` status, not only `active` (#226) | `loop.py:3200-3218`; `TestRowFlipBreadth` |
| T02 | `recheck_terminal_verdict(feature_dir, repo_root)` + `--recheck-verdict FEATURE_ID` — re-reads a **completed** close WU's verdict from disk and calls the existing `fire_terminal_flips` when it now permits the flips | `loop.py:3281`, CLI at `:5723`; `TestVerdictRecheck` |
| T03 | `/accept-hedged-close` — propose-and-confirm operator skill that accepts a standing `met_locally`, writes the audit record, sets `verdict: met`, and hands the flip to `--recheck-verdict` (#243) | `plugins/specfuse/skills/accept-hedged-close/`; 19 tests |
| T04 | `in_progress` / `in_review` added to `lint_plan`'s close-WU verdict-exempt set | `lint_plan.py:626-635`; 3 tests |

**Two things gate 1 produced that this draft is built on.**

1. **T02's primitive is the shape gate 2 copies.** `recheck_terminal_verdict` locates WU
   files from `PLAN.md`'s graph and reads their frontmatter **from disk**, never from an
   in-memory `WorkUnit` — because the auto-close path leaves those `None`. T06's
   enumeration builder has exactly the same constraint (it runs where no `WorkUnit` is
   loaded for the WUs it enumerates) and T06's Context says so.
2. **The one-owner audit found a defect on the same file gate 2 edits.** `loop.py:4462`
   writes `PLAN.md` `status: complete`, which is not in
   `lint_plan.VALID_FEATURE_STATUS`. Re-running the driver against a finished feature
   would overwrite the `done` that `fire_terminal_flips` just wrote. **This is not in gate
   2** — see § *What I deliberately did not draft*.

**Gate 1's premise held.** `PLAN.md` cut the gates on "the flip contract and the auto-close
debt are separable concerns." Nothing in `RETROSPECTIVE.md` contradicts that: every gate-1
finding (the empty-Status-cell `replace` edge, the laundered hedge, `loop.py:4462`,
`/arm-gate`'s missing terminal guard, the `.claude/skills/` symlink drift) is inside the
flip-contract family and none of them touches auto-close's enumeration. The escalation
trigger for a wrong gate cut did not fire.

---

## 2. What changed from `PLAN.md`'s gate-2 sketch, and why

The sketch was explicitly not binding. Three changes.

**a. The post-pass invariant is marker-gated. This is the substantive change.**
The sketch's wording — *"if any non-terminal gate auto-closed and the terminal close's
`## What the loop did NOT verify` never mentions it, escalate"* — is the form that fires on
6 of 11 correctly-closed features. T07 ships the narrowed form: only gates whose auto-close
stub carries T06's marker count as debt. Full evidence in § 4.

**b. A precursor WU (T05) was added that the sketch did not anticipate.** The sketch
assumed auto-close "already knows the gate's WUs, so it can list each one's acceptance
criteria." It does know the WUs — but the parser that slices a WU body's
`**Acceptance criteria.**` section lives in `lint_plan.py`, and `lint_plan.py:35` already
does `from .loop import VERDICT_VALUES`, so `loop.py` cannot import it back. The choice was
a second copy of the parser (which `authoring-work-units` §10 exists to prevent) or a
20-minute extraction into a leaf module. T05 is the extraction.

**c. A fourth WU (T08) was added: the arm-time prediction.** Not in the sketch. T07 is a
new blocking condition on terminal closes, and `close-discipline.md` §4 measured what a
blocking condition with no authoring surface costs: three such guards account for $99.30,
45% of all closing-WU waste, with `assert_gate_review_exists` alone at $53.11 over 15
fires — while `assert_verdict_well_formed` fired 10 times for **$0.00** because it is
checked before the agent spends anything. T08 is the difference between the two kinds. It
is being written in the same gate as the guard rather than after the first refusal, which
is the first time this repo has done that.

**Unchanged from the sketch:** #241 option 1 (auto-close writes the enumeration itself,
mechanically, no agent dispatch) is T06 verbatim.

---

## 3. The four drafted work units

| WU | type | depends on | planned | one line |
|---|---|---|---|---|
| **T05** `shared-wu-section-slicers` | implementation | — | $1.00 | extract `_slice_ac_section` / `_slice_section` into `specfuse/loop/_wu_sections.py` so `loop.py` can read a WU's criteria without a second parser |
| **T06** `autoclose-debt-enumeration` | implementation | T05 | $2.00 | both auto-close stub writers enumerate the gate's unwalked criteria, one `deferred:` line each, plus a machine-readable debt marker |
| **T07** `autoclose-debt-invariant` | implementation | T06 | $2.25 | `assert_autoclose_debt_reconciled` post-pass invariant + its row in `close-discipline.md` §4 |
| **T08** `arm-time-debt-prediction` | implementation | T07 | $1.25 | `lint_plan` WARN when a terminal close body ignores a marked debt — predicts T07's refusal at arm time |
| `G2-CLOSE` | close | T05–T08 | $5.00 | terminal close; `auto_close_disabled: true` |

**The chain is strictly linear and that is deliberate.** T06 cannot enumerate without T05's
slicer; T07 reads a marker only T06 writes; T08 predicts a guard only T07 defines. There is
no parallelism to be had, and a WU dispatched before its dependency would have to invent
the other's contract.

**Red-test compliance (`authoring-work-units` §12).** Every drafted `implementation` WU
names a scoped test that fails on HEAD as its **first** acceptance criterion, except T05
which carries an explicit exemption line.

| WU | AC1 | verified absent on HEAD? |
|---|---|---|
| T05 | `Red-test exempt: pure extraction — the two functions keep their names, signatures, and outputs, and no caller changes.` AC1 is instead a before-and-after regression run of the existing lint suite with the test count recorded | n/a |
| T06 | `tests/test_autoclose_deferral_visibility.py::TestAutoCloseDebtEnumeration::test_intermediate_stub_enumerates_each_substantive_wu_criteria` | yes — class does not exist; `grep -rn "autoclose-debt" --include="*.py" .` returns nothing |
| T07 | `tests/test_loop_post_pass_invariant.py::TestAutoCloseDebtReconciled::test_marked_predecessor_debt_unmentioned_fails` | yes — `grep -rn "assert_autoclose_debt_reconciled" --include="*.py" .` returns nothing |
| T08 | `tests/test_closing_guard_prediction.py::TestAutoCloseDebtPrediction::test_warns_when_terminal_close_body_ignores_marked_debt` | yes — class does not exist in the (existing) file |

All four target **existing** test files. Gate 1's calibration lesson (*"an existing test
file to extend makes the work cheaper, not dearer"*) is why the estimates are what they are.

---

## 4. Satisfiability, answered explicitly (`planning-discipline.md` §2)

> **What does this rule report on an input already in its intended final state?**

### 4a. The enumeration over this repo

Every feature with at least one auto-closed gate, and what each candidate invariant reports
on it. Produced by a read-only script over `.specfuse/features/*/`; `BROAD` is the sketch's
wording, `NARROW` is what T07 ships.

| feature | auto-closed WUs | terminal gate | terminal close itself auto-closed? | **BROAD** fires on | **NARROW** fires on |
|---|---|---|---|---|---|
| FEAT-2026-0016 | g2 `close-intermediate` | 3 | no | **gate 2** | — |
| FEAT-2026-0021 | g1 `close` | 1 | yes | — | — |
| FEAT-2026-0024 | g1 `close-intermediate` | 2 | no | **gate 1** | — |
| FEAT-2026-0025 | g1 `close-intermediate`, g2 `close` | 2 | yes | **gate 1** | — |
| FEAT-2026-0026 | g1, g2 `close-intermediate`, g3 `close` | 3 | yes | **gate 1, gate 2** | — |
| FEAT-2026-0027 | g1, g2 `close-intermediate` | 3 | no | **gate 1, gate 2** | — |
| FEAT-2026-0028 | g1 `close-intermediate` | 2 | no | **gate 1** | — |
| FEAT-2026-0030 | g1 `close` | 1 | yes | — | — |
| FEAT-2026-0031 | g1 `close` | 1 | yes | — | — |
| FEAT-2026-0032 | g1 `close-intermediate` | 2 | no | — | — |
| FEAT-2026-0039 | g1 `close-intermediate` | 2 | no | — | — |
| | | | | **6 of 11** | **0 of 11** |

**Every one of those 11 features is `status: done`.** None of them closed incorrectly. The
BROAD form fires on 6 of them, so *"zero issues"* is unreachable on a tree already in its
final state — the §2 definition of unsatisfiable, and exactly the
`[FEAT-2026-0049/G2-CLOSE]` failure (`ERROR` on a predicate whose correct inputs still trip
it). **The BROAD form must not be armed, and it has not been drafted.**

The NARROW form gates on T06's `<!-- specfuse:autoclose-debt gate=N … -->` marker, which no
existing retrospective carries and none can retroactively acquire (they are static files;
the marker is written only when auto-close fires). Zero on all 11. The obligation attaches
only to gates auto-closed *after* T06 ships — the population that was told about it.

**Two structural facts the table surfaced that the sketch had not accounted for:**

1. **5 of the 11 had their *terminal* close auto-close too** (0021, 0025, 0026, 0030,
   0031). No agent ran, so there is no session that could have written a reconciliation.
   `_fire_and_verify_terminal_flips` is called from **both** the auto-close and the
   dispatched-close path, so a naive invariant would fire on a path with no possible
   remedy. T07 AC5 short-circuits when the close WU itself carries `auto_close: true`, and
   T06's terminal stub is what serves as the record on that path.
2. **The two features BROAD does *not* fire on (0032, 0039) pass for a real reason,** not
   an accident — their terminal closes genuinely discuss the auto-closed gate.
   `FEAT-2026-0032/RETROSPECTIVE.md:14` reads *"no close session ran to write gate 1's
   `## What the loop did NOT verify` list."* That is the behavior gate 2 wants to make
   universal, and it is reachable — two sessions already did it unprompted.

### 4b. What the two *other* drafted checks report on a final-state tree

- **T06** is a writer, not a predicate. It raises nothing. Its degrade path (AC8) turns an
  unparseable WU into a `deferred: <criteria not parseable>` line rather than an exception,
  because it runs inside the close path where a traceback would fail an on-plan gate.
- **T08** is a `WARN` and never changes `lint_plan`'s exit code — the same choice
  `check_closing_guard_literals` documents, for the same reason. Its AC7 requires zero new
  WARNs on this feature and its AC8 requires zero across `.specfuse/features/`.

---

## 5. Runtime probe (`planning-discipline.md` §4)

Gate 2 introduces a new blocking condition, so it may **not** be armed on "mechanical,
nothing design-open." The probe was applied locally and reverted.

**Method.** `assert_autoclose_debt_reconciled` was implemented in `loop.py` and registered
in `POST_PASS_INVARIANTS_BY_TYPE["close"]`, in both the NARROW and BROAD forms (selected by
an env var), and the **full** oracle was run for each.

| run | command | result |
|---|---|---|
| baseline, before probe | `python3 -m unittest discover -s tests` | `Ran 1568 tests` — `OK (skipped=3)` |
| **NARROW probe applied** | same | `Ran 1568 tests` — `OK (skipped=3)` |
| **BROAD probe applied** | same | `Ran 1568 tests` — `OK (skipped=3)` |
| after revert | same | `Ran 1568 tests` — `OK (skipped=3)` |

### The failure list is empty — and that is itself the finding

**Zero tests fail under either variant.** Do not read that as "the invariant is safe." It
means the opposite of what a green suite usually means: **the test suite does not exercise
this surface at all.** No fixture in `tests/` builds a feature with an auto-closed
predecessor gate *and* a dispatched terminal close, so nothing in 1568 tests can distinguish
the unsatisfiable BROAD form from the shipped NARROW one. The probe's real value was
proving the oracle is blind here, which is why:

- **T07 AC1 and AC3 require both a negative and a positive control**, and **AC4 requires the
  no-marker case as its own named test** (`test_unmarked_autoclose_is_not_debt_and_does_not_fire`).
  Those three tests are the coverage the suite is missing today.
- **The satisfiability evidence for arming is § 4's enumeration, not this table.** The
  enumeration is what found the 6-of-11.

### Negative observation (`verification-discipline.md` §3)

A rule that fires on nothing passes every test. The probe was therefore run against
purpose-built inputs, not only the suite:

```
NEGATIVE control (debt marked, never mentioned)    ok=False  expect_ok=False  PASS
    reason: autoclose_debt_unreconciled: gate(s) 1 auto-closed and left a
    deferred-verification debt that this terminal close's `## What the loop did
    NOT verify` section never mentions
POSITIVE control (debt marked, reconciled)         ok=True   expect_ok=True   PASS
```

Both variants produce identical control results — the controls confirm the invariant
*works*; § 4's enumeration is what decides which variant is *satisfiable*.

### Revert confirmed

`specfuse/loop/loop.py` was restored from a pre-probe copy and verified byte-identical:
`shasum` returns `52a271658cd035b90dd6f0189a282f7bd6df191e` for both the working file and
the backup, `grep -c "PROBE" specfuse/loop/loop.py` returns `0`, and the post-revert oracle
run above is green. The only files this WU changed are planning artifacts under
`.specfuse/features/FEAT-2026-0070-terminal-flip-contract/`.

---

## 6. §10 helper-duplication pre-flight (`authoring-work-units` §10)

Every symbol the drafted WUs touch or name, enumerated before scope was declared. **Every
hit below is either in a drafted WU's scope or named in that WU's "Do not touch" with a
reason.**

| symbol | definition | other hits | disposition |
|---|---|---|---|
| `evaluate_auto_close` | `gate_eval.py:285` | `loop.py:61, 3533, 3669`; 4 test files; `draft-feature/SKILL.md:303` | **Do not touch** — T06 changes what auto-close *writes*, never what it *decides*; T07 keeps the predicate and the invariant deliberately uncoupled |
| `AutoCloseDecision` | `gate_eval.py:38` (frozen dataclass) | 22 hits in `specfuse/`; 3 test files incl. `test_autoclose_deferral_visibility.py` | **Do not touch** — T06 AC states the builder reads `PLAN.md` itself rather than adding a field, which would ripple into every `test_gate_eval*.py` fixture for no gain |
| `fire_terminal_flips` | `loop.py:3128` | 32 in `specfuse/`, 8 test files | **Do not touch** in T06 and T07 — gate 1's surface, complete |
| `assert_terminal_flips_fired` | `loop.py:4292` | `loop.py` registration + 3 test files | **T07 scope, registration only.** T07 adds a sibling to `POST_PASS_INVARIANTS_BY_TYPE["close"]` and asserts the order; the function body is in "Do not touch" |
| `recheck_terminal_verdict` (T02's primitive) | `loop.py:3281` | CLI `:5723`; 2 test files | **Do not touch** — T06 reads it for its disk-reading shape and changes nothing |
| `write_stub_retrospective_terminal` | `loop.py:3420` | called at `:3549`; `test_autoclose_deferral_visibility.py` | **T06 scope** |
| `append_stub_retrospective_intermediate` | `loop.py:3574` | called at `:3684`; 2 test files | **T06 scope** |
| `mark_close_wu_auto_closed` | `loop.py:3462` | `:3550`; `test_terminal_flip_ownership.py` | **Do not touch** (T06) — the frontmatter flip incl. `verdict: met` is unchanged |
| `maybe_auto_close_terminal` / `maybe_auto_close_intermediate` | `loop.py:3495` / `:3624` | 3 / 2 test files | **Do not touch** (T06) — callers only; their short-circuits are correct |
| `_slice_ac_section` | `lint_plan.py:126` | `lint_plan.py:652`; `tests/test_lint_oracle_env.py:117` | **T05 scope.** Name and signature preserved as a delegation, so **neither call site is edited** — that is what makes the extraction behavior-preserving |
| `_slice_section` | `lint_plan.py:137` | `lint_plan.py:458, :474, :684, :891` | **T05 scope**, same delegation treatment; all four call sites explicitly out of scope |
| `_AC_START_RE` / `_AC_END_RE` | `lint_plan.py:120, :123` | `:128, :133, :145` — all inside the two functions above | **T05 scope** (moved with them); no other consumer exists |
| `_NON_SUBSTANTIVE_TYPES` | `gate_eval.py:35` | `gate_eval.py:262` — **single** call site | **T06 scope, import-only.** T06 AC4 forbids forking the set into `loop.py` |
| `_CLOSING_TYPES` | `gate_eval.py:34` | `gate_eval.py:206` — single call site | Not touched; recorded so the sibling constant is not mistaken for a duplicate |
| `check_closing_guard_literals` | `lint_plan.py:407` | `:781` — single call site; `tests/test_closing_guard_prediction.py` | **Do not touch** (T08) — T08 adds a sibling function because this table's entries are static per-type regexes and T08's prediction is conditional on feature state |
| `_GUARD_LITERAL_PREDICTIONS` | `lint_plan.py:380` | `:424` — single use | **Do not touch** (T08), same reason |
| `assert_gate_review_exists` | `loop.py:4064` | registered `:4142`; `tests/test_closing_guard_contracts.py:113` | Not touched by gate 2. Named here because it is the guard that governs **this document's filename** and the most expensive in the system |
| `loop.py:4462` `status: "complete"` write | `loop.py:4462` | — | **Do not touch**, named explicitly in T07 — a real gate-1-family defect, adjacent to T07's file, routed to `/fix-bug` (§ 8) |

---

## 7. The cost-reintroduction trap, stated per WU (`[FEAT-2026-0039/G2-CLOSE]`)

Auto-close exists to avoid an agent dispatch. `[FEAT-2026-0039/G2-CLOSE]` records that its
gate 1 auto-closed at $0.00 against a $5.00 estimate and moved the deferred-verification
walk into the terminal close — where it cost **more**, because the session doing it had not
written those WUs. *An auto-closed gate's skipped ceremony is a debt entry, not a saving.*
A fix that writes the enumeration by dispatching a session has traded the defect for the
cost the predicate was built to prevent.

**Every drafted WU carries a "Cost-reintroduction trade" paragraph naming which side it
lands on. All four land on "keeps the saving," and the reasons differ:**

| WU | side | why |
|---|---|---|
| T05 | keeps the saving | compile-time refactor; adds no runtime work of any kind |
| T06 | keeps the saving | reads files the driver has already located, inside a function the auto-close path already calls. No session, no subprocess, no model call. **T06 must report the observed wall-clock delta of the auto-close path as evidence, not assert it** |
| T07 | keeps the saving | file-state check at close-WU outcome time, where `assert_terminal_flips_fired` already runs |
| T08 | keeps the saving | static lint check; runs in a process that has no agent, and its whole purpose is moving a cost from dispatch time to arm time |

**The asymmetry worth naming at arming.** Gate 2 does **not** make auto-close stop saving.
A gate that auto-closes still costs no session. What changes is that it now leaves a list
(T06) that someone downstream is obliged to read (T07) and is told to read before they are
charged for not reading it (T08). That is the debt being *recorded and collected*, not the
saving being cancelled.

---

## 8. What I deliberately did not draft

Four items from gate 1's retrospective that are **not** in gate 2, each with where it goes
instead. The reviewer may overrule any of these at arming.

1. **`loop.py:4462` writes `PLAN.md status: complete`** — an invalid feature status that
   would overwrite a correct `done`. Real defect, found by gate 1's one-owner audit, and
   adjacent to T07's file. **Not drafted as a gate-2 WU**: it is a gate-1-family bug, and
   this repo's own workflow is 1 bug = 1 branch = 1 PR, test-first (`/fix-bug`) — feature
   methodology is the wrong instrument. It needs an issue. Named in T07's "Do not touch"
   so the implementing session does not fix it in passing.
2. **The laundered hedge** — `/accept-hedged-close` overwrites `verdict: met_locally` with
   `met`, so an accepted hedge is byte-identical to a clean one. The retrospective's
   highest-value follow-up (`verdict_accepted_from` / `_reason` / `_at` frontmatter). Not
   drafted: it is a #243 flip-contract concern, not #241 auto-close debt, and folding it
   into gate 2 would cut across the gate boundary `PLAN.md` set. Best as the follow-up
   feature alongside #243's held candidates 2 and 3.
3. **`--recheck-verdict` has no CLI-level test** (only the refusal path was smoke-run).
   Small and real; belongs with item 2 in the flip-contract follow-up.
4. **`.claude/skills/` symlink drift** (`accept-hedged-close`, `adopt-feature`,
   `migrate-to-auto-close` all missing) and **`sync-scaffold.sh` not syncing `docs/`**. Repo
   hygiene, unrelated to either gate. Retrospective § *What I'd change* items 4 and 7.

---

## 9. Cost reconciliation (`planning-discipline.md` §5)

**Every drafted WU is at or above its type's floor.** T05–T08 are `implementation`, priced
from evidence rather than a floor; `G2-CLOSE` is at the `close` floor of $5.00 exactly.

| WU | type | floor | drafted | basis |
|---|---|---|---|---|
| T05 | implementation | — | $1.00 | pure extraction, one new leaf module, two delegating shims. Below gate 1's cheapest WU (T04 $0.99) is the right neighbourhood |
| T06 | implementation | — | $2.00 | largest of the four: new builder + two call sites + 6 new tests. Above gate 1's most expensive actual (T03 $1.54) |
| T07 | implementation | — | $2.25 | new invariant + registration + 6 tests **plus** the `close-discipline.md` §4 row, which the guard-contract test enforces |
| T08 | implementation | — | $1.25 | mirrors T04 (`lint_plan` + 3 tests, actual $0.99) with one extra fixture |
| `G2-CLOSE` | close | **$5.00** | $5.00 | at floor |
| **gate 2 total** | | | **$11.50** | |

**Reconciliation against `PLAN.md`'s $32.00.**

| | planned |
|---|---|
| gate 1, as drafted | $20.50 |
| gate 2, as drafted here | $11.50 |
| **sum** | **$32.00** |
| `PLAN.md` `planned_cost_usd` | $32.00 |
| **delta** | **$0.00** |

It reconciles exactly, and the plan-lint cost-delta WARN that `PLAN.md` § *Notes*
pre-declared is retired by this draft.

**The exact match is arithmetic, not evidence — say so at arming.** Gate 1's *actual* is
running a different shape entirely, and it splits cleanly by half:

| gate 1 | planned | actual | delta |
|---|---|---|---|
| substantive (T01–T04) | $10.00 | $4.6488 | **−53.5%** |
| `G1-CLOSE-INTERMEDIATE` | $4.50 | $6.3713 | **+41.6%** |
| `G1-PLAN` (this WU) | $6.00 | not yet recorded | — |
| gate 1 so far | $20.50 | ≥ $11.0201 | open |

Two consequences for the reviewer:

- **The substantive under-run is systematic, and gate 2's estimates already reflect it.**
  Not one gate-1 WU exceeded 66% of its estimate. `PLAN.md` had priced them *above* the
  $1.33 median because they touch driver internals; the opposite was true — an existing
  test file to extend makes a driver-internals WU cheaper. All four gate-2 WUs extend
  existing test files, and are priced accordingly.
- **The ceremony over-run is the risk, and it is not fixed.** `close-intermediate` came in
  41.6% over its floor. `[FEAT-2026-0069/GATE-1-ARM]` records two `plan-next` observations
  at $15.65 and $16.44 against the $6.00 floor. If this WU lands near those, gate 1 closes
  over $20.50 **despite** its substantive half coming in at less than half of plan, and the
  overrun is entirely ceremony.
- **`G1-PLAN`'s actual is the number to check first at arming.** It is not knowable from
  inside this session. If it lands materially above $6.00, gate 2's $5.00 `close` floor is
  the next thing to doubt — and the right response is `close-discipline.md` §4's, not a
  raised floor: read the failure class before assuming the work was hard.

**Nothing was silently adjusted.** `PLAN.md`'s $32.00 is unchanged and `GATE-02.md`'s
`cost_budget_usd: 16.0` is unchanged; both carry a note recording the confirmation.

**`GATE-02.md` `cost_budget_usd: 16.0` — confirmed, not revised.** §5's corollary (sum plus
one re-attempt of the largest WU) gives $11.50 + $5.00 = $13.75, so `16.0` holds with $2.25
of slack. Trimming to $13.75 was considered and rejected: the largest WU is the $5.00
`close`, and gate 1's `close-intermediate` is the one WU that overran.

---

## 10. Cross-repo contracts (`authoring-work-units` §8)

`plan-next` drafts systematically invent plausible cross-surface values. Every value the
drafted WUs name that lives outside the WU itself, with its authoritative source:

| value | used by | authoritative source | checked? |
|---|---|---|---|
| `<!-- specfuse:autoclose-debt gate=N wus=… criteria=N predicate=… -->` | T06 writes, T07 reads, T08 reads | **Invented by this draft.** T06 AC5 pins the literal and T07's Escalation triggers block if the two disagree | **n/a — new; internal to this feature. The `gate=(\d+)` token is a contract between T06 and T07 and both WUs say so** |
| `## What the loop did NOT verify` | T06 (writes), T07 (scans), T08 | `loop.py:3446, :3609`; `tests/test_autoclose_deferral_visibility.py:47` | ✅ verified against source |
| `POST_PASS_INVARIANTS_BY_TYPE` | T07 | `loop.py:4369` | ✅ verified |
| `_NON_SUBSTANTIVE_TYPES` | T06 | `gate_eval.py:35`, single call site `:262` | ✅ verified |
| `_slice_ac_section` / `_slice_section` / `_AC_START_RE` / `_AC_END_RE` | T05 | `lint_plan.py:120–147` | ✅ verified, all call sites enumerated (§ 6) |
| `check_closing_guard_literals` / `_GUARD_LITERAL_PREDICTIONS` | T08 | `lint_plan.py:407, :380` | ✅ verified |
| `(close-x)` docstring tag convention | T07 AC8 | `tests/test_closing_guard_contracts.py:138` — the regex that finds closing guards | ✅ verified |
| `code` gate set contents | all four WUs' Verification sections | `.specfuse/verification.yml` — tests, lint, security, coverage ≥ 90, leak-scan, 4 bats gates | ✅ verified |
| `auto_close_disabled: true` on `G1-CLOSE-INTERMEDIATE` | T08 AC7's "no new WARN" claim | `WU-90-gate-1-close-intermediate.md` frontmatter | ✅ verified |

---

## 11. Open questions to decide at arming

Six. The first three are the ones that change what gets built.

1. **Accept the marker-gating, or reject the invariant.** § 4 shows the BROAD form is
   unsatisfiable (6 of 11 correctly-closed features). The narrowing makes T07 satisfiable
   but also makes it **inert on all existing history** — it can only ever fire on a gate
   auto-closed after T06 ships. If you want the debt reconciled on the 6 features that
   already carry it, that is a *migration*, not an invariant, and it is not drafted. Is an
   invariant that only binds going forward worth $2.25? *Recommendation: yes — the
   alternative is a predicate that blocks correct closes, and `[FEAT-2026-0049/G2-CLOSE]`
   is what that costs.*

2. **The terminal auto-close path has no reconciler, and gate 2 does not give it one.**
   5 of 11 features had their terminal close auto-close (§ 4a fact 1). On that path no agent
   runs, so T07 short-circuits and T06's enumeration is the *only* record — read by an
   operator, if at all. Gate 2 makes the debt **legible** there, not **collected**. Is that
   acceptable, or does the terminal auto-close path need its own follow-up? *Recommendation:
   accept for gate 2; the terminal stub already tells the operator they are the last line
   (issue #157), and T06 upgrades that from a paragraph to a worklist.*

3. **`write_stub_retrospective_terminal` has no idempotency guard.** Its intermediate
   sibling skips when a `## Gate N … auto-closed` heading already exists; the terminal one
   appends unconditionally, guarded only upstream by `_already_auto_closed`. Today it
   appends ~10 lines; after T06 it could append a hundred. Add the guard in T06 (scope
   creep, but small), or leave it? T06 currently has it in "Do not touch" and forbids the
   session adding one on its own initiative. *Recommendation: add it to T06 as one more AC
   if you are comfortable with the scope; the asymmetry is pre-existing but T06 raises its
   cost.*

4. **Should the enumeration cap be 40 criteria?** T06 AC7 lists the first 40 and emits an
   explicit `… K further criteria not listed` line — no silent truncation. A gate with 8 WUs
   at 10 criteria each hits it. Raise, lower, or drop the cap?

5. **Is T08 worth $1.25, or is `close-discipline.md` §4's row (T07 AC8) enough?** The doc row
   is the human surface, T08 is the mechanical one. #265's measurement says documentation
   alone was what failed — the guards *were* in the source, just not in an authoring
   surface. *Recommendation: keep T08; it is the first time this repo has shipped a guard
   and its prediction together, and that is the whole lesson of $99.30.*

6. **The consumer-visible contract list from gate 1 needs your signature.**
   `RETROSPECTIVE.md` § *Consumer-visible contract changes* enumerates six items and
   explicitly routes acknowledgment to this checkpoint rather than self-acknowledging.
   **Item 1 is a behaviour change for features already on disk** — the roadmap row now
   flips to `done` from any non-`done` status. Read it before arming.

---

## 12. Arming checklist

- [ ] Gate 1's consumer-visible contract list acknowledged (open question 6) — this is the
      human signature `close-discipline.md` §3 requires, and gate 1's close deliberately did
      not self-provide it.
- [ ] `GATE-01.md` § *Reflection notes* written; `GATE-01.md` `status: open → passed`.
- [ ] Open questions 1–5 decided; any WU revised accordingly.
- [ ] `G1-PLAN`'s actual cost read from `events.jsonl` and checked against § 9's ceremony
      risk.
- [ ] `WU-05` … `WU-08` `status: draft → pending`.
- [ ] `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract`
      re-run and read — including any closing-guard-literal WARNs (#269), which are advisory
      and cheaper to fix now than at dispatch.
- [ ] Resume the driver.

`WU-92-gate-2-close.md` stays `status: draft` and is armed by the driver at the gate
boundary, not here.
