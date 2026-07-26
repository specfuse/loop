# Gate-2 review — drafted by `FEAT-2026-0069/G1-PLAN`

The operator's pre-arm document for gate 2 of `FEAT-2026-0069-monitoring-check-targets`.
Flip each gate-2 WU `status: draft` → `pending` only after working the **Open questions**
and **Cross-repo contracts** sections at the bottom.

> **Filename note.** This file is `GATE-02-REVIEW.md`, not `GATE-01-REVIEW.md`. `WU-91`'s
> body and `GATE-01.md`'s definition of done both say "`GATE-01-REVIEW.md`", but the
> driver's `assert_gate_review_exists` (`specfuse/loop/loop.py:4005-4026`) computes the
> expected filename from the **next** gate — `GATE-{this_gate+1:02d}-REVIEW.md` — so for a
> gate-1 `plan-next` that is `GATE-02-REVIEW.md`. A prior attempt of this WU failed
> exactly here (`assert_gate_review_exists: GATE-02-REVIEW.md absent or empty`). The WU
> text is the stale label; the driver is authority. `GATE-01-REVIEW.md` exists alongside
> this file as a pointer so the name `GATE-01.md` promises also resolves. Same divergence
> recorded in `FEAT-2026-0026` and `FEAT-2026-0027`; it is a scaffold wording bug worth
> filing, not a per-feature decision.

---

## 1. What gate 1 shipped

Gate 1 separated the two axes `monitoring.yml` conflated. **`component` stays the unit of
deployment and attribution; `checks[].targets` is now the unit of failure-artifact
enumeration.** Five substantive WUs, all `done`:

| WU | shipped | planned → actual |
|---|---|---|
| `T01` | `targets` accepted and structurally validated — `_check_targets()`, `_TARGET_REQUIRED_FIELDS`, `_TARGETLESS_CHECK_TYPES` in `specfuse/loop/lint_monitoring.py` | $3.00 → $0.74 |
| `T02` | a multi-trigger host component with `targets[]` in the shipped example + the docs `## Check targets` section | $2.50 → $1.51 |
| `T03H` | the tree-wide migration `T02`'s criteria did not ask for — every remaining `dlq` check across six files | $2.00 → $0.83 |
| `T03` | `targets` **required** on `dlq`; the minimal discovery reference-impl change `PLAN.md` §10 pre-registered | $3.00 → **$7.65** (4 attempts, 1 escalation) |
| `T04` | `queue-stalled` check type — enum + example block + docs row, shipped atomically | $2.50 → $1.21 |

**The emitted shape gate 2 must be authored against** — this is the whole reason gate 2 is
drafted now rather than at feature-drafting time. From `.specfuse/monitoring.yml.example:128-170`:

```yaml
  - name: acme-functions-host
    type: multi-trigger-host
    checks:
      - type: dlq
        harvest_mode: peek
        targets:
          - subscription: acme-orders-created-sub
            function: ProcessOrderCreated
          - subscription: acme-orders-cancelled-sub
            function: ProcessOrderCancelled
          - subscription: acme-inventory-sync-sub
            function: SyncInventoryLevels
      - type: heartbeat
        targets:
          - name: nightly-reconciliation
            cron: "0 2 * * *"
            timezone: Etc/UTC
          - name: hourly-cache-warm
            cron: "0 * * * *"
            timezone: Etc/UTC
      - type: queue-stalled
        targets:
          - subscription: acme-orders-created-sub
            function: ProcessOrderCreated
            stall_after: 15m
```

Per-check-type matrix as the validator actually enforces it
(`specfuse/loop/lint_monitoring.py:255-266`): `dlq` and `queue-stalled` **must** carry
`targets` (`subscription` + `function`); `heartbeat` **may** (`name` required, `cron` and
`timezone` accepted and opaque); `error-logs` and `http-5xx` are **rejected**; `invariant`
falls through to "permitted, nothing required" — the accident `T05` exists to decide.

**What gate 1 deliberately did not prove.** `/derive-monitoring` still returns one
component per trigger. The schema can express the right answer; discovery cannot yet
produce it. That is gate 2.

---

## 2. What changed from `PLAN.md`'s gate 2 sketch, and why

The sketch named four elements. All four are drafted; none is deferred. Two are drafted
differently than sketched, and one WU exists that the sketch did not name.

