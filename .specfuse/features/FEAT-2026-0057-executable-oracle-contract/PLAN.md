---
feature_id: FEAT-2026-0057
title: Executable oracle contract — pre-dispatch prep steps and captured oracles
slug: executable-oracle-contract
branch: feat/FEAT-2026-0057-executable-oracle-contract
roadmap_goal: Make a work unit's environment prep and verification oracles run deterministically before its session starts, with the captured output as the agent's input, so a close ceremony interprets machine-produced evidence instead of re-deriving the same commands from prose every attempt.
autonomy_default: review
status: active
planned_cost_usd: 15.00
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

Three substantive work units — at or under the `docs/methodology.md §6`
ceremony-proportionality threshold, so this is a **single gate with a single
terminal `close`**. No `close-intermediate`, no `plan-next`. Should the gate go
off-plan, the `gate_eval` auto-close predicate disables auto-close and the close
WU dispatches as a normal reflective session.

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
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0057/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0057/T01
          - FEAT-2026-0057/T02
          - FEAT-2026-0057/T03
```

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never needs
  to know its own dependencies — they are satisfied by the time the driver hands
  it the file. Deps are scheduling metadata, and scheduling is the driver's job.
- WU file numbers track the correlation sub-ID where it exists (`WU-01` ↔ `/T01`).
  The closing unit uses the reserved high range (90+) so it sorts last.
