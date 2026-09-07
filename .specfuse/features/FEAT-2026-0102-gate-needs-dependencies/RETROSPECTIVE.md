# Retrospective — FEAT-2026-0102, gate dependencies (`needs:`)

## Gate 1

Gate 1 is the only gate. Three substantive units (T01 runner, T02
`gate_commands.py` ordering, T03 flip this repo's `verification.yml`) plus this
close. All three are `done`, each passed on its first attempt, and no unit was
re-armed.

This is the close's **first attempt**.

Every behaviour in `GATE-01.md`'s definition of done was re-demonstrated in this
session against the tree the driver will squash, and the `code` set was timed in
both gate shapes — the pre-feature one and the shipped one — back to back on that
same tree. What those runs show is in `## Measurements`; per
`close-discipline.md` §1 this close measures and a session that did not do the
work reads the measurements and settles the verdict.

## Measurements

Every figure below is a command run in this session. Two harnesses do the work,
both driving the real driver functions rather than re-implementing them:

- a **timing harness** that calls `loop.order_gate_set` then `loop._run_gate_set`
  once per gate and records per-gate wall clock — the same two functions
  `probe_baseline` calls, so the numbers are the probe's own cost, not a proxy
  for it. It is run twice: once against `.specfuse/verification.yml` as shipped
  (`after`), once against the same file with only the `tests` and `coverage`
  gate declarations restored to their pre-feature text as recorded verbatim in
  `WU-03-flip-verification-yml.md` (`before`). Nothing else differs between the
  two runs — same tree, same session, same machine, back to back.
- a **demonstration harness** that exercises each definition-of-done bullet,
  including two purpose-built bad inputs for the CONFIGURATION ERROR bullet and
  a purpose-built red test for the SKIP bullet. It exits non-zero if any check
  fails; it exited **0**.

Both need an unsandboxed shell: this repo's suite includes git-integration tests
that report ~11 spurious failures under a sandbox that denies `.git/` writes.

### Definition of done, bullet by bullet

| # | Behaviour from `GATE-01.md` | Command run in this session | Exit / observation |
|---|---|---|---|
| 1a | A gate may declare `needs: [<gate>]`; the driver runs the set in dependency order | demonstration harness, check `B1` — `order_gate_set` over the live `code` set | **0** — `tests` at index 0, `coverage` at index 3; declared order preserved among unrelated gates (all 16 names identical to declared order, because `coverage` is already declared after `tests`) |
| 1b | A gate whose dependency failed is reported `SKIP` and never counted as a pass | same harness, check `B1` — fixture set of `tests` (pointed at a throwaway dir holding one deliberately-failing test) + `coverage` `needs: [tests]`, run through `_run_gate_set` | **0** — `tests` `ok=False`; `coverage` report is `### coverage: SKIP — dependency 'tests' failed` with `ok=False`; the `coverage` command was never executed |
| 2a | An unresolvable `needs:` target is a CONFIGURATION ERROR, never a silent skip or pass | same harness, check `B2` — **negative observation** on a purpose-built bad set (`coverage` `needs: [nosuchgate]`) through `loop.order_gate_set`, `gate_commands._order_gates`, and `probe_baseline` | **0** — all three refuse. `ValueError: gate 'coverage' declares `needs: [nosuchgate]` but no 'nosuchgate' gate is configured in this set`; `probe_baseline` surfaces it as `CONFIGURATION ERROR: … This is not a work-unit failure — fix verification.yml and re-run.` |
| 2b | A dependency cycle is a CONFIGURATION ERROR | same harness, check `B2` — **negative observation** on a purpose-built two-gate cycle (`a` ↔ `b`), same three entry points | **0** — all three refuse: `` `needs` cycle detected involving gate 'a' ``, surfaced by `probe_baseline` in the same CONFIGURATION ERROR shape |
| 3 | `gate_commands.py` emits gates in the same dependency order the driver uses | same harness, check `B3` — `gate_commands.iter_code_gates` name list vs `loop.order_gate_set` name list over `.specfuse/verification.yml` | **0** — the two 16-element lists are equal |
| 4a | This repo's `code` set runs its test suite **once** per pass | `bash scripts/smoke-test.sh`, counting `Ran <N> tests` lines in its output | **0** — see § *Oracles re-run fresh* below; **1** such line (expected 1) |
| 4b | Measured `code`-set wall clock recorded against the 118s baseline | timing harness, `after` then `before` | **after 173.4s**, **before 320.2s** — see the table and the note below |
| 5 | `tests` and `coverage` still produce distinct `failure_class` values, and a failing test still yields a test-shaped `failure_signature` | same harness, check `B5` — two fixture runs through `_run_gate_set` + `parse_gate_failure_signature` | **0** — red test ⇒ `failure_class='tests'`, `failure_signature='test_deliberately_red'`; passing tests with `coverage report --fail-under=100` ⇒ `coverage` ran (not skipped), `failure_class='coverage'`, signature a `.py` path. The two classes are distinct |
| 6 | The authoring rule in the canonical `plugins/specfuse/skills/verification/SKILL.md` states the new contract | `grep -n "self-contained unless it declares" plugins/specfuse/skills/verification/SKILL.md`; `diff plugins/specfuse/skills/verification/SKILL.md .specfuse/skills/verification/SKILL.md` | rule present at `SKILL.md:112-121` (canonical copy); `diff` **exit 0**, the two copies are byte-identical |
| 7 | Per-criterion state and the narrow/broad oracle contract (`close-discipline.md` §5) | `GATE-01-CRITERIA.md` written by this close | 7 entries, each carrying `kind`, `state`, `proved_at_sha`, `attempt` |

`GATE-01.md` § *Arming discipline* adds two items that bind on this gate's own
review:

| # | Item | Command run in this session | Exit / observation |
|---|---|---|---|
| A2 | Escalation-predicate satisfiability: the CONFIGURATION ERROR reports **zero** on every input already in its intended final state | demonstration harness, check `A2` — `order_gate_set` over every set of every `verification.yml*` in the repo (excluding `.git/` and `build/`) | **0 errors over 3 files / 11 sets**: `.specfuse/verification.yml` (`code`, `doc`, `plannext`, `oracles`), `.specfuse/verification.yml.example` and `specfuse/loop/data/verification.yml.example` (`code`, `doc`, `plannext` each). The one file that now *declares* `needs:` resolves; the ones that do not are untouched by the rule |
| A4 | Runtime probe: time the exact `code`-set commands, not a subset | timing harness runs all **16** declared `code` gates, including the five `bats` suites and `leak-scan`; `bash scripts/smoke-test.sh` re-runs the same derived list | see below — no gate was omitted from either run |

### The `code`-set wall clock

Per-gate wall clock, both shapes, same tree, same session:

| Gate | before (pre-`needs:`) | after (shipped) | Δ |
|---|---|---|---|
| tests | 148.7s | 148.5s | −0.2s |
| lint | 0.1s | 0.1s | — |
| security | 1.1s | 1.1s | — |
| **coverage** | **147.6s** | **0.5s** | **−147.1s** |
| leak-scan | 12.9s | 12.7s | −0.2s |
| agent-policy-example-lint | 0.1s | 0.1s | — |
| event-type-gate | 0.2s | 0.2s | — |
| roadmap-link-gate | 0.0s | 0.0s | — |
| arm-sweep-gate | 0.3s | 0.3s | — |
| monitoring-example-lint | 0.0s | 0.1s | — |
| leak-scan-hook | 1.1s | 1.1s | — |
| sync-scaffold-bats | 4.5s | 4.9s | +0.4s |
| sync-scaffold-symlinks-bats | 1.7s | 1.7s | — |
| init-sh-shim-bats | 1.0s | 1.2s | +0.2s |
| init-skills-bats | 0.1s | 0.1s | — |
| hookspath-conflict-bats | 0.7s | 0.9s | +0.2s |
| **TOTAL** | **320.2s** | **173.4s** | **−146.8s** |

- **Reduction across the `code` set: 146.8s, or 45.8%** of the before-total.
- **Reduction on the `coverage` gate itself: 147.1s, or 99.7%** — 147.6s to 0.5s.
  It no longer executes anything; it reports over the data `tests` produced.
- The eliminated duplicate was **46.1%** of the before-total (147.6 / 320.2).
- `tests` + `coverage` together were **92.5%** of the before-total (296.3 /
  320.2), against the **93%** the `[FEAT-2026-0051/G1-CLOSE]` baseline recorded
  for the same two gates. The shape the baseline named is reproduced almost
  exactly; only its absolute seconds have moved.

**The 118s baseline number is not commensurable with either figure above, and
this close does not pretend otherwise.** `[FEAT-2026-0051/G1-CLOSE]` recorded
"118s wall-clock on this repo's **nine** `code` gates". The `code` set now
declares **sixteen**, and the suite behind the `tests` gate has grown with fifty
features of work — `Ran 3755 tests` in this session's smoke run. The `tests`
gate alone is 148.5s today, more than the entire nine-gate set cost when the
baseline was taken. Comparing 173.4s to 118s
compares two different gate sets over two different test suites and answers
nothing. The comparison this feature can actually make — and the one made above
— is before-vs-after **on one tree, in one session, changing only the two gate
declarations**: 320.2s to 173.4s.

A reader looking for the headline in the baseline's own units: the duplicated
test execution the baseline measured at 93% of probe cost is now 0% of it. The
`coverage` gate executes no tests at all.

### Failure-class breakdown

(no non-passing attempts in scope)

Every `attempt_outcome` event in this feature's `events.jsonl` — three, one per
substantive WU — carries `outcome: passed`, `failure_class: null`,
`failure_signature: null`, `attempt: 1`. There were no retries, no re-arms
(`re_arm_count: 0` throughout), and no `preexisting_gate_failure` halts: both
baseline probes recorded `failing: []`.

### Oracles re-run fresh for this close

Per `close-discipline.md` §1, re-run in this session against the tree the driver
will squash, exit codes read directly. All three are **`broad`** oracles — no
knowable scope, so none of them is carried forward from an earlier attempt:

| Oracle | Command | Result |
|---|---|---|
| Test suite | `python3 -m unittest discover -s tests -q` | **exit 0** — `Ran 3755 tests in 139.219s`, `OK (skipped=3)` |
| Smoke test | `bash scripts/smoke-test.sh` | **exit 0** — `smoke test: OK`. Exactly **1** `Ran <N> tests` line in 4600+ lines of output (`Ran 3755 tests in 143.289s`), against the expected 1. This is the suite-runs-once criterion measured on the real derived gate list, not a subset |
| Plan lint, whole corpus | `python3 -m specfuse.loop.lint_plan <dir>` over every folder under `.specfuse/features/` carrying a `PLAN.md` | **75 folders, 0 non-zero exits, 0 `ERROR:` lines** |
| Closing guards | `python3 -m specfuse.loop.lint_plan .specfuse/features/FEAT-2026-0102-gate-needs-dependencies --closing` | **exit 0** — `CLOSING-READY`. Only two NOTEs, both for post-pass requirements the lint cannot see pre-squash (`close-h` terminal flips, `close-i` which does not apply under `autonomy_default: review`) |

The module form is used rather than the `specfuse` console script deliberately:
the installed build is `specfuse-loop 0.15.0` from a pipx venv, not this
checkout, and it says so itself ("This command is measuring the INSTALLED build,
not your checkout"). Run both ways, `specfuse lint --closing` and the module
agree — `CLOSING-READY`, same two NOTEs — but the module is the one that read
this tree's code.

## Retrospective

### Did the inert-first ordering actually hold the oracle stable?

`PLAN.md`'s task graph orders T01 and T02 before T03 on the explicit claim that
the first two land the mechanism **inert** — nothing declares `needs:` yet, so
every gate runs exactly as it did before, and each unit is verified by the same
oracle it was dispatched under. The question this close was asked is whether that
held in fact, not in intent.

**It held. Neither T01 nor T02 was verified under a gate set it had itself
changed.** Read off the `attempt_outcome` events:

- **T01** (`19:06:07Z`, passed, attempt 1) — `files_touched` is
  `WU-01-gate-needs-runner.md`, `specfuse/loop/loop.py`,
  `tests/test_loop_gate_needs.py`. No `verification.yml`. The `code` set it was
  verified under was byte-identical to the one it was dispatched under, and
  contained no `needs:` key, so the code path T01 added was reachable but never
  taken during its own verification.
- **T02** (`19:42:33Z`, passed, attempt 1) — `files_touched` is
  `WU-02-gate-commands-order.md`, `specfuse/loop/gate_commands.py`,
  `tests/test_gate_commands_needs.py`. Again no `verification.yml`.
- **T03** (`20:13:56Z`, passed, attempt 1) — `files_touched` includes
  `.specfuse/verification.yml`. T03 **is** the unit verified under a gate set it
  changed, and `PLAN.md` says so up front: it is last for exactly that reason,
  and the property is deliberate ("a mistake here fails you rather than passing
  silently"). It passed on its first attempt.

So the ordering discipline did what `[FEAT-2026-0019/G1]` asks of it: exactly one
unit in the feature had its own oracle move underneath it, it was the last one,
and it was the one whose entire job was to move it.

There is a second effect worth recording, because it is the ordering's real
cost rather than its benefit. T01 and T02 each edited `specfuse/loop/`, so each
triggered a `driver_staleness_detected` halt with
`reason: driver_restart_required` — the FEAT-2026-0075 control. The run stopped
twice and an operator restarted it twice. Inert-first ordering does not avoid
those halts; it makes them cheap, because the driver being restarted is a driver
whose new code nothing yet exercises.

### What the `SKIP` verdict changed that was not in the plan

`PLAN.md` motivates `needs:` as a cost argument. Running it surfaced a second
effect the plan does not claim: a failing `tests` gate now produces **one** red
gate instead of two. Before this feature, `coverage`'s command was
`coverage run … && coverage report`, so a red suite failed `tests` and failed
`coverage` for the same root cause — one defect, two failure classes, and a
reader with no way to tell which was primary. That double-report is recorded in
this repo's own operator notes as a live diagnostic nuisance. With `needs:`, the
dependent reports `SKIP` and `parse_gate_failure_signature` attributes the
attempt to `tests`, which is what `spinning_signature_repeat` and
`learnings-suggest` key on. This is a diagnosis improvement that happens to be
free, and it is not why the feature was built.

### What this close did not do

This close did not touch `specfuse/loop/loop.py`, `specfuse/loop/gate_commands.py`,
`.specfuse/verification.yml`, `tests/`, or either copy of the verification skill
— all are T01–T03's `produces:` surface and this WU's **Do not touch**. It
verified them; it did not amend them.

## Cost analysis

`PLAN.md` declares `planned_cost_usd: 29.00` at feature level, which is the sum
of the four per-WU plans: T01 $8.00, T02 $5.00, T03 $6.00, this close $10.00.

Reconciled against `events.jsonl`:

| WU | planned | actual (`task_completed`) | delta | attempts |
|---|---|---|---|---|
| T01 | $8.00 | $1.053505 | **−$6.95 (−87%)** | 1 |
| T02 | $5.00 | $0.808710 | **−$4.19 (−84%)** | 1 |
| T03 | $6.00 | $1.447758 | **−$4.55 (−76%)** | 1 |
| **substantive subtotal** | **$19.00** | **$3.309973** | **−$15.69 (−83%)** | 3 |
| G1-CLOSE | $10.00 | not yet in `events.jsonl` — the driver writes this attempt's `task_completed` after the RESULT block is read | — | 1 |

- **Delta on the three closed units: −$15.69, 83% under plan.** Every unit came
  in at roughly one sixth of its budget, and each passed first time — the plan
  was priced for retries that did not happen. All three ran on `sonnet` at
  `effort: medium`.
- **Restart count: 2.** Two `driver_staleness_detected` events, both
  `halted: true`, `reason: driver_restart_required`, after T01
  (`driver_paths: [specfuse/loop/loop.py]`) and after T02
  (`driver_paths: [specfuse/loop/gate_commands.py]`). Neither is a failure and
  neither cost model tokens; each cost one operator resume of
  `python3 -m specfuse.loop.loop --feature FEAT-2026-0102`.
- **Re-arm count: 0.** `re_arm_count: 0` on every event in the feature.
- Wall clock across the three substantive units: 1058.3s + 1424.3s + 810.1s =
  **3292.7s (54.9 min)** of billed agent time. Set against that, the 146.8s this
  feature removes from **each** `code`-set pass is the arithmetic
  `[FEAT-2026-0051/G1-CLOSE]` recommends — CPU-seconds compared against billed
  agent time — and it repays itself inside this one feature's own gate passes.

## What the loop did NOT verify

Each entry names the criterion, why this loop could not observe it, and the
surface where it actually gets checked.

- **The Maven/jacoco shape from specfuse/specfuse#162.** `PLAN.md` cites that
  issue as the second, larger instance of the duplication — a ~5:10 duplicate
  test execution inside a ~11-minute gate pass over 4303 tests, on a Maven +
  jacoco toolchain. **Not exercised anywhere in this feature.** This repository
  is pure Python and declares no Java gate, no Maven gate, and no jacoco gate in
  `.specfuse/verification.yml`, so there is no oracle here that could run that
  shape; a fixture asserting on surefire/jacoco output would be a test of a
  string this driver never parses. **Where it actually gets checked:**
  clabonte/generator#1713, downstream, where the toolchain exists. What this
  feature ships that the downstream case needs is toolchain-agnostic by
  construction — `needs:` orders and skips, and the driver never reads a
  tool's output to decide which gate a verdict belongs to. That property is what
  `PLAN.md` § *Scope boundary* rejects `emits:` in order to preserve.
- **Whether a real target project's `verification.yml` is improved by adopting
  `needs:`.** This close measured one repository's own gate set. Every other
  Specfuse-integrated project is unchanged and unmeasured — correctly, since
  `needs:` is opt-in and absent-key behaviour is byte-identical to today's
  (demonstrated as check `A2`). **Where it actually gets checked:** each target
  project's own gate timings after its operator declares the key; the shipped
  `verification.yml.example` now demonstrates the pattern so they do not have to
  derive it.
- **`needs:` across the `doc`, `plannext` and `oracles` sets.** Only the `code`
  set was timed and only the `code` set declares the key here. The mechanism is
  set-agnostic — `order_gate_set` is called by `verify()` for whichever set a WU
  type selects — and `A2` swept all 11 sets in all 3 files for configuration
  errors, but no non-`code` set was *run* with a `needs:` edge in it.
  **Where it actually gets checked:** `tests/test_loop_gate_needs.py` (T01),
  which exercises `order_gate_set` and `_run_gate_set` on synthetic sets
  independent of set name.
- **Parallel gate execution and per-attempt gate tiering.** Both are explicitly
  **OUT** in `PLAN.md` § *Scope boundary*; artifact reuse across gates forecloses
  the first, and the second is FEAT-2026-0109. Named here so a reader does not
  mistake their absence for an oversight. **Where it actually gets checked:**
  FEAT-2026-0109.
- **Behaviour on Windows.** `_run_gate_set`'s Windows branch (Git-Bash routing)
  is untouched by this feature and was not run; `oracle_env: macos_local`.
  **Where it actually gets checked:** CI's existing matrix over the unchanged
  subprocess path, and `tests/test_loop_gate_needs.py`, which asserts on ordering
  and skip decisions rather than on process spawning.

## Consumer-visible contract changes

`needs:` is new scaffold-visible surface for every target project. Enumerated:

1. **`needs: [<gate>]`, a new optional per-gate key in
   `.specfuse/verification.yml`** (`added`). A gate declaring it runs after the
   named gate; the runner guarantees the dependency ran, clean, in the same
   invocation, so the declaring gate may reuse artifacts it just produced. The
   guarantee is per-invocation and never cached across attempts. **Absent, the
   behaviour is byte-identical to today's** — every existing `verification.yml`
   in every target project is already in its final state under this rule, which
   is why nothing needs migrating.
2. **A gate whose dependency failed is reported `SKIP`, a third gate outcome
   alongside PASS and FAIL** (`added`). It is `ok=False` — never counted as a
   pass — and its command is never executed. `parse_gate_failure_signature`
   therefore attributes the attempt to the dependency that actually failed, so a
   project that adopts `needs:` sees one red gate where it previously saw two.
   Consumer-visible in gate report text and in `failure_class` values.
3. **Two new CONFIGURATION ERROR conditions** (`added`): a `needs:` target that
   names no gate in the effective set, and a `needs:` cycle. Both are refused
   before any gate runs, in the same shape as the existing unknown-`extra_gates`
   error, and both are reachable only from a `verification.yml` that a project
   edits into that state.
4. **`scripts/smoke-test.sh` and CI now consume a dependency-ordered gate list**
   (`changed`). `gate_commands.iter_code_gates` applies the same stable
   topological sort the driver applies, so the derived CI list and the driver can
   no longer disagree about whether a gate's prerequisites ran. Projects whose
   `smoke-test.sh` derives from `verification.yml` (the shipped shape) get this
   with no edit.
5. **The shipped `verification.yml.example` changed** (`changed`). Its
   `AUTHORING RULE` header now reads "self-contained **unless** it declares
   `needs:`"; a new `PER-GATE `needs:`` block documents the key alongside the
   existing `wu_must_reference` block; and its own `tests`/`coverage` pair now
   demonstrates the pattern (`tests` runs `coverage run -m pytest -q`, `coverage`
   declares `needs: [tests]`). The previous example shipped `pytest -q` next to a
   bare `coverage report`, which reported over whatever `.coverage` file happened
   to be on disk — the stale-artifact trap the file's own authoring rule warns
   about. **Existing projects are unaffected**: this is the seed for newly
   initialized ones. Updated in `.specfuse/verification.yml.example` and its
   in-package copy `specfuse/loop/data/verification.yml.example`, which are
   byte-identical (`diff` exit 0).
6. **The authoring rule in the verification skill changed** (`changed`).
   `plugins/specfuse/skills/verification/SKILL.md` § *The stale-artifact trap* is
   the canonical statement and now carries the `needs:` exception; the generated
   `.specfuse/skills/` copy is byte-identical to it (`diff` exit 0). Landed by
   T03; confirmed unchanged and in sync by this close.

Appended to `CHANGELOG.md`'s `Unreleased` section as one `### Added` entry and
one `### Changed` entry, both tracing `FEAT-2026-0102`, per
`close-discipline.md` §3.

**Human acknowledgment**: `autonomy_default: review`. The operator reviews this
enumeration at the gate-1 review checkpoint, which is the human checkpoint
`PLAN.md` § Notes reserves for exactly this feature — the one close where the
oracle producing the judge's evidence is itself what moved.

## Lessons

### Amended in place: `[FEAT-2026-0051/G1-CLOSE]` — probe cost

The entry recording the 118s probe measurement closed with: *"expect probe cost
to be dominated by whichever gates duplicate each other's work, which is a
`verification.yml` authoring concern rather than a driver one."* The measurement
half stands and is preserved verbatim. **The conclusion half is what this
feature disproves**, and it has been rewritten in place in
`.specfuse/LEARNINGS.md` rather than contradicted from a second entry — a corpus
holding both readings teaches neither.

The duplication was not an authoring mistake. It fell out of the gate-set
contract: the authoring rule required each gate command to be self-contained
(so stale artifacts could not make a gate falsely pass), and the contract
offered no third option between paying for the duplicate run and dropping that
guarantee. The two available workarounds each gave something up — merging
`tests` and `coverage` collapses two `failure_class` values into one, and
dropping `clean` reintroduces the false pass. **The fix was in the driver**: a
`needs:` edge moves the staleness guarantee from a per-command convention to a
runner invariant, enforced once instead of re-asserted in every command string.

No second entry in `.specfuse/LEARNINGS.md` or `.specfuse/LEARNINGS-archive.md`
asserts the retired reading; `grep` for `self-contained`, `stale-artifact`,
`no-build`, `duplicat` returns no other entry making that claim, so the
amendment contradicts nothing.

### New: a recorded baseline number decays against the set it was measured on

`[FEAT-2026-0051/G1-CLOSE]` recorded 118s specifically so a later feature would
not re-derive it, and that was right. But the number was pinned to a gate set
that has since grown from nine gates to sixteen and to a test suite that has
grown with fifty features of work, so this feature's acceptance criterion —
"materially below the 118s baseline" — is not satisfiable by any correct
implementation: the `tests` gate alone now costs more than the entire nine-gate
set did. A recorded measurement that will be used as an acceptance threshold
later must carry the **shape it was measured on** (gate count, suite size, the
per-gate breakdown), and a criterion built on it must compare **before-vs-after
on one tree in one session** rather than against the stored absolute. Stated as
a rule: cite a stored baseline for its *ratio* and its *shape*; re-measure the
*absolute* yourself.

## Verdict

Advisory only, per `close-discipline.md` §1 — the judge session reads
`## Measurements` and settles this.

Every bullet of `GATE-01.md`'s definition of done was demonstrated in this
session with a command and an exit status recorded above; the `code`-set wall
clock fell 45.8% (320.2s → 173.4s) with the duplicated test execution the
feature targeted eliminated entirely (147.6s → 0.5s); the three fresh oracles
are green; and the one lesson this feature falsifies has been amended in place.

The single item a reader should weigh independently is recorded in full in
§ *The `code`-set wall clock*: the shipped set's 173.4s is **above** the stored
118s baseline, because the set grew from nine gates to sixteen between
FEAT-2026-0051 and now. This close does not treat that as the saving being
absent — the same-tree before/after is the commensurable comparison and it is
large — but it does not hide it either, and it is written up as this feature's
one new lesson.
