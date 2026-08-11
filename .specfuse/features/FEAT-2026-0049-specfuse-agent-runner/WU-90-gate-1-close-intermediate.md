---
id: FEAT-2026-0049/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: pending
attempts: 0
planned_cost_usd: 4.50
---

# G1-CLOSE-INTERMEDIATE — gate 1 retrospective, lessons, docs

**Context.** Gate 1 built the conductor's stopping properties with no action
class attached. This unit folds the retrospective, the lessons, and the
documentation for that gate into one session.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` carries a `## Gate 1` heading — that exact heading, which
   `assert_retrospective_gate_section` checks after dispatch — recording what was
   built, what the gate deliberately did not prove, and any deviation from
   PLAN.md's four recorded decisions, with the deviation's reason, not just its
   fact.
2. **Cost reconciliation**: each gate-1 WU's actual `cost_usd` against its
   `planned_cost_usd`, read from `events.jsonl` and WU frontmatter rather than
   estimated, plus the gate total against `cost_budget_usd: 36.00`. Name any WU
   that exceeded its estimate and why — that number feeds `evaluate_auto_close`'s
   per-WU ratio check on every later gate.
3. **Deferred-verification list**: for each acceptance criterion not verified
   in-loop, the criterion, the reason, and where it actually gets checked. If
   every criterion was verified, write
   `(nothing — every acceptance criterion was verified in-loop)` rather than
   omitting the section.
4. Generalizable lessons are staged in `LEARNINGS-pending.md` **in this feature
   folder**. Under `autonomy_default: auto`, `assert_learnings_staged_under_auto`
   forbids touching `.specfuse/LEARNINGS.md`, and `close-b` accepts the staged
   file as satisfying evidence — so do not write "nothing generalizes" unless
   nothing actually does.
5. Documentation reflects what shipped: at minimum, `specfuse-agent`'s existence
   and its caps' real semantics, including the overshoot D3 accepted.
6. `specfuse lint --closing` exits 0 before this WU reports `complete`.

**Do not touch.** Any `specfuse/` source — a closing unit records, it does not
fix. `.specfuse/LEARNINGS.md` (staging file only, per AC4). `.specfuse/roadmap.md`
— the driver owns roadmap flips. Gate 2 and gate 3 WU files (`G1-PLAN`'s).

**Verification.** The `doc` gate set from `.specfuse/verification.yml`, plus
`specfuse lint --closing` exiting 0.

**Escalation triggers.** If cost reconciliation cannot be completed because
`events.jsonl` rows for a gate-1 WU are missing, stop and name the WU rather than
estimating — #1024 records that these rows can be lost between a WU's squash and
the next bookkeeping commit, so an absence is a known failure mode, not a reason
to guess. If a gate-1 acceptance criterion turns out to have been unverifiable as
written, say so plainly in the deferred list rather than reporting it as met.
