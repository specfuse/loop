---
feature_id: FEAT-2026-0049
title: specfuse-agent runner — run-to-drain queue execution with lock, caps, pause-and-switch
slug: specfuse-agent-runner
branch: feat/FEAT-2026-0049-specfuse-agent-runner
roadmap_goal: One operator-launched command drives the whole lifecycle of a specfuse-configured repo — findings, triage, bugs, prioritized feature advancement — as a thin conductor over the existing loop driver and skills, escalating what it cannot handle, for exactly as long and as expensively as the operator allows.
autonomy_default: auto
status: active
planned_cost_usd: 105.00
---

# Plan: specfuse-agent runner

The capstone. Every mechanism this feature needs already ships: the bug lane runs
end to end, triage categorizes and records, the harvester finds and files, the
autofix path decides and fires, the driver executes gates and halts honestly.
What does not exist is the thing that *chooses* among them and keeps choosing
until the work runs out or the operator's budget does.

So this feature builds a conductor, not a capability. It modifies none of the
surfaces it drives. Its entire value is selection, sequencing, and stopping —
and its entire risk is that it runs unattended, which is why the caps, the lock,
and the kill switch are gate 1 rather than a later polish gate.

**Drafted through a real `/draft-feature` interview (2026-08-10).** The four
decisions below are the operator's, recorded with the evidence each was weighed
against.

## Decisions taken at draft time

**D1 — The agent takes its own lock, not the driver's.** `loop.run()` acquires
`.specfuse/.loop.lock` itself at `loop.py:6102` on every non-dry-run, so an agent
holding that same lock would break every driver invocation it makes with
`BlockingIOError`. The agent takes `.specfuse/.agent.lock` instead: two locks,
two independent scopes — one agent per repo, one driver per repo.

The roadmap goal asked for "PID + heartbeat timestamp, stale-lock detection."
**That is not built, deliberately.** `_filelock`'s docstring states the kernel
releases the lock on process death including SIGKILL, so "no stale-lock cleanup
is ever needed" and pidfiles are explicitly ruled out. Building detection for a
condition that cannot occur would be inventing work.

**D2 — All four action classes ship, cut across three gates.** The alternative
was a narrower v1 (bugs and triage only, or features only). Rejected because the
selector *is* this feature, and a selector with one action class is vacuous —
"pick the highest-value action under policy" means nothing until at least two
classes compete for the slot. A narrow v1 would ship a selector the next feature
rewrites.

**D3 — Caps are checked at item boundaries only; a running item is never
interrupted.** A cap can therefore overshoot: `--max-minutes 30` against a
two-hour item stops at two hours. That cost is accepted in exchange for never
manufacturing a killed-mid-work-unit driver state — partially-flipped WU
frontmatter and `events.jsonl` with no commit, whose cheapest known recovery is
to discard the work wholesale. Overshoot costs money; corrupted state costs money
and a manual repair. `--max-minutes` is documented in its own flag help as "do
not start new work after N minutes," and the run summary reports actual elapsed
time.

**D4 — `autonomy_default: auto`.** Operator's decision, taken against a
recommendation of `review` grounded in blast radius (this feature ships a script
that merges PRs and dispatches the driver unattended). Recorded as the operator's
call. Consequence: gates auto-close when `evaluate_auto_close` permits, and
lessons stage to `LEARNINGS-pending.md` rather than landing in
`.specfuse/LEARNINGS.md`.

## Where the new code lives, and why it is not in `specfuse/loop/`

The runner is a new sibling package, `specfuse/agent/`, alongside
`specfuse/loop/` and `specfuse/monitor/`.

This is not only taxonomy. `driver_edit.DRIVER_MODULE_PREFIXES` is
`("specfuse/loop/",)`, so any work unit whose squash touches `specfuse/loop/`
halts the driver for a restart (FEAT-2026-0075). With the conductor under
`specfuse/agent/`, gate 1 takes **one** such halt — T01, which must edit
`_filelock.py` — instead of one per work unit. Under `auto` each halt is a
manual restart, so this is a real cost, not a stylistic preference.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

This feature designs a selection policy and three stopping mechanisms (lock,
caps, kill switch), so the section applies.

- **Grep commands run:**
  - `grep -rn 'get("queue")\|\["queue"\]\|resolve_queue' --include="*.py" specfuse/`
  - `grep -n "^def \|^class " specfuse/loop/_filelock.py specfuse/loop/escalation.py specfuse/loop/agent_policy.py specfuse/loop/heartbeat.py`
  - `grep -n "def run_autofix" -A 18 specfuse/monitor/autofix_run.py`
  - `grep -n "acquire_tree_lock" -B 3 -A 12 specfuse/loop/loop.py`