| sketch element | drafted as | change from the sketch |
|---|---|---|
| re-key `discover_components` onto deployment evidence | `T06` | **The contract change is now written out as a table**, not left as "treat it as a contract change". `evidence_markers` → `deployment_markers` + `scope_prefix`; new sibling `patterns["triggers"]` table; `http_serving` / `message_consuming` become *derived* rather than hand-declared. The sketch did not name where the trigger coordinates live, and that was the load-bearing unknown. |
| the N-trigger fixture | `T07` | Split **out** of the re-key rather than bundled with it. The probe (§4) shows the re-key alone already yields 1 component with N `dlq` targets; what it does not yield is per-schedule `heartbeat` targets. Keeping them together would have let `T06`'s red→green proof pass on the `dlq` half while the heartbeat half stayed silently unimplemented. |
| mechanical target-list generation | `T07` (schedules) + already shipped by `T03` (subscriptions) | Roughly **half of this was already delivered in gate 1**. `suggest_checks` already fans a record's `subscriptions` into one `dlq` target per entry (`tests/test_derive_monitoring_discovery.py:108-118`). It consumes `schedules` nowhere, so a multi-schedule host still gets one target-less `heartbeat` — that gap is `T07`'s substantive change, and it is smaller than the sketch implied. |
| skill method prose | `T08` | Narrowed. The sketch said "Step 1 and Step 4"; gate 1's close already rewrote §4a with the full targets matrix and worked examples. What is stale is the **discovery** half — Step 1's framing, the record-field list, and the Seams table's step-1 rows — plus the matching lines in `PROMPT.md`. |
| — | **`T05` (new)** | Not in the sketch. Gate 1's retrospective routed two fixes into "gate 2's first WU": the `invariant` × `targets` fall-through nobody decided, and the `_check_targets` docstring `T04` made wrong. Drafted with `depends_on: []` so it does not sit on the re-key's critical path. |

**Nothing is deferred out of gate 2.** The two things that stay out of the *feature* were
already decided at drafting and are not relitigated here: fingerprinting is
FEAT-2026-0040's (with the binding constraint that its fingerprint model must include the
target key), and per-target dials / the `environments` × `components` cross-product /
issue #248 are `PLAN.md`'s recorded non-goals.

---

## 3. §10 helper-duplication pre-flight — run and recorded

Commands run in this session, over the whole tree excluding `.git/` and
`.specfuse/features/`:

```
grep -rn "def <symbol>\|<symbol>" --include='*.py' --include='*.md' --include='*.sh' .
```

for each of `discover_components`, `suggest_checks`, `render_monitoring_yml`,
`audit_diagnosability`, `_STACK_A_PATTERNS`, `_STACK_A_TREE`, `_STACK_B_PATTERNS`,
`_STACK_B_TREE`, `_with_subscriptions`, `_STACK_TOKEN_DENYLIST`.

| symbol | definitions | call sites / references | disposition |
|---|---|---|---|
| `discover_components` | **1** — `tests/test_derive_monitoring_discovery.py:58` | 7 in-module call sites (`:373, 394, 418, 419, 441, 445, 464, 682`); 5 prose references across both `SKILL.md` copies (`:103, 294, 301`) and both `PROMPT.md` copies (`:39, 50`) | **in scope**: `T06` (the definition + call sites), `T08` (all prose references, canonical then synced) |
| `suggest_checks` | **1** — `:90` | 12 in-module call sites; prose in both `SKILL.md` (`:105, 295, 301, 328`) and `PROMPT.md` (`:39, 54`) | **in scope**: `T07` (schedules → `heartbeat` targets), `T08` (prose) |
| `render_monitoring_yml` | **1** — `:183` | 4 in-module call sites (`:382, 470, 600, 687`); **zero** prose references | **in scope, narrowly**: `T07` AC6 (quote emitted `cron`) only. Named in `T06`'s *Do not touch* with the reason — nested `targets` rendering already works and is pinned by `TestRenderTargetsRoundTrip:590`. |
| `audit_diagnosability` | **1** — `:132` | 4 in-module call sites; prose in `SKILL.md:296, 301` and `PROMPT.md:39` | **out of scope for code**, named in `T06`'s *Do not touch* with the reason: the probe (§4) confirms it stays green under the re-key, because its role-name property checks `any(name in tree[relpath] …)` across a component's evidence and the deployment artifact stamps the name. Its prose row **is** in `T08`'s scope. |
| `_STACK_A_PATTERNS` / `_STACK_A_TREE` | 1 each — `:268` / `:292` | 7 / 6 in-module call sites | **in scope**: `T06` AC4 migrates both |
| `_STACK_B_PATTERNS` / `_STACK_B_TREE` | 1 each — `:312` / `:336` | 2 each | **in scope**: `T06` AC4 migrates both. Not named in the WU-91 minimum list; found by the enumeration and added, since a re-key that migrates Stack A and forgets Stack B is precisely the §10 failure. |
| `_with_subscriptions` | **1** — `:356` | 3 call sites (`:374, 440/444, 463`) | **in scope, deleted**: `T06` AC7. It is `T03`'s deliberate stand-in for evidence gate 2 derives; leaving it would let every downstream assertion pass on test-injected data rather than discovered data. |
| `_STACK_TOKEN_DENYLIST` | **2** — `tests/test_derive_monitoring_discovery.py:244` **and** `tests/test_design_for_diagnosis_rule.py:25` | 1 use each (`:497`, `:71`) | **out of scope, both hits named**: the duplication is deliberate (the two boundary tests keep identical denylists rather than share an import, documented at `:241-243`). Named in `T06`'s *Do not touch* with the reason, because editing one copy without the other is the exact §10 defect. |

