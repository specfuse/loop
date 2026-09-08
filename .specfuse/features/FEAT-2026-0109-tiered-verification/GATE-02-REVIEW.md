---
gate: 2
drafted_by: FEAT-2026-0109/G1-PLAN
open_questions:
  - "Q1 (T05): is the changed-file selector worth building in gate 2 at all, given the declared-tests rule already takes the per-attempt test run from 146.1s to 3.9s?"
  - "Q2 (T04/T06): should the narrow tier keep the cheap non-test gates (event-type-gate, roadmap-link-gate, arm-sweep-gate) that the roadmap's Goal sentence does not list?"
  - "Q3 (T06): is halting the gate the right response to a red broad run, or should it escalate for review and let the operator decide?"
  - "Q4 (PLAN.md, out of this unit's edit scope): planned_cost_usd is $26.00 against a WU sum of $49.50 — the number needs the operator's hand."
---

# Gate 2 review — the per-attempt tier

Written by `FEAT-2026-0109/G1-PLAN` for the human who arms gate 2. Gate 2's
drafts are `WU-04` … `WU-07` plus the two closing units; all are `status:
draft` and arming is your act, not the driver's.

## If you check only three things, check these

1. **The absent-key default in T04.** A `verification.yml` entry that declares
   no tier must keep today's behaviour — run per attempt *and* in the broad
   run. If that default is inverted (unannotated means per-gate-only), every
   project that upgrades silently stops running most of its gates per attempt,
   and nothing fails to tell them. This is the one decision in the gate that
   is unrecoverable by a later fix, because the damage is silent.
2. **T06 exists and is armed together with T04.** T04 alone ships a driver that
   verifies less per attempt and never makes up the difference. T04 without T06
   is a hollow pass at feature scale. If you reject or defer T06, reject T04
   with it.
3. **T07's decision, in § "The differing-sha gap" below.** I chose to move the
   wording rather than the mechanism. It is a correctness argument, not a
   convenience one, and the retrospective deferred it to this session
   deliberately — if you disagree, T07 is the unit to change and it is cheap
   ($1.50) and independent of the rest.

## What gate 2 is worth — measured, in this session

Run on gate 1's head, under `.venv`, unsandboxed (the sandbox falsely reds
roughly a dozen git/network tests here, so a sandboxed run is not a measurement
of the code). The first two rows are gate 1's `RETROSPECTIVE.md`; rows three
through five were run fresh here.

| Selection | Modules | Tests | Wall clock |
|---|---|---|---|
| Full `code` set (16 gates) | — | — | **169.4s** |
| Full unittest suite alone | 393 | 3788 | 146.1s |
| Every test module importing the driver | 153 | 1704 | **61.8s** |
| A gate-1 unit's own declared modules (T01+T02+T03) | 3 | 14 | **3.9s** |
| `ruff check specfuse .specfuse/scripts tests scripts` | — | — | **0.05s** |

So the narrow tier is roughly **6s against 169.4s per attempt**. Two
consequences worth stating before anyone reads the saving as larger than it is:

- **The win scales with attempts, not with units.** Gate 1 ran three units at
  one attempt each: 3 × 169.4s ≈ 508s of verification. Under gate 2's tier that
  becomes 3 × ~6s + one broad run at 169.4s ≈ 187s — a 5.4-minute saving on a
  clean gate. On a gate where a unit burns its full three attempts the saving
  is far larger, and on a one-unit gate it is nearly nothing. Gate 2 pays off
  exactly where the loop currently hurts most.
- **Moving the non-test gates buys almost nothing on its own.** Tests are
  146.1s of the 169.4s; everything else — lint, security, coverage, leak-scan,
  five bats suites, four linters — is ~23s combined, and `ruff` alone is 0.05s
  of it. The tiering is worth building only because it narrows the *test* run.
  Any design that tiers the cheap gates and leaves `tests` whole is not worth
  its complexity.

## Decisions, and why

### 1. One `code:` list with a per-entry tier, not two top-level lists

