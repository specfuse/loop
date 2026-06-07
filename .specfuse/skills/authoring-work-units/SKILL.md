---
name: authoring-work-units
description: How to write a single Specfuse work unit that won't block spuriously or pass hollowly. Reference for humans authoring WUs in the loop, and for reviewing PM-agent drafts in the orchestrator. Lean; eight evidence-backed rules, one per spot a real run has tripped on.
---

# Authoring a work unit

This skill teaches how to fill the five-section WU contract
(`.specfuse/templates/WU.template.md`, methodology §4) well — section by
section, plus one cross-cutting sizing rule.

**The bar.** Every rule below names a concrete failure mode it prevents. If
a rule can't name the failure, it's filler and was cut. `"Write clear
acceptance criteria"` is filler; `"Scope acceptance-criteria checks to the
feature's own footprint — repo-wide greps trip on pre-existing unrelated
state"` is the right shape. Apply the same bar when adding rules.

This is shared methodology craft — works for the loop (single-repo) and the
orchestrator (multi-repo). The loop is the near-term author, like the
architecture addendum; orchestrator-side adoption is the fold-in.

---

## 1. Context — write for a cold session

The body below the frontmatter is **all a fresh, memoryless session gets**.

- Name the correlation ID (`FEAT-YYYY-NNNN/TNN`) and the grounding files
  (specs, docs, target paths) the session needs to orient.
- **Reference** binding rules under `.specfuse/rules/` — never restate.
  Restated rules drift from source.
- Enough to orient, not a wall. If you're summarizing the feature spec,
  the WU is misscoped — link it instead.

> *Prevents:* a fresh session thrashing for lack of grounding, or acting
> on a restated rule that has since changed at source.

## 2. Acceptance criteria — scope to the feature's own footprint

Criteria that grep or scan the **whole repo** trip on pre-existing,
unrelated state and cause a correct-but-unwanted block. Bound every check
to the feature's own footprint: its slug, the paths it creates or edits,
the symbols it introduces, the files in `generated_surfaces` /
`files_changed`.

- Phrase each criterion as an **objective statement a reviewer can judge
  and a gate can mechanically check** — not an intention. (`"GET /health
  returns 200 with JSON {status, version}"` ✓ — `"endpoint is
  well-tested"` ✗.)
- Avoid compound criteria (`"X and also Y"`). Split so a single failure
  attributes to a single line.
- A criterion that needs inspecting unrelated parts of the repo is the
  wrong shape; narrow the scope, or move the check to a repo-wide
  hygiene WU / the `code` gate set.

> *Prevents:* a throwaway "grep returns zero hits" criterion blocking on a
> stale roadmap pointer the WU never touched (real failure logged in
> `.specfuse/LEARNINGS.md` under `[meta/first-live-use]`); also prevents
> reviewers waving through subjective criteria that hide unmet
> requirements.

## 3. Do not touch — name real paths, AND name what the WU produces

Generic `"don't touch other files"` is one an agent will cross. List the
actual boundaries this WU might brush against:

- The **generated directories** in this repo (`_generated/`, `gen-src/`,
  or whatever your repo declares).
- The **specific sibling-WU files** in this gate, by path, if the gate's
  graph is already laid out and the WU's work is adjacent to theirs.
- **Secrets** files (`.env`, `*.pem`, `*.key`, `credentials.json`) and
  `.git/` internals.
- **The driver owns all git.** The session edits files only — never runs
  `git`. State this even when it feels redundant; without it, an agent
  helpfully runs `git add` and corrupts the driver's bookkeeping.

**Companion rule — name what the WU is expected to produce.** The
boundaries above are one half; the other half is naming the files this WU
should *author*. The Acceptance criteria section (§2) should list the
specific paths the WU is responsible for (e.g. `.github/workflows/cd.yml`
and the CI section of `CLAUDE.md`). A reviewer should be able to point at
every changed file in the squash commit and find it in either the WU's
produces-list or the gate's verification output. Without an explicit
produces-list, an agent can "helpfully" do work that belongs to a later
WU in the same gate (observed: a T01 that wrote CLAUDE.md doc updates
that were T92's job), and the verification gates don't object.

> *Prevents:* an agent reaching into a generated directory because "don't
> touch other files" didn't sound like *this*; side commits the driver's
> squash can't reconcile; and silent over-reach where a WU does adjacent
> work that should have belonged to a sibling WU.

## 4. Verification — name the gates the driver will actually run

The WU's Verification section names gates, but the driver (or branch
protection) runs whatever is in `verification.yml`'s relevant set. If they
disagree, the WU's stated verification is fiction.

