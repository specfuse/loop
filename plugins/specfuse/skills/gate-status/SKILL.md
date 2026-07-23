---
name: gate-status
description: "Report where the loop stands on the active feature. Walks the current gate's WU statuses, reads events.jsonl and per-attempt notes for blocked units, and synthesizes a structured diagnosis \u2014 what's blocked, likely root cause, options, and a recommended next action. Read-only. Run after the loop driver halts on a blocked WU and you're coming back to figure out what to do."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Gate status (interactive, diagnostic)

This skill is the answer to "where do we stand?" after the loop driver
halts on a blocked WU and you come back to a Claude session later. It
reads the canonical files (PLAN.md, GATE-NN.md, WU frontmatter,
events.jsonl, the per-attempt notes under `work/`) and synthesizes a
structured report: which WUs are done / blocked / pending, and for each
blocked WU **what's blocked, likely root cause, options, recommended
action**.

The skill is read-only. It does NOT flip status, edit WUs, fix bugs,
insert hygiene WUs, or run the loop. Those are decisions for you;
this skill exists to make the decision faster and better-informed.

**Run interactively.** If the report surfaces ambiguity (e.g. two
blocked WUs with different recommended actions), the skill may ask a
single clarifying question before recommending. `claude -p` with stdin
redirected reduces this to a one-shot report.

## Hard rules

- **Read-only.** No writes, no commits, no status flips. The skill
  produces text; you act on it.
- **Trace every claim to a file.** Every "blocked because X" must
  cite the specific events.jsonl entry or per-attempt note that says
  so. No inferred-from-vibes diagnoses.
- **Recommend, don't decide.** For each blocked WU, surface options
  with their tradeoffs and a recommendation. The user picks.

## When to invoke

When the loop driver has just halted with `Gate halted: work unit(s)
need human attention`, or any time you come back to a project after a
gap and need a fast read on what state the active feature is in.

## Method

### 1. Locate the active feature

Read `.specfuse/roadmap.md` for rows with `status: active`. If there's
exactly one, that's the target. If zero, report "no active feature"
and stop. If more than one, ask the user which to inspect (or report
all of them at a high level).

**`deferred` and `blocked` features.** If the only candidate (or the one the
user names) is `deferred` or `blocked`, don't report "no active feature" as if
it were missing. Report it as **parked**, and distinguish the two:

- `deferred` — voluntarily parked pending an external decision/dependency, with
  no named blocker (the next gate's arm-gate condition usually spells out what
  it's waiting on).
- `blocked` — waiting on a *named* unmet dependency: an ADR awaiting approval or
  an upstream feature, linked from its roadmap `**Blocked by.**` block. Read
  that block to name exactly what it waits on.

Both are non-dispatchable but resumable — read the PLAN/GATE state anyway. A
human flips it back to `active` when the blocker clears (for `blocked`,
`/block-feature <id> --unblock`); the loop does not auto-resume either.

### 2. Read the canonical state files

For the active feature folder `.specfuse/features/FEAT-YYYY-NNNN-<slug>/`:

- **`PLAN.md`** — feature frontmatter + gates graph. Determines the
  current gate (first one whose `status != passed`).
- **`GATE-NN.md`** — current gate's status (`open`, `awaiting_review`)
  and optional `cost_budget_usd` field. If `cost_budget_usd` is set,
  compare it against the sum of `cost_usd` + `cumulative_cost_usd`
  across the gate's `done` WUs to surface budget headroom or overshoot.
- **WU files** under the gate's `work_units` graph — frontmatter
  `status`, `attempts`, and bodies. Group by status:
  `done`, `in_progress`, `blocked_human`, `pending`, `ready`, `draft`.

  **Attempts/cost caveat (#199):** frontmatter `attempts` and `cost_usd`
  are PER-DISPATCH-CYCLE — a re-arm resets `attempts` to 0 and folds
  prior cost into `cumulative_cost_usd` / prior attempts into
  `cumulative_attempts`. Never quote frontmatter `attempts`/`cost_usd`
  as a WU's lifetime totals (FEAT-2026-0049/WU-06 read as 1 attempt /
  $2.75 when the true totals were 9 / $30.29). For any WU with
  `re_arm_count > 0`, compute lifetime numbers from `events.jsonl`
  (`attempt_outcome` count and `cost_usd` sum per WU, or the
  `task_completed` payload's `attempts_lifetime` /
  `cumulative_cost_usd` fields on drivers >= 0.3.21) — events.jsonl is
  the source of truth; frontmatter cumulative fields are the fallback.
- **`events.jsonl`** — most recent `task_started` / `task_completed` /
  `human_escalation` / `gate_reached` entries. The
  `human_escalation` entries carry `reason` and `blocked_reason` for
  the blocked WUs (post the Bug 1 fix in bcc9bee, these are durable).
  A `human_escalation` with `reason: gate_budget_exceeded` means the
  driver halted the gate to `awaiting_review` before the named WU's
  dispatch because the cumulative cost reached `cost_budget_usd`.
- **`work/<WU>/attempt-*.md`** — verify-output evidence for failed
  attempts on spinning-escalated WUs (also durable post-bcc9bee).

### 3. Build the WU-state table

A compact picture, oriented by the current gate:

```
FEAT-YYYY-NNNN ("title") — Gate N [<gate status>]
  ✓ done           T01, T02
  ⏸ blocked_human  T03
  · pending        T04, G1-RETRO, G1-LESSONS, G1-DOCS, G1-PLAN
```

If there's been driver-bookkeeping vs file-state drift (which Bug 1
caused before bcc9bee), name it explicitly: "T01 frontmatter says
`in_progress` but the commit on the feature branch landed cleanly —
likely a pre-bcc9bee state-flip-lost bug; flip to `done` manually."

