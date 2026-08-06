---
id: FEAT-2026-0056/T08
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
model: sonnet
effort: medium
produces_driver_helper:
  - specfuse.loop.loop.format_reverification_worklist
produces:
  - tests/test_loop_worklist_injection.py
generated_surfaces: []
---

# Put the re-verification worklist in the close session's prompt

**Objective.** Render T07's worklist into a session-prompt section and append it to a
`close` / `close-intermediate` work unit's body at dispatch, so the close is told
which criteria are carried forward and which it must re-verify instead of re-deriving
the whole definition of done.

**Context.** This is `FEAT-2026-0056/T08`, gate 2's wiring unit and the one that makes
a close cheaper. Read `PLAN.md`, `GATE-02.md`, and `.specfuse/rules/close-discipline.md`
§§1 and 5 before editing.

T05 makes the artifact survive a failed attempt; T06 stops a fresh one from being born
red; T07 turns entries into a partition. None of them changes what a close session
sees. This unit does.

**The precedent to follow.** `grep -rn 'wu.body = wu.body' specfuse --include='*.py'`
returns exactly one site — `specfuse/loop/loop.py:3353`, inside `execute_unit_attempt`,
where `format_oracle_capture(prerun_outcome["oracle_results"])` is appended before
`dispatch`. Use the same shape at the same site: a module-level formatter returning a
string (or `""`), appended to `wu.body`, called immediately after
`precreate_dispatch_skeleton(wu, feature_dir)` so the artifact it reads is the one
that call just seeded. Do not fold the rendering into `precreate_dispatch_skeleton` —
that function's contract is "write skeleton files", it returns `None`, and T02 owns it.

**The feature-level question never caches.** `[FEAT-2026-0057/G1-CLOSE]` is the
lesson and `PLAN.md` § *Notes* is the decision: "re-running every producing unit's own
oracle is not the feature-level re-run `close-discipline.md` §1 asks for; a close must
ask a question no unit's criteria asked." Caching is scoped to per-unit criterion
re-verification. The rendered section must say this to the session in so many words —
a worklist that looks like a complete to-do list invites a close to treat it as one,
and criterion 5 makes that line non-optional.

**This unit edits the dispatch path, so the driver must be restarted before anything
observes it.** `[FEAT-2026-0057/G1-CLOSE/driver-edits-need-a-restart]`: Python caches
modules in `sys.modules` at first import, so the `execute_unit_attempt` living in a
running driver's memory is the pre-T08 function object with no call site in it. Gate
1 hit this exact failure — its close was armed to observe T02's seeding and observed
nothing, because the driver process predated T02 by 25 minutes. The restart is
recorded as an arming precondition in `GATE-02.md` § *Arming discipline* and as an
escalation trigger on `G2-CLOSE`. It is a planned gate step, not an operator
afterthought. Your own unit tests will pass either way — they run in fresh
interpreters, which is precisely why the disagreement reads as a mystery.

Binding rules apply by reference — `.specfuse/rules/result-contract.md`,
`never-touch.md`, `security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_loop_worklist_injection.py::test_close_dispatch_prompt_carries_worklist`
   exists and **fails on HEAD before this WU's edits**. Record the failing output in
   the RESULT block before editing production code.
2. `specfuse/loop/loop.py` exports `format_reverification_worklist(wu, feature_dir)
   -> str` returning exactly `""` in each of three cases, each asserted separately:
   `wu.type` is neither `close` nor `close-intermediate`; the gate's
   `GATE-NN-CRITERIA.md` does not exist; the artifact exists but parses to zero
   entries.
3. For an artifact holding at least one carry-forward entry and at least one
   re-verify entry, the returned section states both counts and lists, for each
   carried-forward entry, its `criterion_id`, its `oracle`, and the `attempt` it was
   proved on.
4. The returned section lists each `oracle_groups` pair from T07 once, naming the
   `criterion_id`s it covers — so an oracle command shared by several criteria
   appears as one line of work, not several.
5. The section contains a literal, unconditional statement that the close's own
   feature-level question (`close-discipline.md` §1) is never carried forward and
   runs this attempt regardless of the worklist. Asserted by a test against the
   rendered string.
6. No entry with `kind: broad` appears in the section's carried-forward list —
   asserted against an artifact whose `broad` entry reads `state: pass` with an
   `attempt:` equal to the current one.
7. `execute_unit_attempt` appends the section to `wu.body` after the `oracle_section`
   append and before `dispatch`. Asserted by a test that calls the real
   `execute_unit_attempt` with a stub `dispatch_fn` that captures `wu.body`, on a
   `close-intermediate` WU with a seeded artifact — not by asserting on
   `format_reverification_worklist` alone. The seam is the thing gate 1 got wrong.
8. A `plan-next` work unit's body is unchanged by the same call path — asserted with
   the same stub-`dispatch_fn` harness.
9. `python3 -c "from specfuse.loop.loop import format_reverification_worklist"`
   exits 0.
10. The test named in criterion 1 **passes** after this WU's edits.

**Do not touch.** `precreate_dispatch_skeleton` and `_precreate_criteria_state_stub`
in `specfuse/loop/loop.py` — T02's additive seeding contract; call the first, do not
change either. `build_reverification_worklist` and everything else in
`specfuse/loop/criteria_state.py` — T07's and T01's; import, do not extend.
`specfuse/loop/lint_closing.py` and `specfuse/loop/closing_requirements.py` (T06's
scope, and this unit adds no closing requirement). `_clean_attempt_untracked` and the
`untracked_before` snapshot (T05's scope). `.specfuse/verification.yml`.
`.specfuse/rules/` and `.specfuse/templates/`. `GATE-01.md` and gate 1's work units.
Any other feature's folder under `.specfuse/features/`. Generated directories,
secrets, `.git/`. The driver owns all git operations — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`
(`python3 -m unittest discover -s tests -v -b`), `lint`, `security`, `coverage`
(`--fail-under=90`), `leak-scan`, `event-type-gate`. In addition run criterion 9's
symbol-existence check verbatim and paste its output. Criterion 1's red observation
must be recorded before production edits. Do **not** report the in-situ behaviour of
the running driver as evidence — this session's driver process predates your edits by
construction; report what the tests and a fresh interpreter show, and leave the
in-situ observation to `G2-CLOSE` after the restart.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
appending the section requires changing `precreate_dispatch_skeleton`'s signature or
return type — that is T02's shipped contract and an operator decision; criterion 7's
seam cannot be asserted because `execute_unit_attempt` cannot be driven with a stub
`dispatch_fn` in a test, which would mean the seam is untestable and the wiring
unverifiable; `format_reverification_worklist` is absent from the files you edited or
criterion 9's import fails — do not claim complete; or criterion 6 cannot be satisfied
because T07's partition carries a `broad` entry forward, in which case the soundness
contract has leaked upstream and the finding belongs to T07, not to a workaround
here.
