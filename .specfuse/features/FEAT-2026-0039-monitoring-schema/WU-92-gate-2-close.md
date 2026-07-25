---
id: FEAT-2026-0039/G2-CLOSE
type: close
status: draft
attempts: 0
planned_cost_usd: 5.00
auto_close_disabled: true
oracle_env: macos_local
---

# Gate 2 close — terminal close ceremony (drafted placeholder)

**Objective.** Close this feature in one session after gate 2's skill WUs complete:
produce the gate-2 `RETROSPECTIVE.md`, append durable lessons to
`.specfuse/LEARNINGS.md`, reconcile docs and roadmap, write the feature-arc
verdict, and include the `## Cost analysis` and `## What the loop did NOT verify`
sections. Driver-side terminal flips (gate → `passed`, roadmap row → `done`,
`PLAN.md status` → `done`, auto-archive) fire when the verdict permits.

**Placeholder note.** This close is pre-declared at draft time so the gate graph is
valid and gate 1 reads as non-terminal (the linter treats the last non-empty gate
as terminal). Gate 1's `plan-next` (G1-PLAN) inserts gate 2's substantive WUs
BEFORE this close and updates this WU's `depends_on` to list them. Until then it
stays `status: draft` (unarmed).

**Context.** This is `FEAT-2026-0039/G2-CLOSE`, the feature's terminal close. Read
this feature's `events.jsonl`, both gates' commits, `PLAN.md`'s `roadmap_goal` and
scope boundary, and the gate-1 retrospective. Reference the binding rules under
`.specfuse/rules/`; honor `result-contract.md`, `never-touch.md`, and
`close-discipline.md`. The driver owns all git and the terminal `PLAN.md status`
flip — do not write that field.

**Acceptance criteria.** (Refined by G1-PLAN against what gate 2 actually drafts;
the following are the obligations that hold regardless.)

1. `RETROSPECTIVE.md` covers gate 2 per-WU and the whole feature arc, with a
   `## What I'd change` section.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` ($34.00 at the
   feature level) against actual spend from `events.jsonl`, with the delta named
   per gate.
3. **`## What the loop did NOT verify`** present. This feature has a known
   non-empty entry: the live run of `derive-monitoring` against a real
   multi-component backend never happens in-loop — the skill is interactive and its
   target is a different repository, so a dispatched WU has neither the human
   channel nor commit access. Name it, say the in-loop substitute was a stylized
   repo-tree fixture, and give the exact re-run condition that upgrades it to
   verified: an operator runs the skill against a real project and its drafted
   `monitoring.yml` passes `lint_monitoring` clean. Per the skill's own threshold,
   if the deferred list exceeds two entries or 30% of the gate's criteria, flag the
   feature's gate sizing under `## What I'd change`.
4. **Oracles re-run fresh** (`close-discipline.md` §1): every oracle this feature's
   criteria name is re-run here with full commands and exit codes read directly —
   never a producing WU's self-report.
5. **Consumer-visible contract changes** (§3): enumerate every addition across both
   gates — `validate_monitoring`, the shim CLI, the new `code` gate, the seeded
   example, the seeded rule, the skill — or write exactly `n/a — no consumer-visible
   contract change`. FEAT-2026-0040/0041/0042/0043 are all `blocked` on this
   feature, so this enumeration is their handoff document.
6. The feature-arc verdict is written honestly against `PLAN.md`'s `roadmap_goal`,
   accounting for the two deliberate scope narrowings recorded in the scope
   boundary (the GitHub Actions workflow deferred to FEAT-2026-0040; the live run
   deferred to post-merge operator work).

**Do not touch.** Gate 1 and gate 2 WU source (both gates are done); gate status
flips and the terminal `PLAN.md status` flip (the driver owns both); `.git/`,
secrets. See `.specfuse/rules/never-touch.md`.

**Verification.** The `plannext` gate set the driver runs for `type: close`, plus
the closing-deliverable guards (`assert_cost_analysis_section_when_met`, the
retrospective/lessons presence checks) and `assert_terminal_flips_fired`. This WU
carries `auto_close_disabled: true` because its criteria are load-bearing —
`close-discipline.md` §1 and §3 obligations cannot be satisfied by the auto-close
predicate.

**Escalation triggers.** Emit `status: blocked` if any gate-2 WU did not produce its
declared deliverable — do not write a `met` verdict over a gap. Block if the fresh
oracle re-run disagrees with a producing WU's self-report. Blocked is respectable
(`result-contract.md` rule 4).