- **Verdict:** `found several, reusing; one genuinely absent`.

  **Reusing, not rebuilding:**
  - `specfuse/loop/_filelock.py::acquire_tree_lock` — "the OS auto-releases on
    fd/handle close or process death (SIGKILL included), so no stale-lock cleanup
    is ever needed." Covers the lock property; extended with a filename
    parameter only.
  - `specfuse/loop/escalation.py::emit_escalation` — "Escalation contract:
    needs-human issues (assigned, structured)." Covers every human touchpoint.
  - `specfuse/loop/bug_lane_run.py::run_bug_lane` — "Run the bug lane end to end:
    fix, PR, guarded merge." Covers the entire bug action class.
  - `specfuse/loop/triage.py::list_untriaged` / `apply_triage` — covers the
    triage action class.
  - `specfuse/monitor/autofix_run.py::run_autofix` — "Decide, record, fire, and
    label — for one diagnosed finding issue." Covers the findings action class.
    Its own docstring records that it was shipped **without a caller** on
    purpose: "Not wired into `specfuse monitor run`… `run_autofix` is its own
    entry point." This feature is that caller.
  - `specfuse/loop/agent_policy.py::load_policy` and the `resolve_*` dials —
    cover every policy read except one.

  **Genuinely absent, and therefore built here:** a *reader* for `queue:`.
  `agent_policy.py:225` validates the list against the roadmap and nothing more;
  no code anywhere selects work from it. `/groom-backlog` writes the queue and
  nothing has ever read it. T02 is its first reader.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — this feature raises no check to `ERROR`, flips no `WARNING` to blocking,
and asserts no "zero issues" close predicate. It consumes existing predicates
(`evaluate_merge_guardrails`, `autofix.decide`) without changing their severity.

## Scope boundary — explicitly OUT of this feature

- **Drafting features.** A drafting-needed queue top escalates; the interactive
  `/draft-feature` session stays human in v1. Moving it async is
  [FEAT-2026-0050](../../roadmap.md#feat-2026-0050), which lists this feature as
  its blocker.
- **Cron or event triggering.** The script is operator-launched. A scheduler
  invoking the same script unchanged is a later concern and needs nothing here.
- **Modifying any surface the agent drives.** The driver, the skills, the
  harvester, and the bug lane are consumed as-is. The single exception is
  `_filelock.py`'s filename parameter (T01).
- **An agent database.** All state is derived from GitHub, the roadmap, the
  policy file, and feature folders, or is safely losable. Nothing persists that
  cannot be recomputed.

## Task graph

```yaml
# Closing shape (FEAT-2026-0015):
#   Gates 1, 2 and 3 are non-terminal: close-intermediate + plan-next.
#   Gate 4 is terminal: a single close.
#   The insertion the sizing decision below called for was performed by
#   G2-PLAN on 2026-08-11: gate 3 is the findings gate, the features gate and
#   its terminal close moved from 3 to 4. Gate 4's substantive work units are
#   G3-PLAN's to draft; until then its close placeholder stands alone, the same
#   arrangement gate 3 held before this restructure.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0049/T01
        file: WU-01-agent-lock.md
        depends_on: []
      - id: FEAT-2026-0049/T02
        file: WU-02-state-snapshot.md
        depends_on: []
      - id: FEAT-2026-0049/T03
        file: WU-03-budget-and-pause.md
        depends_on: []
      - id: FEAT-2026-0049/T04
        file: WU-04-conductor-loop.md
        depends_on: [FEAT-2026-0049/T01, FEAT-2026-0049/T02, FEAT-2026-0049/T03]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0049/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0049/T01, FEAT-2026-0049/T02, FEAT-2026-0049/T03, FEAT-2026-0049/T04]
      - id: FEAT-2026-0049/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0049/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      - id: FEAT-2026-0049/T05
        file: WU-05-provider-seam.md
        depends_on: []
      - id: FEAT-2026-0049/T06
        file: WU-06-bugs-provider.md
        depends_on: [FEAT-2026-0049/T05]
      - id: FEAT-2026-0049/T07
        file: WU-07-triage-provider.md
        depends_on: [FEAT-2026-0049/T05]
      - id: FEAT-2026-0049/T08
        file: WU-08-answered-escalations.md
        depends_on: [FEAT-2026-0049/T05]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0049/G2-CLOSE-INTERMEDIATE
        file: WU-93-gate-2-close-intermediate.md
        depends_on: [FEAT-2026-0049/T05, FEAT-2026-0049/T06, FEAT-2026-0049/T07, FEAT-2026-0049/T08]
      - id: FEAT-2026-0049/G2-PLAN
        file: WU-94-gate-2-plan-next.md
        depends_on: [FEAT-2026-0049/G2-CLOSE-INTERMEDIATE]
  - gate: 3
    file: GATE-03.md
    work_units:
      - id: FEAT-2026-0049/T09
        file: WU-09-findings-seam.md
        depends_on: []
      - id: FEAT-2026-0049/T10
        file: WU-10-findings-diagnose-provider.md
        depends_on: [FEAT-2026-0049/T09]
      - id: FEAT-2026-0049/T11
        file: WU-11-findings-autofix-provider.md
        depends_on: [FEAT-2026-0049/T09]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0049/G3-CLOSE-INTERMEDIATE
        file: WU-95-gate-3-close-intermediate.md
        depends_on: [FEAT-2026-0049/T09, FEAT-2026-0049/T10, FEAT-2026-0049/T11]
      - id: FEAT-2026-0049/G3-PLAN
        file: WU-96-gate-3-plan-next.md
        depends_on: [FEAT-2026-0049/G3-CLOSE-INTERMEDIATE]
  - gate: 4
    file: GATE-04.md
    work_units:
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0049/G4-CLOSE
        file: WU-92-gate-4-close.md
        depends_on: []   # G3-PLAN sets real depends_on when it drafts gate 4
```

## A note on `planned_cost_usd`

`105.00` is the sum of the **drafted** work units, recomputed from frontmatter by
`G2-PLAN` rather than adjusted by hand: gate 1's six ($29.50), gate 2's six
($39.50 — T05 was raised from $8.00 to $10.00 at arming, which is why the
previous figure of $72.00 had already drifted $2.00 low), gate 3's five ($31.00,
drafted here), and gate 4's terminal `close` placeholder ($5.00). It is still not
an estimate of the whole feature: gate 4 has no substantive work units yet, so
there is nothing honest to add for them, and `G3-PLAN` raises this figure as it
drafts them. Keeping it equal to the real sum is what lets the 10% drift lint
stay meaningful instead of being permanently red.

