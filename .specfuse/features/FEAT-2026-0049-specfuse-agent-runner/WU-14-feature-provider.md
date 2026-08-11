---
id: FEAT-2026-0049/T14
type: implementation
status: pending
attempts: 0
planned_cost_usd: 6.50
produces:
  - specfuse/agent/providers/feature.py
  - tests/test_agent_provider_feature.py
model: sonnet
effort: medium
gate_set: code
---

# T14 — the feature provider: advance the queue top, escalate, switch

**Context.** `FEAT-2026-0049/T14`. The feature's last action class, and the one
the roadmap goal names first. T12 decides which queue entries are workable; T13
invokes `specfuse run` as a subprocess and names the halt. This unit is the
provider that puts them behind `advertise` / `execute` / `reconcile` and
registers itself, exactly as the five providers before it did.

Two facts from the shipped conductor this work is written against:

> `run_agent` (`specfuse/agent/run.py:252`) gathers **one** snapshot before the
> loop starts and passes that same value to `advertise()` on every iteration.
> Five providers already read live state inside `advertise` for this reason
> (`providers/answers.py`, both findings providers); this unit is the sixth, and
> the one where it matters most — a feature's gate status changes *because of
> this provider's own execute*.
>
> `_select_next` (`run.py:192`) skips any item whose `item_id` is already in
> `handled_ids` (`run.py:213`). A feature advertised under a stable id can
> therefore be advanced at most once per run, whatever the caps say.

**The item id carries the advance point.** `item_id` is
`feature-<FEAT-ID>-g<first un-passed gate>` for a workable entry. After the
driver advances gate 3 and the live-arm flips gate 4 to `pending`, the next
iteration advertises `feature-FEAT-2026-0049-g4` — a new id, so the run keeps
advancing the same feature until it halts, drains, or a cap fires at an item
boundary (D3). Entries that are *not* workable use a stable
`feature-<FEAT-ID>` with no gate suffix, because `emit_escalation` is idempotent
per correlation id (`specfuse/loop/escalation.py:185`) and a stable id is what
stops a second run filing a duplicate needs-human issue.

**Two escalation categories get their first consumer here.** `escalation.py:21`
declares `drafting-needed` and `gate-review` in `CATEGORY_LABELS`; every shipped
provider uses `blocked-wu` and nothing has ever used those two. They are the
right ones and the WU uses them rather than minting a category.

**The driver files no GitHub issue when a work unit blocks** — it writes the
`human_escalation` event and the WU's frontmatter and stops (`loop.py:7242`,
and no `emit_escalation` call exists anywhere in `loop.py`). So a
`HALT_BLOCKED` outcome must carry an `EscalationPayload`; this is the opposite
of `providers/bugs.py:89-93`, where the lane files its own and the provider
deliberately leaves `escalation=None`. Getting this backwards means either a
silent block or a duplicate issue.

**Drafting a feature is out of scope** — PLAN.md § "Scope boundary". A
drafting-needed queue top escalates; async drafting is FEAT-2026-0050, which
lists this feature as its blocker. No code path in this unit may invoke
`/draft-feature`.

**Acceptance criteria.**

1. `tests/test_agent_provider_feature.py::TestFeatureProvider::test_awaiting_review_escalates_and_the_next_queue_entry_is_advertised`
   exists and **fails on HEAD before this WU runs** (the file does not yet
   exist). Run scoped:
   `python3 -m unittest tests.test_agent_provider_feature.TestFeatureProvider.test_awaiting_review_escalates_and_the_next_queue_entry_is_advertised`.
2. `specfuse/agent/providers/feature.py` defines a provider whose `advertise`
   returns one `KIND_FEATURE` `ActionItem` per entry `queue_read.select_workable`
   returns — workable entries and needs-attention entries both — with
   `queue_key` set to the queue entry verbatim so `_select_next` can rank it, and
   `item_id` shaped as described above. `advertise` re-reads feature state
   through `state.read_feature_summaries` rather than trusting
   `snapshot.features`, and a test asserts that a feature whose gate advanced
   between two `advertise` calls is re-advertised under a new `item_id`.
3. The same test passes after this WU's edits.
4. `execute` invokes `driver_invoke.advance_feature` for `WORKABLE` items **only**
   and maps each halt class to one row of this table — one test per row, six
   tests:

   | Halt | Outcome | Escalation |
   |---|---|---|
   | `HALT_ADVANCED` | `completed` | none |
   | `HALT_FEATURE_DONE` | `completed` | none |
   | `HALT_AWAITING_REVIEW` | per `gate_review` — see criterion 6 | `gate-review` under `human` |
   | `HALT_NOT_ARMED` | `escalated` | `gate-review` — a human runs `/arm-gate` |
   | `HALT_BLOCKED` | `escalated` | `blocked-wu`, carrying the blocked WU id and reason |
   | `HALT_DRIVER_ERROR` | `escalated` | `blocked-wu`, carrying the stderr detail |

   A test asserts a `NEEDS_DRAFTING` item reaches **no** driver invocation at
   all: the injected runner sees zero subprocesses for it.