### 4. For each blocked_human WU, synthesize the diagnosis

This is the load-bearing part. For each blocked WU, produce:

#### What's blocked

The WU's ID, title, and which gate it sits in. Quote the agent's
`blocked_reason` verbatim from the most recent `human_escalation`
event for that WU. If the block came from spinning (3 failed
attempts), quote the last attempt's verify output from the `work/`
notes.

#### Likely root cause

A short interpretation drawn from the evidence:

- **Pre-existing bug in an out-of-scope path** — the agent's reason
  names a file/module/symbol outside the WU's "Do not touch" boundary,
  and the verify output shows it failing for a reason unrelated to
  the WU's own work. (Example from the live run: terraform validate
  failing on `automatic_upgrade_channel` in a shared AKS module the
  WU was forbidden from touching.)
- **Missing dependency** — the agent's reason names something that
  doesn't exist yet (e.g. "no router module exists").
- **Spec ambiguity** — the WU's acceptance criteria are
  under-specified or the surfaces it touches are ambiguous.
- **Verification command unsuitable** — the gate command runs the
  whole suite when a scoped command would suffice; or the verify
  output shows a flaky/environmental failure (network, missing
  service).
- **Genuine bug in the WU's own work** (when spinning) — the agent
  tried three times and produced different failures each attempt;
  the WU's scope or acceptance criteria may be misshapen.

Pick the category that best fits the evidence; flag uncertainty
honestly. Don't invent a root cause when the evidence is thin —
write "evidence too thin to attribute; needs human inspection of
<file>" instead.

#### Options

Surface the realistic next moves with their trade-offs. The
methodology offers a small named set; this skill knows them:

- **Insert a hygiene WU** earlier in the gate (or as a precursor),
  scoped narrowly to fix the pre-existing issue. The blocked WU
  then re-runs unmodified. See
  `.specfuse/skills/authoring-work-units/SKILL.md` §7 for the
  hygiene-WU pattern. *Best when* the block is a pre-existing
  out-of-scope bug.
- **Widen the WU's scope** — edit its Do-not-touch / Acceptance
  criteria to permit the cross-cutting fix. Methodology-eroding;
  surface as an option but flag the cost.
- **Fix manually out-of-loop and continue** — make the fix outside
  the loop, then mark the blocked WU done by hand. Methodology-
  eroding (silent drift); surface as an option but flag.
- **Rewrite the WU's acceptance criteria** — when the block is
  spec-ambiguity. Requires editing the WU file before re-arming.
- **Abandon the WU** — mark `status: abandoned` and remove from the
  gate's graph. Appropriate when the WU turned out not to be needed.
- **Add a new substantive WU** ahead of this one — when a missing
  dependency means a real new piece of work is required first.

