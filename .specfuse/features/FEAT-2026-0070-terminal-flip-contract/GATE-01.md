---
gate: 1
status: passed
baseline:
  sha: aa20e4ad16572f8f8c71c5e56f802b2a2479663f
  probed_at: 2026-07-27T03:00:23.399212+00:00
  failing: []
---

# Gate 1 — a correctly-closed feature reaches `done` through the driver, from any legitimate starting state

## Definition of done

- A feature whose roadmap row is `planned` at terminal close reaches `done` — the
  `autonomy: auto` self-dispatch path no longer escalates `roadmap_row_not_done` on a
  correct close (#226).
- A completed close WU whose verdict has since been upgraded to `met` can have its
  terminal flips fired **by the driver**, without re-dispatching the WU.
- An operator can accept a standing `met_locally` verdict through
  `/accept-hedged-close`, leaving an auditable record of the reason and the accepted
  follow-up list — instead of hand-editing three surfaces with no trace (#243).
- `lint_plan` no longer fails a mid-dispatch close WU with a message about the wrong
  thing.
- **Terminal state still has exactly one driver-side writer.** Every path above routes
  through the same helper.
- Every implementation work unit is `done`; retrospective written, durable lessons
  promoted, gate 2 drafted, `GATE-02-REVIEW.md` written.

**What this gate deliberately does NOT do.** It does not stop a feature from *reaching*
`met_locally` (that is #243 candidate 3, held as a follow-up), and it does not touch
auto-close's skipped enumeration (#241, gate 2). It makes the dead end exitable; it does
not remove the dead end.

## The constraint that outranks the acceptance criteria

`[FEAT-2026-0023/G1-CLOSE]`: **terminal-state flips have exactly ONE driver-side owner,
called identically by every close path.** Issue #49 existed because two paths diverged.

T03 is a skill. If it writes `PLAN.md status`, the gate status, or the roadmap row
directly — rather than calling T02's primitive — it has rebuilt #49 with a friendlier
name. A WU that does this has failed even with every gate green, and the reviewer should
reject it at close regardless of its RESULT block.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping gate 2's WUs to `pending`:

- **Runtime probe for the severity flip (§4).** Gate 2's likely shape includes a
  post-pass invariant that escalates when a terminal close ignores an auto-closed
  predecessor's deferred-verification debt. That is a new blocking condition: apply it
  locally, run the **full** oracle (`python3 -m unittest discover -s tests -v`), and paste
  the failure list into `GATE-02-REVIEW.md`. Features in this repo that auto-closed a gate
  are the population it will fire on — confirm the count is finite and intended before
  arming, per §2.
- **Escalation-predicate satisfiability (§2).** Confirm what the new invariant reports on
  a tree already in its intended final state. If that answer is not zero, redesign before
  arming.
- **Closing-guard literal prediction.** `lint_plan`'s arm-time check (#269) now warns when
  a closing WU's body omits a literal its guard will demand. Read those warnings before
  arming rather than paying for them at dispatch.

## Reflection notes

**Armed 2026-07-27.** All four gate-2 drafts accepted, plus `WU-92`. Gate 1 ran
**6 WUs, 6 attempts, 0 failures, $18.52 against $20.50 planned** — the first gate in this
repo's history whose closing pair passed without a single refusal.

**The review artifact caught my own sketch being wrong, and that is the headline.**
`PLAN.md`'s gate-2 sketch proposed an invariant worded *"if any non-terminal gate
auto-closed and the terminal close never mentions it, escalate."* §4's enumeration shows
that form fires on **6 of 11 correctly-closed features**, every one `status: done`. That is
`[FEAT-2026-0049/G2-CLOSE]` verbatim — a predicate whose correct inputs still trip it. T07
ships a marker-gated form that fires on 0 of 11. I wrote the unsatisfiable version; the
§2 discipline caught it before it was armed, which is what the discipline is for.

**Two facts the enumeration surfaced that I had not considered.** Five of the eleven had
their *terminal* close auto-close as well, so no agent exists on that path to write a
reconciliation — a naive invariant would fire where there is no remedy. And the two
features the broad form spares pass for a *real* reason: their closes genuinely discuss the
auto-closed gate, unprompted, which is evidence the target behaviour is reachable.

**The probe's finding is that a green suite means nothing here.** 1568 tests pass under
both the broad and narrow variants, because no fixture builds a feature with an auto-closed
predecessor *and* a dispatched terminal close. The review says so rather than reading green
as safe, and ran purpose-built negative/positive controls instead
(`verification-discipline.md` §3). T07's ACs then require the three tests the suite lacks.

**Both WUs I suspected of being scope creep are justified.** T05 exists because
`lint_plan.py:35` already does `from .loop import VERDICT_VALUES`, so `loop.py` cannot
import the AC-slicer back — the choice was a second parser copy (which §10 exists to
prevent) or a leaf-module extraction. T08 ships the arm-time predictor *in the same gate as
the guard it predicts*, which is the first time this repo has done that and is the entire
lesson of #265's $99.30.

**One error found in the review, and corrected here.** Its arming checklist states that
`WU-92` "is armed by the driver at the gate boundary, not here." It is not:
`loop.py:4520` collects drafts across **all** units in the gate, terminal close included,
and returns 2. FEAT-2026-0069 hit this exactly — the driver refused with *"1 work unit(s)
are in `draft`"*. `WU-92` armed here.

**Open questions decided.** (1) marker-gating accepted — the alternative blocks correct
closes. (2) terminal auto-close path stays legible-not-collected for gate 2; T06 upgrades
the operator's paragraph to a worklist. (3) **idempotency guard accepted into T06 as AC12**
— the asymmetry is pre-existing, but this WU turns a ~10-line duplication into a
hundred-line one that T07 would then read as real debt; T06's estimate raised $2.00 → $2.50
rather than absorbing the scope silently. (4) 40-criterion cap kept — no silent truncation.
(5) T08 kept.

**Consumer-visible contract changes acknowledged** (question 6) — six items, no removals,
no renames, no migration. The operator signed off on item 1, the behaviour change for
features already on disk (the roadmap row now flips to `done` from any non-`done` status),
and on the semantic caveat attached to item 4: `/accept-hedged-close` rewrites
`verdict: met_locally → met`, so consumers reading `met` as "met every criterion" will see
it on features accepted with open follow-ups.

**On the gate's cost.** Ceremony ran $13.87 against $10.50 (+32%) while the four
substantive WUs came in at $4.64 against $10.00 (−54%). Both expensive guards cleared first
try — `assert_retrospective_gate_section`, which cost FEAT-2026-0069 $4.45, and
`assert_gate_review_exists`, the most expensive guard in the system at $53.11 across 15
fires. One gate is not proof, but it is the first run with #268's documented contracts and
#269's arm-time predictor live, and the refusals those were built to prevent did not occur.

**Infra note.** The gate-1 run was killed mid-T03 by the harness. T03's partial output —
both `SKILL.md` copies and a 150-line test — was discarded rather than adopted, because no
`attempt_outcome` event meant the driver never ran its gates. Re-dispatch cost $1.54 and
produced a verified result. Live instance of #223's infra-kill case.