Two symbols beyond WU-91's minimum list were enumerated because the re-key reaches them:

- **`_STACK_B_*`** (above) — a second stack, easy to miss.
- **`validate_monitoring`** — `specfuse/loop/lint_monitoring.py:~50`, imported by
  `tests/test_derive_monitoring_discovery.py:44`, `tests/test_lint_monitoring.py`,
  `tests/test_monitoring_fenced_blocks.py`, and `.specfuse/scripts/lint_monitoring.py`.
  In scope for `T05` (behavior) and named in `T06`'s and `T07`'s *Do not touch* — `T07`
  in particular escalates rather than edits it, since a validator change there would mean
  the emitted shape and the schema disagree.

**Every hit is either in a drafted WU's scope or named in that WU's "Do not touch" with a
reason.** No hit is unaccounted for.

---

## 4. Runtime probe for the re-key (`planning-discipline.md` §4)

The re-key changes what discovery returns for existing fixtures — a behavioral default
change, which may **not** be armed on "mechanical, nothing design-open." A deployment-keyed
`discover_components` was applied locally and the **full** oracle
(`python3 -m unittest discover -s tests -v`, 1473 tests) was run twice. The probe has been
reverted; `diff` against the pre-probe backup is empty and
`python3 -m unittest tests.test_derive_monitoring_discovery` is `OK`.

### Pass 1 — algorithm re-keyed, fixtures untouched

**4 failures of 1473.** This is `T06`'s enumerated test surface, pasted verbatim into that
WU so it does not rediscover its own breakage attempt by attempt:

```
FAIL: test_discovered_config_passes_lint_monitoring (test_derive_monitoring_discovery.TestDiscoveredConfigPassesLint)
      AssertionError: Lists differ: ["missing top-level 'components' key"] != []
FAIL: test_fixture_tree_yields_expected_components (test_derive_monitoring_discovery.TestFixtureTreeYieldsExpectedComponents)
      AssertionError: 0 != 2
FAIL: test_second_stacks_render_also_passes_lint (test_derive_monitoring_discovery.TestNeutralRecordsSurviveASecondStack)
      AssertionError: Lists differ: ["missing top-level 'components' key"] != []
FAIL: test_autofix_round_trips_as_quoted_off_string (test_derive_monitoring_discovery.TestAutofixQuotedInEmittedYaml)
      AssertionError: 'autofix: "off"' not found in '…components:\n'
```

One cause behind all four: the Stack A and Stack B trees carry no deployment artifact, so a
deployment-keyed matcher returns **zero** components and every render is an empty
`components:` block.

### Pass 2 — fixtures migrated too

**1 failure of 1473**, and it is a single equality that has to change:

```
FAIL: test_fixture_tree_yields_expected_components
      AssertionError: ['services/web/deploy.txt', 'services/web/handler.txt'] != ['services/web/handler.txt']
```

**The cascade is bounded to one file.** Nothing outside
`tests/test_derive_monitoring_discovery.py` goes red — not `audit_diagnosability`, not the
validator, not the skill-registration tests, not the scaffold drift guards. `WU-91`'s
escalation trigger (block if the re-key cascades beyond what one gate can hold) does **not**
fire.

### What the probe found that the plan did not predict

