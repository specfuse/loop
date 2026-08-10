---
feature_id: FEAT-2026-0044
title: agent-policy.yml schema + groom-backlog skill
slug: agent-policy-schema
branch: feat/FEAT-2026-0044-agent-policy-schema
roadmap_goal: Give the operator's priorities one auditable, versioned surface — an ordered queue, class rules, budgets, and escalation config the agent reads instead of guessing — plus the periodic ritual that keeps it fed as the backlog evolves.
autonomy_default: auto
status: active
planned_cost_usd: 19.00
---

# Plan: agent-policy.yml schema + groom-backlog skill

**Priority is policy, not intelligence.** The specfuse-agent
([FEAT-2026-0049](../../roadmap.md#feat-2026-0049)) selects work *within* a
declared policy and escalates ties; it never guesses intent. This feature ships
the file that policy lives in, the validator that keeps it honest, and the
grooming ritual that keeps it current.

It is drafted **solo, without an operator interview** (operator instruction,
2026-08-09 — see § *Assumed decisions* below). Every decision a `/draft-feature`
interview would have asked is recorded there with the option taken, so the
operator can veto any of them at PR review before
[FEAT-2026-0048](../../roadmap.md#feat-2026-0048) builds on the schema.

## Scope boundary

**IN.** The `.specfuse/agent-policy.yml` schema and its structural validator; a
reader API; queue-vs-roadmap drift validation; wiring the one dial already
waiting on this file (`apply_triage`'s `auto=`); the `/groom-backlog` skill; and
this repo's own bootstrapped policy file (dogfood).

**OUT — the agent runner itself.** FEAT-2026-0049 consumes this file. This
feature ships no scheduler, no queue execution, no lock.

**OUT — the `bug_automerge` dial and the bug-lane guardrails.**
FEAT-2026-0048 owns them and extends this schema with its own block. The
`bugs:` class-rule block ships here with `preempt`, `min_severity`, and
`automerge` keys because the roadmap row names them; the *enforcement* behind
`automerge` is 0048's.

**OUT — the scoring formula.** FEAT-2026-0011 owns ranking and is `blocked` on
ADR-0002. The queue here is an **explicitly ordered list the operator writes**,
not a computed ranking. When 0011 lands, `/groom-backlog` can propose an order
from the score; the file format does not change.

**OUT — per-component dials.** `monitoring.yml` owns those, and inbound issues
are not components. This boundary was already assessed and settled by
FEAT-2026-0045's retrospective; it is restated here only because the two files
now sit adjacent and the temptation to merge them is real.

## Assumed decisions (drafted without an interview — operator veto at PR review)

Every one of these is a decision question `/draft-feature` would have asked. The
option taken and its one-line reason are recorded so the veto is cheap.

1. **Single gate, single terminal `close`.** Four substantive WUs sits at the
   ceremony-proportionality threshold (`docs/methodology.md` §6). A single gate
   also means no unattended `plan-next` drafting at 3am, which matters because
   this feature runs autonomously overnight.
2. **`autonomy_default: auto`.** Consistent with the overnight run. Note it is
   close to a no-op on a single-gate feature — there is no next gate to arm —
   so the real autonomy here is that no WU boundary halts.
3. **Queue entries are FEAT-IDs only, not a heterogeneous work list.** Bugs are
   handled by class rule (`bugs.preempt`), not by queue position, so the queue
   stays a list of one kind of thing. Mixing issue numbers and FEAT-IDs would
   make every consumer disambiguate on every read.
4. **Queue drift severity is split WARN/ERROR, not uniformly fatal.** An entry
   naming a FEAT-ID absent from the roadmap is an ERROR (a typo or a deleted
   feature — unresolvable). An entry whose feature has gone `done` or
   `abandoned` is a WARN (normal backlog evolution — `/groom-backlog` cleans it).
   A uniformly-fatal check would go red on a correct tree the moment any feature
   completed, which is the unsatisfiable-predicate shape `planning-discipline.md`
   §2 exists to catch. Precedent: `roadmap_link_gate.py` makes exactly this split.
5. **Validator returns `list[str]` findings and is a sibling of, not a caller
   into, `lint_monitoring.py`.** Same shape, no shared helper — two validators
   over unrelated schemas sharing code couples them for no gain. This is the
   `[FEAT-2026-0072/T01]` precedent applied again.
6. **This repo bootstraps a real `.specfuse/agent-policy.yml`,** and the CI gate
   points at it rather than at an example-only file. Unlike `monitoring.yml`
   (which this repo can never have — no deployable components), a roadmap and a
   queue genuinely exist here, so a live file has real signal. An example file
   ships too, for target projects.
7. **`/groom-backlog` proposes and writes only on explicit accept**, matching
   `/pick-feature` and `derive-monitoring`. It is not given an `--auto` mode:
   nothing in the roadmap row asks for one, and an unattended process rewriting
   the operator's own priority declaration inverts the point of the file.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep commands run:**
  - `grep -rl "agent-policy" --include='*.py' --include='*.md' --include='*.yml' .`
  - `grep -n "^def \|^class \|^[A-Z_]* =" specfuse/loop/lint_monitoring.py`
  - `grep -n "def .*roadmap\|def _parse_table_rows" specfuse/loop/lint_roadmap.py`
  - `grep -n "def apply_triage" -A6 specfuse/loop/triage.py`
  - `grep -n "^def \|^class " specfuse/loop/escalation.py`
- **Verdict:** `no existing mechanism for the policy file itself, building new — three surrounding mechanisms found and reused rather than rebuilt.`

The first grep returns only roadmap prose: no schema, no reader, no validator
exists. The rest each returned a mechanism this feature must **not** duplicate:

| Surface this feature needs | Existing mechanism | Verdict |
|---|---|---|
| Structural validator returning findings | `lint_monitoring.py::validate_monitoring(path) -> list[str]` (line 91) | **reuse the shape**, not the code — T01 |
| Reading a FEAT-ID's status from the roadmap | `lint_roadmap.py::_parse_table_rows(lines) -> list` (line 276) | **import and call** — T02 |
| The triage `auto` dial to wire | `triage.py::apply_triage(runner, repo, decisions, *, auto=False)` (line 126) | **supply the value; do not redesign the semantics** — T03 |
| Escalating drift to a human | `escalation.py::emit_escalation(...)` (line 185), FEAT-2026-0046 | **out of scope here** — the validator reports findings; FEAT-2026-0049 decides when a finding escalates |

**Roadmap-row verb check** (`[FEAT-2026-0045/G1-CLOSE/verb-check-table-earns-its-cost]`).
The row's four load-bearing verbs, each grepped:

| Verb from the row | Mechanism it assumes | Backed? |
|---|---|---|
| "validated against the roadmap every agent run" | a roadmap-status reader | **yes** — `_parse_table_rows` |
| "drift escalates, never guessed around" | an escalation contract | **yes** — `emit_escalation`, 0046 shipped |
| "reads … open triaged issues" | triage state on issues | **yes** — `triage.py` marker-first writes |
| "per-candidate trade-offs in the pick-feature style" | the `/pick-feature` output shape | **yes** — skill exists, shape is copyable |

4/4 backed. No unbuilt-mechanism assumption in this row, unlike FEAT-2026-0042's.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the validator report on an input already in its intended final
  state?** **Zero** — but only under the WARN/ERROR split in assumed decision 4.

This is the sharp part, and it is the same trap FEAT-2026-0072 hit. This repo's
bootstrapped queue will name features that *complete*. If "queue entry is not
`planned`/`active`/`blocked`" were an ERROR, the CI gate would go red the first
time any queued feature reached `done` — firing on a correct tree, with the
"fix" being to mutate the operator's priority file to satisfy a linter. So:

- **ERROR** — queue entry names a FEAT-ID with no row in `roadmap.md`. Every
  feature row lives there, including `done` and `abandoned` ones
  (`roadmap-archive.md` holds only detail *sections*), so an ID absent from it
  genuinely does not exist. Unresolvable; a human must fix it.
- **WARN** — queue entry names a feature that is `done` or `abandoned`. Normal
  evolution; `/groom-backlog` proposes its removal. Prints, does not fail.
- **ERROR** — any structural violation (unknown key, wrong type, dial value
  outside its enum, duplicate queue entry).

On the file this feature ships, all three report zero.

## Task graph

```yaml
# Single terminal gate: 4 substantive WUs, at the ceremony-proportionality
# threshold (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0044/T01
        file: WU-01-agent-policy-schema-validator.md
        depends_on: []
      - id: FEAT-2026-0044/T02
        file: WU-02-policy-reader-and-queue-drift.md
        depends_on: [FEAT-2026-0044/T01]
      - id: FEAT-2026-0044/T03
        file: WU-03-wire-triage-auto-dial.md
        depends_on: [FEAT-2026-0044/T02]
      - id: FEAT-2026-0044/T04
        file: WU-04-groom-backlog-skill.md
        depends_on: [FEAT-2026-0044/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0044/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0044/T01
          - FEAT-2026-0044/T02
          - FEAT-2026-0044/T03
          - FEAT-2026-0044/T04
```

T01 is the foundation: it names every load-bearing string (file path, top-level
keys, dial enums) that T02–T04 consume as exact-match literals, per
`[FEAT-2026-0010/G1]`. T03 and T04 are independent of each other and both depend
on T02's reader — neither re-implements policy parsing.

## Notes

- **Load-bearing strings are fixed in T01 and quoted verbatim downstream.** The
  canonical path is `.specfuse/agent-policy.yml`; the module is
  `specfuse/loop/agent_policy.py`; the validator entry point is
  `validate_agent_policy(path) -> list[str]`; the reader is
  `load_policy(path) -> dict`. Every dependent WU repeats these literally rather
  than inferring them from the diff.
- **T04 ships a skill, not a batch mode.** Per `[FEAT-2026-0010/G1]`'s
  downstream-use rule, its Context states explicitly that no WU in this gate
  subprocess-invokes it — the dogfood queue in T02 is written by direct file
  authoring, because the skill's whole contract is that a human accepts its
  proposal.
- A new gate entry lands in `.specfuse/verification.yml`; `tests/` additions are
  Python unit tests only, so no new bats suite and no
  `tests/test_bats_suites_gated.py` interaction.
