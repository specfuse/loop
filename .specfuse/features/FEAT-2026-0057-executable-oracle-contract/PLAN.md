---
feature_id: FEAT-2026-0057
title: Executable oracle contract — pre-dispatch prep steps and captured oracles
slug: executable-oracle-contract
branch: feat/FEAT-2026-0057-executable-oracle-contract
roadmap_goal: Make a work unit's environment prep and verification oracles run deterministically before its session starts, with the captured output as the agent's input, so a close ceremony interprets machine-produced evidence instead of re-deriving the same commands from prose every attempt.
autonomy_default: review
status: active
planned_cost_usd: 23.50
---

# Plan: Executable oracle contract — pre-dispatch prep steps and captured oracles

FEAT-2026-0066's closes hand-drove the same verification stack at least four
times — consumer clone sync, regen, `dotnet build`, six real-SQL-Server
scenarios, full generator suite — from prose instructions, at $8–12 per pass.
One entire close cycle was lost to a consumer clone that had drifted stale,
because the environment-prep step (`git reset --hard origin/main` before a Hard
Rule #2 proof) lived in agent memory and LEARNINGS prose rather than in anything
enforced. Deterministic work re-derived by a frontier model every attempt is the
single biggest recurring close cost in generator-class repos.

The existing-mechanism search below found that most of the execution machinery
already ships. What does not exist is **timing**: every declared command in this
repo runs at work-unit *exit*, as a pass/fail oracle. An agent that needs results
*before* writing a verdict must therefore hand-drive the stack itself — and an
environment-prep step, whose failure is a setup problem rather than a verdict,
has nowhere to live at all. This feature adds the pre-dispatch half and changes
nothing about the exit half.

This file owns the **shape** of the feature: the gate order, which work units
belong to each gate, and the dependency edges between them. It does **not** own
status — each WU file owns its own status, and each GATE file owns its gate's
status.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  - `grep -rn "_run_gate_set\|verification.yml" specfuse/loop/*.py`
  - `grep -n "extra_gates" specfuse/loop/*.py tests/*.py`
  - `sed -n '2855,2900p' specfuse/loop/loop.py` (read `verify()` in full)

- **Verdict:** `found substantial existing mechanism, reusing — building only the pre-dispatch timing hook`

- **What was found, and why it does not suffice.** Four mechanisms already
  cover what the roadmap entry described as new work:

  1. **Named, ordered command sets** — `verification.yml` sets are ordered
     `name:`/`command:` lists, and `gate_commands.py` reads any set by name, not
     just the three this repo declares.
  2. **Per-WU oracle selection** — `extra_gates` (`loop.py:212`, issue #62,
     covered by `tests/test_extra_gates.py`). Its docstring: *"OPTIONAL extra
     verification gate sets, unioned onto the WU-type-selected set by `verify()`.
     Names index into verification.yml the same way the type sets do."* A missing
     name is a named CONFIGURATION ERROR, never a silent pass.
  3. **Deterministic execution and capture** — `_run_gate_set` (`loop.py:2753`)
     already handles `{feature_dir}` substitution, `stdin=DEVNULL`, process-group
     kill on timeout, and Git-Bash routing on Windows.
  4. **Verdict-aware capture and degraded-oracle detection** —
     `select_gate_report_lines` (FEAT-2026-0068) and `detect_degraded_oracle`.

  These do not suffice because all of them run at **exit**. `verify()`'s own
  docstring names the constraint: *"Driver runs the gates itself — the exit
  oracle."* Captured output reaches an agent only as failure feedback on a
  **retry**, so an agent that needs results before writing a verdict still
  hand-drives the stack — after which the driver re-runs it. `extra_gates`
  therefore cannot fix the cost this feature exists to remove, which is why the
  $8–12/pass survived a mechanism that looks like it should have killed it.
  Separately, a fail-fast environment-prep step has no representation at all: a
  gate set runs every entry and ANDs the results, so a failed clone sync would
  still burn a full scenario matrix.

  **This feature therefore builds the pre-dispatch hook and reuses everything
  above unchanged.** `verify()`, `_run_gate_set`, and `extra_gates` are out of
  scope by construction; the new runner calls `_run_gate_set` rather than
  reimplementing it.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — this feature raises no check to `ERROR`, flips no `WARNING` to blocking,
and asserts no "zero issues" close predicate. The two new frontmatter keys are
opt-in: a work unit declaring neither produces no pre-dispatch work and no
behavior change.

## Scope boundary

**IN.** Pre-dispatch prep steps with fail-fast semantics and a distinct halt
class; pre-run oracle sets whose captured output is injected into the session
prompt; a capture budget that preserves verdicts under truncation; one real
oracle set declared and documented in this repo as the adoption proof.

**OUT — per-criterion binding.** FEAT-2026-0056 owns per-criterion DoD state.
This feature's keys are per-WU; the two compose later, and the seam is
deliberately left rather than pre-built.

**OUT — oracle declarations in GATE frontmatter.** The roadmap entry proposed
this; it was dropped when the existing-mechanism search showed per-WU selection
already exists via `extra_gates`. Adding a second declaration surface would
duplicate a working one.

**OUT — any change to `extra_gates`, `_run_gate_set`, or exit-time verification
semantics.** These are called, never modified. This is what keeps the change
additive, and it is what keeps sibling work units' oracles green while the
feature lands (the harness-migration hazard in `.specfuse/LEARNINGS.md`).

## Sizing note

Four substantive work units — at the `docs/methodology.md §6`
ceremony-proportionality threshold, so this remains a **single gate with a single
terminal `close`**. No `close-intermediate`, no `plan-next`. The gate has already
gone off-plan once (see below), so the `gate_eval` auto-close predicate will not
auto-close it; the close dispatches as a normal reflective session, which is what
`auto_close_disabled: true` on `WU-90` already forced.

## Off-plan record — the wiring gap

The first pass through this gate closed `partially_met`. T01, T02, and T03 each
passed every oracle they named, and together they built a mechanism the driver
never calls: `WorkUnit` carried neither `prep` nor `oracles`, `load_wu` parsed
neither key, and `format_oracle_capture` had no caller outside its own test file.

The cause was a boundary error in this plan, not in the units. Keeping the change
additive meant putting the dispatch path on every unit's **Do not touch** list —
which worked, and which also guaranteed that no unit owned the call site. All
three came in 44–76% under their estimates because their specs removed the
ambiguity those estimates were priced for; the same precision is why the wiring
was absent. The underspend and the unmet definition of done are one fact seen
twice.

T04 is the correction: it owns the dispatch call site, and it is the only unit in
this gate for which `specfuse/loop/loop.py` is in scope. Exit-time verification
(`verify()`, `_run_gate_set`, `select_gate_report_lines`) stays out of scope for
every unit including T04 — that boundary was right and is retained.

Recorded spend on the first pass: T01 $0.98, T02 $1.67, T03 $1.40, close $10.69 —
$14.74 against a $15.00 plan. The close alone ran 2.1× its own $5.00 estimate and
consumed 72% of the feature's spend, on a feature whose purpose is reducing close
cost. `planned_cost_usd` is raised to $18.50 to carry T04; the gate's
`cost_budget_usd` is raised to $30.00 because the per-gate brake sums **lifetime**
cost (FEAT-2026-0062), so the first pass's $14.74 counts against it.

## Decisions taken at draft time

Recorded here because the alternatives were live and a later reader will
otherwise re-litigate them:

- **Prep failure escalates immediately rather than burning a retry.** A stale
  clone or a missing tool does not fix itself across attempts, and retrying it is
  how FEAT-2026-0066 lost a full close cycle.
- **The capture budget is a byte cap, not a line cap.** A scenario matrix emits
  long lines. The value itself is deferred to T02 measurement rather than guessed
  at draft time.
- **T01 and T02 stay split.** Truncation behaviour has a testable surface of its
  own, and a red test for "the verdict survives truncation" is cleaner standalone
  than folded into the runner's tests.
- **The pre-dispatch hook is type-agnostic and opt-in.** It fires before dispatch
  regardless of work-unit type; restricting it to `close` units would be an extra
  validation rule, not less work. The close path is what gets tested and
  documented.

## Two-invocation sequencing (binding for this gate)

The second close discovered that **a work unit editing the driver cannot take
effect for any work unit dispatched by the same driver process**: Python caches
modules in `sys.modules` at first import, so T04's wiring was invisible to the
close dispatched 28 minutes later by a process that had imported `loop.py` before
T04 ran. That is why the verdict was `met_locally` rather than `met`.

The same hazard applies one layer down to T06. `execute_unit_attempt` imports
`specfuse.loop.prerun_capture` at call time, but calls it **unconditionally for
every work unit** — so dispatching T05 caches the pre-T06 module, and a close in
that same run would receive the old banner.

Therefore this gate completes in **two driver invocations**:

1. **Run 1** — `G1-CLOSE` sits at `status: blocked_human`. The driver dispatches
   T05 and T06 only.
2. **Run 2** — a human flips `G1-CLOSE` to `pending` (`/unblock-wu`) and starts a
   **fresh** driver process. Its first `execute_unit_attempt` call is the close's,
   so it imports the post-T06 modules and the injected capture reflects both T04's
   wiring and T06's fix.

**Why `blocked_human` rather than `draft` for the hold.** `draft` was tried first
and refused: the arm check (`loop.py:5436`) rejects an entire gate containing any
`draft` work unit, because `draft` means "plan-next drafted this and a human has
not reviewed it." `blocked_human` is excluded from `DISPATCHABLE` by `ready()`
(`loop.py:5295`) and is skipped cleanly, and `/unblock-wu` is its supported route
back to `pending`. The status is honest here in substance: this close genuinely
cannot run correctly until a human performs an action outside the loop — starting
a new driver process — which is what `blocked_human` means. The work unit body
carries an operator note saying so, so it is not misread as a failure.

Run 2 is also what discharges FU-1R, which needs nothing but a restarted driver.
Collapsing these into one invocation reproduces the exact defect this round exists
to clear.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0057/T01
        file: WU-01-pre-dispatch-runner.md
        depends_on: []
      - id: FEAT-2026-0057/T02
        file: WU-02-capture-budget-injection.md
        depends_on: [FEAT-2026-0057/T01]
      - id: FEAT-2026-0057/T03
        file: WU-03-adoption-proof-docs.md
        depends_on: [FEAT-2026-0057/T01, FEAT-2026-0057/T02]
      # Added after the first close returned `partially_met`: T01-T03 built the
      # mechanism and nothing called it, because every one of their Do-not-touch
      # lists forbade the dispatch path and no unit owned the call site. See
      # RETROSPECTIVE.md FU-1 and FU-2.
      - id: FEAT-2026-0057/T04
        file: WU-04-wire-dispatch-path.md
        depends_on:
          - FEAT-2026-0057/T01
          - FEAT-2026-0057/T02
          - FEAT-2026-0057/T03
      # Added after the second close returned `met_locally`. T05 discharges
      # FU-3R (keys live in the driver, absent from every shipped seed); T06
      # discharges FU-5 (informational captures carry a false NO VERDICT FOUND
      # banner instructing the reader to run the command itself).
      - id: FEAT-2026-0057/T05
        file: WU-05-seed-templates.md
        depends_on: [FEAT-2026-0057/T04]
      - id: FEAT-2026-0057/T06
        file: WU-06-oracle-capture-banner.md
        depends_on: [FEAT-2026-0057/T04]
      # --- closing sequence: 1-WU close (terminal gate) ---
      # Held at `status: draft` for the T05/T06 run — see "Two-invocation
      # sequencing" below. Flipped to `pending` and dispatched by a SECOND,
      # freshly-started driver process.
      - id: FEAT-2026-0057/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0057/T01
          - FEAT-2026-0057/T02
          - FEAT-2026-0057/T03
          - FEAT-2026-0057/T04
          - FEAT-2026-0057/T05
          - FEAT-2026-0057/T06
```

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never needs
  to know its own dependencies — they are satisfied by the time the driver hands
  it the file. Deps are scheduling metadata, and scheduling is the driver's job.
- WU file numbers track the correlation sub-ID where it exists (`WU-01` ↔ `/T01`).
  The closing unit uses the reserved high range (90+) so it sorts last.