`scripts/smoke-test.sh` derives CI's gate list from `verification.yml` at run
time (#592) and the CI workflow just invokes that script — the file's own
header says a gate added there is executed by CI with no other edit. A
`code-narrow:` / `code-broad:` split would silently drop gates from CI the
moment the runner kept reading `code:`, which is the exact failure the file's
header records having already happened once ("six gates ended up declared and
never run"). One list, one annotation per entry. **Affects T04.**

### 2. Absent key means "runs in both tiers"

The fail-safe direction is the one where forgetting to annotate costs wall
clock, not coverage. Opting a gate **out** of the per-attempt run is then an
explicit, reviewable declaration, and a project that upgrades without touching
its config behaves byte-identically to today. **Affects T04**; it is a
definition-of-done bullet in `GATE-02.md` for that reason.

### 3. The narrow tier fails safe, never open

Empty selection, a unit whose `produces:` names no test path, an unmapped file,
a missing or stale map — every one of them runs the gate's **full** command. A
narrow tier that ran zero tests and reported PASS would manufacture the hollow
pass this whole methodology exists to prevent, at every attempt of every unit.
**Affects T04 and T05.**

### 4. The broad run happens before the close, and red halts the gate

Not after the close (the close would have written a verdict against unverified
work) and not as advice (a gate red for advice gets ignored — the roadmap-link
gate's comment in `verification.yml` records that lesson). The record is
tree-keyed with T02's existing `HEAD^{tree}` primitive so the three driver
restarts a gate like gate 1's incurs do not re-pay 169.4s each. **Affects T06.**

### 5. The differing-sha gap: **the wording moves, not the mechanism**

`GATE-01.md` claims "Attribution runs at most once per gate". The mechanism —
`gate_baseline_check`'s tree/sha dedup, reached via
`attribute_failure_to_baseline` — guarantees at most once **per tree state per
gate**. Two units failing at different shas, separated by a landed unit that
changed tracked content outside `.specfuse/`, legitimately re-probe. The
covering test exercises the same-tree case only.

I chose to reword the claim. Three reasons, in the order they weigh:

1. **The mechanism is right and the sentence is wrong.** A baseline record is a
   measurement *of a tree*. Reusing it across a landed change would answer "did
   this failure pre-exist?" against a tree that no longer exists — which is
   mis-attribution, the single thing T01 was built to prevent. Holding the
   stronger bound would make attribution wrong precisely in the case gate 2's
   narrowing makes more common.
2. **The cost the bound exists to cap is already capped.** Tree-keying bounds
   probes to one per landed change, on the failure path only. Gate 1 measured
   attribution firing **zero** times across three units. The worst realistic
   case is a small number of ~170s probes on a gate that is already failing —
   which is exactly when a fresh measurement is worth most.
3. **Moving the mechanism is out of a drafting session's authority.** Holding
   "once per gate" literally needs new per-gate state outside
   `gate_baseline_check` — a counter or a gate-scoped already-attributed flag.
   That is the behavioural change this unit's escalation trigger reserves for
   an operator. Choosing the wording keeps T07 to documentation plus tests, and
   is why this session did not block: the decision was answerable from gate 1's
   code and retrospective alone.

T07 therefore corrects three surfaces carrying the same overclaim —
`GATE-01.md`'s bullet, `attribute_failure_to_baseline`'s docstring, and
`PLAN.md` § Notes' "bounded to one dispatch per gate" — and adds the two tests
that make the distinction real: a differing-**tree** case that re-probes (which
has no test anywhere today), and a differing-**sha**, same-tree case that still
dedups. The second is what stops the first from degenerating into "any second
call re-probes". **Affects T07.**

One authoring hazard I found while drafting and put in T07's body so it is not
rediscovered by failing: `_current_tree_hash()` shells out to `git ls-tree
HEAD` in the process's working directory, so the existing `AttributionDedup`
test — which uses a bare temporary directory for the gate file — is really
reading *this repo's* tree, identical across both of its calls. Varying the
tree needs a real temporary git repository, not a monkeypatched hash.

## "Tests touching changed files" — the rule, and the three it beats

This is the open design question `PLAN.md` sequenced gate 1 to inform. Gate 1
made the driver's failure path explicit; here is what that context decides.

**Recommendation: line-granularity coverage contexts, unioned with the unit's
own declared test paths, with a fail-safe fallback to the full command.**

The four options, against the measurements above:

| Rule | What it selects for a `loop.py` edit | Verdict |
|---|---|---|
| **Path convention** (`loop.py` → `test_loop*.py`) | almost nothing — the covering modules are named `test_baseline_provenance.py`, `test_lazy_baseline_e2e.py` | Rejected. Free, and fails **open** — the one direction the tier may not fail. |
| **Import graph** | 153 of 393 modules, 1704 tests, **61.8s** | Rejected. Narrows only 58%, because `loop.py` is one ~9k-line module. Its precision is capped by module granularity and this repo's granularity is wrong for it. |
| **Declared mapping in `verification.yml`** | whatever the operator writes; for `loop.py` it would honestly have to say "everything" | Rejected as the primary rule. Cheap and auditable, but it buys nothing on the file that matters most, and it goes stale silently. |
| **Coverage contexts** (`dynamic_context = "test_function"`) | the tests that executed the changed *lines* | **Chosen.** The only option whose precision is not capped by module size, built from data the broad run already produces under `coverage run`. |

Two things about this recommendation that should be read plainly:

- **It is not a speed unit, and T05 says so in its own body.** T04's
  declared-tests rule already gets 146.1s → 3.9s. T05 adds almost no speed. What
  it adds is **attribution precision**: a unit that edits `loop.py` and breaks a
  test it never declared is otherwise caught only at the broad run, after every
  unit in the gate has landed, when "which unit broke it" is expensive to
  answer. That is the same question gate 1's lazy attribution answers one tier
  down, which is why gate 1 was the right gate to sequence before this decision.
- **The map lags by construction.** The broad run happens before the close, so
  the map an attempt consults describes an earlier tree, and a brand-new source
  file has no entry at all. Both are "unresolvable" and both fall back to the
  full command. In a project's first gate the changed-file half does not narrow
  anything; the declared-tests half works from attempt one. If you would rather
  not carry that asymmetry, Q1 below is the place to say so.

## How gate 2's `feature_oracle` advances gate 1's

Gate 1: `python3 -m unittest tests.test_lazy_baseline_e2e -q`.
Gate 2: `python3 -m unittest tests.test_tiered_verification_e2e -q`.

Gate 1's oracle asserts a negative **at one moment**: on a green gate entry the
`code` set is not executed. A driver that then runs all sixteen gates on every
attempt satisfies it completely — and that is exactly the driver gate 1
shipped. Gate 2's oracle strengthens it in two directions gate 1's could not
reach:

1. **From one moment to every attempt.** Gate 1's claim is the n=1 case of "the
   broad set does not run per attempt". Gate 2's asserts it across several
   attempts inside one dispatched gate: existential becomes universal.
2. **From removal to liveness.** Gate 1 only removed work, so it owed no proof
   that anything still happens. Gate 2's oracle must assert the broad set
   **does** run — once, before the close — and that a red broad run halts the
   gate. Gate 1's oracle has no shape for a liveness property, and this is the
   half that makes narrowing safe rather than merely cheap.

It also closes a hole gate 1's own close named. Narrowing makes a per-attempt
failure cheaper and therefore more likely, so gate 2's oracle must drive a
narrow-tier attempt that **fails** and observe attribution fire. Gate 1's
retrospective records attribution firing **zero** times in production; gate 2's
oracle is the first surface on which that path is part of a gate's exit
condition rather than a unit test alone.

## Roadmap-anchor check

`PLAN.md`'s `roadmap_goal` reads, in part: "*the per-attempt gate set narrows to
what the unit actually touched with the full suite reserved for once per gate*".
The roadmap detail section's `**Goal.**` is more specific: "*Per attempt: the
unit's declared tests, tests touching changed files, lint, and the feature
oracle. Once per gate before the close: the full suite with coverage, bats,
leak-scan, security.*"

| Drafted unit | Anchored to | Verdict |
|---|---|---|
| T04 per-attempt tier | "the per-attempt gate set narrows"; declared tests, lint, feature oracle | On anchor |
| T05 changed-file selector | "tests touching changed files" | On anchor |
| T06 per-gate broad run | "the full suite reserved for once per gate … with coverage, bats, leak-scan, security" | On anchor |
| T07 attribution bound | **not in the roadmap goal** | Off anchor, deliberately — see below |

Three findings:

1. **T07 is off-anchor and in scope by operator decision.** It is a correctness
   carry-over from gate 1, not part of the tiering goal. It is here because the
   operator answered the previous attempt's block by directing that gate 2
   carry one extra unit for this gap, and because gate 2's narrowing is what
   makes the two readings of the bound diverge. If you want gate 2 to be
   strictly the roadmap's goal, T07 is the unit to pull — nothing else depends
   on it.
2. **The roadmap row's title is stale.** Row and detail heading both read
   "Tiered verification and a **cached** baseline probe"; `PLAN.md`'s title and
   the whole of gate 1 say **lazy**. The rescope happened and the row did not
   follow. Editing the roadmap is outside this unit's `produces:`, so it is
   flagged rather than fixed.
3. **The roadmap's `**Goal.**` does not list the cheap non-test gates.** It
   names lint but not `event-type-gate`, `roadmap-link-gate`, `arm-sweep-gate`
   or `agent-policy-example-lint`, which together cost a couple of seconds and
   catch real things. T04's absent-key default means they stay in the
   per-attempt tier unless someone annotates them out. That is the safe
   outcome, and it is Q2 below.

## Open questions

Each is answerable at arm time; none blocks drafting.

- **Q1 — is T05 worth building in gate 2?** *(affects `WU-05`.)* The
  declared-tests rule already delivers 97% of the speed; T05 buys attribution
  precision at the cost of coverage dynamic contexts (slower broad run, larger
  data file) and a lagging map. Deferring it to gate 3 or to a follow-up
  feature is a coherent choice — T04 and T06 stand without it, and T04's
  fail-safe fallback means the "tests touching changed files" clause simply
  resolves to nothing until it lands. My recommendation is to build it, because
  the broad run's late, ambiguous attribution is the thing gate 2 otherwise
  makes worse.
- **Q2 — should the cheap non-test gates stay per-attempt?** *(affects `WU-04`,
  and `WU-06` by consequence.)* They cost ~2s combined. Keeping them is the
  default T04 ships. The roadmap's `**Goal.**` sentence does not list them,
  so an operator reading the roadmap alone might expect them moved.
- **Q3 — halt, or escalate for review, on a red broad run?** *(affects
  `WU-06`.)* T06 drafts "halt the gate, blame no unit". The alternative is to
  record the failure and let the close report it, which is softer and risks a
  close writing a verdict over a red suite. I drafted the strict version
  deliberately; it is the reversible direction.
- **Q4 — `planned_cost_usd`.** *(affects `PLAN.md`, not a WU.)* The frontmatter
  says $26.00 (gate 1's five units plus the scaffolded gate-3 close). Gate 2's
  six drafted units add $23.50 — T04 $4.00, T05 $4.00, T06 $3.50, T07 $1.50,
  close $4.50, plan-next $6.00 — for a WU sum of $49.50, and `lint_plan.py`
  already WARNs at a 90% delta. This unit's scope on `PLAN.md` is the gate-2
  graph list and nothing else, so the number is left for you. $49.50 is the
  arithmetic; gate 3's substantive unit will raise it again.

## Lint state of the drafts

`python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0109-tiered-verification`
exits **0** with zero ERROR findings. The WARNs are known and none is a defect
in the drafts:

- Four `produces` paths were already delivered by a `done` gate-1 unit
  (`loop.py`, `tests/test_lazy_baseline_e2e.py`, `RETROSPECTIVE.md`). Each
  drafted unit states the incremental edit it makes, which is the remedy the
  WARN names. Gate 1's own T02/T03 carry the identical WARN.
- `WU-07` mentions `loop.py` without a `produces_driver_helper` — it adds no
  driver symbol, only a docstring correction and tests. T02 and T03 warn the
  same way.
- Ceremony proportionality (7 substantive units across 3 gates). Gate 3's
  atomicity constraint (`[FEAT-2026-0019/G1]`) is why this feature is three
  gates rather than one; the WARN has no bearing on the drafts.
- The `planned_cost_usd` delta — Q4 above.
