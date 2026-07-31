---
id: FEAT-2026-0053/T10
type: implementation
status: draft
attempts: 0
planned_cost_usd: 3.00
oracle_env: macos_local
provenance: "PLAN.md's scope boundary names gate 3 as 'docs and methodology rewrite'; this WU is the methodology half. The specific edit surface is fixed by G2-PLAN's read of docs/methodology.md §9 against the shipped code: §9's four auto-arm conditions describe a design that was replaced by the eight-class predicate, and §9's per-gate tightening-only override has no consumer in the run loop at all."
produces:
  - docs/methodology.md
  - specfuse/loop/data/docs/methodology.md
  - docs/dev/auto-arm-recovery.md
---

# The autonomy dial, as the run loop actually reads it

**Objective.** Rewrite `docs/methodology.md` §9 so it describes the autonomy
dial the driver actually implements, fold the auto-arm guarantee in from
`docs/dev/auto-arm-recovery.md`, and mark the parts of the old §9 that were
never built as unbuilt rather than leaving them readable as fact.

**Context.** Correlation ID `FEAT-2026-0053/T10`. Gate 3 is the terminal gate
and its job is making `auto` legible to someone who did not build it. This WU
owns the canonical definition; `T11` owns the operator-facing stop-class
reference and `T12` owns migration and opt-in. Do not duplicate their content —
cross-reference it.

**What §9 says today, and why every sentence of it needs checking.** §9 is
eleven lines written before any of this feature existed. It states that under
`auto` the per-gate stop may be skipped "only when all of: the structural lint
passes, the not-yet-reached skeleton was not revised, no task in the gate
carries a `supervised`/auto-forbidden override, and plan-next raised no
escalation." **None of those four is the shipped condition.** What shipped is
`evaluate_arm_predicate(feature_dir, just_closed_gate)` in
`specfuse/loop/arm_eval.py`: eight named stop classes, each returning
fired / clean / not_evaluable, with `would_arm` true only when no class fired.
Three of the eight (`missing_provenance`, `open_questions_human_only`,
`plan_next_lint`) are veto channels fed by model-authored output; the rest are
counters, paths and hardcoded constants. A reader who plans against today's §9
will predict the wrong behavior in both directions — it names conditions that
do not exist and omits every condition that does.

**Two claims in §9 have no implementation, and this WU must not paper over
them.** Established by grep at drafting, `grep -n 'autonomy' specfuse/loop/*.py`:

- **Per-gate override, "tightening only".** The only consumers of the dial read
  `autonomy_default` from `PLAN.md` frontmatter. Nothing reads a per-gate
  autonomy field. The tightening-only override is designed and unbuilt.
- **`supervised` as a distinct level.** Every consumer branches on
  `== "auto"`. `review` and `supervised` are the same behavior today; the
  distinction is a name, not a mechanism.

Write both as unbuilt, in the document, in one sentence each. Do not delete
them silently and do not describe them as working. `.specfuse/rules/`,
`RETROSPECTIVE.md` and this feature's code are the evidence surfaces; if you
find a third claim in §9 with no consumer, treat it the same way.

**One fact, one home (`docs/methodology.md` §2).** `docs/dev/auto-arm-recovery.md`
already carries the one-commit guarantee and the exact
`git reset --hard pre-arm/<feature-id>/gate-<N>` procedure. §9 gets the
*concept* — an arm is exactly one commit, tagged before it lands, so there are
two recoverable states and no third — and links the dev note for the procedure.
The procedure is not restated in §9 and the concept is not re-derived in the
dev note.

**The incremental edit to an already-delivered file, stated so nobody has to
infer it.** `docs/dev/auto-arm-recovery.md` was delivered `done` by `T06` and
appears in this WU's `produces:` anyway, so the plan lint warns about it by
design. The warning is expected and the edit is narrow: **T10 adds one line at
the top of that file pointing at methodology §9 as the conceptual home, and
changes nothing else in it — not the guarantee, not either state, not the
recovery command.** The path stays in `produces:` because the driver's in-diff
gate is the strongest available guarantee that this WU actually touched the dev
note rather than only editing the methodology.

**Acceptance criteria.**

1. `grep -c "not-yet-reached skeleton was not revised" docs/methodology.md`
   returns `0` — the pre-implementation four-condition sketch is gone from §9.
2. §9 states what each of `auto` / `review` / `supervised` means to the run loop
   today: under `auto` the predicate's verdict is acted on at the one flip site
   that can arm; under `review` and `supervised` the predicate is still
   evaluated and still emitted, and nothing acts on it. The sentence recording
   that `review` and `supervised` are behaviorally identical today is present.
3. §9 records the per-gate tightening-only override as designed-but-unbuilt,
   naming that no consumer reads a per-gate autonomy field.
4. §9 names where the human checkpoints on an `auto` feature actually are — every
   escalation, the PR review, and the merge — and states that escalation
   overrides autonomy by control flow (the escalation flip sites return before
   the arm branch is reached), not by a check that could be forgotten.
5. §9 describes an auto-arm as exactly one bookkeeping commit preceded by a
   `pre-arm/<feature-id>/gate-<N>` tag at the pre-arm `HEAD`, and links
   `docs/dev/auto-arm-recovery.md` for the recovery procedure without restating
   the procedure.
6. §9 names the two per-feature artifacts an `auto` feature produces that a
   `review` feature does not (`FEATURE-REVIEW.md`, `LEARNINGS-pending.md`) and
   the two event types this feature added (`arm_predicate_evaluated`,
   `gate_auto_armed`), one line of meaning each, cross-referencing T11's
   stop-class reference and T12's migration guide instead of duplicating them.
7. `docs/dev/auto-arm-recovery.md` gains one line at the top pointing at
   methodology §9 as the conceptual home. Its procedure content is unchanged.
8. `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits `0` — the
   mirrored scaffold copy `specfuse/loop/data/docs/methodology.md` byte-matches
   the canonical `docs/methodology.md`. Editing only one copy fails this.
9. `python3 -m unittest discover -s tests -v` exits `0`. This WU changes
   documentation only; no `.py` file under `specfuse/` is edited.

**Do not touch.** Any file under `specfuse/` other than the mirrored
`data/docs/methodology.md` copy — this WU has no source changes, and a §9 that
cannot be written truthfully without one is an escalation, not a licence. The
new pages under `docs/concepts/` (T11, T12 own those, and both also edit
`docs/README.md`; this WU does not). `.specfuse/rules/`. `RETROSPECTIVE.md`,
`GATE-03-REVIEW.md`, and every other feature-folder artifact. Methodology
sections other than §9 and §3's outcome table cross-reference — a broad
methodology rewrite is not this WU. Generated directories, secrets, `.git/`.
The driver owns all git — you edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_scaffold_data_in_sync -v`. The
grep in criterion 1 is a literal check, run it exactly as written.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if
§9 cannot be made true about the shipped behavior without a code change — that
would make gate 3 an implementation gate wearing a docs label, which is the
condition `G2-PLAN` was told to stop on. Finding an *additional* unbuilt claim
is not that trigger: record it as unbuilt and continue. Emit `status: blocked`
if the two mirrored copies cannot be kept byte-identical for a reason you
cannot resolve inside this WU.
