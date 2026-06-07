# The Specfuse gate-cycle methodology

This document is the canonical definition of the gate cycle: the shared
vocabulary and contracts that the Specfuse Loop and the Specfuse Orchestrator
both implement. It is written to be implementation-agnostic — the loop runs it
single-repo with a driver script; the orchestrator runs it multi-repo with
agents and a polling loop — but the *concepts* defined here mean the same thing
on both surfaces.

> **Authoring note.** While the gate cycle is being proven, the loop is its
> near-term author: the loop runs real features first, and what it learns
> revises these contracts before they are folded into the orchestrator's frozen
> baselines. See [`architecture-addendum-gates-and-iterative-planning.md`](architecture-addendum-gates-and-iterative-planning.md)
> for how the cycle maps onto the orchestrator's state machine and agent roles.

---

## 1. The unit hierarchy

- **Roadmap** — the master index of features for a repository/project, with each
  feature's status (`planned → active → done`/`abandoned`).
- **Feature** — a spec-driven *or directly-authored* unit of value, identified by
  a correlation ID `FEAT-YYYY-NNNN`. A feature owns an ordered list of gates.
- **Gate** — a milestone partition of a feature: an ordered batch of substantive
  work units followed by a mandatory closing sequence and a human review-and-arm
  checkpoint. Gates are numbered within a feature.
- **Work unit (WU)** — a single, self-contained unit of work identified by a
  task-level correlation ID `FEAT-YYYY-NNNN/TNN` for substantive units,
  `FEAT-YYYY-NNNN/TNNH[N…]` for hygiene units that precede a target substantive
  unit, `FEAT-YYYY-NNNN/G<n>-(RETRO|LESSONS|DOCS|PLAN)` for the four-WU closing
  sequence, or `FEAT-YYYY-NNNN/G<n>-CLOSE` for the single-gate `close`
  alternative. A WU is crafted to be completed in one focused agent session.
  It carries its own prompt and is the contract between the planner and the
  executor.

The correlation ID threads the entire lifecycle — it appears in the feature
folder name, the WU file, every event-log entry, the branch, the commit trailer
(`Feature: FEAT-YYYY-NNNN/TNN`), and (in the orchestrator) the GitHub issue.

## 2. Ownership — one fact, one home

- The **PLAN** owns the *shape*: gate order, which WUs belong to each gate, and
  the dependency edges between them.
- The **GATE** owns the *gate*: its status, its definition of done, and the
  human's reflection notes.
- The **WU** owns *itself*: its type, model, status, attempts, and prompt body.

Dependencies live in the PLAN, not in WU frontmatter: a dispatched session never
needs to know its own dependencies — they are satisfied by the time the unit is
handed to it. Dependency edges are scheduling metadata, and scheduling belongs to
the driver/PM, not to the executing session.

## 3. Work unit types

Eight types share one state machine; type affects only who handles the unit and
what its prompt contains.

Substantive:
- `implementation` — code.
- `qa_authoring` / `qa_execution` / `qa_curation` — test-plan authoring,
  execution, and regression-suite curation.

Closing sequence — every gate ends with **one** of two forms:

*Four-WU sequence* (required for multi-gate features; valid for single-gate):
- `retrospective` — feature-local raw observations for the gate.
- `lessons` — promotes the *generalizable* subset of the retrospective into the
  cross-feature `LEARNINGS.md`.
- `docs` — reconciles documentation and roadmap status with what was built.
- `plan-next` — drafts the next gate and writes the human review summary.

*Single-WU alternative* (single-gate features only):
- `close` — collapses all four ceremonies into one session: writes
  `RETROSPECTIVE.md`, promotes lessons to `LEARNINGS.md`, reconciles docs and
  roadmap, and writes the terminal feature-arc verdict. `lint_plan.py` rejects
  this type on any feature with more than one gate.

## 4. The five-section work-unit contract

Every dispatchable WU prompt has these five mandatory sections (a sixth,
`Objective`, is recommended but not enforced):

- **Context** — what this is part of, the correlation ID, the grounding specs/files.
- **Acceptance criteria** — explicit, machine-checkable statements of done.
- **Do not touch** — generated dirs, other units' files, secrets, branch
  protection, `.git/`.
- **Verification** — the exact gate commands that must pass.
- **Escalation triggers** — conditions under which to stop and report `blocked`
  rather than push through.

This is the same five-section contract as the orchestrator's work-unit issue
body (architecture §8). Pattern enforcement (TDD order, a required structure)
belongs in the WU prompt and the shared rules, **not** in finer WU granularity.

## 5. Verification is the exit oracle

