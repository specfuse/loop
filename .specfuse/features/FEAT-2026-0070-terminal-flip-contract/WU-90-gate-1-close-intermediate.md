---
id: FEAT-2026-0070/G1-CLOSE-INTERMEDIATE
type: close-intermediate
status: done
attempts: 1
planned_cost_usd: 4.50
oracle_env: macos_local
auto_close_disabled: true
model: opus
effort: high
gate_set: plannext
driver_version: 0.4.0
started_at: 2026-07-27T03:10:10.769768+00:00
duration_seconds: 985.272
cost_usd: 6.371276
input_tokens: 302
output_tokens: 55171
---

# Gate 1 close-intermediate — retrospective + lessons + docs

**Objective.** Close gate 1: write `RETROSPECTIVE.md`, promote durable lessons, reconcile
the docs the flip contract affects, and enumerate the consumer-visible contract changes
for human acknowledgment. Non-terminal close — no feature-arc verdict, no terminal flips.

**Context.** This is `FEAT-2026-0070/G1-CLOSE-INTERMEDIATE`. Gate 1 shipped the flip
contract: T01 (row flip from any non-`done` status), T02 (the out-of-band verdict-recheck
primitive), T03 (`/accept-hedged-close` built on it), T04 (`lint_plan`'s dispatch-state
exemption). Read this feature's `events.jsonl`, the gate's commits, `PLAN.md`, and root
`.specfuse/LEARNINGS.md`.

`auto_close_disabled: true` is deliberate: AC5 blocks on human acknowledgment of a
consumer-visible contract change, and the auto-close predicate must not be able to skip it.

**Read `close-discipline.md` §4 before writing.** It lists the exact strings the driver
checks — including the `## Gate 1` heading this WU must produce and the
`### Failure-class breakdown` section required when the gate had any failed attempt.
Those guards run *after* dispatch, so a mismatch costs a full re-attempt.

Binding rules under `.specfuse/rules/` apply. The driver owns all git.

**Acceptance criteria.**

1. `RETROSPECTIVE.md` exists with a `## Gate 1` section carrying per-WU outcomes
   (T01–T04) — what worked, what failed, attempts, final cost — plus surprises and a
   `## What I'd change` section.
2. **`## Cost analysis`** present, reconciling `planned_cost_usd` from `PLAN.md` and the
   per-WU frontmatter against actual spend from `events.jsonl`, with the delta named. Gate
   1 planned $20.50. Report the actual against the **as-drafted** figure — do not
   re-baseline onto a mid-gate revision (`[FEAT-2026-0069/G1-CLOSE-INTERMEDIATE]`).
3. **`### Failure-class breakdown`** present if the gate had ≥1 failed attempt, per
   `close-discipline.md` §4. Omit only if every WU passed first try.
4. **`## What the loop did NOT verify`** present, enumerating each acceptance criterion
   whose verification was deferred — the criterion, why, and where it actually gets
   verified. Required even when empty; write
   `(nothing — every acceptance criterion was verified in-loop)` if so.
   **One entry is likely and should not be smoothed away:** T03 ships a skill, and a skill
   is verified by an operator running it, not by a dispatched session. State plainly which
   of its criteria were verified structurally (registration, sync, text assertions) and
   which await a real invocation.
5. **Consumer-visible contract changes** (`close-discipline.md` §3): this is **not**
   `n/a`. Enumerate at minimum — the roadmap row now flips from any non-`done` status
   (behaviour change for `autonomy: auto` features); a new driver entry point exists; a new
   skill exists; `lint_plan` no longer errors on two WU states it previously rejected.
   Block on human acknowledgment.
6. **Verify the one-owner property held.** `grep -c "def fire_terminal_flips"
   specfuse/loop/loop.py` returns `1`, and no surface outside it writes `PLAN.md status`,
   the gate status, or the roadmap row. `[FEAT-2026-0023/G1-CLOSE]` is this gate's central
   constraint and the close is where it gets audited — a gate that passed every test while
   splitting terminal-state ownership has failed.
7. Durable lessons promoted to `.specfuse/LEARNINGS.md`, tagged
   `[FEAT-2026-0070/G1-CLOSE-INTERMEDIATE]`. Candidates worth weighing — promote what
   generalises, not everything: whether "a skill must call a driver primitive rather than
   write state" deserves stating as a general rule rather than a per-feature constraint;
   and whether the pattern behind T04 — *a check enforced in two places, one of which
   cannot explain itself* — is the same defect class as #265 and #272 and should be named
   once.
8. Docs reflect what shipped. If the new entry point or skill needs naming in
   `docs/methodology.md` or `docs/skills.md`, do it here.
9. `python3 .specfuse/scripts/lint_plan.py .specfuse/features/FEAT-2026-0070-terminal-flip-contract`
   passes. The cost-delta WARN documented in `PLAN.md`'s Notes is expected while gate 2 is
   undrafted.

**Do not touch.** Gate 1's WU source (T01–T04 — the gate is done; do not retro-edit their
bodies). Gate 2's WU files — `G1-PLAN` drafts those. `PLAN.md`'s `status` field — the
driver owns terminal flips, and this is a non-terminal close. `.git/`, secrets. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `doc` gate set the driver runs for `type: close-intermediate`, plus
the fresh greps in AC6 and the plan lint in AC9.

**Escalation triggers.** Emit `status: blocked` if any of T01–T04 did not produce its
declared `produces:` files, if AC6's grep shows more than one terminal-state writer, or if
the human acknowledgment AC5 requires is unavailable in this session — a consumer-visible
behaviour change must not be closed on silence. Blocked is a respectable outcome
(`result-contract.md` rule 4).