1. **Two boundary tests pass vacuously on an empty component list.**
   `test_neutral_records_survive_a_second_stack` and `test_output_is_deterministic` both
   stayed **green** through pass 1 — against zero components. `len([]) == len([])`,
   `sorted([]) == sorted([])`, and two empty sets are disjoint. These are the feature's
   provider-neutrality boundary tests and they are currently satisfiable by a discovery
   function that returns nothing. `T06` AC6 adds non-emptiness assertions to both. This is
   an existing defect in the gate-1 test suite, not something the re-key introduces.
2. **The falsifiable core is reachable, and it was checked, not assumed.** A one-deployable
   tree with 3 subscription triggers and 2 schedule triggers was run through the probed
   `discover_components`: it returned **1 component** carrying `subscriptions` of length 3
   and `schedules` of length 2, and `suggest_checks` fanned the subscriptions into a `dlq`
   check with **3 targets**. The `heartbeat` check came back **target-less** — `schedules`
   is derived but unconsumed. That single observation is what split `T07` out of `T06`.
3. **`_miniyaml` parses an unquoted `cron: 0 2 * * *` correctly.** Checked directly, so
   `T07` AC6's quoting requirement is a spelling-consistency choice against the shipped
   example, not a parser fix. Recorded so the WU does not spend an attempt proving it is
   not a parser bug.
4. **`_with_subscriptions` is what makes the current suite look greener than it is.** With
   it in place, `TestDiscoveredConfigPassesLint` passes on subscription data the *test*
   injected. `T06` AC7 deletes it for that reason.

---

## 5. Cost

### Per-WU estimates for gate 2

| WU | type | planned | reasoning |
|---|---|---|---|
| `T05` | implementation | **$2.00** | Two lookup-table entries, one docstring, two tests, one docs row. Comparable to `T03H` ($0.83 actual) and `T04` ($1.21 actual); priced above both because it takes a schema *position*. |
| `T06` | implementation | **$4.00** | The largest. A contract change plus a migration of four fixture constants. The enumerated failure list (§4) removes the discovery cost that made `T03` expensive, but this is the WU most likely to need a second attempt. |
| `T07` | implementation | **$3.50** | A new fixture with cardinality 3+2, a `suggest_checks` change, a renderer quoting change, and a four-clause definition-of-done assertion. |
| `T08` | implementation | **$2.50** | Prose across two files × two copies, plus a sync run and one new test. Priced above a pure-docs WU because the canonical-then-sync choreography has a drift guard behind it. |
| `G2-CLOSE` | close | **$5.00** | The `planning-discipline.md` §5 floor. Gate 1's `close-intermediate` cost **$10.01** across two attempts against this same $5.00 floor, so treat $5.00 as a floor and not an expectation. |
| | | **$17.00** | |

### Reconciliation against `PLAN.md`'s $34.00 — it does not reconcile, and neither number was adjusted

`WU-91` AC9 requires this be reported rather than silently fixed. The arithmetic:

| | |
|---|---|
| gate 1 substantive, actual | **$11.94** (8 attempts across 5 WUs) |
| gate 1 `G1-CLOSE-INTERMEDIATE`, actual | **$10.01** (2 attempts: $4.45 + $5.57) against a $5.00 estimate |
| gate 1 `G1-PLAN`, actual | **not yet in `events.jsonl`** — attempt costs are recorded at outcome time, so this session cannot read its own. This is its **third** attempt (frontmatter `attempts: 2`); the two prior ones both spent without producing the review artifact. |
| gate 2, planned | **$17.00** |
| **feature total** | **≥ $38.95** + `G1-PLAN`, against `PLAN.md`'s **$34.00** |

So the feature is **over its planned figure by at least $4.95** before gate 2 dispatches a
single WU, and the true gap is larger by whatever `G1-PLAN` cost.

**Where the $34.00 went wrong** — and it is worth naming precisely, because
`.specfuse/LEARNINGS.md` `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` warns against re-basing a
plan onto its own failure and then calling the result accuracy:

- Gate 1's **substantive** estimating was good: $11.94 against $11.00 as drafted, +8.6%, and
  four of five WUs came in 39–75% *under*. The entire overrun is `T03`'s three wasted
  attempts ($5.26) caused by one under-scoped acceptance criterion in `T02`.
- Gate 1's **ceremony** estimating was not: $10.01 actual against $5.00 planned for
  `close-intermediate` alone, +100%, and `G1-PLAN` is on its third attempt against another
  $5.00. `planning-discipline.md` §5's $5.00 figure is explicitly a *floor*, and this
  feature is the second dataset saying the floor is well below the mean.