5. A `NEEDS_DRAFTING` entry escalates with `category="drafting-needed"` and a
   payload whose body names FEAT-2026-0050 as where async drafting lives. A test
   asserts the category and asserts the injected runner receives no invocation
   containing `draft-feature`. `BLOCKED` and `UNREADABLE` entries escalate with
   `blocked-wu` and their disposition in the detail.
6. `rules.features.gate_review` decides what an `awaiting_review` halt does, read
   through `queue_read.resolve_gate_review(policy_path, feature_id)` and never
   re-spelled locally: under `human` the item is `escalated` with a
   `gate-review` payload; under `auto` it is `completed`, with the halt named in
   the outcome detail and **no issue filed** (`escalation=None`) — the agent
   cannot arm a gate, so filing nothing is the only honest `auto` behaviour.
   `rules.features.wip_limit` is read through
   `queue_read.resolve_wip_limit(policy_path)` and passed to `select_workable`.
   One test per dial. **OQ-1, OQ-2.**
7. The provider is registered in `default_providers()` (`run.py:385`) and
   constructed with `repo`, `runner`, `policy_path` and `features_root` the same
   way the five existing providers are; a test asserts it appears in the returned
   tuple when `repo` is given. The provider itself issues no `git` command and no
   mutating `gh` call: a test asserts the injected runner receives only the
   driver invocation. **OQ-3.**
8. `reconcile` returns `None` and issues no call — a test asserts it. This is the
   sixth provider to implement the verb as a no-op; `GATE-04-REVIEW.md` § "The
   `reconcile` verdict" records that the terminal close is to report the verb
   never earned its place rather than inventing work for it here.

**Do not touch.** `specfuse/loop/` entirely — `escalation.py` and
`agent_policy.py` are imported and called, never edited; the driver is invoked
as a subprocess through T13 and never imported. `specfuse/monitor/` entirely.
`specfuse/agent/queue_read.py` and `specfuse/agent/driver_invoke.py` — T12's and
T13's modules, consumed as they shipped; a needed change in either is a signal
the seam was drafted wrong, which is an escalation, not an edit here.
`specfuse/agent/state.py`, `budget.py`, `monitoring_read.py`, and the five
existing modules under `specfuse/agent/providers/`. `specfuse/agent/run.py` is
edited **only** to add this provider's construction inside `default_providers`;
`_select_next`'s ranking, the kind constants, the dataclasses and `main()`'s
flags all stay as they are — `KIND_FEATURE` already ranks at tier 1 and needs no
change. `WU-12` and `WU-13`. Any `.specfuse/features/` folder other than
fixtures this unit's tests create under a temporary directory, and
`.specfuse/agent-policy.yml` — the dials are read, never set. The driver owns all
git; this session edits files only and runs no `git` command.

**Verification.** The `code` gate set from `.specfuse/verification.yml`. Plus §9
symbol checks:
`python3 -c "import specfuse.agent.providers.feature as f; print(f)"`
and the registration check:
`python3 -c "from specfuse.agent.run import default_providers; print([type(p).__name__ for p in default_providers(repo='owner/repo')])"`
(the feature provider's class name must appear in the printed list).

**Escalation triggers.** If mapping any halt class to an outcome turns out to
need a seventh class, or needs `driver_invoke` to expose something it does not,
stop and name it rather than widening T13's module from here — a seam that
needed changing by its own consumer is worth a human reading before it lands. If
honouring `gate_review: auto` appears to require the agent to arm a gate — to
flip a draft work unit to `pending`, or to write a gate's `status` — **stop**:
arming is `/arm-gate`'s job and taking it on is the same scope grab as drafting.
If the only way to prove a row of criterion 4's table is to run a real
`specfuse run` against a real feature folder in this repository, stop rather than
doing it: that runs the loop inside the loop, and the fixture-level proof is what
this gate is scoped to. If the queue top at implementation time is this feature
itself — `.specfuse/agent-policy.yml`'s `queue:` reads `FEAT-2026-0049` today —
that is a fixture-design hazard, not a reason to edit the policy file: build the
tests against temporary fixture folders and leave the live policy alone.
