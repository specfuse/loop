---
name: groom-backlog
description: "Periodic ritual that reads real repo state and proposes an ordered `.specfuse/agent-policy.yml` `queue:`, so the file the operator authored does not go stale between check-ins. Triggers: `/groom-backlog`, 'groom the backlog', 'update the queue'."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Groom the backlog (interactive, propose-and-confirm)

`.specfuse/agent-policy.yml`'s `queue:` is the operator's own priority
declaration — the order the loop works `planned` features in when nothing
else pins the choice. It goes stale the week it's written: features complete,
issues arrive triaged, blockers clear. This skill is the periodic grooming
session the roadmap row calls "a ten-minute periodic grooming session [that]
keeps the agent autonomous between check-ins." It reads real state, surfaces
queue-hygiene findings and per-candidate trade-offs, proposes a new ordered
queue, and writes `.specfuse/agent-policy.yml` only on your explicit accept.

**Copies the output shape of `/pick-feature`, not its algorithm.** Read
[`../pick-feature/SKILL.md`](../pick-feature/SKILL.md) for the shape this
skill is patterned on: per-candidate trade-offs in prose with a
recommendation, the human picks. The difference: `/pick-feature` selects
**one** feature and flips it `active`; this skill proposes an **ordered
queue** and writes the policy file. This skill does not restate
`/pick-feature`'s hats wholesale — it references that skill for readers who
want the full hat catalogue.

**Run interactively.** The pick list and the accept/reject decision are the
whole point; `claude -p` with redirected stdin has no channel to receive your
accept, so a headless invocation can only produce the proposal and must stop
before writing.

## When to invoke

Periodically — the roadmap row's own framing is roughly weekly or whenever
the operator notices the queue no longer matches reality. Also useful
whenever `validate_agent_policy` on the live `.specfuse/agent-policy.yml`
reports a `WARN: ` or `ERROR: ` finding against the `queue:` key, since those
are exactly the findings this skill surfaces and proposes fixes for.

## Method

### 1. Read, in this order

1. **The current queue.** Call `load_policy()` (from
   `specfuse/loop/agent_policy.py`) to read the live `.specfuse/agent-policy.yml`
   and get its `queue:` list. `load_policy` raises `FileNotFoundError` when the
   file is absent — if so, treat the current queue as empty and say so, rather
   than inventing a starting order.
2. **Queue-drift findings.** Call `validate_agent_policy()` against the same
   file. It cross-checks every `queue:` entry against `.specfuse/roadmap.md`
   and returns `ERROR: ` findings for entries with no roadmap row at all, and
   `WARN: ` findings for entries whose roadmap status is `done` or
   `abandoned`. These are the machine-checkable half of step 2 below.
3. **The roadmap's `planned` / `active` / `blocked` rows.** Read
   `.specfuse/roadmap.md` directly for the rows `validate_agent_policy` does
   not classify as findings — the standing candidate pool this skill ranks,
   and the `blocked` rows whose `**Blocked by.**` detail block may name
   another queued feature.
4. **Open issues carrying a triage marker.** Bugs and features that have been
   through `/triage-issues` and labeled are signal for what's arrived since
   the queue was last groomed — not this skill's to act on directly (that's
   `/triage-issues`'s job), but relevant context for whether the queue order
   still matches reality.
5. **`.specfuse/LEARNINGS.md`.** Durable lessons that bear on ordering —
   the same kind of input `/pick-feature`'s LEARNINGS hat reads.

### 2. Surface queue hygiene first

Present these findings before any trade-off discussion — they are fixes, not
choices:

- **`WARN: ` findings — proposed for removal.** A queue entry whose roadmap
  status is `done` or `abandoned` no longer belongs in a forward-looking
  priority order. Propose dropping it from the new queue; this is a
  near-automatic hygiene fix; the operator can veto in the accept step.
- **`ERROR: ` findings — unresolvable by this skill.** A queue entry with no
  roadmap row at all is not something grooming can safely guess about — it
  might be a typo'd FEAT-ID, a feature whose roadmap row was deleted, or a
  reference to an ID that never existed. Flag it explicitly and leave it for
  the human to fix (correct the roadmap, correct the queue entry, or drop it
  by hand); do not silently drop or silently keep it.
- **`blocked` reorder candidates.** A `blocked` roadmap row whose blocker is
  itself in the proposed queue is a note, not a hygiene fix: pulling the
  blocker forward unblocks it. Surface this as a reorder consideration in
  step 3, not as an automatic move.

### 3. Per-candidate trade-offs, then a recommended order

