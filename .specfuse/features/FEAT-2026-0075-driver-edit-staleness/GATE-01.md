---
gate: 1
status: passed
cost_budget_usd: 25.50
baseline:
  sha: f8945b128e9fee12516300ef39dccf7b88661f41
  probed_at: 2026-08-07T02:50:38.480017+00:00
  failing: []
---

# Gate 1 — the staleness hazard is visible while it can still be acted on

## Definition of done

- A changed-paths helper exists and a pure predicate answers "does this diff edit the
  driver", keyed on the squash commit's actual file list rather than on any
  author-supplied declaration.
- The moment a work unit's squash lands touching `specfuse/loop/`, the driver prints
  that this process is now stale, that anything dispatched next executes pre-edit
  modules, and that a restart is required before any close can verify the change.
- At gate completion the driver names which units edited itself and which units were
  dispatched after them, and emits a machine-readable record so a close reads the fact
  instead of reconstructing it from `ps` output and `started_at` timestamps.
- Nothing in this gate blocks, refuses, or fails a gate — the whole gate is warn-only.
- `RETROSPECTIVE.md` exists; lessons are promoted to `.specfuse/LEARNINGS.md`; gate 2's
  work units are drafted and `GATE-02-REVIEW.md` is written.

Gate 1 is non-terminal, so the closing sequence is `close-intermediate` followed by
`plan-next`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Driver restart between `T03` and the close. REQUIRED, operator action.** `T02` and
  `T03` both edit `specfuse/loop/loop.py` on the dispatch and gate-completion paths.
  A driver process caches `specfuse.loop.loop` in `sys.modules` at first import, so
  the process that dispatches those units cannot execute them —
  `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`.

  **This is the hazard this feature exists to fix, firing on the feature that fixes
  it.** It has now cost two features real money: FEAT-2026-0057 lost a $5.33 close to
  it, and FEAT-2026-0056 lost three attempts and $3.66 to it in a `spinning_detected`
  escalation — the second time with the mitigating rule already promoted in
  `.specfuse/LEARNINGS.md` and simply not consumed at plan time.

  **Stop the driver after `T03` reports `done`. Start a fresh one before
  `G1-CLOSE-INTERMEDIATE` dispatches.** The close's criterion 1 checks the dispatching
  process's start time against `T03`'s `started_at` and blocks if the restart did not
  happen, rather than reporting a stale observation as a result.

  Per `[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]`, the restart
  buys a *truthful* observation, not a working one — budget for the honest answer
  being "the warning did not fire", and record that as a result rather than as a
  failure of the run.

- **Runtime probe for a default/severity flip (§4).** Not applicable. No work unit in
  this gate introduces a blocking check, raises a severity, or flips a default. The
  whole gate is warn-only by design, which is what keeps gate 2's refusal designable
  against real observed output instead of an assumption.

- **Flag-scope table (§3).** Not applicable — no work unit introduces, gates on, or
  flips a behavior flag. `DRIVER_MODULE_PREFIXES` is data consulted by a predicate,
  not a flag gating a code path on a configurable value.

- **Escalation-predicate satisfiability (§2).** Does not arise for this gate; answered
  in `PLAN.md`. Gate 1 asserts no "zero issues" predicate because it blocks nothing.
  Gate 2's arm-time refusal is where the question becomes load-bearing, and gate 1's
  summary output is deliberately the evidence that will answer it.

## Reflection notes

<Written by the human at review time. What surprised you, what you changed in the
drafted next gate and why, anything the retrospective got wrong. This is your record,
not the agent's — keep it honest.>
