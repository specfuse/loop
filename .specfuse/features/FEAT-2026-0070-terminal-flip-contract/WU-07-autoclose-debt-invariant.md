---
id: FEAT-2026-0070/T07
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.25
produces:
  - specfuse/loop/loop.py
  - tests/test_loop_post_pass_invariant.py
  - .specfuse/rules/close-discipline.md
oracle_env: macos_local
produces_driver_helper: assert_autoclose_debt_reconciled
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-27T04:22:03.991085+00:00
duration_seconds: 926.649
cost_usd: 3.288034
input_tokens: 126
output_tokens: 37328
---

# A terminal close that ignores an auto-closed predecessor's debt is blocked, not silent

**Objective.** Add the post-pass invariant `assert_autoclose_debt_reconciled` so a terminal
close whose retrospective never mentions an auto-closed predecessor gate's marked debt
fails the gate — and document its exact requirement in `close-discipline.md` §4 in the same
squash, so it never costs anyone a refusal to discover.

**Context.** This is `FEAT-2026-0070/T07`, the second half of #241 and **the only severity
flip in this feature**. Read `PLAN.md`, `GATE-02.md`, and `GATE-02-REVIEW.md` first;
`GATE-02-REVIEW.md` carries the arming probe that sized this WU's test surface and the
satisfiability enumeration that fixed its design. Depends on `FEAT-2026-0070/T06`, which
writes the marker this invariant reads.

