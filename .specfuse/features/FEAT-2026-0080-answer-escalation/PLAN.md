---
feature_id: FEAT-2026-0080
title: Operator-answered escalations — guidance that survives into the next agent run
slug: answer-escalation
branch: feat/FEAT-2026-0080-answer-escalation
roadmap_goal: A human can work the needs-human queue one issue at a time, leave guidance the next agent run actually reads, and unpark the issue — without ever triggering a fix themselves.
autonomy_default: auto
status: active
planned_cost_usd: 16.00
---

# Plan: Operator-answered escalations

The agent files a `needs-human` issue when it cannot proceed, and that issue is
where the work stops permanently. `AnsweredEscalationProvider` reads an operator's
numbered reply and posts an acknowledgment, but its own docstring is explicit that
it "does not carry out the chosen option" and leaves `NEEDS_HUMAN_LABEL` in place
"until whichever future provider executes the option removes it." No such provider
exists, and `BugsProvider.advertise` skips every issue carrying `needs-human` or
`blocked-wu`, so an answered escalation is acknowledged and then parked forever.
Observed 2026-08-12: eight open `needs-human` issues, every one also `blocked-wu`.

This feature does **not** build that provider. It builds the human half, because
the human half is what the queue actually needs and because the autonomous half
raises a question — can an agent safely act on a free-text answer unattended —
that is better decided with evidence from real use than at draft time.

So: one human-invoked skill that reads a parked escalation, explains in plain
English what stopped the agent, and offers four dispositions. It triggers no fix
and no retry. Its entire product is **guidance the next run reads** plus the label
release that lets that run happen at all.

## Decisions taken at draft time

**D1 — human-invoked only; no agent-side execution.** `AnsweredEscalationProvider`
is untouched and keeps acknowledging exactly as it does now. The scope boundary
below states this as an explicit non-goal rather than a "later" — an agent acting
unattended on a prose answer is a separate decision, not a deferred slice of this
one.

**D2 — the disposition is "hand off to the skill that owns this category", not a
special case per category.** Every `CATEGORY_LABELS` value already has an owning
skill, and the payloads already name them in prose: the `gate-review` escalation
`FeatureProvider` builds literally offers "Run /arm-gate" as option 1
(`specfuse/agent/providers/feature.py:228`). The skill routes to that owner rather
than reimplementing it.

| Category | Owning skill |
|---|---|
| `gate-review` | `/arm-gate` |
| `drafting-needed` | `/draft-feature` |
| `blocked-wu` | `/unblock-wu` (work-unit level) or `/roadmap-add` (promote) |
| `triage-question` | `/triage-issues` |
| `merge-approval` | merged by hand |

Handing off to `/arm-gate` from inside a human-invoked, interactive skill is the
human performing the review, not the agent automating it. The distinction is the
invoker, not the callee.

**D3 — write order: guidance comment first, label release second.** Follows
`[FEAT-2026-0045/G1-CLOSE/declare-precedence-between-redundant-records]`. The
comment is the authoritative record; the label is a projection of it. A failed
release leaves an issue correctly answered and merely still-parked — recoverable
and visible. The reverse leaves it unparked with no guidance, which is the state
that produced this feature.

**D4 — `skip` writes nothing at all.** Not a comment, not a label edit. An
operator who defers an issue must leave no trace that a later reader could mistake
for a decision.

**D5 — promotion to the roadmap is a first-class disposition.** It is already
happening by hand: FEAT-2026-0079's own roadmap entry records "Promoted from #1183
after the bug lane refused it three times." This feature formalizes a path the
operator already walks.

## Known adjacent defect, deliberately not fixed here

A `gate-review` escalation records on a GitHub issue what `.specfuse/` already
owns — `/attention` reads `awaiting_review` straight from the gate files, so the
issue is a second record of the same fact. That is pre-existing behaviour and
fixing it would mean changing what `FeatureProvider` escalates, which this feature
does not touch. Noted so the next reader does not rediscover it as new.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -rn "remove_label\|remove-label" specfuse/`
- **Verdict:** no existing mechanism, building new. The only hits are
  `specfuse/loop/gh_backend.py:51` and `:86`, which remove `state:ready` and
  `state:in-progress` — feature lifecycle labels, not the human-owned set.

- **Grep command run:** `grep -rn "NEEDS_HUMAN_LABEL" specfuse/`
- **Verdict:** no existing mechanism, building new. Three write sites
  (`escalation.py:163`, `:233`, `:338`) and zero remove sites. The codebase states
  the invariant outright at `specfuse/loop/notify_sla.py:22` — "`NEEDS_HUMAN_LABEL`,
  which is never removed".

- **Grep command run:** `grep -n "gh issue view\|comment" .specfuse/skills/fix-bug/SKILL.md`
- **Verdict:** found a partial mechanism, extending it. `/fix-bug` Step 1 already
  instructs "Read: title, labels, body, comments" (line 66) — the intent exists.
  The command it names one line above, `gh issue view <issue-number>`, does not
  return comment bodies. Verified live against issue #1872: default output ends at
  the issue body; `--comments` is what surfaces them. T02 extends the existing
  instruction rather than adding a new one.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

`n/a — no severity flip.` This feature raises no check to `ERROR`, flips no
`WARNING` to blocking, and asserts no "zero issues" close predicate.

## Scope boundary — explicitly OUT

- **Agent-side autonomous execution of an answer.** `AnsweredEscalationProvider`
  keeps acknowledging and nothing more. Not deferred — excluded.
- **Automating `/arm-gate`, `/draft-feature`, or any owning skill.** The skill
  routes a human to them; it never runs one unattended.
- **Changing the shape of escalation payload options.** `EscalationPayload.options`
  stays `(label, pros, cons)` tuples. No machine-readable disposition field.
- **Any change to `BugsProvider` selection logic**, including
  `_HUMAN_OWNED_LABELS`.
- **Closing the loop on `merge-approval`.** The skill surfaces it and routes to a
  human merge; it opens no PR and merges nothing.

## Verification the loop cannot perform

T01's skill drives `gh` at runtime, but its own acceptance is structural — the
tests assert on `SKILL.md` prose, not on a live API round-trip. Per
`[FEAT-2026-0046/G1-CLOSE]` this WU is priced for wiring a seam, not for
negotiating with GitHub, and the close must name what the stub declined to ask:
whether the guidance comment's marker survives a real `gh issue comment` write and
is found by a subsequent `gh issue view --comments`. The `gate-review` branch is
additionally unverifiable right now — the repository has zero open `gate-review`
escalations and zero `awaiting_review` gates, so that route ships fixture-tested
only. Both belong in the close's `## What the loop did NOT verify` with the exact
re-run that settles them.

## Task graph

```yaml
# Single-gate feature (docs/methodology.md §6 "Ceremony proportionality"):
# 2 substantive WUs ≤ 4, so gate 1 is terminal and carries one `close` WU —
# no close-intermediate, no plan-next.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0080/T01
        file: WU-01-answer-escalation-skill.md
        depends_on: []
      - id: FEAT-2026-0080/T02
        file: WU-02-fix-bug-reads-comments.md
        depends_on: []
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0080/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0080/T01, FEAT-2026-0080/T02]
```

## Notes

- T01 and T02 are independent: they touch disjoint files (a new skill folder
  versus `fix-bug/SKILL.md`) and neither reads the other's output. Sequencing them
  would buy nothing.
- Both WUs edit a skill in two places — the canonical `plugins/specfuse/skills/`
  copy and the vendored `.specfuse/skills/` copy — which are byte-identical by
  convention and asserted so by existing tests.
- Dependencies live here, not in WU frontmatter.
