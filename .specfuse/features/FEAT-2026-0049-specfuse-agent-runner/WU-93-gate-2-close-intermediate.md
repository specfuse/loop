---
id: FEAT-2026-0049/G2-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
---

# G2-CLOSE-INTERMEDIATE — gate 2 retrospective, lessons, docs

**Context.** Gate 2 is the first gate in which the agent *acts* on a live
repository: it fixes bugs through the bug lane, records triage decisions, and
reads operator answers. This unit folds the retrospective, the lessons, and the
documentation for that gate into one session.

It also carries an inherited obligation. Gate 1 **auto-closed**
(`evaluate_auto_close`, predicate=v1), so its close ceremony never ran and its
per-criterion deferred-verification list was never enumerated. `GATE-01.md` and
`RETROSPECTIVE.md`'s `<!-- specfuse:autoclose-debt gate=1 wus=T01,T02,T03,T04
criteria=27 -->` marker both say the same thing: that debt must be reconciled
before the feature's terminal verdict, and auto-close cannot enumerate it. This
is the gate that reconciles it.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` carries a `## Gate 2` heading — that exact heading, which
   `assert_retrospective_gate_section` checks after dispatch — recording what the
   four providers actually do, what the gate deliberately did not prove, and any
   deviation from PLAN.md's recorded decisions with the deviation's reason.
2. **Gate-1 auto-close debt reconciled.** For each of the 27 criteria the
   auto-close listed as deferred, state whether it has since been verified, by
   what, or that it remains unverified. A criterion still unverified is a
   legitimate outcome; recording it as verified without a run is not.
3. **Cost reconciliation**: each gate-2 WU's actual `cost_usd` against its
   `planned_cost_usd`, read from `events.jsonl` and WU frontmatter rather than
   estimated, plus the gate total against `GATE-02.md`'s `cost_budget_usd`. Name
   any WU that exceeded its estimate and why.
4. **Deferred-verification list** for gate 2's own criteria: the criterion, the
   reason, and where it actually gets checked. Any criterion whose verification
   needed a live GitHub repository, a real bug issue, or a real operator answer
   belongs here — the loop's test doubles are not that. If every criterion was
   verified in-loop, write `(nothing — every acceptance criterion was verified
   in-loop)` rather than omitting the section.
5. Generalizable lessons are staged in `LEARNINGS-pending.md` **in this feature
   folder**. Under `autonomy_default: auto`,
   `assert_learnings_staged_under_auto` forbids touching `.specfuse/LEARNINGS.md`.
6. Documentation reflects what shipped: at minimum, which action classes
   `specfuse-agent run` now handles, and that `--max-tokens` enforces a real
   number as of T05 where it previously could not fire.
7. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source — a closing unit records, it does not
fix. `.specfuse/LEARNINGS.md` (staging file only, per AC5). `.specfuse/roadmap.md`
— the driver owns roadmap flips. Gate 1's WU files. Gate 3's WU files and the
gate-restructure `G2-PLAN` owns (`GATE-02-REVIEW.md`'s open question OQ-1) — this
unit records gate 2, it does not re-plan the feature.

**Verification.** The `doc` gate set from `.specfuse/verification.yml`, plus
`specfuse lint --closing` exiting 0.

**Escalation triggers.** If cost reconciliation cannot be completed because
`events.jsonl` rows for a gate-2 WU are missing, stop and name the WU rather than
estimating — #1024 records that these rows can be lost between a WU's squash and
the next bookkeeping commit. If reconciling the gate-1 auto-close debt (AC2)
turns out to require running verification that was never run — rather than
recording that it was not — stop and say which criteria need it: recording an
unverified criterion as verified is the failure the debt marker exists to
prevent.
