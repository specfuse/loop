---
id: FEAT-2026-0113/G3-CLOSE
type: close
status: pending
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
oracles:
  # A verification.yml SET name, not a gate name (docs/methodology.md §2).
  # Naming a gate here halted G2-CLOSE-INTERMEDIATE pre-dispatch as a
  # CONFIGURATION ERROR; the set is `oracles`, holding recent-commits and
  # diff-stat.
  - oracles
---

# G3-CLOSE — terminal close

**Context.** `FEAT-2026-0113/G3-CLOSE`, gate 3, terminal. Folds retrospective,
lessons, docs and the terminal verdict per `close-discipline.md` §5; those
obligations are not restated here. Drafted by `FEAT-2026-0113/G2-PLAN` alongside
gate 3's substantive units, whose shape is in `GATE-03-REVIEW.md`.

The question the feature was opened on is narrower than "does triage assign a
severity". `PLAN.md` measured **31** bug-marked issues carrying a marker and no
severity label, stranded permanently because the marker is the idempotency key
and it is already written. Gate 2 made new issues carry a severity. Gate 3 is the
only gate that can move those 31, and this close is where that is answered
honestly or recorded as `not_met` with `FOLLOW-UPS.md`.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` carries a `## Cost analysis` heading reconciling the
   feature's spend against `planned_cost_usd` and `events.jsonl`.
2. The terminal verdict answers whether the measured 31 stranded issues are
   **routable** after this feature — not merely whether new issues carry a
   severity — and cites `T11`'s recorded evidence for what a real repository's
   selection actually contained.
3. The retrospective states, for gate 3, whether a backfill run disturbed any
   repository's own `severity:*` scheme: zero `gh label create` against a
   declares-own repository and zero descriptions overwritten, measured by argv
   over the whole call sequence as gate 2 measured it, not asserted in prose.
4. Gate 1's carried residual is recorded as discharged or re-carried by name: no
   oracle in gates 1 and 2 read a real issue body outside this repository, and
   `T11` is the unit placed to change that.
5. **`specfuse/agent/severity_backfill.py` is diffed between the commits of the
   three units that declare it** — `T07`, `T09`, `T10` — and the retrospective
   states, per pair, which of the earlier unit's assertions the later one
   replaced. This is gate 2's own durable lesson applied to gate 3: a shared
   `produces:` entry is the signal, "extends, does not rewrite" is a wish rather
   than a guard, and a per-gate criteria artifact can otherwise record a green
   with no test behind it. `T09`'s `grep -c "def _amend_marker"` returning `0` is
   evidence for one pair and not for the others; the diff is what covers the
   rest.
6. `specfuse lint --closing` exits 0 before this unit reports `complete`.

**Do not touch.** Gate 1's and gate 2's work units, their files, and
`GATE-01-CRITERIA.md` / `GATE-02-CRITERIA.md` — a terminal close reports on them
and re-decides none of them. `PLAN.md`'s `status`, which the driver flips
(`fire_terminal_flips`, gated on `verdict_permits_terminal_flips`).
`rules.bugs.min_severity`. Any `specfuse/` source file: a close writes documents,
and a source edit discovered necessary at close time is a follow-up, not a fix to
slip in here.

**Verification.** `specfuse lint --closing` exits 0, plus the `doc` gate set as
declared in `.specfuse/verification.yml`.

**Escalation triggers.** If a criterion cannot be verified because a backfill has
not actually been run against a real repository — only against injected runners —
record `not_met` with a `FOLLOW-UPS.md` entry rather than softening the verdict:
a feature that claims the 31 are routable on the strength of test doubles alone
is the claim this gate exists to make honest. If gate 3's own units contradict
`PLAN.md` — a marker written before its selection was bounded, a label written
before its marker — that is a `blocked` close, not a note in the retrospective.
