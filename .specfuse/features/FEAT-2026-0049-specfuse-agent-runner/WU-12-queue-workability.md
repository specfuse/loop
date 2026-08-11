---
id: FEAT-2026-0049/T12
type: implementation
status: draft
attempts: 0
planned_cost_usd: 5.50
produces:
  - specfuse/agent/queue_read.py
  - tests/test_agent_queue_read.py
model: sonnet
effort: medium
gate_set: code
---

# T12 — the queue-workability classifier and the `rules.features` readers

**Context.** `FEAT-2026-0049/T12`. Gate 4's job is "advance the `queue:` top, and
switch to the next workable item." This unit builds the half that decides what
*workable* means, so the provider (T14) advertises against a rule rather than a
heuristic, and so a queue entry the agent must not act on is classified once, in
one place, instead of being re-derived at three call sites.

Three facts from the shipped code this work is written against:

> `AgentSnapshot` (`specfuse/agent/state.py:90`) already carries
> `queue: tuple` — the ordered `queue:` list read from `agent-policy.yml` — and
> `features: tuple` of `FeatureSummary(feature_id, status, gates)` plus
> `features_errors: dict` keyed by directory name. T02 is the first and only
> reader of `queue:`; nothing has ever matched a queue entry against a feature.
>
> `_select_next` (`specfuse/agent/run.py:192`) ranks a `KIND_FEATURE` item by
> `snapshot.queue.index(item.queue_key)` and escalates any feature item whose
> `queue_key` is not in `queue:`. So every item this gate advertises must carry
> the queue entry verbatim as its `queue_key`.
>
> `rules.features.gate_review` (`human` | `auto`), `rules.features.wip_limit`
> (int >= 1) and the optional per-feature `rules.features.overrides` map are
> **validated by `specfuse/loop/agent_policy.py:371-411` and read by no shipped
> code.** This unit is their first consumer, which is the same shape gate 3's
> OQ-2 drew around monitoring's `diagnose:` dial: a previously inert, validated
> setting becoming behaviour. See `GATE-04-REVIEW.md` OQ-1 and OQ-2.

**Where the readers live, and why not in `agent_policy.py`.** PLAN.md's scope
boundary makes `specfuse/loop/` off-limits with one recorded exception (T01's
`_filelock.py`), and `driver_edit.DRIVER_MODULE_PREFIXES` would halt the driver
for a restart on any WU that touched it. The precedent for an in-package
resolver over the shipped loader is already set: `run._resolve_bugs_preempt`
(`specfuse/agent/run.py:170`) reads `rules.bugs.preempt` through
`agent_policy.load_policy` and applies its own safe default. Both readers here
follow that shape exactly — one module owns the whole `rules.features` section,
so there is no second place to look.

**This module does not re-implement the driver's arm check.** A feature whose
first un-passed gate holds only `draft` work units is still `WORKABLE` here; the
driver answers that question itself by exiting `2` (`specfuse/loop/loop.py:6185`)
and T13 classifies it. Duplicating the arm predicate in the agent is the
second-copy-that-drifts failure `/authoring-work-units` §8 exists to prevent, and
it would cost a real behaviour: the driver's predicate can change without this
module knowing. The price is one cheap driver invocation per unarmed feature per
run, which dispatches nothing.

**Acceptance criteria.**