For calibration when the next estimate is made: gate 1 planned $29.50 and spent
**$5.95** against a $36.00 budget; gate 2 planned $39.50 and spent **$6.66**
against a $45.50 budget. Both came in at roughly a sixth of plan. Gate 3's
estimates deliberately do **not** correct for that — the padding is for a known
guard-contract defect (`planning-discipline.md` §5), not a prediction, and
shrinking it on two observations would be generalising from an outlier. What the
two data points do buy is confidence that the *budget* is not the binding
constraint on this feature.

## Gate map

**Gate 1 — the conductor drains an empty queue.** `specfuse-agent run` acquires
its own lock, honours caps and the PAUSE marker, reads repo state into one
snapshot, runs select→execute→reconcile to completion against zero registered
providers, and prints a run summary. Deliberately has no action class: the loop's
stopping properties are the thing most expensive to get wrong and cheapest to
test in isolation.

**Gate 2 — the agent drains bugs, triage, and answered escalations.** Three
providers over already-shipped composition — bugs (`run_bug_lane`), triage
(`apply_triage`, honouring `rules.triage.auto`), and answered needs-human issues,
which is an action class in its own right rather than a selection detail — plus
the seam they all need: the selector's kind vocabulary, the provider registry, and
the spend ledger that makes `--max-tokens` enforce a real number.

**The findings classes moved out of this gate** — see the sizing decision below.

**Gate 3 — the agent diagnoses and autofixes findings.** Two providers over the
monitoring surface: findings-diagnose (`diagnose_cli`, which renders a body but
neither produces the analysis nor posts it, so the provider supplies both halves)
and findings-autofix (`run_autofix`), plus the seam they share — two more item
kinds and their ranking, and the reader that turns a finding issue into the
`(monitoring_config, component)` pair `run_autofix` requires. Drafted by
`G2-PLAN` on 2026-08-11; see `GATE-03-REVIEW.md`.

**Gate 4 — the agent advances features.** The feature provider reads the queue
top, invokes `specfuse run` **as a subprocess** — never in-process, per D1 and
the live hazards in #757 and #1040 — classifies the driver's halt, escalates on
`awaiting_review`, and switches to the next workable item. Blocked items park
with an escalation; a drafting-needed top escalates per the scope boundary.

**Sizing risk — resolved by `G1-PLAN`, 2026-08-11: split.** Drafting gate 2
against the shipped conductor grew it from five sketched items to seven real work
units, and showed that the two findings classes are the ones that cannot be
exercised against this repository at all. Findings therefore become their own
gate, ahead of the features gate; the evidence is in `GATE-02-REVIEW.md` §
"The sizing decision". Gate 2 as drafted here is the remainder: the provider seam
plus bugs, triage, and answered escalations.

**The insertion was made by `G2-PLAN` on 2026-08-11.** Gate 3 is the findings
gate; the features gate and its terminal `close` moved to gate 4, with the close
WU renumbered `G3-CLOSE` → `G4-CLOSE` and renamed `WU-92-gate-3-close.md` →
`WU-92-gate-4-close.md`. No `done` work unit and no `passed` gate file was
rewritten to do it: the only two files touched by the renumbering were the
features gate (`open`) and its close placeholder (`draft`), neither of which had
ever been dispatched. The gate map and the plan of record now both read four
gates.

## Notes

- Dependencies live here, not in WU frontmatter: a dispatched session never needs
  to know its own dependencies — they are satisfied by the time the driver hands
  it the file.
- WU file numbers track the correlation sub-ID where it exists (`WU-01` ↔ `/T01`).
  Closing units use a reserved high range (90+) so they sort last.
- T01 is the only work unit in gate 1 that touches `specfuse/loop/`, and is
  therefore the only one that halts the driver for a restart.