- The sketch priced gate 2 at **~$13**; drafted against the real emitted shape it is
  **$17.00**, which is the ordinary cost of drafting late rather than an estimating error.

### The lint cost-delta WARN did **not** converge, and the direction flipped

`PLAN.md`'s Notes predicted the WARN would converge once `G1-PLAN` ran. It did not:

- before this WU: `planned_cost_usd $34.00 differs from sum of WU planned costs $28.00
  (delta 18%, threshold 10%)`
- after this WU: the WU sum is **$40.00** ($28.00 + $12.00 of gate-2 substantive), so the
  delta is ~**18% in the opposite direction**.

The prediction assumed gate 2's real WUs would price out near the ~$13 sketch. They price
out at $12.00 substantive, which is close — the sketch's $13 simply never included
`G2-CLOSE`'s $5.00, which was already in the sum being compared. The WARN is non-fatal
(exit `0`) and `lint_plan.py` passes. **Neither `PLAN.md`'s $34.00 nor any WU estimate was
adjusted to silence it**; see Open question 4.

### `GATE-02.md`'s `cost_budget_usd`: revised $18.00 → $22.00

Drafted at $18.00 when gate 2 was a ~$13 sketch. Against a $17.00 plan it is 6% of
headroom — a brake that fires by construction on the terminal close, which is the exact
failure `planning-discipline.md` §5 describes for a budget set to the sum of its own
estimates. Gate 1's evidence makes this concrete: its close-intermediate alone consumed
$10.01. $22.00 carries the $17.00 plan plus roughly one full re-attempt of `T06`, and still
halts a runaway well short of the feature's remaining budget. Revised in `GATE-02.md` with
the reasoning inline.

---

## 6. Cross-repo contracts (`/authoring-work-units` §8)

Every value the drafted WUs name that lives in another system, or that a planner could have
invented. The §8 blind spot is systematic in `plan-next` drafts, so this table is
mandatory rather than decorative.

| value | used by | authoritative source | checked? |
|---|---|---|---|
| target coordinate names `subscription`, `function` | `T06`, `T07` | `specfuse/loop/lint_monitoring.py:260-264` `_TARGET_REQUIRED_FIELDS` | ✅ read this session |
| `heartbeat` target coordinates `name` (required), `cron`, `timezone` (opaque) | `T07` | same table + `_check_targets:300-311` | ✅ |
| `multi-trigger-host` as the component `type` string | `T07` fixture | `.specfuse/monitoring.yml.example:129` | ✅ |
| `code` gate names (`tests`, `lint`, `security`, `coverage`, `leak-scan`, `monitoring-example-lint`, `leak-scan-hook`, `sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`) | all four WUs' Verification sections | `.specfuse/verification.yml:15-69` | ✅ — all ten named, none invented, none omitted |
| canonical-vs-vendored skill path (`plugins/specfuse/skills/` → `.specfuse/skills/`) and the sync script | `T08` | `scripts/sync-scaffold.sh:92-110`; guard `tests/test_skills_vendored_in_sync.py` | ✅ — both copies `cmp`-identical today |
| `_CANONICAL_DIR` as the assertion target for skill-prose tests | `T08` AC1 | `tests/test_derive_monitoring_skill_registration.py:99-107` | ✅ |
| **the `[Function(nameof(...))]` extraction form, and "subscription names come from the trigger attribute, cron + IANA timezone from named constants on the timer classes"** | quoted in `T07`'s Context as the claim it does **not** prove | a downstream .NET backend **outside this tree** | ❌ **unchecked and uncheckable here** — see Open question 5 |
| `stall_after: 15m` on a `queue-stalled` target | not used by any drafted WU | `.specfuse/monitoring.yml.example:170`; opaque to the validator | n/a — discovery never emits `queue-stalled` |

---

## 7. Open questions — decide these before arming

**1. Is rejecting `targets` on `invariant` the right position?** `T05` implements
*reject*, on the reasoning that `invariant` already carries `fingerprint_by` as its
required per-check enumeration key, and `targets` is the generalization of exactly that —
so permitting both gives one check two competing keys that FEAT-2026-0040's fingerprint
model would have to reconcile with nothing in the schema saying which wins. The other two
options gate 1's retrospective listed are *permit deliberately, with a test* and *require a
coordinate*. **Recommendation: reject.** It is the conservative direction (a rejected field
can be permitted later without breaking anyone; the reverse cannot), and gate 1's permissive
fall-through has never been merged or released, so no consumer has ever seen it. If you
prefer a different position, edit `T05` before arming — the WU escalates rather than
silently implementing the opposite of an armed decision.

