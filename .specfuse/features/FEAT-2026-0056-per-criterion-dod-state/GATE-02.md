---
gate: 2
status: open
cost_budget_usd: 23.00
baseline:
  sha: 1d79328bfdd0e84fa79a2a1f7817825e1bd030e6
  probed_at: 2026-08-06T01:28:16.297850+00:00
  failing:
    - gate: coverage
      failure_class: coverage
      failure_signature: $ coverage run --source=specfuse -m unittest discover -s tests && coverage report --fail-under=90
---

# Gate 2 — a re-dispatched close re-verifies only the worklist

## Definition of done

Rewritten by `G1-PLAN` from gate 1's retrospective. Each bullet names the work unit
that delivers it and what it traces to. The draft-time proposal this replaces is
reconciled bullet-by-bullet in § *Disposition of the draft-time proposal* below.

- **The criteria artifact survives a failed close attempt.** (`T05`) Recorded state
  is not deleted and re-seeded blank between attempts of the same close.
  *Traces to:* `RETROSPECTIVE.md` § *The re-arm property, observed rather than
  asserted* — the artifact is created inside the attempt loop, the untracked
  snapshot is taken outside it, and gate 1's close observed the real cleanup
  function unlinking it. **Not in the draft-time proposal**, which assumed state that
  persists. Without it every other bullet here operates on an empty artifact.

- **A freshly seeded artifact lints clean.** (`T06`) A pristine seeded entry — no
  `kind`, no `oracle`, `state: unverified` — is not a `close-l` /
  `close-intermediate-f` finding; every partially annotated entry and every `broad`
  carry-forward stays as blocking as T03 shipped it.
  *Traces to:* `RETROSPECTIVE.md` § *Finding 2* — 41 findings on a freshly seeded
  artifact, so from the first restarted driver every close in this repo starts red.
  **Not in the draft-time proposal.** A feature that makes every close more expensive
  before it makes any close cheaper cannot be closed honestly.

- **Recorded state partitions into a carry-forward set and a re-verification
  worklist, and a `broad` oracle's green is never in the first set.** (`T07`)
  Identical oracle commands across re-verify criteria are grouped once per attempt.
  Anything not provably safe to carry — missing or unrecognized `kind`, `state: fail`,
  `state: unverified`, a criterion new this attempt — is re-verified.
  *Traces to:* `PLAN.md` § *Scope decision: what invalidates a cached green*, the
  feature's stated goal. Merges draft-time bullets 1 and 2.