For each `planned` (and unblocked-if-blocker-clears) candidate, give a short
prose trade-off — the one reason its position in the recommended order is
where it is. Anchor each in whichever of `/pick-feature`'s hats (dependency,
risk, value, cost, LEARNINGS) actually differs for that candidate; don't
force all five onto every entry. Close with one recommended ordered queue and
name the single biggest reason for that ordering, matching `/pick-feature`'s
"Recommendation: #1, because ..." shape.

**Empty queue is a valid outcome, not a failure.** If no `planned` roadmap
rows exist, or the operator's hygiene decisions remove every candidate, the
recommended queue can legitimately be empty. An empty queue means the agent
works bugs only and asks for priorities when it runs out — say this plainly
rather than treating a short list as a problem to solve by padding it.

### 4. Write only on explicit accept

Present the proposed queue (hygiene removals applied, new order shown) and
ask for accept, edit, or reject — mirroring `/pick-feature`'s "which one?"
step. On explicit accept, write the new `queue:` list into
`.specfuse/agent-policy.yml`, preserving every other top-level key
(`version`, `rules`, `budgets`, `escalation`) byte-for-byte unchanged. This
skill writes exactly one file: `.specfuse/agent-policy.yml`, and only that
`queue:` key within it. If the operator asks for an edit, incorporate it and
re-present before writing; if they reject, exit without writing anything.

Emit the RESULT block only when this skill was invoked **non-interactively**
— headless from a calling program that parses the outcome. Its shape is
defined in
[`../../rules/result-contract.md`](../../rules/result-contract.md). Do not
emit it on an interactive run; report to the operator per
[`../../rules/human-output.md`](../../rules/human-output.md) instead. A
headless invocation with no channel to receive an accept can only produce the
proposal, never the write — report `status: blocked` naming that no accept
channel was available.

## What this skill does NOT do

- **No `--auto` mode.** This skill never runs unattended and never writes
  without a human's explicit accept in the current session. An unattended
  process that rewrites the operator's own priority declaration inverts the
  point of the file — `.specfuse/agent-policy.yml`'s `queue:` exists
  precisely because the operator, not the agent, owns priority order. There
  is no flag, config key, or invocation mode that skips the accept step.
- **Does not flip roadmap statuses.** `/pick-feature` owns the `planned` →
  `active` transition; this skill only reads roadmap status, never writes it.
- **Does not create features.** `/draft-feature` owns scaffolding new
  feature folders; this skill only orders what already exists on the
  roadmap.
- **Does not touch `PLAN.md` frontmatter.** `/pick-feature` and
  `/draft-feature` own that surface; this skill never opens a `PLAN.md` for a
  write.
- **Writes only one file.** The only file this skill ever writes is
  `.specfuse/agent-policy.yml`, and only its `queue:` key — `rules:`,
  `budgets:`, and `escalation:` are read but never rewritten by this skill.
- **Key ownership is disjoint: one writer per key block, not per file.**
  This skill owns `queue` in `.specfuse/agent-policy.yml`. It must never
  write `rules`, `budgets`, or `escalation` — those key blocks belong to
  `derive-agent-policy` alone. (The older phrasing, "one writer per config
  file," no longer holds: this skill and `derive-agent-policy` both write
  `.specfuse/agent-policy.yml`, so the invariant that stays true is per key
  block, not per file.)
- **Does not compute a score.** The queue is an operator-authored order, not
  a ranking formula's output — a scoring formula is FEAT-2026-0011's and is
  blocked on ADR-0002. If grooming a queue seems to require a computed score
  rather than a human's ordered judgment, that is out of this skill's scope;
  stop and say so rather than inventing one.

## Escalation framing (binding — `.specfuse/rules/operator-escalation.md`)

Whenever this skill halts for a human decision — an `ERROR: ` finding it
cannot resolve, an ambiguous roadmap reference, a proposed queue the operator
must accept, edit, or reject — present it in the six parts that rule
requires, in plain English, **before** any correlation ID, guard name, or
finding-prefix jargon: what has been done so far; what the issue is about;
what decision is needed and why; why it did not resolve automatically; the
options with their pros and cons; and a recommendation.

Never author the operator's own justification. Where a field records *why a
human decided something* — an accepted reorder, a dropped queue entry — that
text comes from them.

## Version

**v0.1.** First cut of the grooming ritual: queue-hygiene pass plus
trade-off prose plus explicit-accept write. Expected to grow once the loop
has been groomed enough times on a real project's roadmap to know which
reorder heuristics matter and which pick-list shape wears well over repeated
runs.