**2. The `patterns` table contract is a breaking change. Accept it now, or version it?**
`T06` removes `evidence_markers` and the hand-declared `http_serving` /
`message_consuming` booleans. Anyone who wrote a pattern table against gate 1's shape has
to rewrite it. **Recommendation: accept now, unversioned.** The reference implementation is
test-local (there is no `specfuse/loop/` module for it, deliberately), the only pattern
tables in existence are this repo's two fixtures, and the skill prose that teaches the
contract is `T08`'s deliverable in the same gate. Versioning a contract with two known
consumers, both inside this repo, would be ceremony.

**3. Does `T05` belong in gate 2 at all, or is it a separate bug?** It is unrelated to the
re-key and `depends_on: []`. **Recommendation: keep it here.** Gate 1's retrospective
explicitly routed both fixes to "gate 2's first WU", the change is two lookup-table entries
plus a docstring, and `G2-CLOSE` has to enumerate the `invariant` position in its
contract-change table either way — an open fall-through would have to be reported as an
undecided schema position in the feature's terminal close.

**4. `PLAN.md`'s $34.00 vs the $40.00 WU sum — leave both, or re-baseline?** Nothing was
adjusted (§5). The options are: leave `$34.00` as the honest original estimate and let
`G2-CLOSE` reconcile actuals against it; or re-baseline `PLAN.md` to ~$40.00 now and note
the re-baseline. **Recommendation: leave it.** `.specfuse/LEARNINGS.md`
`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]` is direct about this — a plan re-based onto its own
overrun reports the overrun as accuracy. The lint WARN is non-fatal and is itself the
signal. This is a judgement call and it is yours.

**5. Should gate 2 verify the extractability claim against a real repo?** The originating
issue claims every target coordinate is mechanically extractable without asking the
operator. That is confirmed only against a repo outside this tree. `T07`'s Context forbids
its fixture from being cited as evidence for it, and `G2-CLOSE` AC3 carries it as a
`## What the loop did NOT verify` entry with the operator re-run condition named.
**Recommendation: do not try to verify it inside gate 2.** Verifying it needs an operator
running `/derive-monitoring` against a real multi-trigger repo — the same post-merge
operator step FEAT-2026-0039 recorded for its own skill, and the same shape as
`[FEAT-2026-0039/G2-CLOSE]`'s rule about features whose definition of done is an operator
action. If you disagree, the honest way to do it is a follow-up unit against a named real
repo, not a richer fixture.

**6. Confirm discovery still never emits `queue-stalled`.** `T07`'s Stack C fixture is
*exactly* the shape a `queue-stalled` check is for (a multi-subscription host), and the
temptation to emit one there will be real. The existing position — a stall threshold is
operator judgement, the same class as `invariant.query`, so discovery must never invent one
— is pinned by `TestSuggestChecksNeverQueueStalled` and named in `T07`'s *Do not touch*.
**Recommendation: hold the position.** Flagged only because the fixture makes it newly
tempting.

**7. `test_neutral_records_survive_a_second_stack` and `test_output_is_deterministic` pass
on zero components today.** `T06` AC6 fixes it as a rider. If you would rather that landed
as its own hygiene WU with its own commit — it is a pre-existing gate-1 defect, not
something the re-key introduces — split it out before arming. **Recommendation: leave it in
`T06`.** It is two assertions in tests `T06` is already editing, and a separate WU would
cost more in ceremony than the fix.

---

## 8. Arming checklist

- [ ] Question 1 decided; `T05` edited if the answer is not *reject*.
- [ ] Question 2 acknowledged — the `patterns` contract break is accepted.
- [ ] Questions 3–7 read; any WU edits made **before** flipping statuses.
- [ ] Gate 1's consumer-visible contract-change table in `RETROSPECTIVE.md`
      (§ *Consumer-visible contract changes*, 9 items, **item 1 breaking**) acknowledged —
      `close-discipline.md` §3 requires a human signature and this checkpoint is where it goes.
- [ ] `T05`, `T06`, `T07`, `T08` flipped `status: draft` → `pending`.
- [ ] `GATE-01.md` `status: open` → `passed`, with the *Reflection notes* section filled in.
- [ ] `GATE-02.md`'s revised `cost_budget_usd: 22.0` confirmed or re-set.
- [ ] Resume: `python3 .specfuse/scripts/loop.py` (or the driver invocation this repo uses)
      from a venv — never two drivers on one feature.