#### Recommended action

One opinionated default, anchored in the methodology. For the
pre-existing-out-of-scope-bug case, the recommendation is **always**
the hygiene-WU pattern — the other two options exist but the
methodology's invariant ("every committed state change traces to a
dispatched-and-verified WU") survives only that path.

State the recommendation in a single sentence with the specific WU
ID it would insert ("Add `FEAT-XXXX/T1H` titled '<fix>' as a
precursor; flip current T02 back to `pending`; re-run the loop.").

#### Per-attempt outcomes

Source: `events.jsonl` for the active feature. Filter to events where
`event_type == "attempt_outcome"` and `correlation_id` matches the
blocked WU's id. Rows must come from that file only — the skill MUST
NOT infer per-attempt outcomes from any other source.

Render a table in event-file order, one row per matching event:

```
attempt | outcome | failure_class | failure_signature | duration (s) | cost ($)
```

- `failure_class` and `failure_signature` show `-` when null or absent.
- `cost` rendered to 4 decimal places (e.g. `0.0031`).
- `duration` rendered to 3 decimal places (e.g. `12.345`).

After the table, quote the `failure_excerpt` field verbatim for the
**latest failing attempt** (the one immediately preceding the
`human_escalation` event). Quoting only the latest excerpt keeps the
report scannable; earlier excerpts are available in `events.jsonl` for
deeper inspection.

If NO `attempt_outcome` events exist for the WU in `events.jsonl`,
print:

```
(no per-attempt events; legacy feature — see human_escalation above)
```

Do not raise or stop on missing events.

#### Re-arm history

Source: the blocked WU's frontmatter fields `re_arm_count` and
`re_arm_history`. These are written by the driver's re-arm operation
(FEAT-2026-0016 gate 1).

- If `re_arm_count` is absent, treat as `0`.
- If `re_arm_history` is absent, treat as an empty list.

**When `re_arm_count == 0`:** print:

```
re_arm_count: 0 — never re-armed
```

Stop the subsection.

**When `re_arm_count > 0`:** print:

```
re_arm_count: <N>  latest re-arm reason: "<reason>"
```

where `<reason>` is `re_arm_history[-1].reason` quoted verbatim. If
`re_arm_history[-1]` has a `timestamp` field, also print it on the
same line:

```
re_arm_count: <N>  latest re-arm reason: "<reason>"  (re-armed at <timestamp>)
```

### 5. If nothing is blocked but the gate hasn't finished

Report the ready WUs (those whose `depends_on` are all done and
status is `pending`). Tell the user the gate would continue if they
re-ran the loop.

### 6. End with the RESULT block

Per [`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means the report was produced and shown.
`status: blocked` is reserved for the case where the canonical files
themselves are missing or corrupt enough that the report can't be
assembled (e.g. no `PLAN.md`, no `events.jsonl` for a feature whose
WUs have non-pending statuses).

## What this skill does NOT do

- **Does not write or commit anything.** Read-only.
- **Does not insert hygiene WUs, edit WU bodies, or flip statuses.**
  Recommends — the user (or `/draft-feature` / their editor) acts.
- **Does not re-run the loop.** That's `python3
  .specfuse/scripts/loop.py`; the skill names it in the recommended
  action when relevant.
- **Does not diagnose codebase bugs.** It reads what the agent and
  the verify-output said and quotes them; it doesn't go investigate
  whether the bug the agent named is actually a bug.

## Version

**v0.3.** Added `#### Per-attempt outcomes` and `#### Re-arm history`
subsections under §4. Per-attempt table reads `attempt_outcome` events
from `events.jsonl` (correlation-id-filtered); re-arm history reads
`re_arm_count` + `re_arm_history` from WU frontmatter. Both contracts
locked at v1 by FEAT-2026-0016 gate 1 (T01 emits, T02 writes
frontmatter). Legacy features with no `attempt_outcome` records
degrade gracefully to a note rather than failing.

**v0.2.** Added budget-brake fields to §2: `cost_budget_usd` in GATE
files and the `gate_budget_exceeded` escalation event in `events.jsonl`
(landed in `FEAT-2026-0007/T07`). v0.1 established root-cause categories
and option set. Shared methodology craft (loop is near-term author, like
the addendum).
