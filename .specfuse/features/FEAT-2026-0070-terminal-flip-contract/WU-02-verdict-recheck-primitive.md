---
id: FEAT-2026-0070/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.50
produces:
  - specfuse/loop/loop.py
  - tests/test_terminal_flips.py
oracle_env: macos_local
produces_driver_helper: recheck_terminal_verdict
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-27T02:35:16.281763+00:00
duration_seconds: 579.381
cost_usd: 1.203202
input_tokens: 1104
output_tokens: 12881
---

# A driver-side primitive that re-evaluates a completed close WU's verdict and fires the flips

**Objective.** Add a driver entry point that reads a **completed** close WU's verdict from
disk and fires `fire_terminal_flips` when it now permits them — so a feature whose verdict
legitimately changed after close reaches `done` through the driver instead of by hand.

**Context.** This is `FEAT-2026-0070/T02`, the load-bearing WU of gate 1. Read `PLAN.md`
in this folder first; its existing-mechanism verdict is binding on the design.

**The gap, observed rather than theorised.** `fire_terminal_flips` runs at close-WU
*outcome* time, inside the dispatch loop. Once a close WU is `status: done` the driver
never re-dispatches it, so its verdict is never re-read. FEAT-2026-0069 hit this exactly:
its close wrote `met_locally` honestly, the follow-ups were later discharged against a
real external repository, the frontmatter was upgraded to `verdict: met` — and re-running
the driver still fired nothing. The driver's own output said so:

```
Gate 2 complete (retro, lessons, docs, plan-next); terminal gate but PLAN.md not yet `done`.
Inconsistency: terminal gate closed without close ceremony flipping PLAN.md to `done`.
Likely fix: manually flip PLAN.md `status: active -> done`, then /wrap-feature.
```

Three surfaces were then hand-edited. That advice is also incomplete — flipping `PLAN.md`
alone leaves the gate `awaiting_review` and the row `active`, which `/wrap-feature` then
refuses on. Recorded as a second defect on issue #243.

**The constraint that shapes the whole design.** From `.specfuse/LEARNINGS.md`:

> `[FEAT-2026-0023/G1-CLOSE]` **Terminal-state flips must have exactly ONE driver-side
> owner called identically by every close path.**

This WU therefore adds a **caller**, not a second writer. The new primitive locates the
terminal close WU, reads its verdict from disk, and — if permitted — calls the existing
`fire_terminal_flips` unchanged. It must not duplicate any flip logic.
`FEAT-2026-0070/T03` builds the operator skill on top of this; nothing else may write
terminal state.

Read `fire_terminal_flips` (`specfuse/loop/loop.py:3128`) and
`verdict_permits_terminal_flips` (`:134`) before starting. Note the existing function
already reads the verdict **from disk, not from in-memory `wu.verdict`** — that was
FEAT-2026-0023/T01's fix for the auto-close path, and this WU depends on the same
property.

Binding rules in `.specfuse/rules/` apply.

**Acceptance criteria.**

1. **Red test:**
   `tests/test_terminal_flips.py::TestVerdictRecheck::test_upgraded_verdict_fires_flips_without_redispatch`
   exists and **fails on HEAD before this WU's edits** —
   `python3 -m unittest tests.test_terminal_flips.TestVerdictRecheck -v` exits non-zero.
   It builds a feature whose close WU is `status: done` with `verdict: met_locally` and
   whose three surfaces are un-flipped, rewrites the frontmatter to `verdict: met`, invokes
   the new primitive, and asserts all three surfaces reach terminal state. No such entry
   point exists on HEAD.
2. The same test passes after this WU's edits.
3. The primitive **calls `fire_terminal_flips`** and does not reimplement any flip.
   `grep -c "def fire_terminal_flips" specfuse/loop/loop.py` returns `1`, and the new
   function's body contains a call to it. This is the single-owner property; a
   hand-rolled second writer fails the WU regardless of test results.
4. It reads the verdict **from disk**, matching `fire_terminal_flips`'s own contract —
   never from an in-memory `WorkUnit`, which the auto-close path leaves `None`.
5. A verdict that still does **not** permit flips (`met_locally`, `partially_met`,
   `not_met`, absent) leaves every surface untouched and reports why. One test per value.
   The primitive is a re-evaluation, not an override — overriding a standing hedge is
   `FEAT-2026-0070/T03`'s job and requires an operator reason.
6. Re-running it on an already-`done` feature is a **no-op** that does not error. Terminal
   flips are idempotent and this entry point will be run speculatively.
7. It refuses cleanly on a feature with no terminal close WU, or whose close WU is not
   `status: done`, naming which condition failed rather than exiting silently.
8. The entry point is reachable from the CLI — a flag or subcommand on the driver, named
   in `--help`. Name it for what it does (re-check a verdict), not for its first caller.
9. `python3 -c "from specfuse.loop.loop import <new_symbol>"` exits 0
   (`/authoring-work-units` §9 symbol-existence check).
10. `python3 -m unittest discover -s tests -v` exits zero, in particular
    `tests/test_terminal_flip_ownership.py` and `tests/test_verdict_coupling.py`.
11. Coverage stays ≥ 90%.

**Do not touch.**

- The body of `fire_terminal_flips` — this WU calls it. `FEAT-2026-0070/T01` owns its
  roadmap-row branch in this same gate; two WUs editing one function is the conflict this
  boundary avoids.
- `verdict_permits_terminal_flips` (`:134`) — the verdict semantics are correct.
  `met_locally` **should** withhold the flips; this WU adds a way to re-ask the question,
  not a way to change the answer.
- `assert_terminal_flips_fired` — the post-pass invariant is unchanged.
- Any skill under `.specfuse/skills/` — `FEAT-2026-0070/T03` owns the operator surface.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`. Scoped red/green
proof: `python3 -m unittest tests.test_terminal_flips.TestVerdictRecheck -v`. Symbol
check per AC9.

> Sandbox note: the three `bats` gates call `mktemp -d` in `setup`, which the default
> session sandbox denies before any assertion runs
> (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`). Report which sandbox each gate ran under.

**Escalation triggers.** Emit `status: blocked` if firing the flips outside the dispatch
loop requires state the loop only has mid-run (a `WorkUnit` object, an open events handle,
a `head_before` sha) and that state cannot be reconstructed from disk — that would mean
`fire_terminal_flips` is not callable out-of-band and the design needs an operator
decision, not a workaround. Also block if satisfying AC3 appears to require duplicating
flip logic: that is the divergence `[FEAT-2026-0023/G1-CLOSE]` forbids, and issue #49 is
what it cost to learn. Blocked is a respectable outcome (`result-contract.md` rule 4).
