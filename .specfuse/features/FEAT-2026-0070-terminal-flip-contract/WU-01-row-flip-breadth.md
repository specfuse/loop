---
id: FEAT-2026-0070/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - specfuse/loop/loop.py
  - tests/test_terminal_flips.py
oracle_env: macos_local
produces_driver_helper: fire_terminal_flips
---

# Flip the roadmap row to `done` from any non-`done` status, not only `active`

**Objective.** Make `fire_terminal_flips` flip the roadmap row from **any** non-`done`
prior status, so an `autonomy: auto` feature that self-dispatched from a `planned` row
reaches `done` instead of escalating `roadmap_row_not_done` on a correct close.

**Context.** This is `FEAT-2026-0070/T01`, closing issue #226. Read `PLAN.md` in this
folder — its existing-mechanism verdict and the one-owner constraint bind this WU.

The defect is two contradictory assumptions in the same pipeline. An `autonomy: auto`
feature can **self-dispatch from a `planned` row** — nothing gates dispatch on the row
being `active`. But the terminal flip assumes the feature passed through `active` via
`/pick-feature`, so it handles only `active → done`
(`specfuse/loop/loop.py:3211-3218`). The row therefore stays `planned`, and the post-pass
invariant `assert_terminal_flips_fired` escalates:

```
human_escalation | <feature>/G1-CLOSE
  reason: post_pass_invariant_failed
  assertion: roadmap_row_not_done
  summary: "roadmap_row_not_done: status='planned'"
```

**The invariant is correct — it is flagging real state drift.** The bug is the flip's
precondition being too narrow. Do not weaken the invariant.

The current branch structure at `:3206-3222` is: `done` → skip with a log; `active` →
flip; **anything else → warn and do nothing**. That final `else` is what this WU
converts into a flip.

Issue #226 considered and rejected two alternatives, and this WU should not reintroduce
them: a *dispatch guard* refusing to run a feature whose row is `planned` (contradicts
`autonomy: auto` self-start), and having `/draft-feature` set the row `active` when
autonomy is auto (narrow — a human can edit autonomy after drafting, so the flip still
has to be broad).

Binding rules in `.specfuse/rules/` apply. Do not restate them.

**Acceptance criteria.**

1. **Red test:** `tests/test_terminal_flips.py::TestRowFlipBreadth::test_planned_row_flips_to_done`
   exists and **fails on HEAD before this WU's edits** —
   `python3 -m unittest tests.test_terminal_flips.TestRowFlipBreadth -v` exits non-zero.
   It builds a feature whose roadmap row is `planned`, runs `fire_terminal_flips` with a
   `met` verdict, and asserts the row reads `done`. On HEAD the row stays `planned`, so
   the test is red on behaviour, not only on absence.
2. The same test passes after this WU's edits.
3. `fire_terminal_flips` flips the row to `done` from **any** status that is not already
   `done` — at minimum `planned` and `active` are covered by tests. The replacement must
   substitute the actual current status text, not assume the literal `"active"`:
   `status_cell.replace("active", "done", 1)` at `:3215` is exactly the assumption being
   removed.
4. **The already-`done` branch is unchanged** — a second call is still a logged no-op,
   asserted by a test. Terminal flips must stay idempotent; `fire_terminal_flips` is
   called on both the dispatched-close and auto-close paths.
5. **The `active → done` path still works**, asserted explicitly rather than assumed. This
   is the path every existing correct close uses, and it is the regression this WU is most
   likely to cause.
6. An unparseable or absent roadmap row still logs and continues without raising —
   `fire_terminal_flips` is documented non-fatal ("skips via logging, only raises on
   internal exceptions") and that contract does not change here.
7. `assert_terminal_flips_fired` is **not modified**. It was right; see the Do-not-touch
   list.
8. `python3 -m unittest discover -s tests -v` exits zero — in particular
   `tests/test_terminal_flip_ownership.py`, `tests/test_legacy_4wu_terminal_flips.py`, and
   `tests/test_gate_eval_terminal_wiring.py` must all stay green. They pin the one-owner
   property and the auto-close wiring this function sits inside.
9. Coverage stays ≥ 90%.

**Do not touch.**

- `assert_terminal_flips_fired` (`:4233`) — the invariant is correct and is the thing that
  *caught* this bug. Loosening it to accommodate a narrow flip would delete the detector
  instead of fixing the defect.
- `verdict_permits_terminal_flips` (`:134`) — `FEAT-2026-0070/T02` owns the verdict half
  in this same gate. This WU changes only the row-status precondition.
- The PLAN-status and gate-status flips inside `fire_terminal_flips` — out of scope; only
  the roadmap-row branch changes.
- `.specfuse/roadmap.md` — this WU changes the driver, not this repo's own roadmap.
- `.git/`, secrets. The driver owns all git operations — you edit files only. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage`, `leak-scan`, `monitoring-example-lint`, `leak-scan-hook`,
`sync-scaffold-bats`, `init-sh-shim-bats`, `init-skills-bats`. Scoped red/green proof:
`python3 -m unittest tests.test_terminal_flips.TestRowFlipBreadth -v`.

> Sandbox note (`.specfuse/LEARNINGS.md` `[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`): the
> three `bats` gates call `mktemp -d` in `setup`, which the default session sandbox denies
> (`Operation not permitted`) before any assertion runs. Report which sandbox each gate ran
> under; do not read a sandbox denial as a regression.

**Escalation triggers.** Emit `status: blocked` if broadening the precondition requires
changing `assert_terminal_flips_fired` or `_parse_roadmap_row` — either would mean the row
contract is wider than #226 describes, and that is an operator decision rather than
something to absorb. Also block if a test in `test_terminal_flip_ownership.py` fails: that
file pins the single-owner property `[FEAT-2026-0023/G1-CLOSE]` records, and a failure
there means this change has split terminal-state ownership. Blocked is a respectable
outcome (`result-contract.md` rule 4).
