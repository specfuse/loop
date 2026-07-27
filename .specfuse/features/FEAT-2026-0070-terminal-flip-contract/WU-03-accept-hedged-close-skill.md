---
id: FEAT-2026-0070/T03
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - plugins/specfuse/skills/accept-hedged-close/SKILL.md
  - .specfuse/skills/accept-hedged-close/SKILL.md
  - tests/test_accept_hedged_close_skill.py
oracle_env: macos_local
---

# `/accept-hedged-close` — an auditable operator path out of a standing `met_locally`

**Objective.** Add the skill that lets an operator accept a standing `met_locally`
verdict, recording the reason and the accepted follow-up list in the feature folder, then
firing the terminal flips through `FEAT-2026-0070/T02`'s primitive.

**Context.** This is `FEAT-2026-0070/T03`, issue #243 candidate 1. `depends_on: [T02]` —
that primitive is the only thing permitted to reach terminal state.

**The problem this closes.** A `close` WU writing `verdict: met_locally` correctly leaves
every WU `done`, the terminal gate `awaiting_review`, and PLAN + roadmap `active`. For
some features that is the ceiling **by construction**: FEAT-2026-0039's central
deliverable was an interactive skill whose target is a different repository, and no gate
size, extra WU, or amount of test-writing closes that from inside a dispatched session.
`/wrap-feature` then refuses the feature by hard rule and says *"do not attempt manual
reconciliation here"* — so the operator hand-edits three surfaces the driver deliberately
declined to write, leaving no record of why.

Today that override happens anyway. This skill's value is that it leaves a trace.

**The constraint that outranks every acceptance criterion below.**
`[FEAT-2026-0023/G1-CLOSE]`: terminal-state flips have exactly ONE owner inside the
loop package.
**This skill must not write `PLAN.md status`, the gate status, or the roadmap row.** It
gathers the operator's input, writes its own acceptance record, and calls T02's primitive
to do the flipping. A skill that writes those surfaces itself has rebuilt issue #49 with
a friendlier name, and should be rejected at close review even if every gate is green.

Read `.specfuse/skills/unblock-wu/SKILL.md` for the propose-and-confirm posture this
should mirror, and `.specfuse/skills/wrap-feature/SKILL.md` for the refusal it
complements. Skills are canonical in `plugins/specfuse/skills/` and propagated with
`scripts/sync-scaffold.sh` — never hand-edit the `.specfuse/skills/` copy
(`[skills_canonical_plugins_dir]`).

**`Red-test exempt`: not claimed.** AC1 names a genuinely red test.

**Acceptance criteria.**

1. **Red test:**
   `tests/test_accept_hedged_close_skill.py::TestSkillRegistration::test_skill_is_registered_and_canonical`
   exists and **fails on HEAD before this WU runs** — the skill directory does not exist.
   It asserts the canonical `plugins/specfuse/skills/accept-hedged-close/SKILL.md` is
   present with valid frontmatter (`name`, `description`).
2. The same test passes after this WU's edits.
3. **The skill does not write terminal state.** A test asserts `SKILL.md` contains no
   instruction to edit `PLAN.md`'s `status`, the gate `status`, or the roadmap row
   directly, and that it names T02's primitive as the mechanism. This is the WU's
   load-bearing criterion — express it as a grep-shaped assertion over the skill text, not
   as prose in the body.
4. The skill's method requires, before any write: the feature ID; confirmation that its
   close WU is `done` with a hedged verdict; a **one-line operator reason** (empty or
   whitespace-only is refused and re-prompted, matching `unblock-wu`'s rationale
   discipline); and explicit acknowledgment of the standing follow-up list.
5. It writes an **acceptance record** into the feature folder naming: the accepted
   verdict, the operator reason, each outstanding follow-up carried forward verbatim from
   the hedged-follow-up record, and the timestamp. The point is that the override is
   auditable — a flip with no record is what exists today.
6. It **refuses** on a feature whose verdict is `met` (nothing to accept — point at T02's
   primitive), on `not_met`, and on a feature whose close WU is not `done`. One test per
   refusal, each naming which condition failed.
7. It does **not** discharge or close the follow-ups. Accepting a hedge means shipping
   with known-open items, not pretending they are done; the record carries them forward.
   A test asserts the skill text says so.
8. Both copies are byte-identical after `scripts/sync-scaffold.sh` runs:
   `cmp plugins/specfuse/skills/accept-hedged-close/SKILL.md .specfuse/skills/accept-hedged-close/SKILL.md`
   exits 0, and `python3 -m unittest tests.test_skills_vendored_in_sync -v` exits zero.
9. The skill ends with the RESULT block per `.specfuse/rules/result-contract.md`, and its
   `status: blocked` case is reserved for a refusal in AC6 or an unavailable operator.
10. `python3 -m unittest discover -s tests -v` exits zero.

**Do not touch.**

- **The driver package.** `FEAT-2026-0070/T01` and `T02` own it in this gate; this WU
  adds a skill and its test, nothing else, and declares no driver symbol of its own. If
  the primitive T02 shipped does not expose what this skill needs, that is a finding to
  escalate, not to patch around.
- `.specfuse/skills/accept-hedged-close/SKILL.md` **as a direct edit** — it is an output
  of `scripts/sync-scaffold.sh`.
- `.specfuse/skills/wrap-feature/SKILL.md` — its refusal on non-`done` features is
  correct and stays. This skill is the path that makes the feature `done` first; changing
  `wrap-feature` to accept hedged features would remove the checkpoint.
- `.git/`, secrets. The driver owns all git operations. See
  `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`, plus the `cmp` in
AC8. Scoped red/green proof:
`python3 -m unittest tests.test_accept_hedged_close_skill -v`.

> Sandbox note: the three `bats` gates call `mktemp -d` in `setup`, denied by the default
> session sandbox before any assertion runs. Report which sandbox each ran under.
>
> The `.claude/skills/` discovery symlink is an **operator prerequisite, not agent work** —
> Claude Code's sandbox lists `.claude/skills` under `denyWithinAllow`, a deny rule inside
> an allow scope that survives `unsandboxed: true` (`[FEAT-2026-0016/G3-CLOSE]`). Do not
> attempt to create it; a WU that tries will burn an attempt rediscovering this.

**Escalation triggers.** Emit `status: blocked` if T02's primitive cannot be invoked from
a skill context — that is a design finding about the primitive's surface, and patching
around it by writing the flips here is the one thing this WU must not do. Also block if
`scripts/sync-scaffold.sh` does not reproduce the vendored copy. Blocked is a respectable
outcome (`result-contract.md` rule 4).
