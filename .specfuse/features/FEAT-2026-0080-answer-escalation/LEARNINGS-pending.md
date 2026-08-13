# LEARNINGS-pending

**What this file is.** This feature runs under `autonomy_default: auto` — a
closing WU here dispatches without a human reading the gate first. Under
`review` or `supervised`, a promoted lesson lands straight in the repo's
`.specfuse/LEARNINGS.md`, because a human already reviewed the gate that
produced it. Under `auto` nobody did, so the lesson stages here instead: in
this feature directory, not in the repo-wide file that every future feature's
planning step loads. A closing WU's own post-pass check refuses to pass if
its diff touches `.specfuse/LEARNINGS.md` while this feature is in `auto`
mode — this file is where those lessons go instead.

**How a human promotes an entry from here.** At PR review for this feature:

1. Read each entry below. Judge it the way you would judge any
   `LEARNINGS.md` candidate — does it generalize into a rule that should
   change how a FUTURE work unit, in any feature, is written or executed?
2. For each entry you accept, copy it into `.specfuse/LEARNINGS.md` (below
   the `<!-- lessons work units append below this line -->` marker, in that
   file's existing entry format) in the same commit or a follow-up commit to
   the PR branch.
3. For each entry you reject or narrow, leave it here — do not delete it
   silently; a short note on why it didn't generalize helps the next person
   who drafts a similar feature.
4. This file is not read by planning. Nothing here shapes another feature
   until a human has done step 2.

## Format

```
- [FEAT-YYYY-NNNN/G1] Implementation WUs must name the module a new route/handler
  lives in; "add it to the router" cost a blocked attempt when no router existed yet.
```

## Entries

**All four entries below were PROMOTED to `.specfuse/LEARNINGS.md` on 2026-08-13**,
after PR #2245 merged, each carrying the `[FEAT-2026-0080/G1/<slug>]` correlation ID
that file's format requires. None were rejected or narrowed. They are left here
verbatim rather than deleted, per this file's own step 3, so the staging record stays
readable next to what came of it.

Promoted as:

- `[FEAT-2026-0080/G1/a-refusal-message-shorter-than-its-source-means-a-stale-build]`
- `[FEAT-2026-0080/G1/an-instruction-naming-a-mechanism-that-cannot-satisfy-it]`
- `[FEAT-2026-0080/G1/price-a-wu-against-its-declared-acceptance-not-its-runtime-surface]`
- `[FEAT-2026-0080/G1/a-recovery-diagnosis-is-a-hypothesis-until-checked-against-the-reflog]`

<!-- closing work units append below this line -->

- [FEAT-2026-0080/G1] **When a guard refusal's message names fewer accepted paths
  than the guard's source offers, you are not running that source.** Three close
  attempts were refused by `assert_learnings_appended_or_noop` at $40.27 total.
  The sessions had complied — each committed a populated `LEARNINGS-pending.md`
  (180, 85, 138 added lines, visible at reflog commits `22ff27c`, `bc27b30`,
  `9292986`). Post-#1582 that guard renders `no <LEARNINGS.md> or <staging file>
  additions in squash` when the staging arm is live; the recorded refusals named
  only `.specfuse/LEARNINGS.md`, which is byte-for-byte what `08a2210^` — the
  revision before the fix — emits. The branch tree carried the fix; the *running*
  build did not. Diagnosis rule: before treating a guard refusal as a content
  defect, check that the message's **shape** matches the guard source you are
  reading. A message missing a clause the current code always emits is evidence
  of a stale build, and no amount of attempt budget will converge against it.
  This is a second instance of the `build_provenance` hazard already recorded in
  `CHANGELOG.md` (the first cost 14 spurious red results in another close).

- [FEAT-2026-0080/G1] **"An instruction naming a mechanism that cannot satisfy
  the instruction" is a recurring defect shape, and it is invisible to review
  because both halves read as correct in isolation.** This feature contains two
  independent instances. `/fix-bug` Step 1 said "Read: title, labels, body,
  comments" one line under `gh issue view <issue-number>`, a command that does
  not return comments — the intent was right, the named mechanism could not
  deliver it, and it survived undetected long enough to need a feature to fix.
  Then this feature's own close WU criterion 5 told the session to promote
  lessons to `.specfuse/LEARNINGS.md`, the one destination `close-i` forbids
  under `autonomy_default: auto`. Both defects have the same form: a stated
  intent, and directly beside it a named command/path/destination that provably
  cannot achieve it. Authoring rule: when a work unit names both an intent and
  the mechanism for it, verify the mechanism against the intent — run the
  command and read its output, or check the named path against the guard that
  governs it. Reviewing the sentence for plausibility does not catch this class.
  Filed upstream as #2173 for the template and `/draft-feature`.

- [FEAT-2026-0080/G1] **Price a work unit against the acceptance its own plan
  declares, not against the runtime surface it touches.** T01 was estimated at
  $8.00 and T02 at $3.00 on the reasoning that they wire skills driving `gh`;
  they landed at $2.68 and $0.58 (−66% and −81%). PLAN.md had already recorded,
  in *Verification the loop cannot perform*, that their acceptance is structural
  — unit tests asserting on `SKILL.md` prose, no live API call. The estimate
  contradicted a decision the same document made. Estimating rule: a work unit
  whose oracles are structural asserts on files is priced as a documentation
  unit, whatever runtime surface the shipped artifact eventually drives. Where
  the plan already names the oracle, read it before pricing.

- [FEAT-2026-0080/G1] **A diagnosis written into a commit message or a gate
  comment becomes durable state, and gets read as evidence rather than as a
  claim.** The recovery commit for this feature's spin (`589fd96`) recorded that
  "Neither RETROSPECTIVE.md nor LEARNINGS-pending.md was ever produced" and that
  the cause was "an authoring defect in the work unit, not a tool defect". Both
  are contradicted by the attempts' own commits, which are still in the reflog.
  That diagnosis had already propagated into `GATE-01.md`'s budget-raise
  rationale and into issue #2173 before anything checked it against the
  artifacts. Rule: a post-mortem written at recovery time is a hypothesis until
  it is checked against the failed attempts' actual diffs; where those attempts
  were rolled back, `git reflog` still holds them. State the evidence you
  checked alongside the conclusion, so the next reader can tell which it is.
