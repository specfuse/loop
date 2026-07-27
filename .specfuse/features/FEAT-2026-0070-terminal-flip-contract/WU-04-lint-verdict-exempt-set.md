---
id: FEAT-2026-0070/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 1.50
produces:
  - specfuse/loop/lint_plan.py
  - tests/test_lint_plan_verdict_exempt.py
oracle_env: macos_local
produces_driver_helper: lint_plan.lint (close-WU verdict-exempt set)
model: sonnet
effort: medium
gate_set: code
driver_version: 0.4.0
started_at: 2026-07-27T02:44:55.829981+00:00
duration_seconds: 440.009
cost_usd: 0.988023
input_tokens: 60
output_tokens: 7963
---

# Add `in_progress`/`in_review` to `lint_plan`'s close-WU verdict-exempt set

**Objective.** Stop `lint_plan` failing a close WU **mid-dispatch** with an error about
the wrong thing, by exempting the two lifecycle states the driver itself writes during
dispatch.

**Context.** This is `FEAT-2026-0070/T04`, the pre-registered fix from
`.specfuse/LEARNINGS.md`:

> `[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` … `lint_plan.py`'s verdict-exempt set for
> close-type WUs omits `in_progress`/`in_review`, and the driver flips status→`in_progress`
> at dispatch, so plan-lint (the `plannext` gate set) FAILS mid-dispatch on a verdict-less
> close WU — even when AC text says "no terminal verdict." … **Fix the lint exempt-set to
> include in_progress/in_review only as a separate, deliberate WU — do not weaken a gate
> from inside a close session.**

This is that separate, deliberate WU. Verified still live at drafting:
`specfuse/loop/lint_plan.py:626` exempts `{"draft", "pending", "done", "abandoned",
"blocked_human"}` — neither `in_progress` nor `in_review` is present.

**The real defect is diagnostics, not strictness.** The sequence is: driver flips a close
WU to `in_progress` → dispatches the agent → the agent writes its verdict and retrospective
→ the `plannext` gate set (which includes plan-lint) runs. A close WU that *does* write its
verdict passes, because by gate time the verdict exists. A close WU that **fails to write
one** gets a plan-lint error about WU frontmatter shape rather than a message saying "a
close WU must write a verdict" — mid-dispatch, on a surface the agent is not looking at.
Same family as #265 and #272: the driver enforcing a contract whose violation it does not
explain.

Exempting the two states does not lose the check. The verdict requirement on a **completed**
close WU is enforced by `assert_verdict_well_formed`, a driver-side guard that runs at
outcome time and — per the #265 measurement — fires 10 times for **$0.00**, because it is
checked before the agent spends anything. That guard is the right owner; plan-lint firing
on a transient dispatch state is not.

**`Red-test exempt`: not claimed.** AC1 names a genuinely red test.

**Acceptance criteria.**

1. **Red test:**
   `tests/test_lint_plan_verdict_exempt.py::TestDispatchStatesAreExempt::test_in_progress_close_wu_without_verdict_is_not_an_error`
   exists and **fails on HEAD before this WU's edits** —
   `python3 -m unittest tests.test_lint_plan_verdict_exempt -v` exits non-zero. It lints a
   feature whose close WU is `status: in_progress` with no `verdict` and asserts zero
   errors. On HEAD that is an error, so the test is red on behaviour.
2. The same test passes after this WU's edits, and a companion case covers `in_review`.
3. **The check still fires where it should.** A close WU in a *settled* state that requires
   a verdict and lacks one is still an error — assert it explicitly, so this WU cannot be
   read as "verdicts are now optional." Name the states asserted; do not rely on the
   exempt set's complement being obvious.
4. **Satisfiability probe (`planning-discipline.md` §2), run and recorded.** Before
   editing, run `python3 .specfuse/scripts/lint_plan.py` over **every** feature folder in
   `.specfuse/features/` and record the error count. After the edit, run it again. The
   count must not increase, and any decrease must be attributable to a close WU in a
   dispatch state. Paste both counts into the RESULT block — this WU changes a linter, and
   an unmeasured linter change is how a gate starts failing on correct input.
5. The exempt set is expressed so the two added states are visibly *dispatch-transient*,
   not lumped anonymously with `done`/`abandoned`. A one-line comment naming why each state
   is exempt, and naming `assert_verdict_well_formed` as the guard that owns the real
   check, is enough — the next reader must not conclude the requirement was dropped.
6. `python3 -m unittest discover -s tests -v` exits zero — in particular
   `tests/test_verdict_coupling.py`, which pins the verdict semantics this touches.
7. Coverage stays ≥ 90%.

**Do not touch.**

- `assert_verdict_well_formed` in `specfuse/loop/loop.py` — it is the correct owner of the
  verdict requirement and it is already cheap ($0.00 across 10 fires, because it runs
  pre-spend). This WU narrows plan-lint's overlap with it; it does not move the check.
- `VERDICT_VALUES` — the accepted verdict values are unchanged.
- `specfuse/loop/loop.py` generally — `T01` and `T02` own the driver in this gate.
- `docs/methodology.md`'s outcome contract — unrelated surface, corrected separately in
  #272.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the before/after
lint sweep in AC4. Scoped red/green proof:
`python3 -m unittest tests.test_lint_plan_verdict_exempt -v`.

> Sandbox note: the three `bats` gates call `mktemp -d` in `setup`, denied by the default
> session sandbox before any assertion runs. Report which sandbox each ran under.

**Escalation triggers.** Emit `status: blocked` if AC4's sweep shows the error count
*increasing* after the edit — that would mean the exempt set interacts with another check
in a way this WU did not predict, and a linter that newly fails correct input is exactly
the unsatisfiable-predicate failure `planning-discipline.md` §2 exists to prevent. Also
block if making the states exempt requires touching `assert_verdict_well_formed`: the two
checks are meant to be independent, and coupling them would put the verdict requirement in
two places. Blocked is a respectable outcome (`result-contract.md` rule 4).