- For `implementation` WUs, name the `code` set as declared in this
  repo's `verification.yml`. Don't list a gate the file doesn't have, and
  don't omit one it does.
- For fast-iteration or probe work, prefer a **scoped** gate command
  (`pytest tests/test_health.py`, `mvn test -Dtest=HealthTest`) over a
  full-suite one. A minutes-long full run on every attempt makes the
  three-attempt budget effectively one attempt.
- Some runners fail silently on a missing-but-named test (no tests found
  ≠ all passed). Name a real test, and confirm the runner exits non-zero
  when nothing matches.

> *Prevents:* a WU that "passes" the agent's check but fails the driver's
> re-run; and a WU burning each of three attempts on a full suite the
> iteration didn't need.

## 5. Escalation triggers — distinguish "my check tripped" from "the bad thing happened"

Triggers should fire on the **real hazard**, not on any flagging condition.
The best observed agent behaviour, when a criterion tripped ambiguously,
emitted `status: blocked` *and* explained the trip might be a false alarm
on pre-existing state, recommending human review — rather than pushing
through or silently passing.

- Name triggers as conditions, not actions: `"if no router module exists,
  block — that's a different unit of work"`, not `"create the router."`
- When you're unsure whether a tripped criterion is the real failure or
  pre-existing unrelated state, the right move is a reasoned
  `status: blocked` with the evidence. **Blocked is a respectable
  outcome** (see [`../../rules/result-contract.md`](../../rules/result-contract.md));
  a guessed pass is worse than an honest block.
- A trigger that only ever fires on the agent's own bug is not a trigger;
  it's a code-quality concern. Triggers exist for spec/scope ambiguities
  the agent shouldn't resolve unilaterally.

> *Prevents:* the agent forcing a doubtful pass that costs the gate's
> trust budget; also prevents triggers that fire constantly and become
> noise the next reader ignores.

---

## 6. Sizing — one WU = one focused session's work

A WU is crafted to land in a single fresh-session pass. The Ralph property
(fresh context per attempt) only buys leverage when the unit is
small-enough to fit.

- If a WU needs multiple rounds of **unrelated** work, it's two WUs.
  ("Add the endpoint AND refactor the router module" is two.)
- If a WU's acceptance criteria number in the double digits, suspect
  bundling — most well-sized WUs have 2–5 criteria.
- Sizing interacts with gate-cutting (how to slice a feature into the
  right number of gates with the right WUs each). **That's a separate
  skill** and is deferred until multi-gate runs surface decomposition
  evidence; this skill stays at the per-WU level.

> *Prevents:* a WU that exhausts the three-attempt budget on the first
> sub-problem and never reaches the second; also prevents the driver
> producing one squashed commit that mixes two unrelated changes.

---

## 7. Hygiene work units — when a blocked WU points outside its scope

A substantive WU sometimes discovers that its verification can't pass
because of a pre-existing bug in a path its **Do not touch** rule
forbids (a shared module, a dependency version, a config file owned
elsewhere). Observed: a `terraform validate` gate failing on an
`automatic_upgrade_channel`-vs-`automatic_channel_upgrade` mismatch in a
shared module that the WU was correctly forbidden from editing.

The right move is to insert a **hygiene WU** earlier in the gate (or as
a precursor gate) scoped to that fix alone:

- **ID convention.** The hygiene WU's ID is the target substantive
  WU's ordinal followed by `H` — e.g. `FEAT-YYYY-NNNN/T02H` is "the
  hygiene WU for T02." Multiple hygiene WUs for the same target use
  `T02H1`, `T02H2`. See
  [`../../rules/correlation-ids.md`](../../rules/correlation-ids.md)
  for the canonical pattern; the linter (`lint_plan.py`) enforces it.
- **One narrow acceptance criterion** — e.g. `"modules/aks/cluster.tf
  uses the azurerm-3.x attribute name automatic_channel_upgrade"`. The
  hygiene WU's "produces" list names only the broken file.
- **Pass on its own verification** before the blocked WU runs again.
  The blocked WU then re-runs unmodified; its scope and "Do not touch"
  bounds are intact.