**The design is already decided, and the reason is measured — do not re-open it.** The
obvious form of this invariant ("any auto-closed predecessor gate must be named in the
terminal close's deferral list") was applied locally at plan time and run against every
feature in this repo. It **fires on 6 of the 11 features that have auto-closed a gate**, all
of them `status: done` and all closed correctly under the contract in force at the time.
That is an unsatisfiable predicate by `planning-discipline.md` §2 and it must not be built.

The shipped form is **marker-gated**: the invariant considers only gates whose auto-close
stub carries T06's `<!-- specfuse:autoclose-debt gate=N … -->` marker. No historical
retrospective has one, so the same enumeration reports **zero** on all 11. The obligation
attaches to gates auto-closed *after* T06 ships, which is the only population that was ever
told about it. `GATE-02-REVIEW.md` has the full table.

**Read before starting:** `assert_terminal_flips_fired` (`loop.py:4292`) for the invariant
signature and return shape, `POST_PASS_INVARIANTS_BY_TYPE` (`:4369`) for registration,
`verify_post_pass_invariants` (`:4374`) for the dispatch contract, and
`tests/test_loop_post_pass_invariant.py` for the fixture style — these tests are pure
file-state and need no tempdir git repo.

Binding rules in `.specfuse/rules/` apply, `verification-discipline.md` §3 (a severity
claim needs a **negative observation**) especially.

**Acceptance criteria.**

1. **Red test:**
   `tests/test_loop_post_pass_invariant.py::TestAutoCloseDebtReconciled::test_marked_predecessor_debt_unmentioned_fails`
   exists and **fails on HEAD before this WU's edits** —
   `python3 -m unittest tests.test_loop_post_pass_invariant.TestAutoCloseDebtReconciled -v`
   exits non-zero. It builds a feature whose gate-1 close-intermediate is `auto_close: true`
   and whose `RETROSPECTIVE.md` carries T06's marker for gate 1, with a terminal
   `## What the loop did NOT verify` section that never mentions gate 1, and asserts the
   invariant returns `(False, reason)` with `autoclose_debt_unreconciled` in the reason.
   `assert_autoclose_debt_reconciled` does not exist on HEAD.
2. The same test passes after this WU's edits.
3. **Positive control, in the same class:** the identical fixture whose deferral section
   *does* name gate 1 returns `(True, "")`. A guard with no positive control cannot be
   distinguished from one that always fails; a guard with no negative control (AC1) cannot
   be distinguished from a no-op. Both are required.
4. **The satisfiability gate is the marker, and one test says so.** A fixture identical to
   AC1's but with the marker comment removed returns `(True, "")`. This is the single test
   that keeps the invariant off every feature that closed before T06 shipped — name it
   `test_unmarked_autoclose_is_not_debt_and_does_not_fire` so its purpose survives.
5. **The terminal close's own auto-close short-circuits the invariant.** When the close WU
   being checked itself carries `auto_close: true`, return `(True, "")`: no agent ran, so
   there is no session to hold responsible, and T06's terminal stub is already the record.
   One test. Without this the invariant is unsatisfiable on the terminal auto-close path —
   5 of this repo's 11 auto-closing features took exactly that path.
6. **A marker for the terminal gate itself is not a predecessor** and does not fire. One
   test.
7. Registered in `POST_PASS_INVARIANTS_BY_TYPE["close"]` **after**
   `assert_terminal_flips_fired`, and one test asserts both are present in that order —
   `verify_post_pass_invariants` returns on first failure, and a missing terminal flip is
   the more fundamental finding.
8. **`close-discipline.md` §4's guard table gains a row for this guard**, in the same
   squash, naming what it requires exactly: on a `close` WU, when `RETROSPECTIVE.md`
   carries an auto-close debt marker for a gate earlier than the terminal one, the
   `## What the loop did NOT verify` section must name that gate as `gate N`. The function's
   docstring carries a `(close-x)` tag so
   `tests/test_closing_guard_contracts.py::TestEveryClosingGuardIsListed` enforces the
   documentation mechanically. **This AC is the whole point of the WU's price** — issue
   #265 measured three undocumented guard contracts at $99.30, 45% of all closing-WU waste.
9. `python3 -c "from specfuse.loop.loop import assert_autoclose_debt_reconciled"` exits 0
   (`authoring-work-units` §9 symbol-existence check).
10. `python3 -m unittest discover -s tests -v` exits zero, in particular
    `tests/test_closing_guard_contracts.py`, `tests/test_lifecycle_integration.py`, and
    `tests/test_loop_auto_archive.py`.
11. **Satisfiability re-probed against the tree at execution time, not inherited.** Run the
    invariant's marker scan across every `.specfuse/features/*/RETROSPECTIVE.md` and report
    the count of features carrying a debt marker. The expected answer at this WU's dispatch
    is the set of features whose gates auto-closed after T06 shipped — which, on this repo,
    is **zero**. Paste the command and its output. If it is not zero, say which features and
    stop: the plan-time enumeration in `GATE-02-REVIEW.md` has gone stale and the reviewer
    needs to know before the guard is live.
12. Coverage stays ≥ 90%.

**Cost-reintroduction trade (`[FEAT-2026-0039/G2-CLOSE]`).** This WU lands on the **keeps
the saving** side. The invariant is a file-state check that runs in-process at close-WU
outcome time, in the same place `assert_terminal_flips_fired` already runs; it dispatches
nothing. Note the asymmetry it deliberately preserves: it makes the terminal close *pay
attention* to the debt, it does not make auto-close *stop saving*. A gate that auto-closes
still costs no session — it now leaves a list (T06) that someone is obliged to read (T07).

**Do not touch.**

- `assert_terminal_flips_fired` (`loop.py:4292`) — this WU adds a sibling to the same
  registration list; the existing invariant's body, checks, and messages are unchanged.
  Editing it would put two of this feature's gates in one function.
- `verify_post_pass_invariants` (`loop.py:4374`) — the dispatch contract (type-keyed,
  first-failure-returns) is correct and is what AC7 relies on.
- `evaluate_auto_close`, `AutoCloseDecision` — the predicate decides *whether* to
  auto-close; this invariant checks what a later close did about it. Two different
  questions, deliberately not coupled: making the predicate refuse on unreconciled debt
  would fire at the wrong gate and at the wrong time.
- `build_autoclose_debt_enumeration` and the two stub writers — `FEAT-2026-0070/T06` owns
  them. This WU reads the marker T06 writes; if the marker is wrong, that is a T06 defect.
- `fire_terminal_flips`, `recheck_terminal_verdict`, `mark_close_wu_auto_closed` — gate 1's
  surfaces, untouched by gate 2.
- `_GUARD_LITERAL_PREDICTIONS` in `lint_plan.py` — `FEAT-2026-0070/T08` owns the arm-time
  prediction for this guard. Do not add it here; the doc row (AC8) and the lint WARN are
  deliberately separate deliverables.
- **`loop.py:4462`'s `write_frontmatter_field(..., "status", "complete")`** — a real defect
  found by gate 1's close audit (`RETROSPECTIVE.md` § *One-owner audit*), on the same file
  and adjacent to this work. Out of scope: it is a gate-1-family bug, it needs its own
  issue and red test, and this repo fixes bugs on their own branch
  (`.specfuse/skills/fix-bug`). Fixing it here is the "while I was here" drift
  `result-contract.md` §2 forbids.
- `.git/`, secrets. The driver owns all git operations. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml` (tests, ruff, bandit,
coverage ≥ 90%, leak-scan, the four `bats` gates). Scoped red/green proof:
`python3 -m unittest tests.test_loop_post_pass_invariant.TestAutoCloseDebtReconciled -v`.
Symbol check per AC9. The AC11 tree scan is its own reported command.

> Sandbox note: the four `bats` gates call `mktemp -d` in `setup`, which the default session
> sandbox denies before any assertion runs (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
> Report which sandbox each gate ran under.

**Escalation triggers.** Emit `status: blocked` if AC11's scan finds a feature in this repo
that carries a debt marker and would fail the invariant — the plan-time enumeration said
zero, and a non-zero answer means this guard would block a close on evidence the reviewer
has not seen. Also block if the marker T06 shipped does not match the `gate=(\d+)` contract
in `FEAT-2026-0070/T06` AC5: a guard reading a marker that is not there is a guard-shaped
no-op that passes every test, which is worse than no guard. Also block if satisfying AC5
(terminal-auto-close short-circuit) appears to leave the terminal auto-close path with no
reconciliation surface at all — that is a real gap in gate 2's definition of done and the
operator should rule on it rather than have this session invent a third path. Blocked is a
respectable outcome (`result-contract.md` rule 4).