The executing session's self-report is **advisory**. The driver (loop) or the
branch-protection gate (orchestrator) re-runs the unit's verification and *that*
decides done. For `implementation` units the gates mirror branch protection:
tests pass, coverage ≥ threshold, zero warnings, lint clean, security scan clean.
A unit that passes its own checks but would fail the real gate has done the wrong
thing. Keep the loop's `verification.yml` `code` set in lock-step with branch
protection wherever both exist.

## 6. The gate cycle

For each gate, in order:

1. **Plan.** The current gate's WUs are detailed (the first gate by the human/PM
   at feature planning; every later gate by the prior gate's `plan-next`).
2. **Execute.** The driver/PM walks the gate's ready WUs (dependencies met),
   dispatches each as a **fresh** session, verifies, and commits one squashed
   commit per unit. A failed gate is retried with a fresh session carrying the
   failure evidence, up to three attempts (the spinning threshold), then
   escalated for human attention.
3. **Close.** The closing sequence runs as the gate's last units. For multi-gate
   features (and optionally single-gate ones), this is the four-unit sequence
   `retrospective → lessons → docs → plan-next`; `plan-next` drafts the *next*
   gate's WUs and writes a human review summary. For single-gate features only,
   a single `close` WU may substitute, collapsing all four ceremonies into one
   session — no forward-design `plan-next` is needed when there is no next gate.
4. **Review and arm.** The cycle stops for the human, who reviews the next gate's
   draft (guided by the review summary), edits or accepts it, arms the accepted
   units, and signals approval. Then the cycle repeats for the next gate.

The final gate has no next gate to plan; `plan-next` instead signals feature
completion.

### Fresh context per dispatch

Each WU is executed by a new session. All durable state lives in the PLAN, the
GATE/WU files, git history, the event log, and per-unit failure notes — never in
a context window. This is the Ralph property, kept at work-unit granularity
because units are sized to land in one pass.

## 7. plan-next and the review summary

`plan-next` is forward design — the one act in the cycle that is not synthesis
against a log — and takes the strongest model. It reads the gate retrospective
and the cross-feature `LEARNINGS.md`, drafts the next gate's WUs, and may revise
*not-yet-reached* gates (split/merge/re-scope), surfacing any such change loudly
in the review summary. It never touches a gate already passed.

It **drafts but never arms.** Arming — accepting the drafted units so they
execute — is the human's act (or, under automatic mode, a mechanically-gated
auto-arm; see §9). This preserves the highest-leverage human checkpoint: catching
a misframed gate before it becomes merged code.

The review summary is weighted toward **doubt**, not completeness: decisions and
their rationale, an explicit "if you check only three things, check these" list,
a roadmap-anchor check (with a loud flag if the goal itself seems to be drifting),
and open questions — each mapped to the draft WU it affects. The summary is
advisory and owns no state.

## 8. LEARNINGS — the cross-feature feedback loop

`LEARNINGS.md` is an append-only, cross-feature log of durable, reusable rules
distilled by each gate's `lessons` unit. It is read at planning time so each
plan is better than the last. Feature-specific observations stay in that
feature's `RETROSPECTIVE.md`; only rules that would change how a *future* WU is
written or executed graduate to `LEARNINGS.md`. This is the human-scale analogue
of the Ralph loop feeding errors back into the prompt.

## 9. Autonomy

Three levels — `auto`, `review`, `supervised` — set as a feature default and
overridable per gate (tightening only; a gate may be more supervised than the
feature default, never less). Under `auto`, the per-gate stop may be skipped
(plan-next auto-arms the next gate) **only when all of**: the structural lint
passes, the not-yet-reached skeleton was not revised, no task in the gate carries
a `supervised`/auto-forbidden override, and plan-next raised no escalation. If any
fails, the cycle stops for the human regardless of mode. Auto-arm advances toward
execution; it never auto-merges — the merge gate stays human until the QA loop is
trusted. Escalation always overrides autonomy.

## 10. The two execution surfaces

| Concern        | Loop (single-repo)                  | Orchestrator (multi-repo)              |
|----------------|-------------------------------------|----------------------------------------|
| State backend  | WU / GATE file frontmatter          | GitHub issue labels + feature registry |
| Dispatch       | driver shells out (`claude -p`)     | inbox files + polling loop             |
| Branch / merge | one branch, squash per WU            | branch + PR per task, merge watcher    |
| Spec front-end | optional; task graph authored directly | spec-first (specs agent + codegen)  |

Everything above those rows — the unit hierarchy, ownership split, WU contract,
verification-as-oracle, the gate cycle, plan-next, LEARNINGS, and autonomy — is
shared and means the same thing on both surfaces.