- **PLAN.md wiring.** Insert the hygiene WU's row into the gate's
  `work_units` graph BEFORE the target substantive WU. Update the
  target's `depends_on` to include the hygiene WU's ID. Flip the
  target's `status` from `blocked_human` back to `pending` so the
  loop will re-dispatch it after the hygiene WU passes.
- **Evidence requirement.** The hygiene WU's **Context** section
  must quote the blocked WU's `human_escalation` event from
  `events.jsonl` verbatim — the timestamp, the reason, and the
  agent's blocked_reason text. That's the trace from "this fix
  exists because of that block." Without it, a hygiene WU looks
  indistinguishable from speculative pre-emptive work.
- **Never the wrong responses:** do NOT loosen the blocked WU's "Do
  not touch" to permit the cross-cutting fix (muddies its boundary);
  do NOT fix it manually out-of-loop and pretend the gate ran clean
  (silent drift between the methodology's recorded history and git).

The hygiene WU is methodology-honest: every state change goes through
the loop, every commit traces to a WU, every fix has its own evidence
trail. The cost is one more WU; the benefit is the gate cycle stays
trustworthy.

> *Prevents:* the temptation to either widen the blocked WU's scope
> (eroding the per-WU contract) or silently fix out-of-band (eroding
> the audit trail). Both undermine the same invariant — that every
> committed state change traces to a WU that was dispatched, verified,
> and committed by the loop.

---

## 8. Cross-surface contract values — verify against the source, never invent

When an acceptance criterion names a value that lives in **another system** —
a GitHub label name, an API field name, an event-schema key, a shared protocol
constant, a branch/trailer format — that value must be **verified against the
authoritative source before the gate is armed**, not invented from the feature's
own internal conventions. An invented value is a silent correctness risk: it
looks right to the author, satisfies the WU's own AC, passes offline tests, and
fails only at live/integration time.

- For every AC that references an external system's vocabulary, write a **pre-arm
  check line** into the WU spec: `verify <value> against <authoritative source>
  before locking this AC`. The gate review document lists these open
  verifications; the gate is not armed until each is checked.
- This blind spot is **systematic in `plan-next` drafts**, not random — a planner
  drafting a downstream gate will confidently invent plausible, internally
  consistent cross-repo values it cannot see. So every `plan-next` gate review
  should carry a **"Cross-repo contracts" table**: each invented value alongside
  its authoritative source and a checked/unchecked status.

> *Prevents:* the failure observed in `[FEAT-2026-0003/G3-LESSONS]` — a draft
> invented the report-back labels `loop:in-progress`/`loop:complete`; the correct
> values were the orchestrator's canonical `state:in-progress`/`state:done`
> (`naming-convention.md §5.1` + `labels.md`). Caught at gate-3 arming by reading
> the source; had it shipped, every adopted feature would have reported state on
> a label namespace the orchestrator's poller never queries.

---

## This skill distills `.specfuse/LEARNINGS.md`

When a gate's `lessons` work unit surfaces a new authoring rule — one that
would change how a future WU is written or executed — it graduates here
once it's reusable and durable. The pipeline is **runs → retrospective →
lessons → LEARNINGS.md → this skill**. If a rule lives only in LEARNINGS
and would clearly change WU authoring, it's a candidate for promotion on
the next edit.

## Version

**v0.4.** Eight rules. v0.4 (this) added §8 (verify cross-surface
contract values against the authoritative source rather than inventing
them; carry a "Cross-repo contracts" table in every plan-next gate
review) — graduated from `[FEAT-2026-0003/G3-LESSONS]` after a draft
invented GitHub report-back labels that diverged from the orchestrator's
canonical `state:*` scheme. v0.2 added the produces-list companion in §3
and the hygiene-WU pattern in §7. v0.3 tightened §7 with the
canonical `T<NN>H` ID convention (the previous draft left the ID
shape vague; a live insert had to rename `T1H` to `T04` because the
linter regex didn't admit it), the explicit PLAN.md wiring step
(insert + retarget depends_on + flip target status), and the
evidence-from-events-log requirement that grounds the hygiene WU's
Context in a specific human_escalation entry. Expected to keep
growing — each multi-gate or multi-feature run that surfaces a rule
that would change how a future WU is written or executed graduates
here from LEARNINGS.md.