- **The worklist reaches the close session's prompt at dispatch, and says the
  feature-level question always runs.** (`T08`) A `close` / `close-intermediate`
  dispatch carries a rendered section naming the carried-forward criteria with the
  attempt each was proved on, the grouped re-verification commands, and an
  unconditional line that `close-discipline.md` §1's feature-level question is never
  carried forward.
  *Traces to:* the roadmap goal ("a re-dispatched close re-verifies only failed and
  newly-added criteria plus the oracles whose scope cannot be bounded"), and
  `PLAN.md` § *Notes* / `[FEAT-2026-0057/G1-CLOSE]` for the exclusion. Delivers
  draft-time bullets 1 (consumer half) and 3.

- **A reader can tell a carried-forward criterion from one re-proved this attempt.**
  *No new work unit — deliberately.* The mechanism already exists: gate 1's schema
  records `state`, `attempt`, and `proved_at_sha` per entry, so an entry reading
  `state: pass` with an `attempt:` below the current one *is* the carry-forward
  record. `T08` renders the distinction into the session prompt and `G2-CLOSE`
  reports it. Building a second surface would be the duplication
  `planning-discipline.md` §1 exists to prevent.

Gate 2 is the terminal gate, so the closing sequence is the single `close` work unit
(`G2-CLOSE`). **Gate 2 is where the feature's cost claim becomes measurable** — and
`T04` already re-baselined that claim: the repo's `tests` gate is a `broad` oracle
and re-runs every attempt, so what is saved is per-criterion agent reasoning,
regeneration, and the scenario matrix, not the suite.

### Disposition of the draft-time proposal

`GATE-02.md`'s original `## Definition of done` was written before gate 1 ran. Each
of its four bullets, and what happened to it:

| Draft-time bullet | Disposition | Why |
|---|---|---|
| A re-dispatched close reads the prior attempt's `GATE-NN-CRITERIA.md` and produces a worklist (`fail` + new + `broad`) | **Accepted, split across T07 and T08, and gated on T05** | The partition rule is correct and traces to `PLAN.md`. The premise — that a prior attempt's artifact is still there to read — is false on HEAD; T05 makes it true first. |
| Identical oracle commands run once per close attempt, not once per criterion | **Accepted, revised into data** | Kept, but implemented as `oracle_groups` on T07's partition rather than as a behavioural instruction to the close session. An instruction nothing checks is not a definition of done. |
| The close's feature-level question is excluded from the cache and always runs | **Accepted unchanged — deliberately** | Load-bearing per `PLAN.md` § *Notes* and `[FEAT-2026-0057/G1-CLOSE]`; nothing gate 1 observed argues against it. T08 criterion 5 makes it a rendered, asserted line rather than a convention. |
| A close that skips a criterion says so in its own record | **Accepted in intent, rejected as new work** | The record already exists — `state` + `attempt` + `proved_at_sha`, shipped by T01. See the fifth DoD bullet. |

Nothing from the draft-time proposal was rejected outright. Two bullets were added
that it could not have contained, both from defects gate 1's close found in gate 1's
own output.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a severity change (§4). REQUIRED for `T06`.** T06 narrows a
  blocking `specfuse-lint --closing` finding, which is a severity change in §2's
  sense in the de-escalating direction: a tree that lints dirty today can lint clean
  after it. Before arming, apply T06's change locally and run, pasting each output
  into `GATE-02-REVIEW.md`:

  1. the full `code` gate set — the whole oracle, not a subset;
  2. the **initial-state** probe: seed a scratch copy of this feature folder through
     the real `loop._precreate_criteria_state_stub` and lint it from source. Expected
     **41 → 0** findings attributable to `close-intermediate-f`;
  3. the **positive control**: annotate one entry in that scratch copy with
     `- **kind:** \`bogus\`` and re-lint. Expected: **exactly one** finding naming
     that entry. A probe that cannot fire has measured nothing —
     `[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE/console-script-is-not-the-tree]` rule (b);
  4. the corpus sweep, `for d in .specfuse/features/*/; do python3
     .specfuse/scripts/lint_plan.py "$d" --closing; done`, run from the
     `.specfuse/scripts/` shim and **not** the installed `specfuse-lint` console
     script. Gate 1's sweep measured the installed 0.7.1 wheel, which contained
     nothing it was measuring.

  The arming condition is that (2) reaches zero, (3) fires exactly once, and (4) is
  unchanged from gate 1's baseline except for entries this feature's own gate 1
  satisfied. Any other outcome means T06 is mis-scoped: re-draft, do not arm.

- **Driver restart before `G2-CLOSE`. REQUIRED, operator action.** `T05` and `T08`
  both edit `specfuse/loop/loop.py` on the dispatch and reset paths. A driver process
  caches `specfuse.loop.loop` in `sys.modules` at first import, so the process that
  dispatches those units cannot execute them —
  `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`. Gate 1 hit this in its most
  expensive form: its close was armed to observe T02's seeding and observed nothing,
  because the driver predated T02 by 25 minutes, and `RETROSPECTIVE.md` § *Finding 1*
  records that the lesson was already in `LEARNINGS.md` when gate 1 was planned and
  was simply not consumed at plan time. It is consumed here:

  **Stop the driver after `T08` reports `done` and start a fresh one before
  `G2-CLOSE` dispatches.** `G2-CLOSE`'s criterion 2 checks the process start time
  against `T08`'s `started_at` and blocks if the restart did not happen, rather than
  reporting a stale observation as a result. Per
  `[FEAT-2026-0057/G1-CLOSE/restart-buys-honesty-not-correctness]`, the restart buys
  a *truthful* observation, not a working one — budget for the honest answer being
  "the worklist was empty".

- **Flag-scope table (§3).** Not applicable. No work unit in this gate introduces,
  gates on, or flips a behavior flag. `narrow` / `broad` are data on a criterion
  entry and `carry_forward` / `reverify` are a partition of that data; neither gates
  a code path on a configurable value. Same verdict `GATE-01.md` reached, for the
  same reason.

- **Escalation-predicate satisfiability (§2), for T06.** Answered at **both**
  endpoints, which is the half gate 1 never asked:
  - *Final state:* a close that has annotated every entry with a recognized `kind`
    and `state`, with no `broad` entry carrying a stale green, reports **zero**. This
    is unchanged from T03.
  - *Initial state:* the artifact the driver itself seeds — every entry `state:
    unverified`, no `kind`, no `oracle` — reports **zero** after T06, against 41 on
    HEAD. `PLAN.md` asked the final-state question and answered it correctly; the
    predicate was still unsatisfiable because every close *begins* in the initial
    state and no unit in gate 1 filled it in.
  - *Corpus:* unchanged. The requirement is still gated on
    `applies_when="criteria_artifact_present"`, and T06 changes only the entry-level
    predicate inside the check, not the registry record.

- **Existing-mechanism search (§1).** Run at draft time, verdicts recorded:

  | Command | Verdict |
  |---|---|
  | `grep -rniE 'worklist' specfuse --include='*.py'` | One hit — `build_autoclose_debt_enumeration` (`loop.py:4028`), the *deferred-verification* worklist for an auto-closed gate. Different question (what a gate never verified, vs. what recorded state permits skipping) and it reads nothing recorded. **Not reused**; the shared half, `extract_wu_criteria`, was already hoisted by T02. |
  | `grep -rniE 'carry_forward\|carried[- ]forward\|reverif' specfuse --include='*.py'` | One hit, a docstring in `lint_closing.py`. **No existing mechanism, building new** (T07). |
  | `grep -rn 'wu.body = wu.body' specfuse --include='*.py'` | One hit — `loop.py:3353`, `format_oracle_capture`'s append inside `execute_unit_attempt`. **Reusing the shape**; T08 follows it at the same site rather than inventing a second prompt-injection path. |
  | `grep -rn 'CRITERIA.md' specfuse/` | The artifact filename is an f-string literal in three places (`loop.py:2438`, `lint_closing.py:334`, `lint_closing.py:479`). **Extending**: T05 gives it one home before adding a fourth reader. |

## Reflection notes

<Written by the human at review time.>