1. `tests/test_agent_queue_read.py::TestQueueWorkability::test_queue_entry_without_a_feature_folder_needs_drafting`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_queue_read.TestQueueWorkability.test_queue_entry_without_a_feature_folder_needs_drafting`.
2. `specfuse/agent/queue_read.py` exposes five disposition constants —
   `DISPOSITION_WORKABLE`, `DISPOSITION_NEEDS_DRAFTING`, `DISPOSITION_BLOCKED`,
   `DISPOSITION_DONE`, `DISPOSITION_UNREADABLE` — and
   `classify_queue_entry(entry, features, features_errors)` returning exactly one
   of them, in this precedence order: a key in `features_errors` whose directory
   name starts with the entry (the folder exists but its `PLAN.md` did not parse,
   so its `feature_id` is unreadable by construction) → `UNREADABLE`; no
   `FeatureSummary` whose `feature_id` equals the entry → `NEEDS_DRAFTING`; PLAN
   `status` of `blocked` or `deferred` → `BLOCKED`; `done` or `abandoned` →
   `DONE`; `active` or `planned` → `WORKABLE`. Those six are the whole
   vocabulary (`lint_plan.VALID_FEATURE_STATUS`, `lint_plan.py:53`); a value
   outside it is `UNREADABLE`, not silently workable. `planned` is workable
   because a folder already exists — `/pick-feature`'s flip to `active` is
   bookkeeping the driver does not require to advance the gate.
   `UNREADABLE` is checked first because an
   unparseable folder is indistinguishable from an absent one by `feature_id`
   alone, and escalating it as "needs drafting" would tell the operator to draft
   a feature that already exists.
3. The same test passes after this WU's edits.
4. `select_workable(queue, features, features_errors, *, wip_limit)` returns
   `(workable, needs_attention)`: the workable entries in `queue:` order, capped
   at `wip_limit`, and every non-`WORKABLE`, non-`DONE` entry with its
   disposition. A `DONE` entry appears in neither list and **consumes no
   `wip_limit` slot**; a test asserts `wip_limit=1` over a queue of
   `[done, workable, workable]` returns exactly the first workable entry.
   **OQ-1.**
5. `resolve_wip_limit(policy_path)` returns an `int >= 1` and
   `resolve_gate_review(policy_path, feature_id)` returns `"human"` or `"auto"`,
   honouring `rules.features.overrides[feature_id]` when present. Both use the
   safe-default shape of `run._resolve_bugs_preempt` (`run.py:170`): an absent
   policy file, an absent key, or a wrong-typed value resolves to the
   conservative default — `1` and `"human"` — rather than raising. A test covers
   each of those three absent/wrong cases per reader, and one asserts an
   override wins over the section default.
6. `specfuse/agent/state.py` exposes `read_feature_summaries` as a public name
   for what is today `_read_features` (`state.py:237`), with `_read_features`
   retained as an alias so no existing caller changes. `gather_snapshot`'s
   behaviour is unchanged. A test asserts
   `state.read_feature_summaries is state._read_features`.
7. The module performs no write, issues no `gh` call, and reads no work-unit
   file: a test asserts an injected runner receives nothing, and a structural
   test asserts `queue_read.py`'s source contains neither `WU-` nor
   `read_frontmatter` — the mechanical form of "the arm check is the driver's,
   not ours".

**Do not touch.** `specfuse/loop/` entirely — `agent_policy.py` is imported and
called, never edited; a needed change there is a plan change to escalate, not a
WU, and it would halt the driver for a restart. `specfuse/monitor/` entirely.
`specfuse/agent/run.py`, `specfuse/agent/budget.py`, `specfuse/agent/
monitoring_read.py`, and every module under `specfuse/agent/providers/`.
`specfuse/agent/state.py` is edited **only** for criterion 6's rename-plus-alias;
`AgentSnapshot`'s fields, `gather_snapshot`'s signature, and every `gh` call it
issues stay exactly as they are. The sibling gate-4 WU files (`WU-13`, `WU-14`)
and the modules they create. `.specfuse/agent-policy.yml` — this unit reads the
dials, it does not set them. The driver owns all git; this session edits files
only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "from specfuse.agent.queue_read import DISPOSITION_WORKABLE, DISPOSITION_NEEDS_DRAFTING, DISPOSITION_BLOCKED, DISPOSITION_DONE, DISPOSITION_UNREADABLE, classify_queue_entry, select_workable, resolve_wip_limit, resolve_gate_review"`
and
`python3 -c "from specfuse.agent.state import read_feature_summaries, _read_features; assert read_feature_summaries is _read_features"`.

**Escalation triggers.** If classifying a queue entry turns out to need a fact
`FeatureSummary` does not carry — a work-unit status, an attempt count, a gate's
`cost_budget_usd` — stop and name the field rather than widening
`AgentSnapshot`: T02's snapshot is gate 1's shipped surface and changing its
shape is a plan change, not a gate-4 work unit. If honouring `wip_limit` or
`gate_review` turns out to require a new `agent-policy.yml` key of any shape,
stop and say so rather than minting one; that is the boundary T05's and T09's
escalation triggers both drew, and OQ-1/OQ-2 exist to let the operator answer it
first. If promoting `_read_features` breaks any existing caller, stop rather than
updating the caller — that is a sign the rename is not the cheap one this
criterion assumes.
